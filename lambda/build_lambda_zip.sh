#!/usr/bin/env bash
set -euo pipefail

# Empaqueta lambda/backup_rds_s3.py con psycopg2-binary para AWS Lambda Linux x86_64
cd "$(dirname "$0")"
rm -rf package petcare_lambda.zip
mkdir -p package
pip install --target ./package --platform manylinux2014_x86_64 --only-binary=:all: psycopg2-binary
cp backup_rds_s3.py package/
(cd package && zip -r ../petcare_lambda.zip .)
echo "Paquete generado en lambda/petcare_lambda.zip"
