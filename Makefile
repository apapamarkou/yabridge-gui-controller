PYTHON     := python3
PIP        := pip3
VENV       := .venv
VENV_BIN   := $(VENV)/bin
SRC        := src
PKG_NAME   := yabridge-gui-controller

# Use venv python if it exists, otherwise system python
ifeq ($(wildcard $(VENV_BIN)/python),)
    PY := $(PYTHON)
    PYTEST := pytest
    RUFF := ruff
else
    PY := $(VENV_BIN)/python
    PYTEST := $(VENV_BIN)/pytest
    RUFF := $(VENV_BIN)/ruff
endif

.PHONY: all run install uninstall test lint packages package \
        test-packages test-package venv clean help

all: help

## Run the application from source
run:
	PYTHONPATH=$(SRC) $(PY) -m yabridge_gui

## Create a virtual environment and install dev dependencies
venv:
	$(PYTHON) -m venv $(VENV)
	$(VENV_BIN)/pip install --upgrade pip
	$(VENV_BIN)/pip install -e ".[dev]" 2>/dev/null || \
	    $(VENV_BIN)/pip install -e . && \
	    $(VENV_BIN)/pip install pytest ruff pyyaml

## Install the application locally (user install)
install:
	$(PIP) install --user -e .
	@mkdir -p "$(HOME)/.local/share/applications"
	@mkdir -p "$(HOME)/.local/share/icons"
	@cp src/yabridge-gui-controller.png "$(HOME)/.local/share/icons/$(PKG_NAME).png" 2>/dev/null || true
	@cat > "$(HOME)/.local/share/applications/$(PKG_NAME).desktop" <<'EOF'
[Desktop Entry]
Type=Application
Name=Yabridge GUI Controller
Comment=Manage Windows VST/VST3 plugins via yabridge
Exec=$(PKG_NAME)
Icon=$(HOME)/.local/share/icons/$(PKG_NAME).png
Terminal=false
Categories=AudioVideo;Audio;Settings;
StartupNotify=true
EOF
	@echo "Installed. Run: $(PKG_NAME)"

## Uninstall the locally installed application
uninstall:
	$(PIP) uninstall -y $(PKG_NAME) 2>/dev/null || true
	rm -f "$(HOME)/.local/share/applications/$(PKG_NAME).desktop"
	rm -f "$(HOME)/.local/share/icons/$(PKG_NAME).png"
	@echo "Uninstalled."

## Run the test suite
test:
	PYTHONPATH=$(SRC) $(PYTEST) tests/ -v --tb=short

## Run linting and format checks
lint:
	$(RUFF) check $(SRC)/ tests/
	$(RUFF) format --check $(SRC)/ tests/

## Auto-fix lint issues
lint-fix:
	$(RUFF) check --fix $(SRC)/ tests/
	$(RUFF) format $(SRC)/ tests/

## Build ALL package formats
packages:
	@chmod +x packaging/deb/build.sh packaging/rpm/build.sh \
	           packaging/appimage/build.sh packaging/tarball/build.sh
	bash packaging/deb/build.sh
	bash packaging/tarball/build.sh
	@echo ""
	@echo "Note: RPM build requires rpmbuild. AppImage build requires appimagetool."
	@echo "Run individually: bash packaging/rpm/build.sh  /  bash packaging/appimage/build.sh"

## Interactively select and build a single package format
package:
	@echo ""
	@echo "Select package to build:"
	@echo ""
	@echo "  1) deb"
	@echo "  2) rpm"
	@echo "  3) AppImage"
	@echo "  4) tar.gz"
	@echo "  5) all"
	@echo "  q) quit"
	@echo ""
	@read -p "Selection: " sel; \
	case "$$sel" in \
	    1) bash packaging/deb/build.sh ;; \
	    2) bash packaging/rpm/build.sh ;; \
	    3) bash packaging/appimage/build.sh ;; \
	    4) bash packaging/tarball/build.sh ;; \
	    5) $(MAKE) packages ;; \
	    q|Q) echo "Cancelled." ;; \
	    *) echo "Invalid selection." ;; \
	esac

## Test ALL package formats using containers
test-packages:
	@chmod +x packaging/deb/test.sh packaging/rpm/test.sh \
	           packaging/tarball/test.sh packaging/appimage/test.sh
	bash packaging/deb/test.sh
	bash packaging/rpm/test.sh
	bash packaging/tarball/test.sh
	bash packaging/appimage/test.sh

## Interactively select and test a single package format
test-package:
	@echo ""
	@echo "Select package to test:"
	@echo ""
	@echo "  1) deb"
	@echo "  2) rpm"
	@echo "  3) AppImage"
	@echo "  4) tar.gz"
	@echo "  5) all"
	@echo "  q) quit"
	@echo ""
	@read -p "Selection: " sel; \
	case "$$sel" in \
	    1) bash packaging/deb/test.sh ;; \
	    2) bash packaging/rpm/test.sh ;; \
	    3) bash packaging/appimage/test.sh ;; \
	    4) bash packaging/tarball/test.sh ;; \
	    5) $(MAKE) test-packages ;; \
	    q|Q) echo "Cancelled." ;; \
	    *) echo "Invalid selection." ;; \
	esac

## Remove build artifacts
clean:
	rm -rf dist/ build/ *.egg-info src/*.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true

## Show this help
help:
	@echo ""
	@echo "Yabridge GUI Controller — Developer Commands"
	@echo "============================================"
	@echo ""
	@grep -E '^## ' $(MAKEFILE_LIST) | sed 's/## /  /' | \
	    awk 'BEGIN{target=""} /^  [a-z]/{target=$$0; next} {print target": "$$0; target=""}'
	@echo ""
	@grep -E '^[a-zA-Z_-]+:' $(MAKEFILE_LIST) | \
	    grep -v "^all:" | grep -v "^\.PHONY" | \
	    sed 's/:.*//' | \
	    awk '{printf "  make %-20s\n", $$1}'
	@echo ""
