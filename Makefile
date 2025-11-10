PREFIX = /usr/local
SHAREDIR = $(PREFIX)/share/archlinux
BINDIR = $(PREFIX)/bin

BASH_SCRIPTS = \
	admin/checkservices \
	aur/review \
	package/greposcope \
	package/packages-signed-by \
	package/parse-submodules \
	package/pkggrep \
	package/pkgsearch \
	package/rebuild-todo

PYTHON_SCRIPTS = \
	package/check-pkg-urls \
	package/cleanup-list \
	package/srcinfo-pkg-graph \
	package/staging2testing \
	security/security-tracker-check

SCRIPTS = \
	$(BASH_SCRIPTS) $(PYTHON_SCRIPTS)

.PHONY: install
install:
	for script in $(SCRIPTS); do \
		install -Dm755 $${script} -t $(DESTDIR)$(BINDIR)/; \
	done;

.PHONY: uninstall
uninstall:
	for script in $(SCRIPTS); do \
		rm -rf $(DESTDIR)$(BINDIR)/$${script#*/}; \
	done;
	rmdir $(DESTDIR)$(BINDIR)

.PHONY: release
release:
	git describe --exact-match >/dev/null 2>&1 && { echo "Last commit is already tagged" >&2; exit 1; } || true
	git tag -s $(shell date +%Y%m%d)
	git push --tags
	gh release create --generate-notes $(shell date +%Y%m%d)

check: check-bash check-python

check-bash: $(BASH_SCRIPTS)
	shellcheck $^

check-python: $(PYTHON_SCRIPTS)
	flake8 --ignore W503,E123,E126,E128,E305,E501 $^
