.PHONY: fmt lint type test all

fmt:
ruff check --fix .

lint:
ruff check .

type:
mypy --strict src tests

test:
pytest

all: lint type test
