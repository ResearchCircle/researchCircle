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
sudo python3 "$(dirname "$0")/host_storage.py" --project-root "$project_root"
sudo apt-get update
sudo env DEBIAN_FRONTEND=noninteractive apt-get -o Dpkg::Options::=--force-confold install -y docker.io docker-compose-v2
sudo systemctl enable --now containerd docker
sudo usermod -aG docker "$runtime_user"
sudo docker version --format '{{.Server.Version}}'
sudo docker compose version --short
actual_docker_root="$(sudo docker info --format '{{.DockerRootDir}}')"
if [ "$actual_docker_root" != "$project_root/runtime/docker" ]; then
  printf 'Docker is using a different data root; stop and inspect configuration.\n' >&2
  exit 1
fi
actual_containerd_root="$(sudo containerd config dump | python3 -c 'import sys,tomllib; print(tomllib.loads(sys.stdin.read()).get("root", ""))')"
if [ "$actual_containerd_root" != "$project_root/runtime/containerd" ]; then
  printf 'Containerd is using a different configured root; stop and inspect configuration.\n' >&2
  exit 1
fi
# Read only the selected port; never source the private settings as shell code.
http_port="$(python3 - "$project_root/config/runtime.env" <<'PYPORT'
import pathlib,sys
values={}
for line in pathlib.Path(sys.argv[1]).read_text().splitlines():
    key,sep,value=line.partition('=')
    if sep and key.strip()=='TBR_HTTP_PORT': values[key.strip()]=value.strip().strip("\"'")
port=values.get('TBR_HTTP_PORT','8080')
if not port.isdecimal() or not 1 <= int(port) <= 65535: raise SystemExit('Invalid application port.')
print(port)
PYPORT
)"
# Preserve any ingress configured since preparation; never reset Serve.
serve_config="$(sudo tailscale serve status --json)"
if printf '%s' "$serve_config" | python3 -c 'import json,sys; sys.exit(0 if not json.load(sys.stdin) else 1)'; then
  sudo tailscale serve --bg --https=443 "http://127.0.0.1:$http_port"
else
  printf 'Existing Serve configuration preserved; review before changing ingress.\n'
fi
printf 'Runtime installed. A new SSH session will receive Docker group access.\n'
printf 'Application releases, configuration and data belong under %s.\n' "$project_root"
