#!/bin/bash

cd receipts

for file in *.HEIC; do
    sips -s format jpeg "$file" --out "${file%.*}.jpg"
done