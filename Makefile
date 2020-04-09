test:
	docker run -i -v ${PWD}:/data koalaman/shellcheck-alpine sh -c 'cd /data && shellcheck -x bin/* *.sh'
.PHONY: test