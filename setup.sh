#!/bin/bash
# Rebuild the rendering equipment on another Mac. Playback needs no setup.
# Delivered playback: python3 play.py (or double-click Play Course.command).
set -e
cd "$(dirname "$0")"
brew install cairo pango pkg-config uv ffmpeg
uv venv --python 3.12 .venv
uv pip sync requirements.lock --python .venv/bin/python
echo "Equipment ready. Next: ./kitchen check"
