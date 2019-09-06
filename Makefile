PREFIX = /usr/local
SHAREDIR = $(PREFIX)/share/archlinux

SCRIPTS = \
	admin/checkservices \
	aur/review	\
	package/co-maintainers \
	security/security_tracker_check.py \


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
