#!/bin/bash
VERSION="1.0.1"

docker build -t gcr.io/smartfile-422907/smartfile-docker/server-image:$VERSION .
docker push gcr.io/smartfile-422907/smartfile-docker/server-image:$VERSION

