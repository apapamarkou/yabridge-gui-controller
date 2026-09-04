# Release 2.0.0 — Professional Project Refactor

## Overview

Version 2.0.0 is a major refactor of Yabridge GUI Controller, transforming it from a single-script prototype into a professionally structured Python application with a full packaging pipeline, automated setup assistant, guided remediation, and a curated free plugin browser.

---

## What's New

### Packaging Pipeline

Six package formats built via Docker containers:

| Format | Target |
| --- | --- |
| `.deb` | Debian 13, Ubuntu 26.04 |
| `.rpm` | Fedora 44 |
| `.pkg.tar.zst` | Arch Linux |
| `.AppImage` | Universal (Python 3.11 bundled) |
| `.tar.gz` (binary) | Generic Linux |

- Central orchestrators `packaging/scripts/packages.sh` and `packaging/scripts/test-packages.sh` with interactive and non-interactive modes
- Distro versions configured in `packaging/distro-versions.conf`
- AppImage bundles Python 3.11 + PyQt6 + PyYAML via `python-appimage`, with system libs bundled and RPATH patched
- All SELinux-aware Docker volume mounts (`:z` flag)

### Pro Audio Setup Assistant

Complete guided setup flow for Wine + yabridge on Linux:

- **10 environment checks** run in order: Wine, yabridge, PATH, audio group, realtime limits, Wine prefix, VST directories, yabridge paths, PipeWire, WirePlumber
- **Ordered remediation** — Fix button enabled only on the current active step; phase 2 steps locked until session restart after phase 1
- **Single pkexec prompt** — all privileged commands batched into one `pkexec bash -c` call
- **Inline spinner** per row while a fix is running
- **Logout/restart banners** shown in red when changes require a session restart to take effect
- **Realtime limits** checked against `/proc/self/limits` (effective limits) rather than `/etc/security/limits.conf`, so the check reflects the actual running state
- **Auto and manual modes** for profile PATH and realtime limits configuration
- **Diagnostic report** — full system snapshot copyable for GitHub issues

### Arch Linux: multilib Support

Before installing Wine on Arch, the setup assistant automatically:

1. Uncomments `[multilib]` and its `Include` line in `/etc/pacman.conf` if commented, or appends the block if missing
2. Runs `pacman -Sy --noconfirm` to refresh repositories
3. Proceeds with Wine dependency and tarball installation

All `pacman` commands use `--noconfirm` for unattended execution.

### Environment Checks — Fixes

| Check | Fix |
| --- | --- |
| Wine missing | Install Wine Staging 9.21 (tarball) |
| Wine not configured | Run winetricks + set DPI registry key + winecfg |
| yabridge missing | Install yabridge from GitHub release |
| PATH not configured | Auto-write `~/.profile` entries |
| Audio group missing | `usermod -a -G audio` |
| Realtime limits not active | Write `@audio` limits to `/etc/security/limits.conf` |
| VST directories missing | Create standard Wine VST paths |
| yabridge paths not set | `yabridgectl add` for all VST directories |
| PipeWire missing | Install PipeWire + JACK bridge |
| WirePlumber missing/inactive | Install or enable WirePlumber service |

### Wine Configuration

`plan_configure_wine` now sets the DPI registry key before launching `winecfg`:

```bash
wine reg add "HKCU\Control Panel\Desktop" /v LogPixels /t REG_DWORD /d 125 /f
winecfg
```

### Free Plugin Browser

- Curated YAML database under `database/plugins/`
- Each entry: name, developer, category, description, formats, website, download link, optional image
- Searchable and filterable by category inside the application

### Main Window

- Removed redundant "Wine: Not Installed" / "Yabridge: Not Installed" status labels
- **Setup Assistant** button turns red and bold when any environment check is not OK; updates automatically when the Setup Assistant dialog is closed
- **Scan** button is larger (40 px, bold) in its own labeled row

### Sub-dialog UX

- All Setup Assistant sub-dialogs use `setFixedSize(640, 420)` with scrollable `QTextEdit` for output and command text
- Confirm dialog replaced `QMessageBox` with a scrollable `QDialog` — no more truncated command lists

### Documentation

- Per-distro setup guides: `docs/distros/Ubuntu26.04.md`, `Debian13.md`, `Fedora44.md`, `Arch.md`
- `docs/LinuxProAudioSetup.md` — generic guide for other distributions
- `CONTRIBUTING.md` — contribution and packaging guide

### Testing

- 48 unit and integration tests under `tests/unit/` and `tests/integration/`
- Realtime limits tests updated to mock `/proc/self/limits` format
- All tests pass on Python 3.14 with pytest

---

## Bug Fixes

- Fix button not appearing for PipeWire MISSING state
- Fix button not appearing for WirePlumber MISSING state
- Setup Assistant button not turning red for non-wine/yabridge failures
- Realtime limits showing WARNING even when limits were already active after reboot
- Restart warning not appearing for realtime limits
- RPM build failing due to unpackaged `yabridge-gui-controller-gui` binary
- Arch multilib commands running out of order (sudo batching fix in `execute_plan`)
- AppImage bundling `liblzma.so.5` from Ubuntu 24.04 breaking host `xz` on older distros

---

## Upgrade Notes

- Configuration and plugin databases are stored in `~/.config/yabridge-gui-controller/` and `~/.local/share/yabridge/` — no migration needed
