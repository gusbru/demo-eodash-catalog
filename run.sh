#!/bin/bash
set -e

rm -rf build
eodash_catalog
cp -r data build/template_catalog/
cp -r styles build/template_catalog/
cp -r processes build/template_catalog/
cp -r charts build/template_catalog/
npx http-server -p 8001 --cors="Authorization,Content-Type" build/template_catalog