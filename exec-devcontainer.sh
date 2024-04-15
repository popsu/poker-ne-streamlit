#!/bin/bash

set -euo pipefail

# Run this script from external terminal to run bash in the devcontainer

# This is set in the devcontainer.json file
CONTAINER_NAME="poker_ne_streamlit_devcontainer"
CONTAINER_ID="$(docker container list --filter "name=$CONTAINER_NAME" --format "{{.ID}}")"

docker exec -it \
  -w /workspaces/poker-ne-streamlit \
  --env-file="$(pwd)/.devcontainer/container.env" \
  "$CONTAINER_ID" \
  bash
