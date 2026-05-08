# ProxyBridge Skill

A Claude Code/Codex skill that configures and runs [ProxyBridge](https://github.com/sudo-rm-force/proxybridge), a local compatibility bridge that turns Anthropic-compatible or OpenAI-compatible proxy APIs into a Codex-compatible OpenAI Responses endpoint.

## Use Case

When Claude Code works but Codex does not — e.g., you have a proxy API key (53HK, laozhang, 中转站, etc.) that only supports Anthropic `/v1/messages` or OpenAI `/v1/chat/completions`, but Codex requires `/v1/responses`.

## Installation

### Option 1: Link to your Codex skills directory

```bash
git clone https://github.com/suoha888/skill-proxybridge.git ~/.codex/skills/proxybridge
```

### Option 2: Link to your Claude Code skills directory

```bash
git clone https://github.com/suoha888/skill-proxybridge.git ~/.claude/skills/proxybridge
```

## Usage

1. **Setup** your upstream proxy:

```bash
~/.codex/skills/proxybridge/scripts/proxybridgectl.py setup \
  --type anthropic \
  --url "https://your-proxy-api.com" \
  --key "sk-your-key" \
  --model "claude-sonnet-4-5"
```

2. **Start** ProxyBridge:

```bash
~/.codex/skills/proxybridge/scripts/proxybridgectl.py start
```

3. **Test**:

```bash
~/.codex/skills/proxybridge/scripts/proxybridgectl.py test
```

4. **Configure Codex** — paste the output into `~/.codex/config.toml`:

```bash
~/.codex/skills/proxybridge/scripts/proxybridgectl.py codex-config
```

5. **Run Codex**:

```bash
export PROXYBRIDGE_API_KEY=local
codex -p proxybridge
```

## `--type` Options

| Type | When to Use |
|------|-------------|
| `anthropic` | Claude Code works, `/v1/messages`, Anthropic API |
| `chat_completions` | OpenAI-compatible, `/v1/chat/completions` |
| `responses` | Provider already supports Responses endpoint |

## Other Commands

```bash
proxybridgectl.py status    # Check if ProxyBridge is running
proxybridgectl.py stop       # Stop ProxyBridge
proxybridgectl.py restart    # Restart
proxybridgectl.py logs       # View logs
```

## Platform Support

Currently includes `proxybridge-darwin-arm64` (macOS Apple Silicon). For other platforms, download ProxyBridge binary from [sudo-rm-force/proxybridge](https://github.com/sudo-rm-force/proxybridge) and replace `assets/bin/proxybridge-darwin-arm64`.

## Files

```
proxybridge/
├── SKILL.md                    # This skill definition
├── agents/openai.yaml          # Agent config
├── references/codex-config.md  # Codex config reference
├── scripts/proxybridgectl.py  # Controller script
└── assets/bin/                 # ProxyBridge binary
```

## Troubleshooting

- **401** → upstream API key is wrong
- **404** → base URL includes endpoint suffix, or `--type` is wrong
- **400** → model name is wrong
- **Connection refused** → ProxyBridge not running
