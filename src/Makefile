default:
	@echo "Default target not supported - use one of: lint, env" && exit 1

lint:
	pylint -rn -f parseable *.py

env:
	virtualenv --python=python3 env
	guild init --env env
	. env/bin/activate && \
	  pip install cython numpy && \
	  pip install -r requirements.txt
