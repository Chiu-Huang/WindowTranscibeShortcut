from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ContractModel(BaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)


class JobMetadata(ContractModel):
    preset: str | None = Field(default=None, description='Selected job preset or profile name.')
    job_name: str | None = Field(default=None, description='Human-readable job label.')
    job_id: str | None = Field(default=None, description='Caller-supplied correlation id.')
    labels: dict[str, str] = Field(default_factory=dict, description='Arbitrary job labels.')


class SubtitleSegment(ContractModel):
    start: float = Field(ge=0, description='Segment start time in seconds.')
    end: float = Field(ge=0, description='Segment end time in seconds.')
    text: str = Field(min_length=1, description='Segment text payload.')

    @model_validator(mode='after')
    def validate_time_range(self) -> 'SubtitleSegment':
        if self.end < self.start:
            raise ValueError('Segment end timestamp must be greater than or equal to start timestamp.')
        return self


class TranslatedSubtitleSegment(SubtitleSegment):
    original_text: str | None = Field(
        default=None,
        description='Optional original text that was translated into the segment text.',
    )


class RawTranscriptMetadata(ContractModel):
    provider: str = Field(description='ASR provider identifier.')
    input_file_path: Path = Field(description='Input media path resolved by the transcription service.')
    segment_count: int = Field(ge=0, description='Number of transcript segments in order.')
    language_hint: str | None = Field(default=None, description='Optional source language hint supplied by the caller.')
    model_name: str | None = Field(default=None, description='Underlying model identifier.')
    output_subtitle_path: Path | None = Field(
        default=None,
        description='Subtitle output path when the orchestration flow has already written subtitles.',
    )


class TranscribeRequest(ContractModel):
    input_file_path: Path = Field(description='Absolute or relative media path visible to the transcription service.')
    source_language_hint: str | None = Field(default=None, description='Optional source language hint.')
    metadata: JobMetadata = Field(default_factory=JobMetadata, description='Preset and caller job metadata.')


class TranscribeResponse(ContractModel):
    detected_language: str = Field(description='Language detected or inferred by the ASR service.')
    segments: list[SubtitleSegment] = Field(default_factory=list, description='Ordered transcript segments.')
    raw_transcript_metadata: RawTranscriptMetadata = Field(description='Raw transcript metadata from the ASR stage.')

    @model_validator(mode='after')
    def validate_segment_count(self) -> 'TranscribeResponse':
        if self.raw_transcript_metadata.segment_count != len(self.segments):
            raise ValueError('Raw transcript metadata segment_count must match the number of segments.')
        return self


class TranslateRequest(ContractModel):
    lines: list[str] | None = Field(default=None, description='Plain text lines to translate in order.')
    segments: list[SubtitleSegment] | None = Field(
        default=None,
        description='Subtitle segments to translate while preserving timestamps.',
    )
    source_language: str = Field(description='Source language code.')
    target_language: str = Field(description='Target language code.')

    @model_validator(mode='after')
    def validate_input_variant(self) -> 'TranslateRequest':
        has_lines = self.lines is not None
        has_segments = self.segments is not None
        if has_lines == has_segments:
            raise ValueError('Provide exactly one of lines or segments.')
        if self.lines is not None and not self.lines:
            raise ValueError('lines must not be empty when provided.')
        if self.segments is not None and not self.segments:
            raise ValueError('segments must not be empty when provided.')
        return self

    @property
    def item_count(self) -> int:
        return len(self.lines) if self.lines is not None else len(self.segments or [])


class TranslateResponse(ContractModel):
    translated_lines: list[str] | None = Field(default=None, description='Translated lines in input order.')
    translated_segments: list[TranslatedSubtitleSegment] | None = Field(
        default=None,
        description='Translated subtitle segments in input order.',
    )
    requested_count: int = Field(ge=0, description='Number of requested items.')
    translated_count: int = Field(ge=0, description='Number of translated items returned.')

    @model_validator(mode='after')
    def validate_counts(self) -> 'TranslateResponse':
        has_lines = self.translated_lines is not None
        has_segments = self.translated_segments is not None
        if has_lines == has_segments:
            raise ValueError('Provide exactly one of translated_lines or translated_segments.')
        actual_count = len(self.translated_lines) if self.translated_lines is not None else len(self.translated_segments or [])
        if self.requested_count != self.translated_count:
            raise ValueError('requested_count must match translated_count.')
        if actual_count != self.translated_count:
            raise ValueError('translated_count must match the number of translated items.')
        return self


class ServiceStageStatus(ContractModel):
    stage: Literal['transcription', 'translation', 'subtitle_write'] = Field(description='Pipeline stage name.')
    status: Literal['pending', 'skipped', 'completed', 'failed'] = Field(description='Stage outcome.')
    detail: str | None = Field(default=None, description='Optional status detail.')


class ErrorDetail(ContractModel):
    stage: str = Field(description='Stage that raised the error.')
    message: str = Field(description='Human-readable error message.')
    error_type: str | None = Field(default=None, description='Error class or category.')


class OrchestratorJobResponse(ContractModel):
    status: Literal['completed', 'failed'] = Field(description='Overall orchestration status.')
    output_subtitle_path: Path | None = Field(default=None, description='Resolved subtitle output path.')
    stages: list[ServiceStageStatus] = Field(default_factory=list, description='Per-stage status details.')
    transcription: TranscribeResponse | None = Field(default=None, description='Transcription payload when available.')
    error: ErrorDetail | None = Field(default=None, description='Structured error details when orchestration fails.')
