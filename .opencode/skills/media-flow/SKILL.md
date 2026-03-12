---
name: media-flow
description: Implement capture flow, upload progress, and retry logic for the media domain
---

# media-flow - Media Domain Flow

Implements capture flow, upload progress, and retry logic. Third in the media domain chain (3/6).

## Usage
```
/media-flow
```

## Parameters
- None. This skill consumes media-schema and media-provider outputs and produces flow artifacts.

## What It Does
1. Implements **MediaNotifier** — Riverpod StateNotifier for media state
2. Defines **MediaState** — idle, capturing, uploading, error, completed
3. Registers **mediaProvider** — Riverpod provider exposing MediaNotifier
4. Orchestrates **capture flow** — camera/gallery → validate → compress
5. Orchestrates **upload flow** — progress tracking, retry on failure
6. Handles **retry logic** — exponential backoff, max retries
7. Manages **media list** — cache, refresh, delete

## Output
- `media_notifier.dart` — MediaNotifier (StateNotifier<MediaState>)
- `media_state.dart` — MediaState sealed class / union type
- `media_provider.dart` — mediaProvider (Riverpod Provider)

## What It Must NOT Do
- Call other agents or use the Task tool (emit `REQUEST:` if delegation needed)
- Write schema/entity/DTO code (media-schema responsibility)
- Write repository or data source code (media-provider responsibility)
- Write UI components or screens (media-ui responsibility)
- Write route guards or middleware
- Write tests

## Tech Stack
- **State:** Riverpod (StateNotifier, Provider)
- **Backend:** Supabase Storage (via media-provider repository)
- **Architecture:** Clean Architecture (presentation/application layer)
- **Domain:** media (TaskSpec domain)
