---
name: proxybridge
description: Configure and run ProxyBridge, a local compatibility bridge that turns Anthropic-compatible or OpenAI-compatible proxy APIs into a Codex-compatible OpenAI Responses endpoint. Use when the user wants to connect Codex, Aider, OpenCode, Cursor, or another OpenAI Responses client to a proxy API key that does not natively support Codex; when they mention Anthropic API, Claude Code works but Codex does not, /v1/responses, /v1/messages, Chat Completions, 53HK, laozhang, 中转站, API key conversion, or local OpenAI-compatible endpoint setup.
---

# ProxyBridge

Use this skill to give the user a no-code entrypoint for running ProxyBridge locally.

The user should not need to edit project code. Prefer the bundled script:

```bash
~/.codex/skills/proxybridge/scripts/proxybridgectl.py
```

## Default Workflow

1. Identify the upstream API shape:
   - If the user says Claude Code works, Anthropic, Claude, or `/v1/messages`, use `anthropic`.
   - If the user says OpenAI-compatible, Chat Completions, or `/v1/chat/completions`, use `chat_completions`.
   - If the user says the provider already supports Responses or gives Codex config with `wire_api = "responses"`, use `responses`.
   - If unclear, start with `anthropic` when Claude Code works, otherwise `chat_completions`.

2. Collect only three required values:
   - Upstream base URL, without endpoint suffix. Example: use `https://api.example.com`, not `https://api.example.com/v1/messages`.
   - API key.
   - Upstream model name that already works with that provider.

3. Run setup:

```bash
~/.codex/skills/proxybridge/scripts/proxybridgectl.py setup \
  --type anthropic \
  --url "https://api.example.com" \
  --key "sk-..." \
  --model "claude-sonnet-4-5"
```

4. Start ProxyBridge:

```bash
~/.codex/skills/proxybridge/scripts/proxybridgectl.py start
```

5. Test:

```bash
~/.codex/skills/proxybridge/scripts/proxybridgectl.py test
```

6. Show Codex config:

```bash
~/.codex/skills/proxybridge/scripts/proxybridgectl.py codex-config
```

Tell the user to paste that TOML into `~/.codex/config.toml`, then run:

```bash
export PROXYBRIDGE_API_KEY=local
codex -p proxybridge
```

## Commands

- `setup`: Store local config under `~/.proxybridge/config.env` with file mode `0600`.
- `start`: Start the bundled ProxyBridge binary in the background.
- `stop`: Stop the background process.
- `restart`: Stop then start.
- `status`: Show whether ProxyBridge is running.
- `test`: Check `/health`, `/v1/models`, `/v1/responses`, and `/v1/responses/compact`.
- `codex-config`: Print the Codex profile TOML.
- `logs`: Show recent logs from `~/.proxybridge/proxybridge.log`.

## Safety

- Never print the full API key back to the user.
- Do not edit `~/.codex/config.toml` unless the user explicitly asks.
- Do not modify the ProxyBridge source project while using this skill.
- Store runtime files only under `~/.proxybridge/`.

## Troubleshooting

- 401 usually means the upstream API key is wrong.
- 404 usually means the base URL includes the endpoint suffix or the upstream type is wrong.
- 400 usually means the model name is wrong or the provider does not support the requested field.
- Connection refused on `127.0.0.1:9090` means ProxyBridge is not running.

