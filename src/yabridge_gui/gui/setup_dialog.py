"""Pro Audio Setup Assistant dialog."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt, QThread, QTimer, pyqtSignal
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from yabridge_gui.core.distro import detect_distribution
from yabridge_gui.core.environment import CheckStatus, EnvironmentCheck, run_environment_checks
from yabridge_gui.core.installer import InstallPlan, get_installer
from yabridge_gui.services.diagnostics import generate_diagnostic_report

_STATUS_ICONS = {
    CheckStatus.OK: ("✓", "color: green;"),
    CheckStatus.MISSING: ("✗", "color: red;"),
    CheckStatus.WARNING: ("⚠", "color: orange;"),
    CheckStatus.UNKNOWN: ("?", "color: gray;"),
    CheckStatus.UNSUPPORTED: ("—", "color: gray;"),
}

_SPINNER_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

# Ordered setup steps: (check_name, fix_key).
# Steps 0-4 are "phase 1" (before logout); 5-9 are "phase 2" (after logout).
_SETUP_ORDER: list[str] = [
    "wine",           # 0
    "yabridge",       # 1
    "profile_paths",  # 2
    "audio_group",    # 3
    "rt_limits",      # 4
    "wine_configured",# 5
    "vst_dirs",       # 6
    "yabridge_paths", # 7
    "pipewire",       # 8
    "wireplumber",    # 9
]

# Index of first phase-2 step (needs logout before proceeding)
_PHASE2_START = 5


class _WorkerThread(QThread):
    finished = pyqtSignal(bool, str)

    def __init__(self, plan: InstallPlan):
        super().__init__()
        self._plan = plan

    def run(self) -> None:
        from yabridge_gui.core.installer import get_installer

        installer = get_installer()
        ok, output = installer.execute_plan(self._plan)
        self.finished.emit(ok, output)


class SetupDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Pro Audio Setup Assistant")
        self.setMinimumSize(700, 520)
        self._distro = detect_distribution()
        self._installer = get_installer(self._distro)
        self._checks: list[EnvironmentCheck] = []
        self._active_check_name: str | None = None
        self._spinner_timer: QTimer | None = None
        self._spinner_frame: int = 0
        self._spinner_label: QLabel | None = None
        self._logout_banner: QLabel | None = None
        self._init_ui()
        self._refresh()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)

        distro_label = QLabel(
            f"<b>Distribution:</b> {self._distro.name} {self._distro.version} "
            f"({'Supported' if self._distro.supported else 'Not supported'})"
        )
        layout.addWidget(distro_label)

        if not self._distro.supported:
            warn = QLabel(
                "<b style='color:orange'>⚠ Your distribution is not currently supported for "
                "automatic setup.</b><br>You can follow the manual setup instructions."
            )
            warn.setWordWrap(True)
            layout.addWidget(warn)

        # Logout suggestion banner (hidden by default)
        self._logout_banner = QLabel()
        self._logout_banner.setWordWrap(True)
        self._logout_banner.setStyleSheet(
            "background: #3a2a00; color: #ffcc44; padding: 6px; border-radius: 4px;"
        )
        self._logout_banner.hide()
        layout.addWidget(self._logout_banner)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self._checks_widget = QWidget()
        self._checks_layout = QVBoxLayout(self._checks_widget)
        self._checks_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll.setWidget(self._checks_widget)
        layout.addWidget(scroll)

        btn_layout = QHBoxLayout()
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self._refresh)
        diag_btn = QPushButton("Diagnostic Report")
        diag_btn.clicked.connect(self._show_diagnostic)
        docs_btn = QPushButton("View Setup Docs")
        docs_btn.clicked.connect(self._open_docs)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)

        btn_layout.addWidget(refresh_btn)
        btn_layout.addWidget(diag_btn)
        btn_layout.addWidget(docs_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

    # ------------------------------------------------------------------
    # Ordering helpers
    # ------------------------------------------------------------------

    def _check_by_name(self, name: str) -> EnvironmentCheck | None:
        return next((c for c in self._checks if c.name == name), None)

    def _active_step_index(self) -> int:
        """Return the index in _SETUP_ORDER of the first non-OK step."""
        for i, name in enumerate(_SETUP_ORDER):
            c = self._check_by_name(name)
            if c is None or c.status != CheckStatus.OK:
                return i
        return len(_SETUP_ORDER)  # all done

    def _needs_logout_before_phase2(self) -> bool:
        """True when phase-1 is done but PATH/audio group are not yet active in session."""
        active = self._active_step_index()
        if active < _PHASE2_START:
            return False
        profile = self._check_by_name("profile_paths")
        audio = self._check_by_name("audio_group")
        profile_pending = profile is not None and profile.status == CheckStatus.WARNING and bool(profile.logout_warning)
        audio_pending = audio is not None and audio.status == CheckStatus.WARNING and bool(audio.logout_warning)
        return profile_pending or audio_pending

    # ------------------------------------------------------------------
    # Refresh / row building
    # ------------------------------------------------------------------

    def _refresh(self) -> None:
        self._checks = run_environment_checks()
        self._spinner_label = None

        # Update logout banner
        if self._needs_logout_before_phase2():
            self._logout_banner.setText(
                "⟳  PATH or audio group changes are pending a session restart. "
                "Please <b>logout and log back in</b>, then continue setup from step 6 onwards."
            )
            self._logout_banner.show()
        else:
            self._logout_banner.hide()

        while self._checks_layout.count():
            item = self._checks_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        active_idx = self._active_step_index()
        waiting_logout = self._needs_logout_before_phase2()
        for check in self._checks:
            step_idx = _SETUP_ORDER.index(check.name) if check.name in _SETUP_ORDER else -1
            btn_enabled = (
                step_idx == active_idx
                and not (waiting_logout and step_idx >= _PHASE2_START)
            )
            self._checks_layout.addWidget(self._make_check_row(check, btn_enabled))

    def _make_check_row(self, check: EnvironmentCheck, btn_enabled: bool = True) -> QWidget:
        wrapper = QWidget()
        v = QVBoxLayout(wrapper)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)

        row = QWidget()
        h = QHBoxLayout(row)
        h.setContentsMargins(4, 2, 4, 2)

        is_active = self._active_check_name == check.name
        if is_active:
            icon_lbl = QLabel(_SPINNER_FRAMES[0])
            icon_lbl.setStyleSheet("color: #4a9eff;")
            self._spinner_label = icon_lbl
        else:
            icon, style = _STATUS_ICONS.get(check.status, ("?", ""))
            icon_lbl = QLabel(icon)
            icon_lbl.setStyleSheet(style)
        icon_lbl.setFixedWidth(20)

        name_lbl = QLabel(f"<b>{check.label}</b>")
        name_lbl.setFixedWidth(180)

        detail_lbl = QLabel(check.detail or "")
        detail_lbl.setWordWrap(True)
        detail_lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        h.addWidget(icon_lbl)
        h.addWidget(name_lbl)
        h.addWidget(detail_lbl)

        if check.status != CheckStatus.OK and not is_active and check.fix_key:
            btn = QPushButton("Fix")
            btn.setFixedWidth(60)
            btn.setEnabled(btn_enabled and self._distro.supported)
            btn.clicked.connect(lambda _, c=check: self._attempt_fix(c))
            h.addWidget(btn)

        v.addWidget(row)

        if check.logout_warning:
            warn_lbl = QLabel(f"  \u27f3 {check.logout_warning}")
            warn_lbl.setStyleSheet("color: orange; font-size: 11px; padding-left: 24px;")
            warn_lbl.setWordWrap(True)
            v.addWidget(warn_lbl)

        return wrapper

    # ------------------------------------------------------------------
    # Fix flow
    # ------------------------------------------------------------------

    def _attempt_fix(self, check: EnvironmentCheck) -> None:
        if check.fix_key in ("configure_profile", "configure_rt_limits"):
            self._ask_manual_or_auto(check)
            return

        plan = self._get_plan_for(check.fix_key)
        if plan is None:
            return
        self._confirm_and_run(check, plan)

    def _ask_manual_or_auto(self, check: EnvironmentCheck) -> None:
        """Show a dialog explaining config-file changes, then let user pick Manual or Auto."""
        if check.fix_key == "configure_profile":
            description = (
                "This will add PATH and WINEFSYNC entries to <b>~/.profile</b> "
                "and optionally <b>~/.xsessionrc</b>."
            )
        else:
            description = (
                "This will add <b>@audio</b> realtime priority lines to "
                "<b>/etc/security/limits.conf</b>."
            )

        dlg = QDialog(self)
        dlg.setWindowTitle(f"Fix: {check.label}")
        dlg.setMinimumWidth(420)
        layout = QVBoxLayout(dlg)

        info = QLabel(
            f"<b>This operation requires config file changes.</b><br><br>{description}"
            "<br><br>Choose how to proceed:"
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        btn_row = QHBoxLayout()
        manual_btn = QPushButton("Manual (Instructions)")
        auto_btn = QPushButton("Auto")
        cancel_btn = QPushButton("Cancel")
        btn_row.addWidget(manual_btn)
        btn_row.addWidget(auto_btn)
        btn_row.addStretch()
        btn_row.addWidget(cancel_btn)
        layout.addLayout(btn_row)

        choice: list[str] = []
        manual_btn.clicked.connect(lambda: (choice.append("manual"), dlg.accept()))
        auto_btn.clicked.connect(lambda: (choice.append("auto"), dlg.accept()))
        cancel_btn.clicked.connect(dlg.reject)
        if dlg.exec() != QDialog.DialogCode.Accepted or not choice:
            return

        if choice[0] == "manual":
            plan = self._get_plan_for(check.fix_key)
            if plan:
                self._show_plan_instructions(plan)
        else:
            if check.fix_key == "configure_profile":
                plan = self._installer.plan_configure_profile_auto()
            else:
                plan = self._installer.plan_configure_rt_limits_auto()
            self._confirm_and_run(check, plan)

    def _confirm_and_run(self, check: EnvironmentCheck, plan: InstallPlan) -> None:
        if plan.is_manual:
            self._show_plan_instructions(plan)
            return

        cmd_text = "\n".join(plan.commands)
        sudo_note = (
            "\n\nAdministrator privileges will be required." if plan.requires_sudo else ""
        )
        logout_note = (
            "\n\nA logout/reboot will be required after this change."
            if plan.requires_logout
            else ""
        )

        msg = QMessageBox(self)
        msg.setWindowTitle(f"Confirm: {plan.title}")
        msg.setText(
            f"The following actions will be performed:\n\n{cmd_text}{sudo_note}{logout_note}\n\nContinue?"
        )
        msg.setStandardButtons(QMessageBox.StandardButton.Cancel | QMessageBox.StandardButton.Ok)
        if msg.exec() != QMessageBox.StandardButton.Ok:
            return

        self._active_check_name = check.name
        self._spinner_frame = 0
        self._refresh()

        self._spinner_timer = QTimer(self)
        self._spinner_timer.timeout.connect(self._tick_spinner)
        self._spinner_timer.start(80)

        self._worker = _WorkerThread(plan)
        self._worker.finished.connect(lambda ok, out: self._on_worker_done(ok, out, plan.title))
        self._worker.start()

    def _tick_spinner(self) -> None:
        if self._spinner_label is not None:
            self._spinner_label.setText(
                _SPINNER_FRAMES[self._spinner_frame % len(_SPINNER_FRAMES)]
            )
        self._spinner_frame += 1

    def _on_worker_done(self, ok: bool, output: str, title: str) -> None:
        if self._spinner_timer:
            self._spinner_timer.stop()
            self._spinner_timer = None
        self._active_check_name = None
        self._spinner_label = None
        self._show_output_dialog(ok, title, output)
        self._refresh()

    # ------------------------------------------------------------------
    # Dialogs
    # ------------------------------------------------------------------

    def _show_output_dialog(self, ok: bool, title: str, output: str) -> None:
        dlg = QDialog(self)
        dlg.setWindowTitle(f"{'Completed' if ok else 'Failed'}: {title}")
        dlg.setMinimumSize(600, 400)
        layout = QVBoxLayout(dlg)
        status_lbl = QLabel(
            "<b style='color:green'>Completed successfully.</b>"
            if ok
            else "<b style='color:red'>Operation failed.</b>"
        )
        layout.addWidget(status_lbl)
        text = QTextEdit()
        text.setReadOnly(True)
        text.setFontFamily("monospace")
        text.setPlainText(output or "(no output)")
        layout.addWidget(text)
        btn = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        btn.rejected.connect(dlg.reject)
        layout.addWidget(btn)
        dlg.exec()

    def _show_plan_instructions(self, plan: InstallPlan) -> None:
        dlg = QDialog(self)
        dlg.setWindowTitle(f"Instructions: {plan.title}")
        dlg.setMinimumSize(560, 360)
        layout = QVBoxLayout(dlg)
        layout.addWidget(
            QLabel("<b>Manual action required</b> — copy the commands below into a terminal.")
        )
        text = QTextEdit()
        text.setReadOnly(True)
        text.setFontFamily("monospace")
        text.setPlainText(plan.manual_instructions)
        layout.addWidget(text)
        btn_row = QHBoxLayout()
        if plan.copyable_commands:
            copy_btn = QPushButton("Copy Commands")
            clipboard_text = "\n".join(plan.copyable_commands)
            copy_btn.clicked.connect(lambda: QApplication.clipboard().setText(clipboard_text))
            btn_row.addWidget(copy_btn)
        close_btn = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        close_btn.rejected.connect(dlg.reject)
        btn_row.addStretch()
        layout.addLayout(btn_row)
        layout.addWidget(close_btn)
        dlg.exec()

    def _get_plan_for(self, fix_key: str) -> InstallPlan | None:
        match fix_key:
            case "install_wine":
                return self._installer.plan_install_wine_full()
            case "configure_wine":
                return self._installer.plan_configure_wine()
            case "install_yabridge":
                return self._installer.plan_install_yabridge()
            case "install_pipewire_jack":
                return self._installer.plan_install_pipewire_jack()
            case "create_vst_dirs":
                return self._installer.plan_create_vst_dirs()
            case "configure_yabridge_paths":
                return self._installer.plan_configure_yabridge_paths()
            case "configure_rt_limits":
                return self._installer.plan_configure_rt_limits()
            case "configure_profile":
                return self._installer.plan_configure_profile()
            case "add_audio_group":
                return self._installer.plan_add_audio_group()
            case "enable_wireplumber":
                return InstallPlan(
                    title="Enable WirePlumber",
                    commands=["systemctl --user --now enable wireplumber.service"],
                    requires_sudo=False,
                )
            case _:
                return None

    def _show_diagnostic(self) -> None:
        report = generate_diagnostic_report()
        dlg = QDialog(self)
        dlg.setWindowTitle("Diagnostic Report")
        dlg.setMinimumSize(600, 400)
        layout = QVBoxLayout(dlg)
        text = QTextEdit()
        text.setReadOnly(True)
        text.setPlainText(report)
        layout.addWidget(text)
        copy_btn = QPushButton("Copy to Clipboard")
        copy_btn.clicked.connect(lambda: QApplication.clipboard().setText(report))
        close_btn = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        close_btn.rejected.connect(dlg.reject)
        btn_row = QHBoxLayout()
        btn_row.addWidget(copy_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)
        layout.addWidget(close_btn)
        dlg.exec()

    def _open_docs(self) -> None:
        import subprocess

        doc_file = self._distro.doc_file or "others.md"
        candidates = [
            Path(__file__).parent.parent.parent.parent / doc_file,
            Path(f"/usr/share/doc/yabridge-gui-controller/{doc_file}"),
        ]
        for p in candidates:
            if p.exists():
                subprocess.Popen(["xdg-open", str(p)])
                return
        QMessageBox.information(self, "Documentation", f"Documentation file not found: {doc_file}")
