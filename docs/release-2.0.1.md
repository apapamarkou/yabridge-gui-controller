# Release 2.0.1

## Changes since 2.0.0

### Audio Apps Browser

- Renamed from "Free Plugins Browser" to "Audio Apps Browser" throughout the application
- All source files renamed: `free_plugin.py` → `audio_app.py`, `free_plugins_dialog.py` → `audio_apps_dialog.py`, `FreePlugin` class → `AudioApp`
- Database info files renamed from `plugin.yaml` → `info.yaml` to reflect that entries can be DAWs or other software, not just plugins
- `category` field now supports multiple tags — accepts either a single string or a list in `info.yaml`:
  ```yaml
  category:
    - Compressor
    - Saturation
  ```
- Image thumbnail is now clickable — opens a full-size scrollable preview window
- Added "Update Apps List" button at the bottom of the left panel — downloads the latest `database/software/` entries from the GitHub `main` branch and refreshes the list

### Database

- Large expansion of the database with entries from Analog Obsession, Audio Damage, and additional open-source tools
- Added DAW entries (Ardour, Reaper)
- All existing entries migrated to `info.yaml`

### Setup Assistant

- Fix button now appears correctly for **PipeWire MISSING** state (was missing `fix_key`)
- Fix button now appears correctly for **WirePlumber MISSING** state
- **Setup Assistant button** in the main window now turns red when _any_ environment check fails, not only Wine/yabridge
- Setup Assistant button colour updates automatically when the dialog is closed
- **Confirm dialog** replaced `QMessageBox` with a scrollable `QDialog` + `QTextEdit` — long command lists no longer overflow
- **Realtime limits** check now reads `/proc/self/limits` (effective process limits) instead of parsing `/etc/security/limits.conf` — correctly reflects whether limits are active in the current session
- Red restart warning shown under the Realtime limits row when limits are configured in `limits.conf` but not yet active (requires restart)
- **Wine configuration** step now sets the DPI registry key before launching `winecfg`:
  ```bash
  wine reg add "HKCU\Control Panel\Desktop" /v LogPixels /t REG_DWORD /d 125 /f
  ```

### Arch Linux

- Added multilib enable step before Wine installation — uncomments `[multilib]` in `/etc/pacman.conf` or appends it if missing
- Fixed command ordering issue in `execute_plan` — `sudo` commands containing shell operators are now correctly batched and run in order
- All `pacman` commands use `--noconfirm` for unattended execution

### Packaging

- RPM: added missing `yabridge-gui-controller-gui` binary to `%files` (was causing build failure)
- `fallback_version` bumped to `2.0.1` in `pyproject.toml`

### Developer

- Added `make format` target — runs `ruff format` without the lint check
- Realtime limits unit tests updated to mock `/proc/self/limits` format

---

## Upgrade Notes

- Rename any custom database entries from `plugin.yaml` to `info.yaml`
- `category` in `info.yaml` can now be a list — single string values continue to work
- Tag the release with `git tag v2.0.1` after merging
