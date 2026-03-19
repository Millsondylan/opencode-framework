---
name: maps-schema
description: Define location, geofence, place, and type IDs 130–139 for the maps domain
---

# maps-schema - Maps Domain Schema

Defines location, geofence, place, and maps state types for the maps domain. First in the maps domain chain (1/6).

## Usage
```
/maps-schema
```

## Parameters
- None. This skill produces schema artifacts for the maps domain.

## What It Does
1. Defines **Location** entity with Hive persistence (`@HiveType` typeId: 130)
2. Defines **Geofence** model with Hive persistence (typeId: 131)
3. Defines **Place** model with Hive persistence (typeId: 132)
4. Creates **LocationDTO**, **PlaceDTO** for API/transport layer
5. Creates **LocationValidator** for input validation
6. Defines location types (point, region, route)

## Output
- `location.dart` — Location model with `@HiveType(typeId: 130)`
- `geofence.dart` — Geofence model with `@HiveType(typeId: 131)`
- `place.dart` — Place model with `@HiveType(typeId: 132)`
- `location_dto.dart` — Location DTO for API/transport
- `place_dto.dart` — Place DTO for API/transport
- `location_validator.dart` — Location input validation

## What It Must NOT Do
- Call other agents or use the Task tool (emit `REQUEST:` if delegation needed)
- Write repository code
- Write state management (Riverpod providers)
- Write UI components
- Write tests

## Tech Stack
- **Persistence:** Hive (local storage)
- **Architecture:** Clean Architecture (domain/entity layer)
- **Domain:** maps (TaskSpec domain)
