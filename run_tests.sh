#!/usr/bin/env bash
# Primary entrypoint for running tests against the repo

set -euo pipefail

BASE_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
USE_DOCKER="${USE_DOCKER:-true}"

function run_wrapper() {
    local run_cmd="${1}"
    local docker_image="${2:-}"

    if [[ "${USE_DOCKER}" == "true" ]]; then
        run_cmd="cd /data && ${run_cmd}"
        docker run -i --rm -v "${BASE_DIR}":/data "${docker_image}" sh -c "${run_cmd}"
    else
        eval "${run_cmd}"
    fi
}

function run_shellcheck() {
    echo "Running shellcheck"
    run_wrapper "shellcheck -x bin/* *.sh" koalaman/shellcheck-alpine
}

function run_pylint() {
    echo "Running pylint"
    run_wrapper 'pip3 install -U -r requirements.txt && pylint --msg-template="{path}:{line}:{column}:{C}:({symbol}){msg}" pythonlib' python:3.8
}

function run_all() {
    echo "Running all tests"
    local failed_tests=()

    run_shellcheck || failed_tests+=("Shellcheck")
    run_pylint || failed_tests+=("pylint")

    if [[ "${#failed_tests[@]}" -gt 0 ]]; then
        echo "FAILED TESTS: ${failed_tests[*]}"
        exit 1
    fi
}

function cleanup() {
    rm -f TEST_SCRIPT
}

while test $# -gt 0; do
    _key="$1"
    case "$_key" in
        --pylint)
            run_pylint
            shift;;
        --shellcheck)
            run_shellcheck
            shift;;
        --)
            shift
            run_all
            break;;
        *)
            echo "ERROR: invalid option"
            exit 1
            ;;
    esac
done

trap cleanup EXIT
