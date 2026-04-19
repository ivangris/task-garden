# Providers

## Overview

Task Garden uses provider interfaces so AI and infrastructure backends can be swapped without changing domain logic.

Providers should be runtime-selectable through settings.

## Principles

- local providers must be supported first
- cloud providers must be optional
- provider failures must not destroy user data
- provider responses must be normalized into shared schemas
- providers must not write directly to the database

## Provider categories

### STTProvider
Used for audio transcription.

#### Responsibilities
- transcribe file/blob input
- optionally support streaming transcription
- normalize output into shared transcript result format

#### Implementations
- `WhisperCppSTTProvider`
- `OpenAITranscriptionProvider`

### TaskExtractionProvider
Used for:
- task extraction
- optional weekly planning note generation
- optional recap narrative generation

#### Implementations
- `OllamaExtractionProvider`
- `OpenAIExtractionProvider`

### SyncProvider
Used for local-only mode or future multi-device sync.

#### Implementations
- `LocalOnlySyncProvider`
- `RemoteApiSyncProvider`

### AuthProvider
Used only once hosted sync is enabled.

#### Implementations
- `NoAuthProvider`
- future hosted auth provider

## STTProvider contract

### Input
- audio file or blob
- optional transcription options

### Output
- transcript text
- optional segments
- provider metadata
- model metadata

## TaskExtractionProvider contract

### Input
- raw entry or transcript text
- optional context
- schema version
- prompt version

### Output
- normalized extraction batch
- structured candidates
- summary
- open questions

### Important
Task extraction providers should return structured data matching the repository schema expectations.

## Configuration

Provider configuration should support:

- provider selection
- base URL for compatible providers
- model name
- local model path or executable path where relevant
- API key where relevant
- timeout settings
- local-only mode
- cloud-enabled toggle

## Defaults

### Default STT
Local provider

### Default extraction
Local provider

### Default sync
Local-only provider

## Provider selection behavior

If local-only mode is enabled:
- local providers only
- cloud providers hidden or disabled

If cloud mode is enabled:
- provider selection may include cloud options
- settings must clearly show which provider is active

## Security

- never hardcode API keys
- do not expose server-side secrets to the frontend
- treat cloud usage as opt-in
- sanitize provider errors before displaying them to the user

## Failure behavior

### If transcription fails
- preserve audio metadata
- preserve raw entry shell
- allow retry
- allow manual text fallback

### If extraction fails
- preserve raw entry
- preserve transcript if present
- allow retry
- allow manual task creation

### If narrative generation fails
- recap metrics should still be viewable
- narrative can be omitted or retried later

## Testing expectations

Test:
- normalization of each provider response
- provider switching
- config fallback behavior
- disabled-by-default cloud behavior
- extraction schema validation