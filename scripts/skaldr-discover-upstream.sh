#!/usr/bin/env bash
# Discover the actual default branch of the official CachyOS source via Git.
# This avoids unauthenticated GitHub REST requests, which can return HTTP 403.
# Fail closed: no guessed fallback branch and no branch creation.
set -euo pipefail

if [[ $# -ne 0 ]]; then
    echo "Usage: skaldr-discover-upstream.sh (no arguments)" >&2
    exit 2
fi

upstream_url="https://github.com/CachyOS/CachyOS-Live-ISO.git"
if ! remote_head="$(git -c protocol.version=2 ls-remote --symref "$upstream_url" HEAD)"; then
    echo "::error::Cannot query the official CachyOS Git HEAD; refusing upstream merge." >&2
    exit 1
fi

# Git protocol emits: ref: refs/heads/<default-branch> TAB HEAD
# Restrict output to a valid, single-line branch name before writing GITHUB_OUTPUT.
branch="$(printf '%s\n' "$remote_head" | awk '
    $1 == "ref:" && $3 == "HEAD" && $2 ~ /^refs\/heads\/[A-Za-z0-9._\/-]+$/ {
        sub(/^refs\/heads\//, "", $2)
        print $2
        exit
    }
')"

if [[ -z "$branch" || "$branch" == *..* || "$branch" == */ || "$branch" == /* ]]; then
    echo "::error::Git did not return a valid symbolic default branch; refusing upstream merge." >&2
    exit 1
fi

printf '%s\n' "$branch"
