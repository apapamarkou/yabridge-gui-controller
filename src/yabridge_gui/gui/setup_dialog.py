"""Pro Audio Setup Assistant dialog."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt, QThread, pyqtSignal
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
        self.setMinimumSize(700, 500)
        self._distro = detect_distribution()
        self._installer = get_installer(self._distro)
        self._checks: list[EnvironmentCheck] = []
        self._init_ui()
        self._refresh()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)

        # Distro info
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

        # Checks area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self._checks_widget = QWidget()
        self._checks_layout = QVBoxLayout(self._checks_widget)
        self._checks_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll.setWidget(self._checks_widget)
        layout.addWidget(scroll)

        # Buttons
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

    def _refresh(self) -> None:
        self._checks = run_environment_checks()
        # Clear existing rows
        while self._checks_layout.count():
            item = self._checks_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for check in self._checks:
            self._checks_layout.addWidget(self._make_check_row(check))

    def _make_check_row(self, check: EnvironmentCheck) -> QWidget:
        row = QWidget()
        h = QHBoxLayout(row)
        h.setContentsMargins(4, 2, 4, 2)

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

        if check.status != CheckStatus.OK:
            _MANUAL_KEYS = {
                "configure_rt_limits",
                "configure_profile",
                "add_audio_group",
                "configure_wine",
            }
            if check.fix_available and self._distro.supported:
                fix_btn = QPushButton("Fix")
                fix_btn.setFixedWidth(60)
                fix_btn.clicked.connect(lambda _, c=check: self._attempt_fix(c))
                h.addWidget(fix_btn)
            elif check.fix_key in _MANUAL_KEYS:
                instr_btn = QPushButton("Instructions")
                instr_btn.setFixedWidth(90)
                instr_btn.clicked.connect(lambda _, c=check: self._show_manual_instructions(c))
                h.addWidget(instr_btn)

        return row

    def _attempt_fix(self, check: EnvironmentCheck) -> None:
        plan = self._get_plan_for(check.fix_key)
        if plan is None:
            return

        if plan.is_manual:
            self._show_plan_instructions(plan)
            return

        # Show confirmation
        cmd_text = "\n".join(plan.commands)
        sudo_note = (
            "\n\nAdministrator privileges (sudo) will be required." if plan.requires_sudo else ""
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

        self._worker = _WorkerThread(plan)
        self._worker.finished.connect(lambda ok, out: self._fix_done(ok, out, plan.title))
        self._worker.start()

    def _fix_done(self, ok: bool, output: str, title: str) -> None:
        self._show_output_dialog(ok, title, output)
        self._refresh()

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

    def _show_manual_instructions(self, check: EnvironmentCheck) -> None:
        plan = self._get_plan_for(check.fix_key)
        if plan:
            self._show_plan_instructions(plan)

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
        copy_btn = QPushButton("Copy Commands")
        clipboard_text = "\n".join(plan.copyable_commands)
        copy_btn.clicked.connect(lambda: QApplication.clipboard().setText(clipboard_text))
        close_btn = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        close_btn.rejected.connect(dlg.reject)
        btn_row.addWidget(copy_btn)
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
        # Try to find the doc relative to the project
        candidates = [
            Path(__file__).parent.parent.parent.parent / doc_file,
            Path(f"/usr/share/doc/yabridge-gui-controller/{doc_file}"),
        ]
        for p in candidates:
            if p.exists():
                subprocess.Popen(["xdg-open", str(p)])
                return
        QMessageBox.information(self, "Documentation", f"Documentation file not found: {doc_file}")
