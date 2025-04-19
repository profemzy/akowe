.PHONY: clean test lint format check install seed

clean:
	rm -rf __pycache__
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf build
	rm -rf dist
	rm -rf *.egg-info

test:
	python -m tests.test_basic

lint:
	flake8 .

format:
	black .

check: lint test

install:
	pip install -r requirements.txt

run:
	python app.py

setup:
	python direct_setup.py

seed:
	python tools/seed_db.py
