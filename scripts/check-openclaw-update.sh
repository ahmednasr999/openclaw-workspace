#!/bin/bash
CURRENT=$(openclaw --version 2>/dev/null)
LATEST=$(npm show openclaw version 2>/dev/null)

if [ "$CURRENT" != "$LATEST" ] && [ -n "$LATEST" ]; then
  echo "UPDATE_AVAILABLE: $CURRENT -> $LATEST"
  exit 0
else
  exit 1
fi
