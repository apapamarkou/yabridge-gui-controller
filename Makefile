.PHONY: run test lint lint-fix install uninstall venv clean \
        packages package test-packages test-package test-appimage help

PYTHON := python3
VENV   := .venv

ifeq ($(wildcard $(VENV)/bin/python),)
    PY     := $(PYTHON)
    PYTEST := pytest
    RUFF   := ruff
else
    PY     := $(VENV)/bin/python
    PYTEST := $(VENV)/bin/pytest
    RUFF   := $(VENV)/bin/ruff
endif

run:
	PYTHONPATH=src $(PY) -m yabridge_gui

venv:
	$(PYTHON) -m venv $(VENV)
	$(VENV)/bin/pip install --upgrade pip
	$(VENV)/bin/pip install -e ".[dev]" 2>/dev/null || \
	    $(VENV)/bin/pip install -e . && \
	    $(VENV)/bin/pip install pytest ruff pyyaml

install:
	bash install

uninstall:
	pip3 uninstall -y yabridge-gui-controller 2>/dev/null || true
	rm -f "$(HOME)/.local/share/applications/yabridge-gui-controller.desktop"
	rm -f "$(HOME)/.local/share/icons/hicolor/256x256/apps/yabridge-gui-controller.png"
	@echo "Uninstalled."

test:
	PYTHONPATH=src $(PYTEST) tests/ -v --tb=short

lint:
	$(RUFF) check src/ tests/
	$(RUFF) format --check src/ tests/

lint-fix:
	$(RUFF) check --fix src/ tests/
	$(RUFF) format src/ tests/

packages:
	bash packaging/scripts/packages.sh

package:
	bash packaging/scripts/packages.sh --interactive

test-packages:
	bash packaging/scripts/test-packages.sh

test-package:
	bash packaging/scripts/test-packages.sh --interactive

test-appimage:
	bash packaging/tests/test-appimage.sh packaging/output/YabridgeGuiController-*.AppImage

clean:
	rm -rf dist/ build/ *.egg-info src/*.egg-info packaging/output/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true

help:
	@echo ""
	@echo "Yabridge GUI Controller — Developer Commands"
	@echo "============================================"
	@echo ""
	@echo "  make run            Run from source"
	@echo "  make venv           Create virtualenv and install dev deps"
	@echo "  make install        Install locally (runs ./install)"
	@echo "  make uninstall      Remove local installation"
	@echo "  make test           Run test suite"
	@echo "  make lint           Lint and format check"
	@echo "  make lint-fix       Auto-fix lint issues"
	@echo "  make packages       Build all package formats (non-interactive)"
	@echo "  make package        Interactively select and build a package"
	@echo "  make test-packages  Test all packages with Docker"
	@echo "  make test-package   Interactively select and test a package"
	@echo "  make test-appimage  Test the AppImage directly"
	@echo "  make clean          Remove build artifacts"
	@echo ""
