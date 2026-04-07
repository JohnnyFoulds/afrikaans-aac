.PHONY: setup test lint format

setup:
	conda env create -f environment.yml || conda env update -f environment.yml --prune

test:
	pytest

lint:
	ruff check scripts .claude/scripts

format:
	ruff format scripts .claude/scripts
	ruff check --fix scripts .claude/scripts
