"""Distribution-specific installer abstractions."""

from __future__ import annotations

import subprocess
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

from yabridge_gui.core.distro import Distribution, detect_distribution
from yabridge_gui.core.wine import WINE_DIR, WINE_URL, WINE_VERSION
from yabridge_gui.core.yabridge import YABRIDGE_DIR, YABRIDGE_URL, YABRIDGE_VERSION


@dataclass
class InstallPlan:
    """Describes what will happen before execution."""

    title: str
    commands: list[str]  # executable command strings
    requires_sudo: bool
    requires_logout: bool = False
    is_manual: bool = False
    manual_instructions: str = ""
    # Commands shown in the clipboard button — only the raw shell commands,
    # no prose or comment lines. Auto-derived from manual_instructions if empty.
    copyable_commands: list[str] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.copyable_commands is None:
            self.copyable_commands = _extract_commands(self.manual_instructions)


def _extract_commands(text: str) -> list[str]:
    """Return only executable lines from instruction text (skip comments/prose)."""
    cmds = []
    for line in text.splitlines():
        stripped = line.strip()
        if (
            stripped
            and not stripped.startswith("#")
            and not stripped[0].isalpha()
            or stripped.startswith(
                (
                    "sudo ",
                    "wget ",
                    "curl ",
                    "tar ",
                    "mkdir ",
                    "chmod ",
                    "cat ",
                    "cp ",
                    "rm ",
                    "systemctl ",
                    "update-",
                    "./",
                    "export ",
                    "nano ",
                    "winecfg",
                    "./winetricks",
                )
            )
        ):
            cmds.append(stripped)
    return cmds


