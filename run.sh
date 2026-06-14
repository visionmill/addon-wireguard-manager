#!/usr/bin/env bash
set -euo pipefail

mkdir -p /data/wireguard /data/clients /etc/wireguard

# Symlink generated config into the standard wg-quick location.
if [ -f /data/wireguard/wg0.conf ]; then
  ln -sf /data/wireguard/wg0.conf /etc/wireguard/wg0.conf
fi

# Try to bring up WireGuard when a config already exists. Do not crash the UI if it fails.
if [ -f /etc/wireguard/wg0.conf ]; then
  wg-quick down wg0 >/dev/null 2>&1 || true
  wg-quick up wg0 >/tmp/wg-up.log 2>&1 || cat /tmp/wg-up.log || true
fi

WEB_PORT="8099"
if [ -f /data/options.json ]; then
  WEB_PORT="$(python3 - <<'PY'
import json
try:
    print(json.load(open('/data/options.json')).get('web_port', 8099))
except Exception:
    print(8099)
PY
)"
fi

exec gunicorn --bind "0.0.0.0:${WEB_PORT}" --workers 1 --threads 8 server:app
