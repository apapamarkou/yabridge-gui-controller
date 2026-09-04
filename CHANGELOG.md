# Changelog

## [2.0.0] — Unreleased

### Added
- `src/` layout with proper Python package structure
- `pyproject.toml` with setuptools-scm versioning
- Pro Audio Setup Assistant with environment detection
- Guided remediation for Debian 13, Ubuntu 26.04, Fedora 44, Arch Linux
- Manual instructions for unsupported distributions
- Free Plugin Browser with YAML-based database
- Diagnostic report generation
- pytest test suite
- Ruff linting
- GitHub Actions CI
- `.deb`, `.rpm`, `.AppImage`, `.tar.gz` packaging
- `Makefile` developer interface
- Distribution detection via `/etc/os-release`

### Changed
- Refactored single-file application into layered package architecture
- GUI separated from core logic and OS interfaces
- Error handling improved throughout

### Preserved
- All original plugin listing functionality
- Original scan/sync workflow
- Original environment checks (wine, yabridgectl)
- Original About dialog content

## [1.0.0]

- Initial release
