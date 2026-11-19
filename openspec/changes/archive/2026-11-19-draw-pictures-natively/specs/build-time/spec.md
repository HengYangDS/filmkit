## REMOVED Requirements

### Requirement: A render's worker count is eight unless one is named for a measurement

**Reason**: a worker was a browser page that captured frames for one encoder. A native render starts no browser; it is divided into spans, each with its own encoder, which `native-picture` states with their count and the variable that names another for a measurement.

**Migration**: a measurement that set `FILMKIT_RENDER_WORKERS` sets `FILMKIT_RENDER_SPANS`. A receipt records `spans` where it recorded `workers`.
