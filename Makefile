# Variables
DOCKER_COMPOSE_FILE := docker-compose.tests.yaml
DOCKER_SERVICE_NAME := tests-web

# Phony targets
.PHONY: lint-all lint-black lint-isort lint-flake8 lint-mypy lint-pylint lint-ruff

# Build the linting service
build-tests:
	docker-compose -f $(DOCKER_COMPOSE_FILE) build $(DOCKER_SERVICE_NAME)

# Run all tests


# Run all linters
lint-all: build-tests
	docker-compose -f $(DOCKER_COMPOSE_FILE) run --rm $(DOCKER_SERVICE_NAME) /bin/bash -c \
		"black --check --diff . && \
		isort --check-only --diff . && \
		flake8 . && \
		mypy . && \
		pylint **/*.py && \
		ruff check ."

# Individual linter targets
lint-black: build-tests
	docker-compose -f $(DOCKER_COMPOSE_FILE) run --rm $(DOCKER_SERVICE_NAME) black --check --diff .

lint-isort: build-tests
	docker-compose -f $(DOCKER_COMPOSE_FILE) run --rm $(DOCKER_SERVICE_NAME) isort --check-only --diff .

lint-flake8: build-tests
	docker-compose -f $(DOCKER_COMPOSE_FILE) run --rm $(DOCKER_SERVICE_NAME) flake8  --verbose .

lint-mypy: build-tests
	docker-compose -f $(DOCKER_COMPOSE_FILE) run --rm $(DOCKER_SERVICE_NAME) mypy --config-file=pyproject.toml .

lint-pylint: build-tests
	docker-compose -f $(DOCKER_COMPOSE_FILE) run --rm $(DOCKER_SERVICE_NAME) pylint --rcfile=/pyproject.toml **/*.py */*.py *.py

lint-ruff: build-tests
	docker-compose -f $(DOCKER_COMPOSE_FILE) run --rm $(DOCKER_SERVICE_NAME) ruff check .

# Run a specific command in the linting container
lint-custom:
	@if [ -z "$(cmd)" ]; then \
		echo "Usage: make lint-custom cmd='your command here'"; \
		exit 1; \
	fi
	docker-compose -f $(DOCKER_COMPOSE_FILE) run --rm $(DOCKER_SERVICE_NAME) /bin/bash -c "$(cmd)"


check-db:
	docker-compose -f $(DOCKER_COMPOSE_FILE) run --rm $(DOCKER_SERVICE_NAME) \
		/bin/bash -c "/bin/bash /check_db_connect.sh"

pytest: build-tests
	docker-compose -f $(DOCKER_COMPOSE_FILE) run --rm $(DOCKER_SERVICE_NAME) \
		/bin/bash -c "\
		echo 'Checking database connection...' && \
		/bin/bash /check_db_connect.sh && \
		echo 'Database connection successful. Running pytest...' && \
		pytest || \
		(echo 'Database connection failed or tests failed' && exit 1)"

pytest-cov: build-tests
	docker-compose -f $(DOCKER_COMPOSE_FILE) run --rm $(DOCKER_SERVICE_NAME) \
		/bin/bash -c "\
		echo 'Checking database connection...' && \
		/bin/bash /check_db_connect.sh && \
		echo 'Database connection successful. Running pytest with coverage...' && \
		pytest --cov=. --cov-report=term-missing || \
		(echo 'Database connection failed or tests failed' && exit 1)"

local-black:
	black --config=./pyproject.toml .
