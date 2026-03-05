# endpoints

Public repo for shared endpoint config used by llm-api-proxy and other consumers.

## model-type-endpoints.toml (preferred for app lookup)

Keyed by **model type**: `embedding`, `llm`, `rerank`, `visual`. Each section has `base_url`, optional `model`, optional `base_urls[]` for fallback. Consumers ask for a type (e.g. embedding) and get the endpoint; which machine serves it is irrelevant. Tokens for model-type lookup: `~/.config/model-type-keys.toml` (sections = type or type-1, type-2, …; key = `model_key`). See workspace Cursor rule `model-type-endpoints-lookup`.

**Local lookup module:** `scripts/model_type_endpoints_lookup.py` (stdlib only: tomllib or tomli). Use in this repo or copy into others; no dependency on another workspace repo.

- `get_endpoint(model_type)` → `{ "base_url", "model" }` (from hardcoded URL; section order: type, type-1, type-2, …).
- `get_model_key(model_type)` → API key from `~/.config/model-type-keys.toml`, same section order.
- Optional: `get_working_endpoint(model_type, ...)` (probe `base_urls` and cache), `invalidate_working(model_type=None)`.

```bash
python3 scripts/model_type_endpoints_lookup.py get_endpoint llm
python3 scripts/model_type_endpoints_lookup.py get_model_key llm
```

## remote-machine-endpoints.toml

Stores dynamic ngrok base URLs per machine (e.g. LM Studio exposed via ngrok).  
**Updated by llm-api-proxy** from `config/remote-machine-endpoints.toml` via:

```bash
cd llm-api-proxy && make publish-remote-endpoints
```

Consumers can use the raw file URL (e.g. GitHub raw or GitLab) or download it:

- **llm-api-proxy**: `make fetch-remote-endpoints` downloads this file into `config/remote-machine-endpoints.toml`, or set `REMOTE_MACHINE_ENDPOINTS_URL` to the public URL to load it directly.
- **Any Makefile/task**: Download the TOML from the public URL and reuse (e.g. `curl -sL $(REMOTE_MACHINE_ENDPOINTS_URL) -o config/remote-machine-endpoints.toml`).