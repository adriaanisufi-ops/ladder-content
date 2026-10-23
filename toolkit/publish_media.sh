#!/usr/bin/env bash
# Put finished videos on the public `media` branch and print their raw URLs.
# Usage: bash toolkit/publish_media.sh out/2026-10-24
# The branch is rebuilt from scratch every time (force push), so it only ever holds
# the latest batch and the repo doesn't grow. Metricool copies each file to its own
# storage when the post is scheduled, so older files aren't needed after scheduling.
set -euo pipefail
SRC=$(cd "$1" && pwd)
DAY=$(basename "$SRC")
REPO=adriaanisufi-ops/ladder-content
TMP=$(mktemp -d)
cd "$TMP"
git init -q
git checkout -q --orphan media
mkdir -p "$DAY"
cp "$SRC"/*.mp4 "$DAY"/
git add -A
git -c user.name="Claude" -c user.email="noreply@anthropic.com" commit -q -m "media $DAY"
git remote add origin "https://github.com/$REPO"
git push -q -f origin media
for f in "$DAY"/*.mp4; do
  echo "https://raw.githubusercontent.com/$REPO/media/$f"
done
rm -rf "$TMP"
