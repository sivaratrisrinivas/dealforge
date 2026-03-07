#!/usr/bin/env bash
# Railway build: install deps and build Chroma DB (ingest) so it's baked into the image.
set -e
pip install -r requirements.txt
python ingest.py
