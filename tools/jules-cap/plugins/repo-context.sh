#!/usr/bin/env bash
set -euo pipefail

printf 'repo=%s\n' "$(pwd)"
printf 'head=%s\n' "$(git rev-parse --short HEAD 2>/dev/null || echo unknown)"
printf '%s\n' '--- git status ---'
git status --short --branch
printf '%s\n' '--- top level ---'
find . -maxdepth 1 -mindepth 1 -printf '%f\n' 2>/dev/null | sort
