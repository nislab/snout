# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line.
SPHINXOPTS    =
SPHINXBUILD   = python $(shell which sphinx-build)
SPHINXPROJ    = Snout
SOURCEDIR     = .
APISRCDIR     = source
BUILDDIR      = _build

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help Makefile apidoc clean

create-builddir:
	@mkdir -p $(BUILDDIR)

create-sourcedir:
	@mkdir -p $(APISRCDIR)

apidoc: | create-sourcedir
	@rm -f $(APISRCDIR)/* && sphinx-apidoc -o ./$(APISRCDIR) ..
	@ln -s ../../README.md $(APISRCDIR)/README.md

clean:
	@rm -rf $(APISRCDIR)/*
	@rm -rf $(BUILDDIR)/*

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: Makefile apidoc | create-builddir
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
	@ln -s ../../../../assets $(BUILDDIR)/$@/source/assets