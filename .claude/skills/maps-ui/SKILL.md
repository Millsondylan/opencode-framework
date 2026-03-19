---
name: maps-ui
description: Implement MapScreen, place details, and directions for the maps domain
---

# maps-ui - Maps Domain UI

Implements MapScreen, place details, and directions. Fourth in the maps domain chain (4/6).

## Usage
```
/maps-ui
```

## Parameters
- None. This skill consumes maps-flow outputs and produces UI artifacts.

## What It Does
1. Implements **MapScreen** — map widget, markers, user location
2. Implements **PlaceDetailsSheet** — bottom sheet with place info
3. Implements **DirectionsView** — route display, steps, ETA
4. Implements **PlaceSearchBar** — search input, suggestions
5. Handles **permission states** — request, denied, granted
6. Uses **Material 3** — components, theming, typography

## Output
- `map_screen.dart` — MapScreen widget
- `place_details_sheet.dart` — PlaceDetailsSheet widget
- `directions_view.dart` — DirectionsView widget
- `place_search_bar.dart` — PlaceSearchBar widget

## What It Must NOT Do
- Call other agents or use the Task tool (emit `REQUEST:` if delegation needed)
- Write schema/entity/DTO code (maps-schema responsibility)
- Write repository or data source code (maps-provider responsibility)
- Write flow/state orchestration (maps-flow responsibility)
- Write route guards or middleware
- Write tests

## Tech Stack
- **UI:** Material 3 (Flutter), google_maps_flutter or mapbox_gl
- **State:** Riverpod (read mapsProvider, call MapsNotifier methods)
- **Architecture:** Clean Architecture (presentation layer)
- **Domain:** maps (TaskSpec domain)
