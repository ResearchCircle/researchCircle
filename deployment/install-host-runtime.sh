#!/usr/bin/env bash
# Run as the normal G14 user in an interactive terminal.
set -euo pipefail
if [ "$(id -u)" -eq 0 ]; then
  printf 'Run this script as the normal login user, not through sudo.\n' >&2
  exit 1
fi
project_root="$HOME/researchCircle"
runtime_user="$(id -un)"
if [ -L "$project_root" ]; then
  printf 'Project root must not be a symlink.\n' >&2
  exit 1
fi
mkdir -p "$project_root/setup" "$project_root/logs"
chmod 700 "$project_root" "$project_root/setup" "$project_root/logs"
# Authentication stays in this terminal; no password is stored or forwarded.
sudo -v
sudo apt-get update
sudo env DEBIAN_FRONTEND=noninteractive apt-get install -y docker.io docker-compose-v2
sudo systemctl enable --now docker
sudo usermod -aG docker "$runtime_user"
sudo docker version --format '{{.Server.Version}}'
sudo docker compose version --short
# Preserve any ingress configured since preparation; never reset Serve.
serve_config="$(sudo tailscale serve status --json)"
if printf '%s' "$serve_config" | python3 -c 'import json,sys; sys.exit(0 if not json.load(sys.stdin) else 1)'; then
  sudo tailscale serve --bg --https=443 http://127.0.0.1:18088
else
  printf 'Existing Serve configuration preserved; review before changing ingress.\n'
fi
printf 'Runtime installed. A new SSH session will receive Docker group access.\n'
printf 'Application releases, configuration and data belong under %s.\n' "$project_root"
