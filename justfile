VIRTUAL_ENV := ".venv"
VIRTUAL_BIN := VIRTUAL_ENV + "/bin"
PROJECT_NAME := "shentry"
TEST_DIR := "tests"

# Clean the project
clean:
    rm -rf {{VIRTUAL_ENV}} dist/ *.egg-info/ .*cache htmlcov *.lcov .coverage
    find . -name '*.pyc' -delete

# Test the project and generate an HTML coverage report
coverage:
    {{VIRTUAL_BIN}}/pytest --cov={{PROJECT_NAME}} --cov-branch --cov-report=html --cov-report=lcov --cov-report=term-missing --cov-fail-under=50

# Lint the project with flake8
flake8:
    {{VIRTUAL_BIN}}/flake8 {{PROJECT_NAME}}.py {{TEST_DIR}}/

# Install the project locally
install:
    uv venv
    uv pip install -e '.[dev]'

# Run linters on the project
lint: flake8

# Test the project
test:
    {{VIRTUAL_BIN}}/pytest
