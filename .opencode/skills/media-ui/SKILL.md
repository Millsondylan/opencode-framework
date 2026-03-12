---
name: media-ui
description: Implement CameraScreen, GalleryPicker, and upload progress UI for the media domain
---

# media-ui - Media Domain UI

Implements CameraScreen, GalleryPicker, and upload progress UI. Fourth in the media domain chain (4/6).

## Usage
```
/media-ui
```

## Parameters
- None. This skill consumes media-flow outputs and produces UI artifacts.

## What It Does
1. Implements **CameraScreen** — live camera preview, capture button
2. Implements **GalleryPicker** — grid/list, multi-select, permissions
3. Implements **UploadProgressWidget** — progress bar, cancel, retry
4. Implements **MediaPreview** — thumbnail, full-screen preview
5. Handles **error states** — snackbars, banners, inline messages
6. Uses **Material 3** — components, theming, typography

## Output
- `camera_screen.dart` — CameraScreen widget
- `gallery_picker.dart` — GalleryPicker widget
- `upload_progress_widget.dart` — UploadProgressWidget
- `media_preview.dart` — MediaPreview widget

## What It Must NOT Do
- Call other agents or use the Task tool (emit `REQUEST:` if delegation needed)
- Write schema/entity/DTO code (media-schema responsibility)
- Write repository or data source code (media-provider responsibility)
- Write flow/state orchestration (media-flow responsibility)
- Write route guards or middleware
- Write tests

## Tech Stack
- **UI:** Material 3 (Flutter)
- **State:** Riverpod (read mediaProvider, call MediaNotifier methods)
- **Architecture:** Clean Architecture (presentation layer)
- **Domain:** media (TaskSpec domain)
