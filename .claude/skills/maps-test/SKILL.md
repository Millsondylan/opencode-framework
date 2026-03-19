---
name: maps-test
description: Write mock location and geofence tests for the maps domain
---

# maps-test - Maps Domain Test

Writes mock location and geofence tests. Sixth in the maps domain chain (6/6).

## Usage
```
/maps-test
```

## Parameters
- None. This skill consumes all prior maps domain outputs and produces test artifacts.

## What It Does
1. Writes **unit tests** for maps logic (validators, guards, geofence)
2. Provides **mock location** — fake GPS position for testing
3. Writes **geofence tests** — enter, exit, boundary
4. Writes **geocoding tests** — search, reverse geocode
5. Achieves **>80% coverage** for maps domain code
6. Uses `mocktail` or `mockito` for mocking; `flutter_test` for widget/integration tests

## Output
- `maps_repository_test.dart` — Unit tests for MapsRepository
- `maps_notifier_test.dart` — Unit tests for MapsNotifier
- `geofence_test.dart` — Geofence tests
- `mock_location_data_source.dart` — Mock location for tests

## What It Must NOT Do
- Call other agents or use the Task tool (emit `REQUEST:` if delegation needed)
- Write implementation code (schema, provider, flow, guard, UI)
- Write production maps logic
- Modify existing implementation files except to add testability hooks if strictly required

## Tech Stack
- **Testing:** flutter_test, mocktail or mockito
- **Backend Mock:** Mock Google Maps/Mapbox client
- **State Mock:** Mock Riverpod overrides
- **Architecture:** Clean Architecture (test layer mirrors domain structure)
- **Domain:** maps (TaskSpec domain)