class BaseInstaller(ABC):
    def __init__(self, distro: Distribution):
        self.distro = distro

    @abstractmethod
    def plan_install_wine_deps(self) -> InstallPlan: ...

    @abstractmethod
    def plan_install_pipewire_jack(self) -> InstallPlan: ...

    @abstractmethod
    def plan_install_qpwgraph(self) -> InstallPlan: ...

    def plan_install_yabridge(self) -> InstallPlan:
        return InstallPlan(
            title="Install yabridge",
            commands=[
                f"mkdir -p {YABRIDGE_DIR}",
                f"curl -L -o /tmp/yabridge-{YABRIDGE_VERSION}.tar.gz {YABRIDGE_URL}",
                f"tar -xzf /tmp/yabridge-{YABRIDGE_VERSION}.tar.gz -C {YABRIDGE_DIR} --strip-components=1",
            ],
            requires_sudo=False,
        )

    def plan_install_wine_full(self) -> InstallPlan:
        """Full wine-staging install: deps + tarball download + desktop entry."""
        deps_plan = self.plan_install_wine_deps()
        tarball_plan = self.plan_install_wine_tarball()
        return InstallPlan(
            title="Install Wine Staging (full)",
            commands=deps_plan.commands + tarball_plan.commands,
            requires_sudo=deps_plan.requires_sudo,
        )

    def plan_install_wine_tarball(self) -> InstallPlan:
        from pathlib import Path

        home = str(Path.home())
        apps_dir = f"{home}/.local/share/applications"
        desktop_entry = (
            f'mkdir -p "{apps_dir}"\n'
            f"cat > \"{apps_dir}/wine921.desktop\" <<'EOF'\n"
            f"[Desktop Entry]\n"
            f"Name=Wine 9.21\n"
            f"Comment=Run Windows applications with Wine 9.21\n"
            f"Exec={home}/.local/share/wine-staging-{WINE_VERSION}/bin/wine %f\n"
            f"Terminal=false\n"
            f"Type=Application\n"
            f"MimeType=application/x-ms-dos-executable;application/x-msdownload;\n"
            f"NoDisplay=false\n"
            f"Categories=Utility;\n"
            f"EOF\n"
            f'update-desktop-database "{apps_dir}"'
        )
        return InstallPlan(
            title="Install Wine Staging",
            commands=[
                f"curl -L -o wine-{WINE_VERSION}-staging-amd64.tar.xz {WINE_URL}",
                f"mkdir -p {WINE_DIR}",
                f"tar -xJf wine-{WINE_VERSION}-staging-amd64.tar.xz --strip-components=1 -C {WINE_DIR}",
                desktop_entry,
            ],
            requires_sudo=False,
        )

    def plan_create_vst_dirs(self) -> InstallPlan:
        from yabridge_gui.core.yabridge import VST_DIRS

        return InstallPlan(
            title="Create VST directories",
            commands=[f'mkdir -p "{d}"' for d in VST_DIRS],
            requires_sudo=False,
        )

    def plan_configure_yabridge_paths(self) -> InstallPlan:
        home = Path.home()
        vst_dirs = [
            home / ".wine/drive_c/Program Files/Steinberg/VstPlugins",
            home / ".wine/drive_c/Program Files/Common Files/VST3",
            home / ".wine/drive_c/Program Files/VSTPlugins",
        ]
        cmds = [f'yabridgectl add "{d}"' for d in vst_dirs]
        cmds.append("yabridgectl set --path-auto")
        return InstallPlan(title="Configure yabridge paths", commands=cmds, requires_sudo=False)

    def plan_add_audio_group(self) -> InstallPlan:
        import os

        user = os.getenv("USER") or os.getenv("LOGNAME") or "$USER"
        return InstallPlan(
            title="Add user to audio group",
            commands=[f"sudo usermod -a -G audio {user}"],
            requires_sudo=True,
            requires_logout=True,
        )

    def plan_configure_wine(self) -> InstallPlan:
        winetricks_url = (
            "https://raw.githubusercontent.com/Winetricks/winetricks/master/src/winetricks"
        )
        return InstallPlan(
            title="Configure Wine (winetricks + winecfg)",
            commands=[
                f"wget -O /tmp/winetricks {winetricks_url}",
                "chmod +x /tmp/winetricks",
                "/tmp/winetricks vcrun6sp6",
                'wine reg add "HKCU\\Control Panel\\Desktop" /v LogPixels /t REG_DWORD /d 125 /f',
                "winecfg",
            ],
            requires_sudo=False,
        )

    def plan_configure_rt_limits(self) -> InstallPlan:
        return InstallPlan(
            title="Configure realtime limits",
            commands=[],
            requires_sudo=True,
            is_manual=True,
            manual_instructions=(
                "Open the file in a terminal:\n\n"
                "sudo nano /etc/security/limits.conf\n\n"
                "Add the following lines before '# End of file':\n\n"
                "@audio           -      rtprio           95\n"
                "@audio           -      memlock          unlimited\n"
                "@audio           -      nice             10\n"
            ),
        )

    def plan_configure_rt_limits_auto(self) -> InstallPlan:
        """Insert only missing @audio lines before '# End of file' in /etc/security/limits.conf."""
        limits_file = "/etc/security/limits.conf"
        try:
            content = Path(limits_file).read_text()
        except OSError:
            content = ""
        lines_to_add = []
        if "rtprio" not in content or "@audio" not in content:
            lines_to_add.append("@audio           -      rtprio           95")
        if "memlock" not in content or "@audio" not in content:
            lines_to_add.append("@audio           -      memlock          unlimited")
        if "nice" not in content or "@audio" not in content:
            lines_to_add.append("@audio           -      nice             10")
        if not lines_to_add:
            return InstallPlan(
                title="Configure realtime limits",
                commands=[],
                requires_sudo=False,
                manual_instructions="All required lines already present.",
            )
        block = "\n".join(lines_to_add)
        if "# End of file" in content:
            new_content = content.replace("# End of file", f"{block}\n# End of file", 1)
        else:
            new_content = content.rstrip("\n") + f"\n{block}\n# End of file\n"
        # Write to a temp file, then pkexec cp it into place
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", suffix=".conf", delete=False) as tmp:
            tmp.write(new_content)
            tmp_name = tmp.name
        return InstallPlan(
            title="Configure realtime limits (auto)",
            commands=[f"pkexec cp {tmp_name} {limits_file}"],
            requires_sudo=True,
        )

    def plan_configure_profile(self) -> InstallPlan:
        return InstallPlan(
            title="Configure ~/.profile",
            commands=[],
            requires_sudo=False,
            is_manual=True,
            manual_instructions=(
                "Open the file in a terminal:\n\n"
                "nano ~/.profile\n\n"
                "Add the following lines:\n\n"
                f'export PATH="$PATH:$HOME/.local/share/yabridge:$HOME/.local/share/wine-staging-{WINE_VERSION}/bin"\n'
                "export WINEFSYNC=1\n\n"
                "If your display manager does not source ~/.profile at login (e.g. LightDM),\n"
                "also open ~/.xsessionrc:\n\n"
                "nano ~/.xsessionrc\n\n"
                "And add:\n\n"
                'if [ -r "$HOME/.profile" ]; then\n'
                '    . "$HOME/.profile"\n'
                "fi\n"
            ),
        )

    def plan_configure_profile_auto(self) -> InstallPlan:
        """Append only missing PATH/env lines to ~/.profile (and ~/.xsessionrc if needed)."""
        from pathlib import Path as _Path

        home = _Path.home()
        profile = home / ".profile"
        xsession = home / ".xsessionrc"

        profile_content = profile.read_text() if profile.exists() else ""
        lines_to_add = []
        if (
            ".local/share/yabridge" not in profile_content
            or f"wine-staging-{WINE_VERSION}" not in profile_content
        ):
            lines_to_add.append(
                f'export PATH="$PATH:$HOME/.local/share/yabridge:$HOME/.local/share/wine-staging-{WINE_VERSION}/bin"'
            )
        if "WINEFSYNC" not in profile_content:
            lines_to_add.append("export WINEFSYNC=1")

        cmds = []
        if lines_to_add:
            block = "\n".join(lines_to_add)
            cmds.append(f"printf '\\n{block}\\n' >> {profile}")

        xsession_content = xsession.read_text() if xsession.exists() else ""
        source_snippet = '. "$HOME/.profile"'
        if source_snippet not in xsession_content:
            snippet = 'if [ -r "$HOME/.profile" ]; then\n    . "$HOME/.profile"\nfi'
            cmds.append(f"printf '\\n{snippet}\\n' >> {xsession}")

        if not cmds:
            return InstallPlan(
                title="Configure PATH (auto)",
                commands=[],
                requires_sudo=False,
                manual_instructions="All required lines already present.",
            )
        return InstallPlan(
            title="Configure PATH (auto)",
            commands=cmds,
            requires_sudo=False,
        )

    def execute_plan(self, plan: InstallPlan) -> tuple[bool, str]:
        """Execute a non-manual plan. Returns (success, output).

        All sudo commands are batched into a single pkexec call so the user
        is only prompted for a password once.
        """
        if plan.is_manual:
            return False, "Manual action required"

        sudo_cmds: list[str] = []
        other_cmds: list[str] = []
        for cmd_str in plan.commands:
            has_shell_ops = "\n" in cmd_str or any(op in cmd_str for op in ("<<", "&&", "|", "$"))
            parts = [] if has_shell_ops else _parse_cmd(cmd_str)
            if parts and parts[0] == "sudo":
                sudo_cmds.append(" ".join(parts[1:]))
            elif has_shell_ops and cmd_str.lstrip().startswith("sudo "):
                sudo_cmds.append(cmd_str.lstrip()[len("sudo ") :])
            else:
                other_cmds.append(cmd_str)

        output_lines: list[str] = []

        # Run all sudo commands in one pkexec bash -c invocation
        if sudo_cmds:
            combined = " && ".join(sudo_cmds)
            try:
                r = subprocess.run(
                    ["pkexec", "bash", "-c", combined],
                    capture_output=True,
                    text=True,
                    timeout=300,
                )
                output_lines.append(r.stdout + r.stderr)
                if r.returncode != 0:
                    return False, "\n".join(output_lines)
            except (FileNotFoundError, OSError, subprocess.TimeoutExpired) as e:
                return False, str(e)

        # Run non-sudo commands individually
        for cmd_str in other_cmds:
            if "\n" in cmd_str or any(op in cmd_str for op in ("<<", "&&", "|")):
                parts = ["bash", "-c", cmd_str]
            else:
                parts = _parse_cmd(cmd_str)
            try:
                r = subprocess.run(parts, capture_output=True, text=True, timeout=300)
                output_lines.append(r.stdout + r.stderr)
                if r.returncode != 0:
                    return False, "\n".join(output_lines)
            except (FileNotFoundError, OSError, subprocess.TimeoutExpired) as e:
                return False, str(e)

        return True, "\n".join(output_lines)


