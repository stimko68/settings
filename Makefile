black:
	black *
.PHONY: black

clean:
	find . -name "*.pyc" -type f -delete
.PHONY: clean

pylint:
	./run_tests.sh --pylint
.PHONY: pylint

shellcheck:
	./run_tests.sh --shellcheck
.PHONY: shellcheck

test:
	./run_tests.sh
.PHONY: test
