TESTS=./tests/
RESULTS=./tests/results/
PACKAGES=madcore
OPTIONS=--cover-erase --with-coverage --cover-package=${PACKAGES} --cover-html --cover-html-dir=${RESULTS} --with-xunit --xunit-file=${RESULTS}backend_xunit.xml
LINT_MAX_LINE_LENGTH=120

install:
	pip install madcore --upgrade

test-env: clean install
	mkdir -p ${RESULTS}

test:  test-env
	nosetests ${TESTS}

testc: test-env
	nosetests ${TESTS} ${OPTIONS}

lint:
	flake8 --max-line-length=${LINT_MAX_LINE_LENGTH} --exclude=./build .

pylint:
	time pylint madcore --rcfile=pylint.rc

clean:
	rm -rf deb_dist/ dist/ build/ madcore.egg-info/
