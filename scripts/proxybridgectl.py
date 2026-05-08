#!/usr/bin/env python3
import argparse
import json
import os
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

HOME = Path.home()
SKILL_DIR = Path(__file__).resolve().parents[1]
BIN = SKILL_DIR / "assets" / "bin" / "proxybridge-darwin-arm64"
STATE_DIR = HOME / ".proxybridge"
CONFIG = STATE_DIR / "config.env"
PIDFILE = STATE_DIR / "proxybridge.pid"
LOGFILE = STATE_DIR / "proxybridge.log"
DEFAULT_LISTEN = "127.0.0.1:9090"


def main():
    parser = argparse.ArgumentParser(description="ProxyBridge local controller")
    sub = parser.add_subparsers(dest="cmd", required=True)

    setup = sub.add_parser("setup", help="store upstream API settings")
    setup.add_argument("--type", choices=["anthropic", "chat_completions", "responses"], default="anthropic")
    setup.add_argument("--url", required=True, help="upstream base URL, without /v1/messages or /v1/responses")
    setup.add_argument("--key", required=True, help="upstream API key")
    setup.add_argument("--model", required=True, help="upstream model name")
    setup.add_argument("--listen", default=DEFAULT_LISTEN)

    sub.add_parser("start", help="start ProxyBridge")
    sub.add_parser("stop", help="stop ProxyBridge")
    sub.add_parser("restart", help="restart ProxyBridge")
    sub.add_parser("status", help="show status")
    sub.add_parser("test", help="test local endpoint")
    sub.add_parser("codex-config", help="print Codex config.toml snippet")
    sub.add_parser("logs", help="show recent logs")

    args = parser.parse_args()
    STATE_DIR.mkdir(parents=True, exist_ok=True)

    if args.cmd == "setup":
        setup_config(args)
    elif args.cmd == "start":
        start()
    elif args.cmd == "stop":
        stop()
    elif args.cmd == "restart":
        stop()
        start()
    elif args.cmd == "status":
        status()
    elif args.cmd == "test":
        test()
    elif args.cmd == "codex-config":
        codex_config()
    elif args.cmd == "logs":
        logs()


def setup_config(args):
    url = args.url.rstrip("/")
    if url.endswith("/v1/messages"):
        url = url[: -len("/v1/messages")]
    if url.endswith("/v1/responses"):
        url = url[: -len("/v1/responses")]
    if url.endswith("/v1/chat/completions"):
        url = url[: -len("/v1/chat/completions")]

    data = {
        "UPSTREAM_TYPE": args.type,
        "UPSTREAM_BASE_URL": url,
        "UPSTREAM_API_KEY": args.key,
        "UPSTREAM_MODEL": args.model,
        "LISTEN_ADDR": args.listen,
        "PASSTHROUGH_MODEL": "false",
        "ALLOW_CLIENT_API_KEY": "false",
        "ANTHROPIC_VERSION": "2023-06-01",
    }
    CONFIG.write_text("\n".join(f"{k}={shell_quote(v)}" for k, v in data.items()) + "\n")
    os.chmod(CONFIG, 0o600)
    print(f"Saved config: {CONFIG}")
    print(f"Upstream: {args.type} {url} model={args.model} key={redact(args.key)}")
    print("Next: proxybridgectl.py start")


def start():
    if not BIN.exists():
        fail(f"ProxyBridge binary not found: {BIN}")
    if running():
        print("ProxyBridge is already running.")
        status()
        return
    env = os.environ.copy()
    env.update(load_env())
    listen = env.get("LISTEN_ADDR", DEFAULT_LISTEN)
    log = open(LOGFILE, "ab")
    proc = subprocess.Popen([str(BIN)], cwd=str(STATE_DIR), env=env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    PIDFILE.write_text(str(proc.pid))
    time.sleep(0.7)
    if not running():
        print("ProxyBridge failed to start. Recent logs:")
        logs()
        sys.exit(1)
    print(f"ProxyBridge running at http://{listen}/v1")
    print("Next: proxybridgectl.py test")


def stop():
    pid = read_pid()
    if not pid:
        print("ProxyBridge is not running.")
        return
    try:
        os.kill(pid, signal.SIGTERM)
        time.sleep(0.5)
    except ProcessLookupError:
        pass
    PIDFILE.unlink(missing_ok=True)
    print("ProxyBridge stopped.")


def status():
    pid = read_pid()
    if pid and process_alive(pid):
        listen = load_env().get("LISTEN_ADDR", DEFAULT_LISTEN)
        print(f"running pid={pid} url=http://{listen}/v1")
    else:
        print("stopped")


def test():
    env = load_env()
    listen = env.get("LISTEN_ADDR", DEFAULT_LISTEN)
    base = f"http://{listen}"
    check("health", "GET", f"{base}/health")
    check("models", "GET", f"{base}/v1/models")
    body = {"model": "gpt-5-codex", "input": "只回复 pong", "max_output_tokens": 300}
    check("responses", "POST", f"{base}/v1/responses", body)
    check("compact", "POST", f"{base}/v1/responses/compact", {"model": "gpt-5-codex", "input": "compact"})


def codex_config():
    listen = load_env().get("LISTEN_ADDR", DEFAULT_LISTEN)
    print(f"""[model_providers.proxybridge]
name = "ProxyBridge"
base_url = "http://{listen}/v1"
env_key = "PROXYBRIDGE_API_KEY"
wire_api = "responses"

[profiles.proxybridge]
model_provider = "proxybridge"
model = "gpt-5-codex"
model_reasoning_effort = "high"
""")


def logs():
    if not LOGFILE.exists():
        print("No logs yet.")
        return
    lines = LOGFILE.read_text(errors="replace").splitlines()
    for line in lines[-80:]:
        print(line)


def check(name, method, url, body=None):
    try:
        data = None if body is None else json.dumps(body).encode()
        req = urllib.request.Request(url, data=data, method=method)
        req.add_header("Authorization", "Bearer local")
        req.add_header("Content-Type", "application/json")
        with urllib.request.urlopen(req, timeout=45) as resp:
            text = resp.read().decode(errors="replace")
        print(f"OK   {name}")
        if name in ("responses", "compact"):
            print(text[:500])
    except urllib.error.HTTPError as e:
        print(f"FAIL {name}: HTTP {e.code}")
        print(e.read().decode(errors="replace")[:500])
    except Exception as e:
        print(f"FAIL {name}: {e}")


def load_env():
    if not CONFIG.exists():
        fail(f"No config found. Run setup first: {CONFIG}")
    env = {}
    for line in CONFIG.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        env[k] = v.strip().strip("'").strip('"')
    return env


def running():
    pid = read_pid()
    return bool(pid and process_alive(pid))


def read_pid():
    if not PIDFILE.exists():
        return None
    try:
        return int(PIDFILE.read_text().strip())
    except ValueError:
        return None


def process_alive(pid):
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


def shell_quote(value):
    return "'" + str(value).replace("'", "'\\''") + "'"


def redact(value):
    value = str(value)
    if len(value) <= 8:
        return "***"
    return value[:4] + "..." + value[-4:]


def fail(message):
    print(f"ERROR: {message}", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    main()
