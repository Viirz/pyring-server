#!/bin/sh

set -e

echo "(+) Building and starting Docker containers..."
sudo docker compose up -d --build --force-recreate

echo "(+) Installation complete!"
