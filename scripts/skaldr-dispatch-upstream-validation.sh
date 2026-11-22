#!/usr/bin/env bash
# GitHub's GITHUB_TOKEN git pushes do not trigger push workflows.
# Explicitly dispatch both exact-branch CI workflows after a verified upstream merge.
set -euo pipefail

if [[ $# -ne 1 || ! "$1" =~ ^[0-9a-f]{40}$ ]]; then
  echo "::error::Expected exactly one 40-character lowercase commit SHA." >&2
  exit 2
fi
expected_sha="$1"

if [[ "${GITHUB_REPOSITORY:-}" != "pomercier/Skaldr-OS" ]]; then
  echo "::error::Refusing validation dispatch outside the official Skaldr repository." >&2
  exit 1
fi
if [[ -z "${GH_TOKEN:-}" ]]; then
  echo "::error::A GitHub Actions token with actions:write is required." >&2
  exit 1
fi
local_sha="$(git rev-parse HEAD)"
remote_sha="$(git ls-remote --exit-code origin refs/heads/master | cut -f1)"
if [[ "$local_sha" != "$expected_sha" || "$remote_sha" != "$expected_sha" ]]; then
  echo "::error::Local HEAD or remote master differs from upstream merge $expected_sha; refusing stale validation." >&2
  exit 1
fi

# Both calls use workflow_dispatch, one of the only events that can be
# initiated with GITHUB_TOKEN. No branch is created and no bypass is allowed.
gh api --silent -X POST \
  "repos/$GITHUB_REPOSITORY/actions/workflows/skaldr-checks.yml/dispatches" \
  -f ref=master
gh api --silent -X POST \
  "repos/$GITHUB_REPOSITORY/actions/workflows/build.yml/dispatches" \
  -f ref=master

printf 'Dispatched source regressions and full ISO/VM validation for %s\n' "$expected_sha"
