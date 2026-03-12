---
name: maps-provider
description: Implement Google Maps/Mapbox and geocoding for the maps domain
---

# maps-provider - Maps Domain Provider

Implements Google Maps/Mapbox integration and geocoding. Second in the maps domain chain (2/6).

## Usage
```
/maps-provider
```

## Parameters
- None. This skill consumes maps-schema outputs and produces provider artifacts.

## What It Does
1. Implements **MapsRepository** — domain-facing repository interface
2. Implements **LocationDataSource** — device GPS, position stream
3. Implements **GeocodingDataSource** — reverse geocode, place search
4. Implements **MapsRemoteDataSource** — Google Maps/Mapbox API client
5. Handles **geofence monitoring** — enter/exit events
6. Handles **route calculation** — directions, ETA

## Output
- `maps_repository.dart` — MapsRepository implementation
- `location_data_source.dart` — Device location/GPS
- `geocoding_data_source.dart` — Geocoding API client
- `maps_remote_data_source.dart` — Google Maps/Mapbox client

## What It Must NOT Do
- Call other agents or use the Task tool (emit `REQUEST:` if delegation needed)
- Write schema/entity/DTO code (maps-schema responsibility)
- Write flow/state orchestration (maps-flow responsibility)
- Write UI components
- Write tests

## Tech Stack
- **Backend:** Google Maps / Mapbox
- **Plugins:** geolocator, geocoding
- **State:** Riverpod (provider registration only, not flow logic)
- **Architecture:** Clean Architecture (data layer)
- **Domain:** maps (TaskSpec domain)
