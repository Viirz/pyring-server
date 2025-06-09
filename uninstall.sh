#!/bin/sh
set -e

echo "(+) Stopping and removing Docker containers..."
sudo docker compose down --rmi all -v --remove-orphans >/dev/null 2>&1 || true

echo "(+) Cleanup complete!"
