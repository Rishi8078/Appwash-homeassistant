# API discovery tools

Experimental, read-only scripts used to map the current AppWash / Miele MOVE
API. They are **not** part of the Home Assistant integration: nothing under
`tools/` is imported at runtime and none of it is a dependency of the
component.

## Contents

- `appwash_api_finder_v2.py` — logs in through the Cognito hosted UI and probes
  the documented endpoints with GET requests only. It never mutates data and
  never enumerates UUIDs.
- `v2_report.md` — the report produced by the run that the current integration
  is based on. It is the source of truth for the endpoints and response shapes
  implemented in `api.py` / `models.py`.

## Running

```bash
pip install requests beautifulsoup4 python-dotenv
# credentials are read from a local .env file, never committed
printf 'APPWASH_EMAIL=you@example.com\nAPPWASH_PASSWORD=...\n' > .env
python tools/appwash_api_finder_v2.py
```
