# Provider Plugin Framework

## Design rules

- Business logic never imports provider-specific code.
- Providers advertise datasets and licensing metadata.
- Health, quality, and confidence are separate measurements.
- Public-source licensing and commercial-use status are visible to administrators.
- Every execution records counts, timing, validation issues, quality, and confidence.
- Disabled providers cannot be run.
- The bundled demo provider exists only for development.

## Initial provider

`nfl.demo` supports the `TEAM` dataset and loads all 32 NFL teams.

## Admin APIs

- `GET /api/v1/admin/providers`
- `POST /api/v1/admin/providers/{provider_code}/enable`
- `POST /api/v1/admin/providers/{provider_code}/disable`
- `POST /api/v1/admin/providers/{provider_code}/run/{dataset}`
- `GET /api/v1/admin/providers/executions`
