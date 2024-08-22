.PHONY: help
help: ## Display this help message
	@echo "Usage: make <target>"
	@echo
	@echo "Available targets:"
	@grep --extended-regexp --no-filename '^[a-zA-Z_-]+:.*## ' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "	%-20s%s\n", $$1, $$2}'

.PHONY: install
install: ## Install package
	poetry lock --no-update
	poetry install

.PHONY: tests
tests: ## Run unit tests with coverage
	poetry run coverage run --source=geoservercloud -m pytest tests -vvv --color=yes
	poetry run coverage report
