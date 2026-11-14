#!/usr/bin/env bash
# GAMA site deployer — static server + Cloudflare tunnel helper
# Usage:
#   ./deploy_site.sh [--port 8100] [--host 0.0.0.0] [--dir DIR]
#   ./deploy_site.sh --tunnel [--port 8100] [--dir DIR]
#   ./deploy_site.sh --named-tunnel NAME [--port 8100] [--dir DIR]
#   ./deploy_site.sh --stop [--port 8100]
#   ./deploy_site.sh --status [--port 8100]
set -euo pipefail

PORT=8100
HOST=0.0.0.0
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ACTION=start
TUNNEL_MODE=""
TUNNEL_NAME=""
CF_CONFIG=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --port) PORT="${2:?--port needs a value}"; shift 2 ;;
    --host) HOST="${2:?--host needs a value}"; shift 2 ;;
    --dir)  DIR="${2:?--dir needs a value}"; shift 2 ;;
    --tunnel) ACTION=start; TUNNEL_MODE=quick; shift ;;
    --named-tunnel) ACTION=start; TUNNEL_MODE=named; TUNNEL_NAME="${2:?--named-tunnel needs a name}"; shift 2 ;;
    --config) CF_CONFIG="${2:?--config needs a path}"; shift 2 ;;
    --stop) ACTION=stop; shift ;;
    --status) ACTION=status; shift ;;
    -h|--help)
      sed -n '2,8p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
      exit 0 ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
done

if ! [[ "$PORT" =~ ^[0-9]+$ ]] || (( PORT < 1 || PORT > 65535 )); then
  echo "invalid port: $PORT" >&2
  exit 2
