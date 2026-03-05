# endpoints

Public repo for shared endpoint config used by llm-api-proxy and other consumers.

## model-type-endpoints.toml (preferred for app lookup)

Keyed by **model type**: `embedding`, `llm`, `rerank`, `visual`. Each section has `base_url`, optional `model`, optional `base_urls[]` for fallback. Consumers ask for a type (e.g. embedding) and get the endpoint; which machine serves it is irrelevant. Set `MODEL_TYPE_ENDPOINTS_FILE` or `MODEL_TYPE_ENDPOINTS_URL` to this file. Tokens stay in `~/.config/lmstudio-model-keys.toml` (model name → key). See workspace Cursor rule `model-type-endpoints-lookup` and `dotfiles/scripts/model_type_endpoints_lookup.py` for the contract and reference implementation.

## remote-machine-endpoints.toml

Stores dynamic ngrok base URLs per machine (e.g. LM Studio exposed via ngrok).  
**Updated by llm-api-proxy** from `config/remote-machine-endpoints.toml` via:

```bash
cd llm-api-proxy && make publish-remote-endpoints
```

Consumers can use the raw file URL (e.g. GitHub raw or GitLab) or download it:

- **llm-api-proxy**: `make fetch-remote-endpoints` downloads this file into `config/remote-machine-endpoints.toml`, or set `REMOTE_MACHINE_ENDPOINTS_URL` to the public URL to load it directly.
- **Any Makefile/task**: Download the TOML from the public URL and reuse (e.g. `curl -sL $(REMOTE_MACHINE_ENDPOINTS_URL) -o config/remote-machine-endpoints.toml`).