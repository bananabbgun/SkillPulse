.PHONY: sample collect-sample dashboard test spark-sample

sample:
	python -m skillpulse.run_all --sample

spark-sample:
	python -m skillpulse.run_all --sample --require-spark

collect-sample:
	python -m skillpulse.ingestion.collect --sample

dashboard:
	python -m streamlit run skillpulse/dashboard/app.py

test:
	python -m pytest tests

