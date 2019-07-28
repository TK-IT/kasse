#!/bin/bash

set -euo pipefail

FILE=stopwatch/static/stopwatch/stopwatch.min.js
TMP="$FILE.$$"
TAG=localhost/kasse:latest

docker build -t "$TAG" .
docker run --rm --entrypoint /bin/sh "$TAG" -c "cat '$FILE'" > "$TMP" && mv "$TMP" "$FILE"
