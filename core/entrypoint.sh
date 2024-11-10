#!/bin/bash

if [ -z "$(ls -A /app/typings)" ]; then
  cp -rv /app/cat_typings/* /app/typings
  chmod -Rv a-w /app/typings/*
fi

if [ -z "$(ls -A /app/.vscode)" ]; then
  cp -rv /app/vscode_settings/* /app/.vscode
fi

exec "$@"