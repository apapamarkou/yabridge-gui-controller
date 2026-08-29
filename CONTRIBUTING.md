# Contributing

Contributions are welcome.

## Development setup

```bash
git clone https://github.com/apapamarkou/yabridge-gui-controller.git
cd yabridge-gui-controller
make venv
source .venv/bin/activate
```

## Before submitting a pull request

```bash
make lint   # must pass
make test   # must pass
```

## Packaging

Build all packages:

```bash
make packages
```

Build a specific format interactively:

```bash
make package
```

Test packages with Docker:

```bash
make test-packages   # all formats
make test-package    # interactive
```

Built packages appear in `packaging/output/`. Distro versions are configured in `packaging/distro-versions.conf`.

## Adding a free plugin to the database

1. Create `database/plugins/<slug>/`
2. Add `plugin.yaml` (see existing entries for format)
3. Optionally add `image.png`
4. Submit a pull request

## Reporting issues

Use **Setup Assistant → Diagnostic Report** to generate a system report and include it in your issue.
