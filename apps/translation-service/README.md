# Translation service

This app owns translation provider selection and all backend-specific configuration.

## Entrypoints

- Console script: `window-transcribe-translation-service-api`
- Module: `python -m window_transcribe_translation_service`

## Environment

Copy `.env.example` to `.env` inside `apps/translation-service/` and configure the providers you want to enable.

## API

- `GET /health`
- `GET /providers`
- `POST /translate`

`POST /translate` accepts either raw `lines` or timestamped `segments` and validates that the provider returns the same number of items that it received.
