SHELL := /bin/bash

.PHONY: env clean publish docs

init: env
	source env/bin/activate && python setup.py develop

clean:
	git clean -Xfd

env:
	mkdir -p env && cd env && virtualenv --no-site-packages . && cd ..

publish:
	python setup.py sdist upload

docs:
	cd docs && make html