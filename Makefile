.DEFAULT_GOAL := help

.PHONY: help
help: ## This help
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

st: ## Run streamlit
	python -m streamlit run main.py

update-python-deps: ## Update python dependencies
	uv pip compile --upgrade requirements.txt requirements-dev.txt

requirements.txt: requirements.in ## Compile requirements.in
	uv pip compile requirements.in --generate-hashes -o requirements.txt

requirements-dev.txt: requirements-dev.in ## Compile requirements-dev.in
	uv pip compile requirements-dev.in --generate-hashes -o requirements-dev.txt

sync-requirements: requirements.txt requirements-dev.txt ## Sync virtualenv with requirements.txt
	uv pip sync requirements.txt requirements-dev.txt
