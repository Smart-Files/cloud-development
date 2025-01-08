VERSION := latest
IMAGE_NAME := gcr.io/smartfile-422907/smartfile-docker/server-image

.PHONY: build push deploy

# @local dev
run-local:
	python3 -m project.app

build:
	docker build -t $(IMAGE_NAME):$(VERSION) .

push: build
	docker push $(IMAGE_NAME):$(VERSION)

test:
	docker-compose up smartfile-chat-app --build

run:
	docker run -t $

up:
	docker-compose up

deploy: push
