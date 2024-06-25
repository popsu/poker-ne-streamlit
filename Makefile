DEFAULE := help


.PHONY: help
help: ## This help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

st: ## Run streamlit
	streamlit run main.py

update-python-deps: ## Update python dependencies
	pip list --outdated | cut -d ' ' -f1 | xargs -n1 pip install -U
	pip freeze > requirements.txt
