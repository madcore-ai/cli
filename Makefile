TESTS=./tests/
RESULTS=./tests/results/
PACKAGES=madcore
OPTIONS=--verbose --cover-erase --with-coverage --cover-package=${PACKAGES}
LINT_MAX_LINE_LENGTH=120

install:
	pip install madcore --upgrade

test-env: clean install
	mkdir -p ${RESULTS}

test:
	nosetests --verbose ${TESTS}

testc:
	nosetests ${TESTS} ${OPTIONS}

lint:
	flake8 --max-line-length=${LINT_MAX_LINE_LENGTH} --exclude=./build --exclude=./madcore/libs/__init__.py .

pylint:
	time pylint madcore --rcfile=pylint.rc

clean:
	rm -rf deb_dist/ dist/ build/ madcore.egg-info/
