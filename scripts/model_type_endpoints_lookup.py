#!/usr/bin/env python3
"""
Model-type endpoint and token lookup. Option B: local implementation per repo.

- Endpoints: fetched from hardcoded URL (DeepSpringAI/endpoints main).
- Tokens: ~/.config/model-type-keys.toml, section key = model_key; same section order (type, type-1, type-2, ...).
- Stdlib only: tomllib (3.11+) or tomli fallback. No dependency on another workspace repo.
"""
from __future__ import annotations

import json
import urllib.request
from pathlib import Path
from typing import Any, Callable, Optional

# Hardcoded: public endpoints TOML (raw content URL)
MODEL_TYPE_ENDPOINTS_URL = "https://raw.githubusercontent.com/DeepSpringAI/endpoints/main/model-type-endpoints.toml"
# Hardcoded: token TOML path (section = type or type-n, key = model_key)
MODEL_TYPE_KEYS_PATH = Path.home() / ".config" / "model-type-keys.toml"

MODEL_TYPES = ("embedding", "llm", "rerank", "visual")

try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib  # type: ignore
    except ImportError:
        tomllib = None  # type: ignore

_working_cache: dict[str, Any] = {}
_file_cache_path: Optional[Path] = None
_endpoints_cache: Optional[dict[str, Any]] = None


def _section_keys_for_type(model_type: str):
    """Yield section keys in order: type, type-1, type-2, ..."""
    yield model_type
    n = 1
    while True:
        yield f"{model_type}-{n}"
        n += 1


def _load_endpoints_toml() -> dict[str, Any]:
    """Fetch endpoints TOML from hardcoded URL; cache in memory."""
    global _endpoints_cache
    if _endpoints_cache is not None:
        return _endpoints_cache
    try:
        req = urllib.request.Request(MODEL_TYPE_ENDPOINTS_URL)
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read()
            _endpoints_cache = tomllib.loads(raw.decode("utf-8") if isinstance(raw, bytes) else raw)
            return _endpoints_cache
    except Exception:
        _endpoints_cache = {}
        return _endpoints_cache


def _first_section(data: dict[str, Any], model_type: str) -> Optional[dict[str, Any]]:
    """Return first section dict for model_type (trying type, type-1, type-2, ...)."""
    for key in _section_keys_for_type(model_type):
        if key != model_type and key not in data:
            break
        section = data.get(key)
        if isinstance(section, dict):
            return section
    return None


def get_endpoint(model_type: str) -> Optional[dict[str, Any]]:
    """
    Return endpoint config for model_type: { "base_url", "model" } (and optional "base_urls").
    Lookup order: section "type", then "type-1", "type-2", ...
    """
    if model_type not in MODEL_TYPES:
        return None
    data = _load_endpoints_toml()
    section = _first_section(data, model_type)
    if not section:
        return None
    base_url = (section.get("base_url") or "").strip()
    if not base_url:
        return None
    urls = section.get("base_urls")
    base_urls_list = [u.strip() for u in urls] if isinstance(urls, list) else []
    result: dict[str, Any] = {
        "base_url": base_url.rstrip("/") if not base_url.endswith("/v1") else base_url,
        "model": (section.get("model") or "").strip() or None,
    }
    if base_urls_list:
        result["base_urls"] = base_urls_list
    return result


def get_model_key(model_type: str) -> Optional[str]:
    """
    Return API key for model_type from ~/.config/model-type-keys.toml.
    Section key = model_key. Lookup order: type, type-1, type-2, ...
    """
    if model_type not in MODEL_TYPES or not tomllib:
        return None
    path = MODEL_TYPE_KEYS_PATH.expanduser().resolve()
    if not path.exists():
        return None
    try:
        with open(path, "rb") as f:
            data = tomllib.load(f)
    except Exception:
        return None
    for key in _section_keys_for_type(model_type):
        if key != model_type and key not in data:
            break
        section = data.get(key)
        if not isinstance(section, dict):
            continue
        raw = section.get("model_key")
        if isinstance(raw, str) and raw.strip():
            return raw.strip()
    return None