fi
if [[ "$DIR" != /* ]]; then
  DIR="$(cd "$DIR" && pwd)"
fi

PIDFILE="/tmp/gama-site-${PORT}.pid"
LOGFILE="/tmp/gama-site-${PORT}.log"
TPIDFILE="/tmp/gama-site-tunnel-${PORT}.pid"
TLOGFILE="/tmp/gama-site-tunnel-${PORT}.log"
DIRFILE="/tmp/gama-site-${PORT}.dir"

is_running() {
  [[ -f "$PIDFILE" ]] || return 1
  local pid
  pid="$(cat "$PIDFILE" 2>/dev/null || true)"
  [[ -n "$pid" ]] || return 1
  kill -0 "$pid" 2>/dev/null || return 1
  grep -q "http.server" "/proc/$pid/cmdline" 2>/dev/null || return 1
  return 0
}

tunnel_running() {
  [[ -f "$TPIDFILE" ]] || return 1
  local pid
  pid="$(cat "$TPIDFILE" 2>/dev/null || true)"
  [[ -n "$pid" ]] || return 1
  kill -0 "$pid" 2>/dev/null || return 1
  grep -q "cloudflared" "/proc/$pid/cmdline" 2>/dev/null || return 1
  return 0
}

tunnel_url() {
  [[ -f "$TLOGFILE" ]] || return 1
  grep -Eo 'https://[a-z0-9-]+\.trycloudflare\.com' "$TLOGFILE" 2>/dev/null | tail -n 1
}

stop_all() {
  if tunnel_running; then
    local tpid; tpid="$(cat "$TPIDFILE")"
    kill "$tpid" 2>/dev/null || true
    for _ in $(seq 1 30); do kill -0 "$tpid" 2>/dev/null || break; sleep 0.1; done
    kill -9 "$tpid" 2>/dev/null || true
    rm -f "$TPIDFILE"
    echo "stopped tunnel pid $tpid"
  fi
  if ! is_running; then
    echo "server not running (pid file: $PIDFILE)"
    rm -f "$PIDFILE"
    return 0
  fi
  local pid; pid="$(cat "$PIDFILE")"
  kill "$pid" 2>/dev/null || true
  for _ in $(seq 1 50); do kill -0 "$pid" 2>/dev/null || break; sleep 0.1; done
  if kill -0 "$pid" 2>/dev/null; then kill -9 "$pid" 2>/dev/null || true; fi
  rm -f "$PIDFILE" "$DIRFILE"
  echo "stopped server pid $pid (port $PORT)"
}

status_all() {
  local rc=0
  if is_running; then
    local rdir; rdir="$(cat "$DIRFILE" 2>/dev/null || echo "$DIR")"
    echo "server: running pid $(cat "$PIDFILE") on http://${HOST}:${PORT} (dir $rdir, log $LOGFILE)"
    local code
    code="$(curl -s -o /dev/null -w '%{http_code}' --max-time 3 "http://127.0.0.1:${PORT}/" 2>/dev/null || true)"
    echo "http:   GET / -> ${code:-no-response}"
  else
    echo "server: not running (port $PORT)"; rc=1
  fi
  if tunnel_running; then
    local u; u="$(tunnel_url || true)"
    echo "tunnel: running pid $(cat "$TPIDFILE") ${u:-<url not parsed yet>} (log $TLOGFILE)"
  else
    echo "tunnel: not running"
  fi
  return $rc
}

case "$ACTION" in
  stop) stop_all; exit 0 ;;
  status) status_all; exit $? ;;
esac

if [[ ! -f "$DIR/index.html" ]]; then
  echo "missing $DIR/index.html (use --dir to point at a site root)" >&2
  exit 1
fi

if is_running; then
  echo "already running pid $(cat "$PIDFILE") on http://${HOST}:${PORT}"
else
  if ! command -v python3 >/dev/null 2>&1; then
    echo "python3 not found" >&2; exit 1
  fi
  nohup python3 -m http.server "$PORT" --bind "$HOST" --directory "$DIR" \
    >>"$LOGFILE" 2>&1 &
  PID=$!
  echo "$PID" >"$PIDFILE"
  echo "$DIR" >"$DIRFILE"

  READY=0
  for _ in $(seq 1 50); do
    kill -0 "$PID" 2>/dev/null || break
    if curl -s -o /dev/null --max-time 1 "http://127.0.0.1:${PORT}/" 2>/dev/null; then
      READY=1; break
    fi
    sleep 0.1
  done
  if [[ "$READY" -ne 1 ]]; then
    echo "failed to start server on port $PORT; last log lines:" >&2
    tail -n 20 "$LOGFILE" >&2 || true
    stop_all >/dev/null 2>&1 || true
    exit 1
  fi
  echo "site up: http://${HOST}:${PORT}/ (pid $PID, log $LOGFILE, dir $DIR)"
fi

if [[ -z "$TUNNEL_MODE" ]]; then
  exit 0
fi

if ! command -v cloudflared >/dev/null 2>&1; then
  echo "cloudflared not found" >&2
  exit 1
fi

if tunnel_running; then
  echo "tunnel already running pid $(cat "$TPIDFILE") $(tunnel_url || true)"
  exit 0
fi

case "$TUNNEL_MODE" in
  quick)
    : >"$TLOGFILE"
    nohup cloudflared tunnel --url "http://127.0.0.1:${PORT}" --no-autoupdate \
      >>"$TLOGFILE" 2>&1 &
    TPID=$!
    echo "$TPID" >"$TPIDFILE"
    URL=""
    for _ in $(seq 1 60); do
      kill -0 "$TPID" 2>/dev/null || break
      URL="$(tunnel_url || true)"
      [[ -n "$URL" ]] && break
      sleep 0.25
    done
    if [[ -z "$URL" ]]; then
      echo "quick tunnel did not return a URL; last log lines:" >&2
      tail -n 20 "$TLOGFILE" >&2 || true
      kill "$TPID" 2>/dev/null || true
      rm -f "$TPIDFILE"
      exit 1
    fi
    echo "tunnel (quick): $URL -> http://127.0.0.1:${PORT} (pid $TPID, log $TLOGFILE)"
    echo "note: quick tunnel URL is TEMPORARY and does not bind gamai.io/gamabalkan.io"
    ;;
  named)
    if [[ -z "$CF_CONFIG" ]]; then
      for c in /root/.cloudflared/config.yml /etc/cloudflared/config.yml /root/.cloudflared/config.yaml; do
        [[ -f "$c" ]] && CF_CONFIG="$c" && break
      done
    fi
    if [[ -z "$CF_CONFIG" || ! -f "$CF_CONFIG" ]]; then
      echo "no cloudflared config found (looked for /root/.cloudflared/config.yml, /etc/cloudflared/config.yml)." >&2
      echo "create it (see DNS_SETUP.md) or pass --config PATH." >&2
      exit 1
    fi
    if ! cloudflared tunnel list 2>/dev/null | awk '{print $2}' | grep -qx "$TUNNEL_NAME"; then
      echo "tunnel '$TUNNEL_NAME' not found in account (cloudflared tunnel list)." >&2
      exit 1
    fi
    if ! grep -q "127.0.0.1:${PORT}\|localhost:${PORT}" "$CF_CONFIG" 2>/dev/null; then
      echo "warning: $CF_CONFIG ingress does not mention 127.0.0.1:${PORT}; serving anyway" >&2
    fi
    : >"$TLOGFILE"
    nohup cloudflared tunnel --config "$CF_CONFIG" run "$TUNNEL_NAME" \
      >>"$TLOGFILE" 2>&1 &
    TPID=$!
    echo "$TPID" >"$TPIDFILE"
    sleep 2
    if ! kill -0 "$TPID" 2>/dev/null; then
      echo "named tunnel failed to start; last log lines:" >&2
      tail -n 20 "$TLOGFILE" >&2 || true
      rm -f "$TPIDFILE"
      exit 1
    fi
    echo "tunnel (named '$TUNNEL_NAME'): running pid $TPID via $CF_CONFIG (log $TLOGFILE)"
    echo "DNS: CNAME <host> -> ${TUNNEL_NAME}.cfargotunnel.com is NOT set by this script (manual step, see DNS_SETUP.md)"
    ;;
esac
