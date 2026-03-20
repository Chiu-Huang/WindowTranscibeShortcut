# Transcribe service

Standalone ASR-only service that owns WhisperX model loading and transcript generation.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
cp .env.example .env
```

## Run

```bash
./entrypoint.sh --warmup
```

## Endpoints

- `GET /health`
- `POST /warmup`
- `POST /transcribe`

The service returns only ASR output and metadata. It does not perform translation or subtitle writing.