def _probe_http_health(url: str, timeout: float = 3.0) -> bool:
    url = (url or "").rstrip("/")
    if url.endswith("/v1"):
        health_url = url[:-3] + "/health"
    else:
        health_url = url + "/health" if not url.endswith("/health") else url
    try:
        with urllib.request.urlopen(urllib.request.Request(health_url), timeout=timeout) as resp:
            return 200 <= getattr(resp, "status", 200) < 300
    except Exception:
        return False


def get_working_endpoint(
    model_type: str,
    probe_fn: Optional[Callable[[str], bool]] = None,
    use_file_cache: bool = False,
    file_cache_path: Optional[Path] = None,
) -> Optional[dict[str, Any]]:
    """
    Return endpoint for model_type. If section has base_urls[], probe in order and cache first working.
    Otherwise returns same as get_endpoint (base_url + model).
    """
    global _file_cache_path
    info = get_endpoint(model_type)
    if not info:
        return None
    base_urls = info.get("base_urls") or []
    if not base_urls:
        return {"base_url": info["base_url"], "model": info.get("model")}
    probe = probe_fn or _probe_http_health
    options = [info["base_url"]] + list(base_urls)
    if model_type in _working_cache:
        cached = _working_cache[model_type]
        if isinstance(cached, str) and cached in options:
            return {"base_url": cached, "model": info.get("model")}
        if isinstance(cached, int) and 0 <= cached < len(options):
            return {"base_url": options[cached], "model": info.get("model")}
        del _working_cache[model_type]
    if use_file_cache:
        path = file_cache_path or (Path.home() / ".cache" / "model-type-endpoints" / "working.json")
        _file_cache_path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            try:
                with open(path, encoding="utf-8") as f:
                    data = json.load(f)
                idx = data.get(model_type)
                if idx is not None and 0 <= idx < len(options):
                    _working_cache[model_type] = options[idx]
                    return {"base_url": options[idx], "model": info.get("model")}
            except Exception:
                pass
    for i, url in enumerate(options):
        try:
            if probe(url):
                _working_cache[model_type] = i
                if use_file_cache:
                    p = file_cache_path or (Path.home() / ".cache" / "model-type-endpoints" / "working.json")
                    _file_cache_path = p
                    try:
                        p.parent.mkdir(parents=True, exist_ok=True)
                        data = {}
                        if p.exists():
                            with open(p, encoding="utf-8") as f:
                                data = json.load(f)
                        data[model_type] = i
                        with open(p, "w", encoding="utf-8") as f:
                            json.dump(data, f, indent=2)
                    except Exception:
                        pass
                return {"base_url": url, "model": info.get("model")}
        except Exception:
            continue
    return None


def invalidate_working(model_type: Optional[str] = None) -> None:
    """Clear working-endpoint cache for model_type, or all if model_type is None."""
    global _working_cache, _file_cache_path
    if model_type:
        _working_cache.pop(model_type, None)
        p = _file_cache_path or (Path.home() / ".cache" / "model-type-endpoints" / "working.json")
        if p.exists():
            try:
                with open(p, encoding="utf-8") as f:
                    data = json.load(f)
                data.pop(model_type, None)
                with open(p, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)
            except Exception:
                pass
    else:
        _working_cache.clear()
        p = _file_cache_path or (Path.home() / ".cache" / "model-type-endpoints" / "working.json")
        if p.exists():
            try:
                p.write_text("{}", encoding="utf-8")
            except Exception:
                pass


def main() -> int:
    import sys

    if len(sys.argv) < 3:
        print("Usage: model_type_endpoints_lookup.py get_endpoint <embedding|llm|rerank|visual>", file=sys.stderr)
        print("       model_type_endpoints_lookup.py get_model_key <embedding|llm|rerank|visual>", file=sys.stderr)
        return 1
    cmd, key = sys.argv[1].strip().lower(), sys.argv[2].strip()
    if cmd == "get_endpoint":
        out = get_endpoint(key)
        if not out:
            return 1
        print(out.get("base_url", ""))
        return 0
    if cmd == "get_model_key":
        out = get_model_key(key)
        if not out:
            return 1
        print(out)
        return 0
    return 1


if __name__ == "__main__":
    import sys

    sys.exit(main())
