#!/bin/sh
set -e

venv="./.venv/bin"
flake8="${venv}/flake8"
isort="${venv}/isort"
black="${venv}/black"

${isort} --profile=black examples/ experiments/ lib/
${black} -l 100 examples/ experiments/ lib/
${flake8} examples/ experiments/ lib/
