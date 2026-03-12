---
name: media-provider
description: Implement camera/gallery access, upload, and compression for the media domain
---

# media-provider - Media Domain Provider

Implements camera/gallery access, upload to CDN, and compression. Second in the media domain chain (2/6).

## Usage
```
/media-provider
```

## Parameters
- None. This skill consumes media-schema outputs and produces provider artifacts.

## What It Does
1. Implements **MediaRepository** — domain-facing repository interface
2. Implements **CameraDataSource** — image_picker, camera plugin
3. Implements **GalleryDataSource** — gallery picker, multi-select
4. Implements **MediaUploadDataSource** — Supabase Storage or CDN upload
5. Implements **compression** — image resize, quality, format conversion
6. Handles **upload progress** — stream progress, cancellation

## Output
- `media_repository.dart` — MediaRepository implementation
- `camera_data_source.dart` — CameraDataSource (image_picker)
- `gallery_data_source.dart` — GalleryDataSource
- `media_upload_data_source.dart` — MediaUploadDataSource (Supabase Storage)
- Compression utilities

## What It Must NOT Do
- Call other agents or use the Task tool (emit `REQUEST:` if delegation needed)
- Write schema/entity/DTO code (media-schema responsibility)
- Write flow/state orchestration (media-flow responsibility)
- Write UI components
- Write tests

## Tech Stack
- **Backend:** Supabase Storage
- **Plugins:** image_picker, camera
- **State:** Riverpod (provider registration only, not flow logic)
- **Architecture:** Clean Architecture (data layer)
- **Domain:** media (TaskSpec domain)
