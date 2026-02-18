# endpoints

Public repo for shared endpoint config used by llm-api-proxy and other consumers.

## remote-machine-endpoints.toml

Stores dynamic ngrok base URLs per machine (e.g. LM Studio exposed via ngrok).  
**Updated by llm-api-proxy** from `config/remote-machine-endpoints.toml` via:

```bash
cd llm-api-proxy && make publish-remote-endpoints
```

Consumers can use the raw file URL (e.g. GitHub raw or GitLab) or download it:

- **llm-api-proxy**: `make fetch-remote-endpoints` downloads this file into `config/remote-machine-endpoints.toml`, or set `REMOTE_MACHINE_ENDPOINTS_URL` to the public URL to load it directly.
- **Any Makefile/task**: Download the TOML from the public URL and reuse (e.g. `curl -sL $(REMOTE_MACHINE_ENDPOINTS_URL) -o config/remote-machine-endpoints.toml`).