PYTHON_BINARY := python3
VIRTUAL_ENV := venv
VIRTUAL_BIN := $(VIRTUAL_ENV)/bin
PROJECT_NAME := shentry
TEST_DIR := tests

## help - Display help about make targets for this Makefile
help:
	@cat Makefile | grep '^## ' --color=never | cut -c4- | sed -e "`printf 's/ - /\t- /;'`" | column -s "`printf '\t'`" -t

## clean - Clean the project
clean:
	rm -rf $(VIRTUAL_ENV) dist/ *.egg-info/ .*cache htmlcov *.lcov .coverage
	find . -name '*.pyc' -delete

## coverage - Test the project and generate an HTML coverage report
coverage:
	$(VIRTUAL_BIN)/pytest --cov=$(PROJECT_NAME) --cov-branch --cov-report=html --cov-report=lcov --cov-report=term-missing --cov-fail-under=50

## flake8 - Lint the project with flake8
flake8:
	$(VIRTUAL_BIN)/flake8 $(PROJECT_NAME).py $(TEST_DIR)/

## install - Install the project locally
install:
	$(PYTHON_BINARY) -m venv $(VIRTUAL_ENV)
	$(VIRTUAL_BIN)/pip install -r requirements-tests.txt -e .

## lint - Run linters on the project
lint: flake8

## test - Test the project
test:
	$(VIRTUAL_BIN)/pytest

.PHONY: help clean coverage flake8 install lint test
