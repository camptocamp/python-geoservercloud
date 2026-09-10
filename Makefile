.PHONY: help
help: ## Display this help message
	@echo "Usage: make <target>"
	@echo
	@echo "Available targets:"
	@grep --extended-regexp --no-filename '^[a-zA-Z_-]+:.*## ' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "	%-20s%s\n", $$1, $$2}'

.PHONY: install
install: ## Install package
	poetry lock
	poetry install

.PHONY: tests
tests: ## Run unit tests with coverage
	poetry run coverage run --source=geoservercloud -m pytest tests -vvv --color=yes
	poetry run coverage report

.PHONY: docs
docs: ## Generate documentation with Sphinx in docs/build
	rm -rf docs/build
	poetry run sphinx-build -b html docs/source docs/build

.PHONY: acceptance-tests
acceptance-tests: install acceptance-tests-setup acceptance-tests-up ## Run acceptance tests (starts GeoServer and DB via docker compose)
	@echo "Running acceptance tests..."; \
	GEOSERVER_ACCEPTANCE_CONFIG=geoserver_acceptance_tests/ci.config.yaml poetry run pytest --pyargs geoserver_acceptance_tests.tests -v; \
	status=$$?; \
	echo "Stopping docker compose services..."; \
	cd geoserver_acceptance_tests/compose && docker compose -f ci.compose.yaml down -v; \
	exit $$status

.PHONY: acceptance-tests-setup
acceptance-tests-setup: ## Setup acceptance test environment (extract sample data)
	poetry run extract-test-data geoserver_acceptance_tests/compose/geoserver_data

.PHONY: acceptance-tests-up
acceptance-tests-up: ## Start acceptance test Docker services
	@echo "Starting docker compose services..."
	cd geoserver_acceptance_tests/compose && docker compose -f ci.compose.yaml up -d --wait

.PHONY: acceptance-tests-down
acceptance-tests-down: ## Stop acceptance test Docker services
	cd geoserver_acceptance_tests/compose && docker compose -f ci.compose.yaml down -v

.PHONY: acceptance-tests-logs
acceptance-tests-logs: ## Show logs from acceptance test Docker services
	cd geoserver_acceptance_tests/compose && docker compose -f ci.compose.yaml logs