class AptInstaller(BaseInstaller):
    """Installer for Debian/Ubuntu."""

    def plan_install_wine_deps(self) -> InstallPlan:
        if self.distro.id == "ubuntu":
            libasound = "libasound2t64:amd64 libasound2t64:i386"
        else:
            libasound = "libasound2:amd64 libasound2:i386"
        pkgs = (
            f"libc6:amd64 libc6:i386 cabextract curl wget "
            f"libfreetype6:amd64 libfreetype6:i386 "
            f"libfontconfig1:amd64 libfontconfig1:i386 "
            f"libx11-6:amd64 libx11-6:i386 "
            f"libxext6:amd64 libxext6:i386 "
            f"libxrender1:amd64 libxrender1:i386 "
            f"libxcursor1:amd64 libxcursor1:i386 "
            f"libxi6:amd64 libxi6:i386 "
            f"libxinerama1:amd64 libxinerama1:i386 "
            f"libxrandr2:amd64 libxrandr2:i386 "
            f"{libasound} libgl1:amd64 libgl1:i386"
        )
        return InstallPlan(
            title="Install Wine dependencies",
            commands=[
                "sudo dpkg --add-architecture i386",
                "sudo apt update",
                f"sudo apt install -y {pkgs}",
            ],
            requires_sudo=True,
        )

    def plan_install_pipewire_jack(self) -> InstallPlan:
        return InstallPlan(
            title="Install PipeWire JACK packages",
            commands=[
                "sudo apt install -y pipewire-jack pipewire-audio-client-libraries libspa-0.2-jack",
                "systemctl --user --now enable wireplumber.service",
                "sudo mkdir -p /etc/pipewire/media-session.d",
                "sudo touch /etc/pipewire/media-session.d/with-jack",
                "sudo cp /usr/share/doc/pipewire/examples/ld.so.conf.d/pipewire-jack-*.conf /etc/ld.so.conf.d/",
                "sudo ldconfig",
            ],
            requires_sudo=True,
        )

    def plan_install_qpwgraph(self) -> InstallPlan:
        return InstallPlan(
            title="Install qpwgraph",
            commands=["sudo apt install -y qpwgraph"],
            requires_sudo=True,
        )


