PREFIX = /usr/local
SHAREDIR = $(PREFIX)/share/archlinux
REPO = contrib
TAG = $(shell git describe --abbrev=0 --tags)

SCRIPTS = \
	admin/checkservices \
	aur/review	\
	package/co-maintainers \
	package/staging2testing \
	security/security-tracker-check \
	package/cleanup-list.py \


.PHONY: install
install:
	install -dm0755 $(DESTDIR)$(SHAREDIR)
	for script in $(SCRIPTS); do \
		install -Dm755 $${script} -t $(DESTDIR)$(SHAREDIR)/contrib/$${script%/*}; \
	done;

.PHONY: uninstall
uninstall:
	for script in $(SCRIPTS); do \
		rm -rf $(DESTDIR)$(SHAREDIR)/contrib/$${script%/*}; \
	done;
	rmdir $(DESTDIR)$(SHAREDIR)

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
