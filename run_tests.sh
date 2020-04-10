#!/usr/bin/env bash
# Run tests against the repo

set -euo pipefail

BASE_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
USE_DOCKER="${USE_DOCKER:-true}"

function run_shellcheck() {
    local cmd="shellcheck -x bin/* *.sh"
    docker run -i -v "${BASE_DIR}":/data koalaman/shellcheck-alpine sh -c 'cd /data && '
}

function run_pylint() {
    printf "pip3 install -U -r requirements.txt \npylint --msg-template=\"{path}:{line}:{column}:{C}:({symbol}){msg}\" pythonlib\n" > TEST_SCRIPT

    if [[ "${USE_DOCKER}" == "true" ]]; then
        docker run -i -v "${BASE_DIR}":/data python:3.8 bash -c 'cd /data && bash TEST_SCRIPT'
    else
        bash TEST_SCRIPT
    fi
}

function run_all() {
    run_shellcheck
    run_pylint
}

function cleanup() {
    rm -f TEST_SCRIPT
}

while test $# -gt 0; do
    _key="$1"
    case "$_key" in
        --pylint)
            echo 'Running pylint tests'
            run_pylint
            shift;;
        --shellcheck)
            echo 'Running shellcheck'
            run_shellcheck
            shift;;
        --)
            shift
            break;;
        *)
            run_all
            ;;
    esac
done

trap cleanup EXIT
