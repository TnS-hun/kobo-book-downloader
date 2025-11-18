#!/bin/sh
set -e

# Ensure directories exist
mkdir -p /config /downloads

# Ensure settings are stored under the writable config volume
export XDG_CONFIG_HOME=/config

# If running as root and PUID/PGID are set, adjust ownership
if [ "$(id -u)" = "0" ] && [ -n "$PUID" ] && [ -n "$PGID" ]; then
  # Make volumes and app directory writable by the mapped user.
  chown -R "$PUID:$PGID" /config /downloads /app 2>/dev/null || true
fi

# Determine mode: UI (Flask) or CLI
MODE="cli"
case "$UI_ENABLED" in
  1|true|TRUE|yes|YES)
    MODE="ui"
    ;;
esac

if [ "$MODE" = "ui" ]; then
  # Web UI mode: run Flask app (webapp.app:app).
  PORT="${UI_PORT:-5000}"
  CMD="python -m webapp.app"
else
  # CLI mode: run kobo-book-downloader with KBD_COMMAND
  if [ -z "$KBD_COMMAND" ]; then
    echo "[WARN] KBD_COMMAND not set, defaulting to 'info'" >&2
    KBD_COMMAND="info"
  fi

  CMD="python kobo-book-downloader $KBD_COMMAND"
fi

# Drop privileges if needed
if [ "$(id -u)" = "0" ] && [ -n "$PUID" ] && [ -n "$PGID" ]; then
  exec gosu "$PUID:$PGID" sh -c "$CMD"
fi

exec sh -c "$CMD"
