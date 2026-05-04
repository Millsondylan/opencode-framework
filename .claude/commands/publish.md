---
description: "Run release candidate packaging and publish to Play and Chrome Web Store tracks"
---

# /publish

Package a release candidate and upload it to the configured store tracks. `/publish` assumes the pipeline has already produced a green `decide-agent` COMPLETE; it does not run build or test stages. It invokes `publishing/play/release.py` for Play API v3 uploads and the Chrome automator for Chrome Web Store listings, per ADR-0019.

## Arguments

- `<project>`: project directory (defaults to current working directory).
- `--track <track>`: Play track, one of `internal`, `closed`, `open`, `production`. Defaults to `internal` for safety.
- `--rollout <percent>`: staged rollout percentage for production (1, 5, 10, 20, 50, 100). Ignored on non-production tracks.
- `--chrome`: also push the Chrome Web Store listing via the automator.
- `--dry-run`: validate credentials, manifest, and AAB without uploading.

## Pipeline

Runs the publish-only track:

1. release-candidate packaging (signed AAB build, obfuscation, debug symbol split per ADR-0021)
2. release-manifest validation (version codes, tracks, release notes, changelog)
3. Play Developer API v3 upload to the selected track
4. closed-testing gate enforcement when track is `production` (ADR-0020: 12 testers, 14 consecutive days)
5. staged rollout configuration on production
6. Chrome Web Store automator run (only when `--chrome` is set)
7. store listing sync (real UI screenshots inside Claude-generated frames per ADR-0022)

## Example

```
/publish --track internal
/publish ./apps/finance --track production --rollout 10
/publish --track production --rollout 100 --chrome
/publish --dry-run
```

## Related

- ADR-0019 (Play API v3 and Chrome automator split)
- ADR-0020 (closed testing 12 testers, 14 days)
- ADR-0021 (Android API 35, 16 KB pages, Play Billing v8.3.0+)
- ADR-0022 (real UI screenshots inside generated frames)
- ADR-0023 (Shorebird code push for Dart-only patches)
- `publishing/play/release.py` for the Play track implementation
- `/ship` for the end-to-end pipeline that calls `/publish` as its final phase
