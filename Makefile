.PHONY: test lint format check-all

# Run pytest
test:
	docker-compose run --rm test-web pytest -v

# Run pylint
lint:
	docker-compose run --rm test-web pylint **/*.py

# Run flake8
flake8:
	docker-compose run --rm test-web flake8 .

# Run black in check mode
black-check:
	docker-compose run --rm test-web black --check .

# Run black and modify files
format:
	docker-compose run --rm test-web black .

# Run all checks
check-all: test lint flake8 black-check

# Run all checks and format
check-and-format: check-all format
