# Codex config snippet

Paste into `~/.codex/config.toml`:

```toml
[model_providers.proxybridge]
name = "ProxyBridge"
base_url = "http://127.0.0.1:9090/v1"
env_key = "PROXYBRIDGE_API_KEY"
wire_api = "responses"

[profiles.proxybridge]
model_provider = "proxybridge"
model = "gpt-5-codex"
model_reasoning_effort = "high"
```

Then run:

```bash
export PROXYBRIDGE_API_KEY=local
codex -p proxybridge
```
