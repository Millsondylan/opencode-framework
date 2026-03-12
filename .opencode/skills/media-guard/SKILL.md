---
name: media-guard
description: Implement file size limits, format validation, and EXIF stripping for the media domain
---

# media-guard - Media Domain Guard

Implements file size limits, format validation, and EXIF stripping. Fifth in the media domain chain (5/6).

## Usage
```
/media-guard
```

## Parameters
- None. This skill consumes media-schema and media-provider outputs and produces guard artifacts.

## What It Does
1. Implements **FileSizeGuard** — validates file size before upload
2. Implements **FormatGuard** — validates allowed formats (JPEG, PNG, etc.)
3. Implements **ExifStripper** — removes EXIF metadata from images
4. Integrates with Riverpod media state for guard decisions
5. Handles **rejection** — user feedback when guard fails

## Output
- `file_size_guard.dart` — FileSizeGuard for size validation
- `format_guard.dart` — FormatGuard for format validation
- `exif_stripper.dart` — ExifStripper for metadata removal

## What It Must NOT Do
- Call other agents or use the Task tool (emit `REQUEST:` if delegation needed)
- Write schema/entity/DTO code (media-schema responsibility)
- Write provider/repository code (media-provider responsibility)
- Write flow/state orchestration (media-flow responsibility)
- Write UI components or screens
- Write tests (media-test responsibility)

## Tech Stack
- **State:** Riverpod (reads media state for guard decisions)
- **Architecture:** Clean Architecture (guard layer)
- **Domain:** media (TaskSpec domain)
