# Translation service

Standalone translation-only service that owns local Transformers/Torch model loading and subtitle line translation.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
cp .env.example .env
```

## Run

```bash
python -m window_transcribe_translation_service --warmup
```

## Endpoints

- `GET /health`
- `GET /providers`
- `POST /warmup`
- `POST /translate`

`POST /translate` accepts either raw `lines` or timestamped `segments`, uses the local Transformers pipeline for translation, and returns the same number of translated items that it received.
