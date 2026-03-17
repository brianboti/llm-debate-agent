.PHONY: test fmt build-web run-batch

test:
	cd backend && pytest -q

fmt:
	cd backend && ruff check --fix src tests

build-web:
	cd web && npm ci && npm run build

run-batch:
	python scripts/run_experiment.py data/sample_questions.jsonl --limit 3
