PRODUCT=lcg-info-dynamic-maui
VERSION=2.1.0
RELEASE=1

TAR=/bin/tar

SRCS = lcg-info-dynamic-maui TorqueMauiConfParser.py

_rpmtopdir = $(PWD)/rpm-build
_rpmsrcdir = $(_rpmtopdir)/SOURCES
_rpmbuilddir = $(_rpmtopdir)/BUILD
_prodsrcdir = $(_rpmbuilddir)/$(PRODUCT)-$(VERSION)

all:	rpm

# Required to disable building pyc/pyo
rpm:	$(_rpmsrcdir)/$(PRODUCT).tar.gz
	@echo Building rpm...
        # __os_install_post redefinition required to disable building pyc/pyo
	@rpmbuild -ba --define '_sourcedir $(_rpmsrcdir)' \
                      --define '_builddir $(_rpmbuilddir)' \
                      --define 'prodversion $(VERSION)' \
                      --define 'prodrelease $(RELEASE)' \
                      --define '__os_install_post %{nil}' \
                         $(PRODUCT).spec
	@rm -R $(_rpmsrcdir)

$(_rpmsrcdir)/$(PRODUCT).tar.gz: $(SRCS) $(_rpmbuilddir) $(_rpmsrcdir)
	@echo "Building tar file for sources ($(SRCS))..."
	@if [ -d  $(_prodsrcdir) ]; then \
	  rm -Rf $(_prodsrcdir); \
	fi
	@mkdir -p $(_prodsrcdir)
	@cp $(SRCS) $(_prodsrcdir)
	@$(TAR) -cz -C $(_rpmbuilddir) --exclude .svn --exclude CVS --exclude '*.py[co]' -f $@ $(PRODUCT)-$(VERSION)

$(_rpmbuilddir):
	@mkdir -p $(_rpmbuilddir)

$(_rpmsrcdir):
	@mkdir -p $(_rpmsrcdir)

