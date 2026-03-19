---
name: media-test
description: Write mock camera, upload tests, and guard tests for the media domain
---

# media-test - Media Domain Test

Writes mock camera, upload tests, and guard tests. Sixth in the media domain chain (6/6).

## Usage
```
/media-test
```

## Parameters
- None. This skill consumes all prior media domain outputs and produces test artifacts.

## What It Does
1. Writes **unit tests** for media logic (validators, guards, compression)
2. Provides **mock camera** — fake image capture for testing
3. Writes **upload tests** — progress, retry, cancellation
4. Writes **guard tests** — file size, format, EXIF stripping
5. Achieves **>80% coverage** for media domain code
6. Uses `mocktail` or `mockito` for mocking; `flutter_test` for widget/integration tests

## Output
- `media_repository_test.dart` — Unit tests for MediaRepository
- `media_notifier_test.dart` — Unit tests for MediaNotifier
- `file_size_guard_test.dart` — FileSizeGuard tests
- `format_guard_test.dart` — FormatGuard tests
- `mock_camera_data_source.dart` — Mock camera for tests

## What It Must NOT Do
- Call other agents or use the Task tool (emit `REQUEST:` if delegation needed)
- Write implementation code (schema, provider, flow, guard, UI)
- Write production media logic
- Modify existing implementation files except to add testability hooks if strictly required

## Tech Stack
- **Testing:** flutter_test, mocktail or mockito
- **Backend Mock:** Mock Supabase Storage client
- **State Mock:** Mock Riverpod overrides
- **Architecture:** Clean Architecture (test layer mirrors domain structure)
- **Domain:** media (TaskSpec domain)
