SHELL := /bin/bash

# Define the absolute directory of the script
ROOT_DIR := $(shell dirname $(realpath $(firstword $(MAKEFILE_LIST))))

# Add the following 'help' target to your Makefile
# And add help text after each target name starting with '\#\#'

.PHONY: help
help: ## Show help for each of the Makefile recipes.
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'


###
### Commands for **outside** of Docker container development.
###

.PHONY: dev-up
dev-up: ## Creating Docker containers
	@echo 'Creating Docker containers for development'
	@DOCKER_DEFAULT_PLATFORM=linux/amd64 docker compose -f docker-compose.dev-backend.yml build
	@DOCKER_DEFAULT_PLATFORM=linux/amd64 docker compose -f docker-compose.dev-backend.yml up -d

.PHONY: dev-stop
dev-stop: ## Stopping Docker containers
	@echo 'Stopping Docker containers'
	@docker compose -f docker-compose.dev-backend.yml stop

.PHONY: dev-clean
dev-clean: ## Stopping and removing Docker containers
	@echo 'Stopping and removing Docker containers'
	@docker compose -f docker-compose.dev-backend.yml down

.PHONY: dev-recreate ## Run `dev-clean` and then `dev-up` in order. Anything right of `|` runs in the defined order
dev-recreate: | dev-clean dev-up

###
### Commands for **inside** of Docker container development.
###
