#!/usr/bin/env bash
# Run tests against the repo

BASE_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"


function run_shellcheck() {
    docker run -i -v "${BASE_DIR}":/data koalaman/shellcheck-alpine sh -c 'cd /data && shellcheck -x bin/* *.sh'
}

function run_pylint() {
    docker run -i -v "${BASE_DIR}":/data python3:3.8-alpine sh -c '
    cd /data
    pip3 install -U -r requirements.txt
    pylint --msg-template="{path}:{line}:{column}:{C}:({symbol}){msg}" pythonlib/
    '
}