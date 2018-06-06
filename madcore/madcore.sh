#!/bin/bash +x
# to activate: ln -s /Users/polfilm/git/cli/madcore/madcore.sh /usr/local/bin/madcore
$ echo $PWD
pushd () {
    command pushd "$@" > /dev/null
}

popd () {
    command popd "$@" > /dev/null
}


pushd $(python -c "import os; print(os.path.dirname(os.path.realpath('/usr/local/bin/madcore')))")
    source ../../venv_cli/bin/activate
popd


pushd $(python -c "import os; print(os.path.dirname(os.path.realpath('/usr/local/bin/madcore')))")
    python -u madcore.py "$@"
popd
