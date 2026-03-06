#!/bin/bash
# summarize skill wrapper

INPUT="$1"
shift

# Check if input is provided
if [ -z "$INPUT" ]; then
  echo "Usage: summarize <url|file|-> [options]"
  echo "Run 'summarize --help' for more options"
  exit 1
fi

# Run summarize
summarize "$INPUT" "$@"
