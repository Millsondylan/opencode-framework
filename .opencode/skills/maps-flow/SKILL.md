---
name: maps-flow
description: Implement location tracking, place search, and route for the maps domain
---

# maps-flow - Maps Domain Flow

Implements location tracking, place search, and route. Third in the maps domain chain (3/6).

## Usage
```
/maps-flow
```

## Parameters
- None. This skill consumes maps-schema and maps-provider outputs and produces flow artifacts.

## What It Does
1. Implements **MapsNotifier** — Riverpod StateNotifier for maps state
2. Defines **MapsState** — location, places, route, loading, error
3. Registers **mapsProvider**, **locationProvider**, **placeProvider**
4. Orchestrates **location tracking** — start, stop, stream
5. Orchestrates **place search** — query, results, select
6. Orchestrates **route** — calculate, display, navigate
7. Handles **geofence events** — enter, exit callbacks

## Output
- `maps_notifier.dart` — MapsNotifier (StateNotifier<MapsState>)
- `maps_state.dart` — MapsState sealed class / union type
- `maps_provider.dart` — mapsProvider (Riverpod Provider)

## What It Must NOT Do
- Call other agents or use the Task tool (emit `REQUEST:` if delegation needed)
- Write schema/entity/DTO code (maps-schema responsibility)
- Write repository or data source code (maps-provider responsibility)
- Write UI components or screens (maps-ui responsibility)
- Write route guards or middleware
- Write tests

## Tech Stack
- **State:** Riverpod (StateNotifier, Provider)
- **Backend:** Google Maps/Mapbox (via maps-provider repository)
- **Architecture:** Clean Architecture (presentation/application layer)
- **Domain:** maps (TaskSpec domain)