class DnfInstaller(BaseInstaller):
    """Installer for Fedora."""

    def plan_install_wine_deps(self) -> InstallPlan:
        pkgs = (
            "glibc.i686 cabextract curl wget freetype freetype.i686 "
            "fontconfig fontconfig.i686 libX11 libX11.i686 libXext libXext.i686 "
            "libXrender libXrender.i686 libXcursor libXcursor.i686 "
            "libXi libXi.i686 libXinerama libXinerama.i686 libXrandr libXrandr.i686"
        )
        return InstallPlan(
            title="Install Wine dependencies",
            commands=[f"sudo dnf -y install {pkgs}"],
            requires_sudo=True,
        )

    def plan_install_pipewire_jack(self) -> InstallPlan:
        # Fedora ships PipeWire with JACK support by default
        return InstallPlan(
            title="PipeWire JACK (Fedora)",
            commands=[],
            requires_sudo=False,
            is_manual=True,
            manual_instructions="Fedora 44 ships PipeWire with JACK support by default. No additional packages needed.",
        )

    def plan_install_qpwgraph(self) -> InstallPlan:
        return InstallPlan(
            title="Install qpwgraph",
            commands=["sudo dnf install -y qpwgraph"],
            requires_sudo=True,
        )


class PacmanInstaller(BaseInstaller):
    """Installer for Arch Linux."""

    def plan_enable_multilib(self) -> InstallPlan:
        # If already uncommented: do nothing.
        # If commented out: uncomment it.
        # If absent entirely: append it.
        cmd = (
            "grep -q '^\\[multilib\\]' /etc/pacman.conf || "
            "{ grep -q '^#\\[multilib\\]' /etc/pacman.conf && "
            "sed -i '/^#\\[multilib\\]/{s/^#//;n;s/^#//}' /etc/pacman.conf || "
            "printf '\\n[multilib]\\nInclude = /etc/pacman.d/mirrorlist\\n' >> /etc/pacman.conf; }"
        )
        return InstallPlan(
            title="Enable multilib repository",
            commands=[
                f'sudo bash -c "{cmd}"',
                "sudo pacman -Sy --noconfirm",
            ],
            requires_sudo=True,
        )

    def plan_install_wine_full(self) -> InstallPlan:
        multilib = self.plan_enable_multilib()
        deps = self.plan_install_wine_deps()
        tarball = self.plan_install_wine_tarball()
        return InstallPlan(
            title="Install Wine Staging (full)",
            commands=multilib.commands + deps.commands + tarball.commands,
            requires_sudo=True,
        )

    def plan_install_wine_deps(self) -> InstallPlan:
        pkgs = (
            "glibc lib32-glibc cabextract curl wget freetype2 lib32-freetype2 "
            "fontconfig lib32-fontconfig libx11 lib32-libx11 libxext lib32-libxext "
            "libxrender lib32-libxrender libxcursor lib32-libxcursor libxi lib32-libxi "
            "libxinerama lib32-libxinerama libxrandr lib32-libxrandr "
            "alsa-lib lib32-alsa-lib mesa lib32-mesa libpulse lib32-libpulse"
        )
        return InstallPlan(
            title="Install Wine dependencies",
            commands=[
                "sudo pacman -S --needed --noconfirm multilib-devel",
                f"sudo pacman -S --needed --noconfirm {pkgs}",
            ],
            requires_sudo=True,
        )

    def plan_install_pipewire_jack(self) -> InstallPlan:
        return InstallPlan(
            title="PipeWire JACK (Arch)",
            commands=[],
            requires_sudo=False,
            is_manual=True,
            manual_instructions="Arch Linux ships PipeWire with JACK support. Ensure pipewire-jack is installed.",
        )

    def plan_install_qpwgraph(self) -> InstallPlan:
        return InstallPlan(
            title="Install qpwgraph",
            commands=["sudo pacman -S --needed --noconfirm qpwgraph"],
            requires_sudo=True,
        )


class UnsupportedInstaller(BaseInstaller):
    """Fallback for unsupported distributions."""

    def _manual(self, title: str) -> InstallPlan:
        return InstallPlan(
            title=title,
            commands=[],
            requires_sudo=False,
            is_manual=True,
            manual_instructions="See others.md for manual setup instructions.",
        )

    def plan_install_wine_deps(self) -> InstallPlan:
        return self._manual("Install Wine dependencies")

    def plan_install_pipewire_jack(self) -> InstallPlan:
        return self._manual("Install PipeWire JACK")

    def plan_install_qpwgraph(self) -> InstallPlan:
        return self._manual("Install qpwgraph")


def get_installer(distro: Distribution | None = None) -> BaseInstaller:
    if distro is None:
        distro = detect_distribution()
    match distro.family:
        case "debian":
            return AptInstaller(distro)
        case "fedora":
            return DnfInstaller(distro)
        case "arch":
            return PacmanInstaller(distro)
        case _:
            return UnsupportedInstaller(distro)


def _parse_cmd(cmd_str: str) -> list[str]:
    """Split a command string into a list, handling simple quoted args."""
    import shlex

    return shlex.split(cmd_str)
