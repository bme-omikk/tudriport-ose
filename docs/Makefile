# Common dependencies
COMMON=Makefile inject.tex
# builder commands
PANDOC-HTML=pandoc --toc --standalone --number-sections

PANDOC-PDF =pandoc --toc --standalone --number-sections --include-in-header inject.tex
PANDOC-PDF+=-Vpapersize:a4 -Vmargin-left:0.7in -Vmargin-right:0.7in -Vmargin-top=1.0in -Vmargin-bottom=1.0in

# Add two-format targets (HTML and PDF) here as .html
TARGETS-BOTH=kovetelmeny-specifikacio.html telepites.html
# add html-only and pdf-only targets below
TARGETS-HTML=$(TARGETS-BOTH)
TARGETS-PDF =$(subst .html,.pdf,$(TARGETS-BOTH))
# assemble full list of targets, andd specific, if necessary
TARGETS=$(TARGETS-HTML) $(TARGETS-PDF)

.PHONY: clean all html pdf

all: $(TARGETS)

html: $(TARGETS-HTML)

pdf: $(TARGETS-PDF)

clean:
	rm -f $(TARGETS)

# This is a so called static pattern rule to allow tab completion on pattern rules
# see: https://www.gnu.org/software/make/manual/html_node/Static-Usage.html#Static-Usage
#
$(TARGETS-HTML): %.html: %/README.md $(COMMON)
	$(PANDOC-HTML) $< --output=$@

$(TARGETS-PDF): %.pdf: %/README.md $(COMMON)
	$(PANDOC-PDF)  $< --output=$@
