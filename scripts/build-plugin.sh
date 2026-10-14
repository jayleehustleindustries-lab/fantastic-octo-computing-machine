#!/usr/bin/env bash
# Packages plugin/neuralhud into dist/neuralhud.plugin (a zip Claude can install).
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
out="$root/dist/neuralhud.plugin"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
mkdir -p "$root/dist"
(cd "$root/plugin/neuralhud" && zip -qrX "$tmp/neuralhud.plugin" . -x '*.DS_Store')
mv "$tmp/neuralhud.plugin" "$out"
echo "built $out"
