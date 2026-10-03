.PHONY: start test eval lint

start:
	python -m uvicorn src.main:app --reload

test:
	python -m pytest -q -p no:cacheprovider

eval:
	python evaluation/run_retrieval_eval.py

lint:
	python -m compileall -q src tests evaluation scripts

