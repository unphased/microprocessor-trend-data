SHELL := /usr/bin/env bash
ROOT := $(shell pwd)

.PHONY: help check inspect generate generate-check generate-rebuild-check interactive snapshot render clean

help:
	@echo "Targets:"
	@echo "  make check     Check required tools"
	@echo "  make inspect   Print repo structure"
	@echo "  make generate  Rebuild .dat files from newdata.txt"
	@echo "  make generate-check"
	@echo "                 Show generator diffs without writing"
	@echo "  make generate-rebuild-check"
	@echo "                 Show full normalization diffs without writing"
	@echo "  make interactive"
	@echo "                 Build embeddable interactive HTML/SVG"
	@echo "  make snapshot  Copy current data into output/data-snapshot"
	@echo "  make render    Render existing gnuplot charts"
	@echo "  make clean     Remove generated output only"

check:
	./scripts/check_tools.sh

inspect:
	python3 ./scripts/inspect_repo.py "$(ROOT)"

generate:
	python3 ./scripts/generate_dat.py --repo "$(ROOT)"

generate-check:
	python3 ./scripts/generate_dat.py --repo "$(ROOT)" --check

generate-rebuild-check:
	python3 ./scripts/generate_dat.py --repo "$(ROOT)" --check --rebuild

interactive:
	python3 ./scripts/build_interactive_html.py --repo "$(ROOT)"

snapshot:
	python3 ./scripts/snapshot_data.py "$(ROOT)" "$(ROOT)/output/data-snapshot"

render:
	./scripts/render_existing.sh "$(ROOT)" "$(ROOT)/output"

clean:
	rm -rf "$(ROOT)/output"/*
