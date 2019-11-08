ensure-venvdir:
	test -d venv || (python3 -m venv venv && . venv/bin/activate && pip install --upgrade pip && pip install -Ur requirements.txt)

venv: | ensure-venvdir

venv-update: | venv
	. venv/bin/activate && pip install --upgrade pip && pip install -Ur requirements.txt

.PHONY: pep8 test test-coverage clean docs install-pydeps

pep8:
	@flake8 Snout.py --exit-zero --tee --output-file=tests/pep8.log

docs:
	cd docs && make html

test:
	pytest --junitxml=tests/report.xml tests

test-coverage:
	python3 -m pytest --cov=snout tests/

.PHONY: ensure-submodules
ensure-submodules:
	@git submodule status
	@git submodule init
	@git submodule sync
	@git submodule update
	@git submodule status

install-deps-apt-update:
	apt-get update -qq

install-deps-pybombs-update:
	pybombs update

install-deps-texlive: | install-deps-apt-update
	apt-get install -y -qq texlive

install-deps-gr:
	pybombs install gr-foo gr-ieee-80211 gr-ieee-802154

install-deps: install-deps-texlive install-deps-gr

install-vendor-btle: | ensure-submodules
	mkdir -p vendor/BTLE/host/build && \
		cmake -Bvendor/BTLE/host/build -Hvendor/BTLE/host && \
		make -C vendor/BTLE/host/build && \
		make install -C vendor/BTLE/host/build

install-vendor-scapy-radio: | ensure-submodules
	cd scapy-radio/scapy && \
		pip3 install .

install-vendor: install-vendor-btle install-vendor-scapy-radio

install-pydeps:
	pip3 install --upgrade pip && pip3 install -Ur requirements.txt

install: | install-deps install-vendor install-pydeps
	pip3 install .

develop: | install-pydeps
	pip3 install -e .

clean:
	rm -rf venv
	rm -rf tests/coverage-report
	rm -rf .coverage
	rm -rf tests/report.xml
	rm -rf tests/pep8.log
	rm -rf .pytest_cache
	find -iname "*.pyc" -delete
	find -iname "__pycache__" -delete
