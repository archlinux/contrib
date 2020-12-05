PREFIX = /usr/local
SHAREDIR = $(PREFIX)/share/archlinux
BINDIR = $(PREFIX)/bin
REPO = contrib
TAG = $(shell git describe --abbrev=0 --tags)

SCRIPTS = \
	admin/checkservices \
	aur/review	\
	package/pkgsearch \
	package/staging2testing \
	security/security-tracker-check \
	package/cleanup-list \
	package/srcinfo-pkg-graph \


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

.PHONY: tag
tag:
	git describe --exact-match >/dev/null 2>&1 || git tag -s $(shell date +%Y%m%d)
	git push --tags

.PHONY: release
release:
	mkdir -p releases
	git archive --prefix=${REPO}-${TAG}/ -o releases/${REPO}-${TAG}.tar.gz ${TAG};
	gpg --detach-sign -o releases/${REPO}-${TAG}.tar.gz.sig releases/${REPO}-${TAG}.tar.gz
	hub release create -m "Release: ${TAG}" -a releases/${REPO}-${TAG}.tar.gz.sig -a releases/${REPO}-${TAG}.tar.gz ${TAG}
