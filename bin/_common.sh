#!/usr/bin/env bash


# Check that the current dir is a Git repo
_git_repo_check() {
    if [[ ! -d "${PWD}/.git" ]]; then
        echo "ERROR: Must be in a valid Git repo to run this command"
        exit 1
    fi
}