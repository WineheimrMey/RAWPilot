from __future__ import annotations

import json
from pathlib import Path

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import (
    QColor,
    QDesktopServices,
    QDragEnterEvent,
    QDragLeaveEvent,
    QDragMoveEvent,
    QDropEvent,
    QFont,
    QPixmap,
)
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QStackedWidget,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from .api_client import QwenApiClient
from .history import HistoryStore, ProjectRecord
from .i18n import tr
from .importer import collect_raw_files
from .lightroom_bridge import LightroomBridge, LightroomError, detect_lightroom
from .models import Diagnosis, EditPlan, ProcessResult
from .settings import AppSettings, config_dir
from .task_manager import TaskManager


APP_STYLE = """
* {
    font-family: "Microsoft YaHei UI", "Segoe UI Variable", sans-serif;
    font-size: 13px;
    color: #ECE9E1;
}
QMainWindow, QDialog, QWidget#AppRoot { background: #0A0B0B; }
QFrame#TopBar {
    background: #0E0F0F;
    border-bottom: 1px solid #292824;
}
QFrame#Rail {
    background: #0E0F0F;
    border-right: 1px solid #282722;
}
QFrame#Canvas {
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #151615,stop:1 #101111);
    border: 1px solid #2B2B27;
    border-radius: 16px;
}
QFrame#Canvas[dropActive="true"] {
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #211D16,stop:1 #111211);
    border: 2px solid #D7AE68;
}
QFrame#Card {
    background: #121312;
    border: 1px solid #2B2B27;
    border-radius: 14px;
}
QFrame#AccentCard {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #1D1B16,stop:1 #151512);
    border: 1px solid #4A402E;
    border-radius: 14px;
}
QFrame#Hairline { background: #2A2925; max-height: 1px; }
QLabel#Monogram {
    background: qradialgradient(cx:.35,cy:.25,radius:1,stop:0 #E6C786,stop:1 #B78645);
    color: #15110C;
    border-radius: 12px;
    font-family: "Georgia";
    font-size: 27px;
    font-weight: 800;
}
QLabel#Brand { color: #F6F3EA; font-size: 20px; font-weight: 680; }
QLabel#BrandSub { color: #77766F; font-size: 10px; letter-spacing: 2px; }
QLabel#Eyebrow {
    color: #B99A65;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 2px;
}
QLabel#HeroTitle { color: #F5F1E8; font-size: 23px; font-weight: 620; }
QLabel#SectionTitle { color: #F1EEE6; font-size: 16px; font-weight: 650; }
QLabel#Body { color: #CBC8BF; font-size: 13px; }
QLabel#Muted { color: #85837C; font-size: 11px; }
QLabel#Tiny { color: #686760; font-size: 10px; }
QLabel#StatusChip {
    background: #211F19;
    color: #D7B979;
    border: 1px solid #4A422F;
    border-radius: 12px;
    padding: 5px 12px;
    font-size: 10px;
    letter-spacing: 1px;
}
QLabel#Preview {
    background: #050606;
    border: 1px solid #252622;
    border-radius: 12px;
    color: #5F5F59;
    font-size: 12px;
}
QLabel#AnalysisLead {
    color: #D8D3C7;
    background: transparent;
    padding: 2px;
    font-size: 12px;
}
QPushButton {
    background: #191A18;
    border: 1px solid #34342F;
    border-radius: 9px;
    color: #DEDBD3;
    min-height: 37px;
    padding: 0 14px;
    font-weight: 560;
}
QPushButton:hover { background: #22231F; border-color: #625B4D; }
QPushButton:pressed { background: #151613; }
QPushButton:disabled { color: #575750; background: #151614; border-color: #242520; }
QPushButton#Primary {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #C99954,stop:1 #E0BD78);
    color: #17120C;
    border: 1px solid #E4C37F;
    font-weight: 750;
    min-height: 46px;
}
QPushButton#Primary:hover { background: #E2BE77; }
QPushButton#Nav {
    background: transparent;
    border: none;
    border-radius: 8px;
    color: #807F78;
    min-height: 34px;
    padding: 0 16px;
}
QPushButton#Nav:checked { background: #22211C; color: #E4C88F; }
QPushButton#Ghost { background: transparent; border-color: #30312C; }
QPushButton#TextButton {
    background: transparent;
    border: none;
    color: #B89B69;
    padding: 0 4px;
    min-height: 25px;
}
QLineEdit, QPlainTextEdit {
    background: #0D0E0D;
    border: 1px solid #34342F;
    border-radius: 9px;
    padding: 10px;
    selection-background-color: #8A693C;
}
QLineEdit:focus, QPlainTextEdit:focus { border-color: #A88A58; }
QPlainTextEdit#DirectorNotes {
    background: #10110F;
    color: #EEE9DD;
    font-size: 13px;
    padding: 13px;
}
QTableWidget {
    background: transparent;
    alternate-background-color: #151614;
    border: none;
    gridline-color: transparent;
    outline: none;
}
QTableWidget::item {
    border-bottom: 1px solid #272824;
    padding: 8px 7px;
}
QTableWidget::item:selected { background: #2A261E; color: #F6E8CD; }
QHeaderView::section {
    background: #10110F;
    color: #74736D;
    border: none;
    border-bottom: 1px solid #2B2C27;
    padding: 8px 7px;
    font-size: 10px;
    font-weight: 700;
}
QListWidget {
    background: transparent;
    border: none;
    outline: none;
}
QListWidget::item {
    border-bottom: 1px solid #292A25;
    padding: 13px 10px;
    color: #C9C6BD;
}
QListWidget::item:selected {
    background: #28251D;
    color: #F0D59C;
    border-left: 2px solid #C79A54;
}
QTabWidget::pane { border: none; background: transparent; }
QTabBar::tab {
    background: transparent;
    color: #73726C;
    border: none;
    border-bottom: 2px solid transparent;
    padding: 10px 12px;
}
QTabBar::tab:selected { color: #E1C58D; border-bottom-color: #C39751; }
QProgressBar {
    background: #0B0C0B;
    border: 1px solid #292A25;
    border-radius: 4px;
    height: 7px;
    color: transparent;
}
QProgressBar::chunk {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #9E743E,stop:1 #E0BC75);
    border-radius: 3px;
}
QStatusBar { background: #0A0B0B; color: #77766F; border-top: 1px solid #22231F; }
QCheckBox { spacing: 8px; }
QCheckBox::indicator { width: 17px; height: 17px; }
"""

# Editorial darkroom theme. These selectors intentionally sit after the base
# rules so the application can keep its stable widget behavior while adopting
# a materially different visual system.
APP_STYLE += """
* {
    font-family: "Segoe UI Variable", "Microsoft YaHei UI", sans-serif;
    font-size: 13px;
    color: #E8E4DA;
}
QMainWindow, QDialog, QWidget#AppRoot {
    background: #080A09;
}
QFrame#TopBar {
    background: #090B0A;
    border-bottom: 1px solid #252721;
}
QFrame#UtilityRail {
    background: #0D0F0E;
    border: 1px solid #252821;
    border-radius: 18px;
}
QFrame#DirectorRail {
    background: #0B0D0C;
    border-left: 1px solid #252821;
}
QFrame#Canvas {
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #121512,stop:1 #0D100E);
    border: 1px solid #292C25;
    border-radius: 20px;
}
QFrame#Canvas[dropActive="true"] {
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #221D13,stop:1 #0E110F);
    border: 2px solid #D6AC61;
}
QFrame#ImageWell {
    background: #050706;
    border: 1px solid #2A2D26;
    border-radius: 14px;
}
QFrame#Card {
    background: #101310;
    border: 1px solid #282B24;
    border-radius: 14px;
}
QFrame#AccentCard {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #1C1A14,stop:1 #11130F);
    border: 1px solid #51462F;
    border-radius: 16px;
}
QFrame#Inset {
    background: #0A0C0B;
    border: 1px solid #23261F;
    border-radius: 11px;
}
QFrame#ActionDock {
    background: #0F120F;
    border-top: 1px solid #2A2D25;
}
QFrame#Hairline {
    background: #2B2E27;
    min-height: 1px;
    max-height: 1px;
}
QLabel#Monogram {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #E3BE73,stop:.52 #C5924B,stop:1 #8D6230);
    color: #100D08;
    border: 1px solid #E8CB8D;
    border-radius: 15px;
    font-family: "Georgia";
    font-size: 30px;
    font-weight: 800;
}
QLabel#Brand {
    color: #F6F1E7;
    font-size: 22px;
    font-weight: 700;
}
QLabel#BrandSub {
    color: #73766E;
    font-size: 9px;
    letter-spacing: 3px;
}
QLabel#Eyebrow {
    color: #B99155;
    font-size: 9px;
    font-weight: 750;
    letter-spacing: 2px;
}
QLabel#HeroTitle {
    color: #F5F0E6;
    font-family: "Microsoft YaHei UI";
    font-size: 27px;
    font-weight: 600;
}
QLabel#SectionTitle {
    color: #F0EBE1;
    font-size: 17px;
    font-weight: 680;
}
QLabel#DisplayTitle {
    color: #F6F0E4;
    font-family: "Microsoft YaHei UI";
    font-size: 30px;
    font-weight: 600;
}
QLabel#Body { color: #CAC8BE; font-size: 13px; }
QLabel#Muted { color: #858880; font-size: 11px; }
QLabel#Tiny { color: #666A62; font-size: 9px; letter-spacing: 1px; }
QLabel#StepNo {
    background: #242118;
    color: #D8B56E;
    border: 1px solid #4A402D;
    border-radius: 12px;
    min-width: 24px;
    max-width: 24px;
    min-height: 24px;
    max-height: 24px;
    font-size: 10px;
    font-weight: 750;
}
QLabel#StatusChip {
    background: #171711;
    color: #D8B56E;
    border: 1px solid #49402D;
    border-radius: 13px;
    padding: 5px 12px;
    font-size: 9px;
    font-weight: 700;
    letter-spacing: 1px;
}
QLabel#Tag {
    background: #151814;
    color: #A6A99F;
    border: 1px solid #2D312A;
    border-radius: 11px;
    padding: 4px 9px;
    font-size: 9px;
    letter-spacing: 1px;
}
QLabel#AnalysisLead {
    color: #D7D2C6;
    background: transparent;
    padding: 0;
    font-size: 12px;
    line-height: 1.5;
}
QLabel#Preview {
    background: transparent;
    border: none;
    color: #5B5F57;
    font-size: 11px;
}
QPushButton {
    background: #151815;
    border: 1px solid #32362E;
    border-radius: 10px;
    color: #DCD8CF;
    min-height: 38px;
    padding: 0 15px;
    font-weight: 580;
}
QPushButton:hover {
    background: #1C201B;
    border-color: #71624A;
    color: #F3EBDD;
}
QPushButton:pressed { background: #101310; }
QPushButton:disabled {
    color: #555950;
    background: #111310;
    border-color: #22251F;
}
QPushButton#Primary {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #B9823E,stop:.55 #D5AA62,stop:1 #E6C982);
    color: #151008;
    border: 1px solid #E8CA86;
    border-radius: 12px;
    font-weight: 780;
    min-height: 48px;
}
QPushButton#Primary:hover {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #C28A43,stop:1 #F0D694);
}
QPushButton#Nav {
    background: transparent;
    border: none;
    border-radius: 9px;
    color: #777B73;
    min-height: 36px;
    padding: 0 18px;
    font-weight: 650;
}
QPushButton#Nav:hover { color: #D8D4CA; background: #131613; }
QPushButton#Nav:checked {
    background: #1B1B15;
    color: #E2C78E;
    border: 1px solid #343024;
}
QPushButton#Ghost { background: transparent; border-color: #30342C; }
QPushButton#TextButton {
    background: transparent;
    border: none;
    color: #C09A5C;
    padding: 0;
    min-height: 26px;
}
QLineEdit, QPlainTextEdit {
    background: #090C0A;
    border: 1px solid #30342C;
    border-radius: 11px;
    padding: 10px 12px;
    selection-background-color: #8B6637;
}
QLineEdit:focus, QPlainTextEdit:focus {
    background: #0C0F0D;
    border-color: #9F7C48;
}
QPlainTextEdit#DirectorNotes {
    background: #0B0E0C;
    color: #EEE8DB;
    border: 1px solid #3B382B;
    font-size: 13px;
    padding: 14px;
}
QTableWidget {
    background: transparent;
    alternate-background-color: #111411;
    border: none;
    gridline-color: transparent;
    outline: none;
}
QTableWidget::item {
    border-bottom: 1px solid #272B24;
    padding: 9px 8px;
}
QTableWidget::item:selected {
    background: #29251A;
    color: #F5E5C5;
    border-bottom-color: #5A4930;
}
QHeaderView::section {
    background: #0C0F0D;
    color: #6F746B;
    border: none;
    border-bottom: 1px solid #292D25;
    padding: 9px 8px;
    font-size: 9px;
    font-weight: 750;
    letter-spacing: 1px;
}
QListWidget::item {
    border-bottom: 1px solid #292D25;
    padding: 15px 11px;
    color: #C9C6BD;
}
QListWidget::item:selected {
    background: #262218;
    color: #F1D59C;
    border-left: 3px solid #C8954D;
}
QTabWidget::pane {
    border: 1px solid #272B24;
    border-radius: 12px;
    background: #090C0A;
    top: -1px;
}
QTabBar::tab {
    background: transparent;
    color: #70746C;
    border: none;
    border-bottom: 2px solid transparent;
    padding: 10px 13px;
    font-weight: 620;
}
QTabBar::tab:hover { color: #C9C4B9; }
QTabBar::tab:selected {
    color: #E4C37D;
    border-bottom-color: #C4934C;
}
QProgressBar {
    background: #080A09;
    border: 1px solid #252921;
    border-radius: 4px;
    height: 6px;
    color: transparent;
}
QProgressBar::chunk {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #8E6331,stop:1 #E1BD72);
    border-radius: 3px;
}
QStatusBar {
    background: #080A09;
    color: #6F736B;
    border-top: 1px solid #20231E;
    font-size: 10px;
}
"""


def label(text: str, object_name: str = "") -> QLabel:
    widget = QLabel(text)
    if object_name:
        widget.setObjectName(object_name)
    return widget


def card(accent: bool = False) -> QFrame:
    frame = QFrame()
    frame.setObjectName("AccentCard" if accent else "Card")
    return frame


def step_header(number: str, title: str, caption: str = "") -> QWidget:
    host = QWidget()
    row = QHBoxLayout(host)
    row.setContentsMargins(0, 0, 0, 0)
    row.setSpacing(10)
    number_label = label(number, "StepNo")
    number_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    row.addWidget(number_label)
    text = QVBoxLayout()
    text.setSpacing(0)
    text.addWidget(label(title, "SectionTitle"))
    if caption:
        text.addWidget(label(caption, "Tiny"))
    row.addLayout(text, 1)
    return host


def translate_widget_tree(root: QWidget, language: str) -> None:
    """Translate widgets created from the canonical Chinese source strings."""

    widgets = [root, *root.findChildren(QWidget)]
    for widget in widgets:
        if isinstance(widget, (QLabel, QPushButton, QCheckBox)):
            widget.setText(tr(widget.text(), language))
        if isinstance(widget, (QLineEdit, QPlainTextEdit)):
            widget.setPlaceholderText(tr(widget.placeholderText(), language))
        if isinstance(widget, QTabWidget):
            for index in range(widget.count()):
                widget.setTabText(index, tr(widget.tabText(index), language))
        if isinstance(widget, QTableWidget):
            for column in range(widget.columnCount()):
                item = widget.horizontalHeaderItem(column)
                if item:
                    item.setText(tr(item.text(), language))


class SettingsDialog(QDialog):
    def __init__(self, settings: AppSettings, parent=None):
        super().__init__(parent)
        self.setWindowTitle("连接与输出 · 原光 RAWPilot")
        self.resize(700, 720)
        self.setStyleSheet(APP_STYLE)
        root = QVBoxLayout(self)
        root.setContentsMargins(30, 26, 30, 26)
        root.setSpacing(14)
        root.addWidget(label("DARKROOM CONNECTION", "Eyebrow"))
        root.addWidget(label("连接你的调色工作流", "DisplayTitle"))
        note = label("模型只阅读压缩 JPEG 预览和白名单 EXIF；完整 RAW 永远留在本机。", "Muted")
        note.setWordWrap(True)
        root.addWidget(note)

        model_card = card(accent=True)
        model_col = QVBoxLayout(model_card)
        model_col.setContentsMargins(16, 15, 16, 15)
        model_col.setSpacing(11)
        model_col.addWidget(step_header("01", "模型服务", "VISION / LANGUAGE / PRIVATE KEY"))
        form = QFormLayout()
        form.setVerticalSpacing(14)
        form.setHorizontalSpacing(18)
        self.base = QLineEdit(settings.api_base_url)
        self.base.setPlaceholderText("https://api-inference.modelscope.cn/v1")
        self.key = QLineEdit(settings.api_key)
        self.key.setPlaceholderText("API Key · 只保存在这台电脑")
        self.key.setEchoMode(QLineEdit.EchoMode.Password)
        self.vision = QLineEdit(settings.vision_model)
        self.language = QLineEdit(settings.language_model)
        form.addRow("API Base URL", self.base)
        form.addRow("API Key", self.key)
        form.addRow("视觉模型", self.vision)
        form.addRow("语言模型", self.language)
        model_col.addLayout(form)
        self.mock = QCheckBox("使用 Mock API，离线测试完整流程")
        self.mock.setChecked(settings.mock_mode)
        model_col.addWidget(self.mock)
        test_button = QPushButton("测试模型连接")
        test_button.setObjectName("Ghost")
        test_button.clicked.connect(self.test_api)
        model_col.addWidget(test_button)
        root.addWidget(model_card)

        lightroom_card = card()
        lightroom_col = QVBoxLayout(lightroom_card)
        lightroom_col.setContentsMargins(16, 15, 16, 15)
        lightroom_col.setSpacing(10)
        lightroom_col.addWidget(step_header("02", "Lightroom Classic", "LOCAL BRIDGE / JPEG EXPORT"))
        self.lightroom = QCheckBox("调用本机 Lightroom 调色并导出 JPEG")
        self.lightroom.setChecked(settings.lightroom_enabled)
        lightroom_col.addWidget(self.lightroom)
        self.lightroom_path = QLineEdit(settings.lightroom_path or str(detect_lightroom() or ""))
        choose = QPushButton("浏览")
        choose.setObjectName("Ghost")
        choose.clicked.connect(self.choose_lightroom)
        row = QHBoxLayout()
        row.addWidget(self.lightroom_path, 1)
        row.addWidget(choose)
        lightroom_col.addLayout(row)
        bridge_note = label(
            "Bridge 会执行基础面板、HSL、曲线、色彩分级、颗粒以及可用的 AI 区域蒙版。",
            "Muted",
        )
        bridge_note.setWordWrap(True)
        lightroom_col.addWidget(bridge_note)
        root.addWidget(lightroom_card)
        root.addStretch(1)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Save).setText("保存连接")
        buttons.button(QDialogButtonBox.StandardButton.Save).setObjectName("Primary")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("取消")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)
        self.interface_language = settings.interface_language
        self.setWindowTitle(tr(self.windowTitle(), self.interface_language))
        translate_widget_tree(self, self.interface_language)

    def _tr(self, text: str, **values: object) -> str:
        return tr(text, self.interface_language, **values)

    def value(self) -> AppSettings:
        return AppSettings(
            api_base_url=self.base.text().strip(),
            api_key=self.key.text().strip(),
            vision_model=self.vision.text().strip(),
            language_model=self.language.text().strip(),
            mock_mode=self.mock.isChecked(),
            lightroom_enabled=self.lightroom.isChecked(),
            lightroom_path=self.lightroom_path.text().strip(),
            interface_language=self.interface_language,
        )

    def test_api(self) -> None:
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            reply = QwenApiClient(self.value()).test_connection()
            QMessageBox.information(
                self,
                self._tr("连接成功"),
                self._tr("模型服务已响应：{reply}", reply=reply[:80]),
            )
        except Exception as exc:
            QMessageBox.warning(self, self._tr("连接失败"), str(exc))
        finally:
            QApplication.restoreOverrideCursor()

    def choose_lightroom(self) -> None:
        filename, _ = QFileDialog.getOpenFileName(
            self,
            self._tr("选择 Adobe Lightroom Classic"),
            self.lightroom_path.text(),
            self._tr("Lightroom (Lightroom.exe);;应用程序 (*.exe)"),
        )
        if filename:
            self.lightroom_path.setText(filename)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = AppSettings.load()
        self.setWindowTitle(self._tr("原光 RAWPilot · AI Digital Darkroom"))
        self.resize(1680, 1020)
        self.setMinimumSize(1240, 800)
        self.setStyleSheet(APP_STYLE)
        self.setAcceptDrops(True)
        self.files: list[Path] = []
        self.results: dict[int, ProcessResult] = {}
        self.style_by_path: dict[str, str] = {}
        self.manager = TaskManager()
        self.history = HistoryStore()
        self.current_project_id = ""
        self._loading_prompt = False
        self._preflight_active = False
        self._batch_active = False
        self._build()
        self.refresh_history()

    def _tr(self, text: str, **values: object) -> str:
        return tr(text, self.settings.interface_language, **values)

    def _build(self) -> None:
        root = QWidget()
        root.setObjectName("AppRoot")
        page = QVBoxLayout(root)
        page.setContentsMargins(0, 0, 0, 0)
        page.setSpacing(0)
        page.addWidget(self._top_bar())
        self.pages = QStackedWidget()
        self.pages.addWidget(self._studio_page())
        self.pages.addWidget(self._history_page())
        page.addWidget(self.pages, 1)
        self.setCentralWidget(root)
        self.statusBar().setSizeGripEnabled(False)
        translate_widget_tree(root, self.settings.interface_language)
        self.setWindowTitle(self._tr("原光 RAWPilot · AI Digital Darkroom"))
        if hasattr(self, "language_button"):
            self.language_button.setText(
                "EN" if self.settings.interface_language == "zh_CN" else "中文"
            )
        self._update_mode()

    def _top_bar(self) -> QFrame:
        bar = QFrame()
        bar.setObjectName("TopBar")
        bar.setFixedHeight(92)
        row = QHBoxLayout(bar)
        row.setContentsMargins(28, 16, 28, 15)
        row.setSpacing(15)
        mark = label("R", "Monogram")
        mark.setAlignment(Qt.AlignmentFlag.AlignCenter)
        mark.setFixedSize(54, 54)
        row.addWidget(mark)
        brand = QVBoxLayout()
        brand.setSpacing(2)
        brand.addWidget(label("原光 RAWPilot", "Brand"))
        brand.addWidget(label("PHOTOGRAPHIC INTELLIGENCE · PRIVATE DARKROOM", "BrandSub"))
        row.addLayout(brand)
        row.addSpacing(38)
        self.studio_nav = QPushButton("工作台")
        self.studio_nav.setObjectName("Nav")
        self.studio_nav.setCheckable(True)
        self.studio_nav.setChecked(True)
        self.studio_nav.clicked.connect(lambda: self.switch_page(0))
        self.history_nav = QPushButton("项目档案")
        self.history_nav.setObjectName("Nav")
        self.history_nav.setCheckable(True)
        self.history_nav.clicked.connect(lambda: self.switch_page(1))
        row.addWidget(self.studio_nav)
        row.addWidget(self.history_nav)
        row.addStretch()
        row.addWidget(label("STUDIO / 07", "Tag"))
        self.mode_chip = label("", "StatusChip")
        row.addWidget(self.mode_chip)
        self.language_button = QPushButton("EN")
        self.language_button.setObjectName("Ghost")
        self.language_button.setToolTip("中文 / English")
        self.language_button.clicked.connect(self.toggle_language)
        row.addWidget(self.language_button)
        settings_button = QPushButton("连接与输出")
        settings_button.setObjectName("Ghost")
        settings_button.clicked.connect(self.open_settings)
        row.addWidget(settings_button)
        return bar

    def toggle_language(self) -> None:
        if self._preflight_active or self._batch_active:
            QMessageBox.information(
                self,
                self._tr("任务进行中"),
                self._tr("请等待当前任务完成后再切换语言。"),
            )
            return
        self.save_current_prompt()
        row = self.table.currentRow() if hasattr(self, "table") else -1
        page = self.pages.currentIndex() if hasattr(self, "pages") else 0
        output = self.output.text() if hasattr(self, "output") else str(Path.cwd() / "output")
        log_text = self.log_view.toPlainText() if hasattr(self, "log_view") else ""
        refine_text = self.refine_feedback.toPlainText() if hasattr(self, "refine_feedback") else ""
        self.settings.interface_language = (
            "en_US" if self.settings.interface_language == "zh_CN" else "zh_CN"
        )
        self.settings.save()
        self._build()
        self.output.setText(output)
        self.refresh_table()
        self.refresh_history()
        self.log_view.setPlainText(log_text)
        self.refine_feedback.setPlainText(refine_text)
        self.switch_page(page)
        if 0 <= row < len(self.files):
            self.table.selectRow(row)
            self.show_selected()

    def _studio_page(self) -> QWidget:
        page = QWidget()
        layout = QHBoxLayout(page)
        layout.setContentsMargins(20, 18, 0, 16)
        layout.setSpacing(16)
        layout.addWidget(self._studio_rail())

        center = QVBoxLayout()
        center.setContentsMargins(0, 0, 0, 0)
        center.setSpacing(12)
        center.addWidget(self._viewer(), 1)
        center.addWidget(self._filmstrip())
        center_host = QWidget()
        center_host.setLayout(center)
        layout.addWidget(center_host, 1)
        layout.addWidget(self._editor_panel())
        return page

    def _studio_rail(self) -> QFrame:
        rail = QFrame()
        rail.setObjectName("UtilityRail")
        rail.setFixedWidth(256)
        col = QVBoxLayout(rail)
        col.setContentsMargins(17, 19, 17, 16)
        col.setSpacing(11)
        col.addWidget(label("DARKROOM SESSION", "Eyebrow"))
        col.addWidget(label("新建工作底片", "HeroTitle"))
        copy = label(
            "把一张 RAW 交给调色导演。先看片，再决定；每次调整都保留原始底片。",
            "Muted",
        )
        copy.setWordWrap(True)
        col.addWidget(copy)
        col.addSpacing(5)
        col.addWidget(step_header("01", "选择底片", "ARW · CR2 · CR3 · NEF · RAF · DNG"))
        choose_files = QPushButton("＋  选择 RAW")
        choose_files.setObjectName("Primary")
        choose_files.clicked.connect(self.import_files)
        choose_folder = QPushButton("扫描整个文件夹")
        choose_folder.setObjectName("Ghost")
        choose_folder.clicked.connect(self.import_folder)
        col.addWidget(choose_files)
        col.addWidget(choose_folder)
        col.addSpacing(10)

        line = QFrame()
        line.setObjectName("Hairline")
        col.addWidget(line)
        col.addSpacing(3)
        col.addWidget(step_header("02", "成片去向", "XMP · EDIT PLAN · JPEG"))
        self.output = QLineEdit(str(Path.cwd() / "output"))
        self.output.setCursorPosition(0)
        col.addWidget(self.output)
        browse = QPushButton("更改输出目录")
        browse.setObjectName("Ghost")
        browse.clicked.connect(self.choose_output)
        col.addWidget(browse)
        col.addSpacing(10)

        self.session_meta = label("尚未载入底片", "Body")
        self.session_meta.setWordWrap(True)
        session = card()
        session_col = QVBoxLayout(session)
        session_col.setContentsMargins(12, 11, 12, 11)
        session_col.setSpacing(4)
        session_col.addWidget(label("CURRENT CONTACT SHEET", "Eyebrow"))
        session_col.addWidget(self.session_meta)
        col.addWidget(session)
        clear = QPushButton("清空当前工作台")
        clear.setObjectName("TextButton")
        clear.clicked.connect(self.clear_batch)
        self.clear_button = clear
        col.addWidget(clear, alignment=Qt.AlignmentFlag.AlignLeft)
        col.addStretch()

        privacy = card(accent=True)
        privacy_col = QVBoxLayout(privacy)
        privacy_col.setContentsMargins(13, 13, 13, 13)
        privacy_col.setSpacing(5)
        privacy_col.addWidget(label("LOCAL NEGATIVE", "Eyebrow"))
        privacy_note = label("完整 RAW 留在这台电脑\n云端只看压缩预览与白名单 EXIF", "Muted")
        privacy_note.setWordWrap(True)
        privacy_col.addWidget(privacy_note)
        col.addWidget(privacy)
        return rail

    def _viewer(self) -> QFrame:
        viewer = QFrame()
        viewer.setObjectName("Canvas")
        self.viewer_frame = viewer
        col = QVBoxLayout(viewer)
        col.setContentsMargins(20, 18, 20, 20)
        col.setSpacing(14)
        top = QHBoxLayout()
        text = QVBoxLayout()
        text.setSpacing(3)
        text.addWidget(label("THE VIEWING TABLE", "Eyebrow"))
        self.preview_title = label("等待一张底片", "DisplayTitle")
        text.addWidget(self.preview_title)
        top.addLayout(text)
        top.addStretch()
        top.addWidget(label("BEFORE / AFTER", "Tag"))
        self.frame_meta = label("RAW · LOCAL PREVIEW", "StatusChip")
        top.addWidget(self.frame_meta)
        col.addLayout(top)

        rule = QFrame()
        rule.setObjectName("Hairline")
        col.addWidget(rule)

        compare = QHBoxLayout()
        compare.setSpacing(14)

        source_well = QFrame()
        source_well.setObjectName("ImageWell")
        source_box = QVBoxLayout()
        source_box.setContentsMargins(10, 9, 10, 10)
        source_box.setSpacing(7)
        source_head = QHBoxLayout()
        source_head.addWidget(label("01  CAMERA NEGATIVE", "Eyebrow"))
        source_head.addStretch()
        source_head.addWidget(label("INPUT", "Tag"))
        source_box.addLayout(source_head)
        self.preview = QLabel(
            "将 RAW 拖入这张看片台\n\n原片只读 · 本地提取预览"
        )
        self.preview.setObjectName("Preview")
        self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview.setMinimumSize(210, 410)
        source_box.addWidget(self.preview, 1)
        source_well.setLayout(source_box)
        compare.addWidget(source_well, 1)

        output_well = QFrame()
        output_well.setObjectName("ImageWell")
        output_box = QVBoxLayout()
        output_box.setContentsMargins(10, 9, 10, 10)
        output_box.setSpacing(7)
        output_head = QHBoxLayout()
        output_head.addWidget(label("02  DIRECTOR'S PRINT", "Eyebrow"))
        output_head.addStretch()
        output_head.addWidget(label("LIGHTROOM", "Tag"))
        output_box.addLayout(output_head)
        self.output_preview = QLabel("等待第一张工作样片\n\n完成后在这里逐项对照")
        self.output_preview.setObjectName("Preview")
        self.output_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.output_preview.setMinimumSize(210, 410)
        output_box.addWidget(self.output_preview, 1)
        output_well.setLayout(output_box)
        compare.addWidget(output_well, 1)
        col.addLayout(compare, 1)

        footer = QHBoxLayout()
        footer.setSpacing(8)
        footer.addWidget(label("LOCAL PREVIEW", "Tag"))
        footer.addWidget(label("NON-DESTRUCTIVE", "Tag"))
        footer.addWidget(label("COLOR MANAGED", "Tag"))
        footer.addStretch()
        footer.addWidget(label("拖入 RAW 即刻开始初审", "Tiny"))
        col.addLayout(footer)
        return viewer

    def _filmstrip(self) -> QFrame:
        panel = card()
        panel.setFixedHeight(224)
        col = QVBoxLayout(panel)
        col.setContentsMargins(16, 13, 16, 13)
        col.setSpacing(8)
        row = QHBoxLayout()
        row.addWidget(label("CONTACT SHEET / 本次底片", "Eyebrow"))
        row.addStretch()
        self.batch_meta = label("0 FRAMES", "Tiny")
        row.addWidget(self.batch_meta)
        col.addLayout(row)
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["底片", "AI 初审", "调色意图", "最终输出"])
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.table.itemSelectionChanged.connect(self.show_selected)
        col.addWidget(self.table)
        return panel

    def _editor_panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("DirectorRail")
        panel.setFixedWidth(432)
        col = QVBoxLayout(panel)
        col.setContentsMargins(20, 18, 20, 16)
        col.setSpacing(11)
        col.addWidget(label("DIRECTOR'S DESK", "Eyebrow"))
        header = QHBoxLayout()
        title_col = QVBoxLayout()
        title_col.setSpacing(1)
        title_col.addWidget(label("调色导演手记", "HeroTitle"))
        title_col.addWidget(label("READ · INTERPRET · GRADE · REVIEW", "Tiny"))
        header.addLayout(title_col)
        header.addStretch()
        self.analysis_state = label("等待看片", "StatusChip")
        header.addWidget(self.analysis_state)
        col.addLayout(header)
        self.analysis_lead = label(
            "导入后，Agent 会先阅读光线、色彩、主体层次与潜在技术问题，再提出可修改的导演建议。",
            "AnalysisLead",
        )
        self.analysis_lead.setWordWrap(True)
        col.addWidget(self.analysis_lead)

        prompt_card = card(accent=True)
        prompt_col = QVBoxLayout(prompt_card)
        prompt_col.setContentsMargins(14, 13, 14, 13)
        prompt_col.setSpacing(9)
        prompt_head = QHBoxLayout()
        prompt_head.addWidget(label("03  EDITORIAL INTENT", "Eyebrow"))
        prompt_head.addStretch()
        prompt_head.addWidget(label("可编辑", "Tag"))
        prompt_col.addLayout(prompt_head)
        self.style = QPlainTextEdit()
        self.style.setObjectName("DirectorNotes")
        self.style.setPlaceholderText("Agent 看片后会在这里写下一版自然语言调色方向。你可以像对调色师说话一样修改。")
        self.style.setMinimumHeight(160)
        self.style.textChanged.connect(self.save_current_prompt)
        prompt_col.addWidget(self.style)
        hint = label("你确认的文字，是本次成片唯一的创作委托。", "Tiny")
        prompt_col.addWidget(hint)
        col.addWidget(prompt_card)

        self.tabs = QTabWidget()
        self.diagnosis = QPlainTextEdit()
        self.plan = QPlainTextEdit()
        self.log_view = QPlainTextEdit()
        for editor in (self.diagnosis, self.plan, self.log_view):
            editor.setReadOnly(True)
            editor.setFrameStyle(QFrame.Shape.NoFrame)
        self.diagnosis.setPlaceholderText("AI 初审完成后显示画面问题与区域建议。")
        self.plan.setPlaceholderText("执行后显示通过边界校验的 Lightroom 参数。")
        self.log_view.setPlaceholderText("本次工作台日志。")
        self.tabs.addTab(self.diagnosis, "初审")
        self.tabs.addTab(self.plan, "配方")
        self.tabs.addTab(self.log_view, "日志")

        post_page = QWidget()
        post_col = QVBoxLayout(post_page)
        post_col.setContentsMargins(4, 10, 4, 4)
        post_col.setSpacing(9)
        post_col.addWidget(label("AFTER THE FIRST PRINT", "Eyebrow"))
        post_title = label("继续导演这张照片", "SectionTitle")
        post_col.addWidget(post_title)
        post_note = label(
            "描述当前成片哪里不对。Agent 会以这一版参数为起点做增量修订，旧版本不会被覆盖。",
            "Muted",
        )
        post_note.setWordWrap(True)
        post_col.addWidget(post_note)
        self.refine_feedback = QPlainTextEdit()
        self.refine_feedback.setObjectName("DirectorNotes")
        self.refine_feedback.setPlaceholderText(
            "例如：整体有点灰，再暖一些；前景可以亮一点，但窗外不要过曝；红色太艳，电影感减弱。"
        )
        self.refine_feedback.setMinimumHeight(112)
        post_col.addWidget(self.refine_feedback)
        quick_one = QHBoxLayout()
        for text in ("整体再亮一点", "更暖一些", "降低对比"):
            button = QPushButton(text)
            button.setObjectName("Ghost")
            button.clicked.connect(
                lambda checked=False, phrase=text: self.add_refine_phrase(phrase)
            )
            quick_one.addWidget(button)
        post_col.addLayout(quick_one)
        quick_two = QHBoxLayout()
        for text in ("减少饱和", "暗部更通透", "电影感减弱"):
            button = QPushButton(text)
            button.setObjectName("Ghost")
            button.clicked.connect(
                lambda checked=False, phrase=text: self.add_refine_phrase(phrase)
            )
            quick_two.addWidget(button)
        post_col.addLayout(quick_two)
        self.refine_button = QPushButton("按意见生成新版本  ↻")
        self.refine_button.setObjectName("Primary")
        self.refine_button.setEnabled(False)
        self.refine_button.clicked.connect(self.refine_current)
        post_col.addWidget(self.refine_button)
        post_col.addStretch()
        self.tabs.addTab(post_page, "修订")
        self.tabs.tabBar().setUsesScrollButtons(False)
        self.tabs.tabBar().setExpanding(True)
        col.addWidget(self.tabs, 1)

        self.progress = QProgressBar()
        self.progress.setRange(0, 1)
        self.progress.setValue(0)
        col.addWidget(self.progress)
        action_row = QHBoxLayout()
        self.retry_button = QPushButton("重试失败")
        self.retry_button.setObjectName("Ghost")
        self.retry_button.clicked.connect(self.retry_failed)
        self.start_button = QPushButton("开始导演调色  →")
        self.start_button.setObjectName("Primary")
        self.start_button.clicked.connect(self.start_processing)
        action_row.addWidget(self.retry_button)
        action_row.addWidget(self.start_button, 1)
        col.addLayout(action_row)
        return panel

    def _history_page(self) -> QWidget:
        page = QWidget()
        layout = QHBoxLayout(page)
        layout.setContentsMargins(22, 20, 22, 18)
        layout.setSpacing(16)
        list_panel = QFrame()
        list_panel.setObjectName("UtilityRail")
        list_panel.setFixedWidth(356)
        left = QVBoxLayout(list_panel)
        left.setContentsMargins(19, 20, 19, 17)
        left.setSpacing(9)
        left.addWidget(label("THE ARCHIVE", "Eyebrow"))
        left.addWidget(label("暗房项目档案", "HeroTitle"))
        archive_note = label("每一次导演决定、参数配方和输出版本都会留在这里，方便重新进入工作状态。", "Muted")
        archive_note.setWordWrap(True)
        left.addWidget(archive_note)
        left.addSpacing(8)
        self.project_list = QListWidget()
        self.project_list.currentItemChanged.connect(self.show_history_project)
        left.addWidget(self.project_list, 1)
        layout.addWidget(list_panel)

        detail = QFrame()
        detail.setObjectName("Canvas")
        right = QVBoxLayout(detail)
        right.setContentsMargins(22, 20, 22, 20)
        top = QHBoxLayout()
        text = QVBoxLayout()
        text.addWidget(label("SELECTED EDITION", "Eyebrow"))
        self.history_title = label("选择一个项目", "DisplayTitle")
        text.addWidget(self.history_title)
        self.history_meta = label("还没有项目记录", "Muted")
        text.addWidget(self.history_meta)
        top.addLayout(text)
        top.addStretch()
        self.restore_button = QPushButton("重新进入工作台")
        self.restore_button.setObjectName("Ghost")
        self.restore_button.clicked.connect(self.restore_project)
        self.open_history_output = QPushButton("查看最终成片")
        self.open_history_output.clicked.connect(self.open_selected_history_output)
        top.addWidget(self.restore_button)
        top.addWidget(self.open_history_output)
        right.addLayout(top)

        content = QHBoxLayout()
        preview_card = card()
        preview_col = QVBoxLayout(preview_card)
        preview_col.setContentsMargins(12, 12, 12, 12)
        self.history_preview = QLabel("SELECT A PROJECT EDITION")
        self.history_preview.setObjectName("Preview")
        self.history_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.history_preview.setMinimumSize(420, 460)
        preview_col.addWidget(self.history_preview, 1)
        self.history_items = QListWidget()
        self.history_items.setFixedHeight(120)
        self.history_items.currentItemChanged.connect(self.show_history_item)
        preview_col.addWidget(self.history_items)
        content.addWidget(preview_card, 1)

        notes = card(accent=True)
        notes.setFixedWidth(430)
        notes_col = QVBoxLayout(notes)
        notes_col.setContentsMargins(15, 15, 15, 15)
        notes_col.addWidget(label("FINAL DIRECTOR'S NOTE", "Eyebrow"))
        self.history_prompt = QPlainTextEdit()
        self.history_prompt.setReadOnly(True)
        self.history_prompt.setMinimumHeight(145)
        notes_col.addWidget(self.history_prompt)
        notes_col.addWidget(label("RECIPE / DIAGNOSIS / REVIEW", "Eyebrow"))
        self.history_detail = QPlainTextEdit()
        self.history_detail.setReadOnly(True)
        notes_col.addWidget(self.history_detail, 1)
        content.addWidget(notes)
        right.addLayout(content, 1)
        layout.addWidget(detail, 1)
        return page

    def switch_page(self, index: int) -> None:
        self.pages.setCurrentIndex(index)
        self.studio_nav.setChecked(index == 0)
        self.history_nav.setChecked(index == 1)
        if index == 1:
            self.refresh_history()

    def _update_mode(self) -> None:
        if self.settings.mock_mode:
            self.mode_chip.setText("●  MOCK · OFFLINE")
            self.statusBar().showMessage(self._tr("离线 Mock 模式 · 本地演练完整流程"))
        else:
            suffix = " · LRC" if self.settings.lightroom_enabled else ""
            self.mode_chip.setText("●  QWEN ONLINE" + suffix)
            self.statusBar().showMessage(self._tr("在线看片模式 · 只发送 1024px JPEG 预览与白名单 EXIF"))

    def import_files(self) -> None:
        names, _ = QFileDialog.getOpenFileNames(
            self,
            self._tr("选择 RAW 底片"),
            "",
            self._tr("RAW 底片 (*.arw *.cr2 *.cr3 *.nef *.raf *.dng)"),
        )
        self.add_paths(names)

    def import_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, self._tr("选择 RAW 文件夹"))
        if folder:
            self.add_paths([folder])

    def add_paths(self, paths) -> int:
        existing = set(self.files)
        new_files = [path for path in collect_raw_files(paths) if path not in existing]
        if not new_files:
            return 0
        start = len(self.files)
        self.files.extend(new_files)
        self.refresh_table()
        self.table.selectRow(start)
        self._launch_preflight(new_files, list(range(start, len(self.files))))
        return len(new_files)

    def _set_drop_active(self, active: bool) -> None:
        if not hasattr(self, "viewer_frame"):
            return
        self.viewer_frame.setProperty("dropActive", active)
        self.viewer_frame.style().unpolish(self.viewer_frame)
        self.viewer_frame.style().polish(self.viewer_frame)
        self.viewer_frame.update()
        if active:
            self.statusBar().showMessage(self._tr("松开鼠标即可导入 RAW 或扫描整个文件夹"))

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        mime = event.mimeData()
        if not mime.hasUrls():
            event.ignore()
            return
        paths = [Path(url.toLocalFile()) for url in mime.urls() if url.isLocalFile()]
        if any(
            path.is_dir()
            or path.suffix.lower() in {".arw", ".cr2", ".cr3", ".nef", ".raf", ".dng"}
            for path in paths
        ):
            event.acceptProposedAction()
            self._set_drop_active(True)
        else:
            event.ignore()

    def dragMoveEvent(self, event: QDragMoveEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dragLeaveEvent(self, event: QDragLeaveEvent) -> None:
        self._set_drop_active(False)
        self._update_mode()
        event.accept()

    def dropEvent(self, event: QDropEvent) -> None:
        self._set_drop_active(False)
        paths = [
            url.toLocalFile()
            for url in event.mimeData().urls()
            if url.isLocalFile()
        ]
        count = self.add_paths(paths)
        if count:
            event.acceptProposedAction()
            self.statusBar().showMessage(
                self._tr("已拖入 {count} 张 RAW · Agent 正在读取预览并初审", count=count)
            )
        else:
            event.ignore()
            self.statusBar().showMessage(
                self._tr("未发现支持的 RAW；请选择 ARW、CR2、CR3、NEF、RAF 或 DNG")
            )

    def _launch_preflight(self, files: list[Path], row_map: list[int]) -> None:
        self._preflight_active = True
        self.start_button.setEnabled(False)
        self.analysis_state.setText(self._tr("正在看片"))
        self.progress.setRange(0, len(files))
        self.progress.setValue(0)
        self._preflight_done = 0
        worker = self.manager.analyze(files, self.settings)
        worker.signals.item_status.connect(
            lambda index, status: self.on_status(row_map[index], status)
        )
        worker.signals.item_done.connect(
            lambda index, result: self.on_preflight_done(row_map[index], result)
        )
        worker.signals.finished.connect(self.on_preflight_finished)

    def on_preflight_done(self, index: int, result: ProcessResult) -> None:
        self.results[index] = result
        if result.suggested_style:
            self.style_by_path[str(result.source)] = result.suggested_style
        self._preflight_done += 1
        self.progress.setValue(self._preflight_done)
        self.refresh_row(index)
        self.log_view.appendPlainText(
            f"[{result.status}]  {result.source.name}"
            + (f"\n{result.error}" if result.error else "\n" + self._tr("Agent 已生成可编辑建议"))
        )
        if self.table.currentRow() == index or self.table.currentRow() < 0:
            self.table.selectRow(index)
            self.show_selected()

    def on_preflight_finished(self) -> None:
        self._preflight_active = False
        self.start_button.setEnabled(bool(self.files))
        self.analysis_state.setText(self._tr("建议已就绪"))
        self.statusBar().showMessage(self._tr("AI 初审完成 · 请确认或修改每张照片的调色建议"))

    def clear_batch(self) -> None:
        if self._preflight_active or self._batch_active:
            QMessageBox.information(self, self._tr("任务进行中"), self._tr("请等待当前任务完成后再清空。"))
            return
        self.files.clear()
        self.results.clear()
        self.style_by_path.clear()
        self.refresh_table()
        self.preview.setPixmap(QPixmap())
        self.preview.setText(self._tr("把 RAW 从文件夹拖到这里"))
        self.output_preview.setPixmap(QPixmap())
        self.output_preview.setText(self._tr("等待第一张工作样片\n\n完成后在这里逐项对照"))
        self.preview_title.setText(self._tr("等待一张底片"))
        self.style.clear()
        self.diagnosis.clear()
        self.plan.clear()
        self.log_view.clear()
        self.refine_feedback.clear()
        self.refine_button.setEnabled(False)
        self.analysis_state.setText(self._tr("等待看片"))

    def refresh_table(self) -> None:
        self.table.setRowCount(len(self.files))
        for row in range(len(self.files)):
            self.refresh_row(row)
        count = len(self.files)
        self.batch_meta.setText(f"{count} FRAMES")
        self.session_meta.setText(
            self._tr("{count} 张底片\n等待你确认每张建议", count=count)
            if count else self._tr("尚未载入底片")
        )

    def refresh_row(self, row: int) -> None:
        if row >= len(self.files):
            return
        path = self.files[row]
        result = self.results.get(row, ProcessResult(source=path))
        prompt = self.style_by_path.get(str(path), "")
        prompt_excerpt = prompt.replace("\n", " ")[:34] + ("…" if len(prompt) > 34 else "")
        output = result.rendered_path or result.xmp_path
        values = (
            path.name,
            self._tr(result.status),
            prompt_excerpt or self._tr("等待 Agent 建议"),
            str(output or "—"),
        )
        for column, value in enumerate(values):
            item = self.table.item(row, column) or QTableWidgetItem()
            item.setText(value)
            if column == 1:
                item.setForeground(self._status_color(result.status))
            self.table.setItem(row, column, item)
        self.table.setRowHeight(row, 42)

    @staticmethod
    def _status_color(status: str) -> QColor:
        return {
            "成功": QColor("#8EBB96"),
            "失败": QColor("#D77B6A"),
            "处理中": QColor("#D8B36D"),
            "分析中": QColor("#C6A261"),
            "待确认": QColor("#9DB6B0"),
            "等待": QColor("#77766F"),
        }.get(status, QColor("#77766F"))

    def choose_output(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, self._tr("选择成片输出目录"), self.output.text())
        if folder:
            self.output.setText(folder)

    def open_settings(self) -> None:
        dialog = SettingsDialog(self.settings, self)
        if dialog.exec():
            self.settings = dialog.value()
            try:
                if self.settings.lightroom_enabled:
                    LightroomBridge(self.settings.lightroom_path).install_plugin()
                self.settings.save()
            except LightroomError as exc:
                QMessageBox.warning(self, self._tr("Lightroom Bridge 安装失败"), str(exc))
                return
            self._update_mode()
            self.statusBar().showMessage(self._tr("连接与输出设置已保存在 {path}", path=config_dir()))

    def save_current_prompt(self) -> None:
        if self._loading_prompt:
            return
        row = self.table.currentRow()
        if 0 <= row < len(self.files):
            self.style_by_path[str(self.files[row])] = self.style.toPlainText().strip()
            self.refresh_row(row)

    def add_refine_phrase(self, phrase: str) -> None:
        current = self.refine_feedback.toPlainText().strip()
        self.refine_feedback.setPlainText(
            (current + ("；" if current and self.settings.interface_language == "zh_CN" else "; " if current else "") + self._tr(phrase)).strip()
        )
        self.refine_feedback.setFocus()

    def start_processing(self) -> None:
        if not self.files:
            QMessageBox.information(self, self._tr("还没有底片"), self._tr("请先导入 RAW 文件或文件夹。"))
            return
        if self._preflight_active:
            QMessageBox.information(self, self._tr("Agent 正在看片"), self._tr("请等待 AI 初审完成。"))
            return
        missing = [path.name for path in self.files if not self.style_by_path.get(str(path), "").strip()]
        if missing:
            QMessageBox.information(
                self,
                self._tr("还有建议未确认"),
                self._tr("这些底片还没有可执行提示词：\n") + "\n".join(missing[:8]),
            )
            return
        self.current_project_id = self.history.begin(Path(self.output.text()), self.files).id
        self._launch_batch(self.files, list(range(len(self.files))))

    def retry_failed(self) -> None:
        rows = [row for row, result in self.results.items() if result.status == "失败"]
        if not rows:
            QMessageBox.information(self, self._tr("无需重试"), self._tr("当前批次没有失败任务。"))
            return
        if not self.current_project_id:
            self.current_project_id = self.history.begin(
                Path(self.output.text()), [self.files[row] for row in rows]
            ).id
        self._launch_batch([self.files[row] for row in rows], rows)

    def _launch_batch(self, files: list[Path], row_map: list[int]) -> None:
        self._batch_active = True
        self.start_button.setEnabled(False)
        self.retry_button.setEnabled(False)
        self.clear_button.setEnabled(False)
        self.refine_button.setEnabled(False)
        self.analysis_state.setText(self._tr("正在调色"))
        self._batch_done = 0
        self.progress.setRange(0, len(files))
        self.progress.setValue(0)
        styles = {str(path): self.style_by_path.get(str(path), "") for path in files}
        prepared = {
            str(self.files[row]): self.results[row]
            for row in row_map
            if row in self.results
        }
        worker = self.manager.start(
            files,
            Path(self.output.text()),
            styles,
            self.settings,
            prepared,
        )
        worker.signals.item_status.connect(
            lambda index, status: self.on_status(row_map[index], status)
        )
        worker.signals.item_done.connect(
            lambda index, result: self.on_done(row_map[index], result)
        )
        worker.signals.finished.connect(self.on_finished)

    def on_status(self, index: int, status: str) -> None:
        item = self.table.item(index, 1)
        if item:
            item.setText(self._tr(status))
            item.setForeground(self._status_color(status))

    def on_done(self, index: int, result: ProcessResult) -> None:
        self.results[index] = result
        prompt = self.style_by_path.get(str(result.source), result.final_prompt)
        if self.current_project_id:
            self.history.record(self.current_project_id, result, prompt)
        self.refresh_row(index)
        self._batch_done += 1
        self.progress.setValue(self._batch_done)
        self.log_view.appendPlainText(
            f"[{result.status}]  {result.source.name}"
            + (
                f"\n{result.error}"
                if result.error
                else "\n" + self._tr("配方、XMP 与项目记录已保存")
            )
            + (f"\n{result.quality_note}" if result.quality_note else "")
        )
        self.table.selectRow(index)
        self.show_selected()

    def on_finished(self) -> None:
        self._batch_active = False
        self.start_button.setEnabled(True)
        self.retry_button.setEnabled(True)
        self.clear_button.setEnabled(True)
        self.analysis_state.setText(self._tr("调色完成"))
        self.show_selected()
        success = sum(result.status == "成功" for result in self.results.values())
        failed = sum(result.status == "失败" for result in self.results.values())
        self.statusBar().showMessage(
            self._tr(
                "批次完成 · {success} 成功 · {failed} 失败 · 已写入项目档案",
                success=success,
                failed=failed,
            )
        )
        self.refresh_history()

    def refine_current(self) -> None:
        row = self.table.currentRow()
        if row < 0 or row not in self.results:
            QMessageBox.information(self, self._tr("还没有成片"), self._tr("请先选择一张已经完成调色的照片。"))
            return
        current = self.results[row]
        if current.status != "成功" or not current.plan:
            QMessageBox.information(self, self._tr("当前版本不可修订"), self._tr("请先完成第一版智能调色。"))
            return
        feedback = self.refine_feedback.toPlainText().strip()
        if not feedback:
            QMessageBox.information(self, self._tr("还没有修改意见"), self._tr("请描述当前成片哪里不满意。"))
            return
        self._batch_active = True
        self.start_button.setEnabled(False)
        self.retry_button.setEnabled(False)
        self.clear_button.setEnabled(False)
        self.refine_button.setEnabled(False)
        self.analysis_state.setText(self._tr("正在二次调色"))
        self.progress.setRange(0, 0)
        self.refine_project_id = self.history.begin(
            Path(self.output.text()),
            [current.source],
            title=self._tr("{stem} · 后处理", stem=current.source.stem),
        ).id
        worker = self.manager.refine(
            current,
            Path(self.output.text()),
            feedback,
            self.settings,
        )
        worker.signals.item_status.connect(
            lambda index, status: self.on_status(row, status)
        )
        worker.signals.item_done.connect(
            lambda index, result: self.on_refine_done(row, result)
        )
        worker.signals.finished.connect(self.on_refine_finished)

    def on_refine_done(self, row: int, result: ProcessResult) -> None:
        self.results[row] = result
        self.history.record(
            self.refine_project_id,
            result,
            result.final_prompt,
        )
        self.refresh_row(row)
        self.table.selectRow(row)
        self.show_selected()
        self.log_view.appendPlainText(
            f"[{self._tr('后处理')}{self._tr(result.status)}]  {result.source.name}"
            + (f"\n{result.error}" if result.error else "\n" + self._tr("已生成独立修订版本"))
            + (f"\n{result.quality_note}" if result.quality_note else "")
        )

    def on_refine_finished(self) -> None:
        self._batch_active = False
        self.progress.setRange(0, 1)
        self.progress.setValue(1)
        self.start_button.setEnabled(True)
        self.retry_button.setEnabled(True)
        self.clear_button.setEnabled(True)
        self.show_selected()
        result = self.results.get(self.table.currentRow())
        if result and result.status == "成功":
            self.analysis_state.setText(self._tr("新版本已生成"))
            self.statusBar().showMessage(
                self._tr("后处理完成 · 新旧版本均已保留，可继续输入下一轮意见")
            )
            self.refine_feedback.clear()
        else:
            self.analysis_state.setText(self._tr("后处理失败"))
            self.statusBar().showMessage(self._tr("后处理未完成 · 请查看日志后重试"))
        self.refresh_history()

    def show_selected(self) -> None:
        row = self.table.currentRow()
        if row < 0 or row >= len(self.files):
            return
        path = self.files[row]
        result = self.results.get(row)
        self.preview_title.setText(path.name)
        self.frame_meta.setText(path.suffix.upper().lstrip(".") + " · LOCAL PREVIEW")
        if result and result.preview_path and result.preview_path.exists():
            self._set_pixmap(self.preview, result.preview_path)
        else:
            self.preview.setPixmap(QPixmap())
            self.preview.setText(self._tr("AGENT 正在读取嵌入预览…" if result else "等待 AI 初审"))
        if result and result.rendered_path and result.rendered_path.exists():
            self._set_pixmap(self.output_preview, result.rendered_path)
        else:
            self.output_preview.setPixmap(QPixmap())
            self.output_preview.setText(self._tr("等待 Lightroom 成片\n完成后自动并排显示"))

        self._loading_prompt = True
        self.style.setPlainText(self.style_by_path.get(str(path), ""))
        self._loading_prompt = False
        if not result:
            self.analysis_lead.setText(self._tr("等待 Agent 检查这张底片。"))
            self.diagnosis.clear()
            self.plan.clear()
            self.refine_button.setEnabled(False)
            return
        if result.diagnosis:
            diagnosis = result.diagnosis
            self.analysis_lead.setText(diagnosis.summary or diagnosis.scene)
            self.diagnosis.setPlainText(self._diagnosis_text(diagnosis))
        else:
            self.analysis_lead.setText(result.error or self._tr("尚未完成初审"))
            self.diagnosis.setPlainText(result.error)
        self.plan.setPlainText(
            json.dumps(result.plan.model_dump(), ensure_ascii=False, indent=2)
            if result.plan else ""
        )
        self.analysis_state.setText(self._tr(result.status))
        self.refine_button.setEnabled(
            not self._batch_active
            and result.status == "成功"
            and result.plan is not None
        )

    def _diagnosis_text(self, diagnosis: Diagnosis) -> str:
        regions = "\n".join(
            f"  · {name}: {advice}"
            for name, advice in diagnosis.local_edit_opportunities.items()
        ) or self._tr("  · 暂无明确局部区域")
        return (
            f"{self._tr('画面判断')}\n{diagnosis.scene}\n\n"
            f"{self._tr('曝光')}\n{diagnosis.exposure}\n\n"
            f"{self._tr('白平衡')}\n{diagnosis.white_balance}\n\n"
            f"{self._tr('高光 / 暗部')}\n{diagnosis.highlights}\n{diagnosis.shadows}\n\n"
            f"{self._tr('肤色 / 噪声')}\n{diagnosis.skin_tone}\n{diagnosis.noise}\n\n"
            f"{self._tr('适合局部处理的区域')}\n{regions}"
        )

    def _set_pixmap(self, target: QLabel, path: Path) -> None:
        pixmap = QPixmap(str(path))
        if pixmap.isNull():
            target.setText(self._tr("预览不可用"))
            return
        size = target.size()
        pixmap = pixmap.scaled(
            max(size.width() - 8, 100),
            max(size.height() - 8, 100),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        target.setText("")
        target.setPixmap(pixmap)

    def refresh_history(self) -> None:
        selected_id = ""
        if self.project_list.currentItem():
            selected_id = self.project_list.currentItem().data(Qt.ItemDataRole.UserRole)
        self.project_list.clear()
        for project in self.history.load():
            complete = sum(item.status == "成功" for item in project.items)
            stamp = project.created_at.replace("T", " ")[:16]
            item = QListWidgetItem(
                f"{project.title}\n{stamp}  ·  {complete}/{len(project.items)} "
                + ("complete" if self.settings.interface_language == "en_US" else "完成")
            )
            item.setData(Qt.ItemDataRole.UserRole, project.id)
            self.project_list.addItem(item)
            if project.id == selected_id:
                self.project_list.setCurrentItem(item)
        if self.project_list.count() and not self.project_list.currentItem():
            self.project_list.setCurrentRow(0)

    def _selected_project(self) -> ProjectRecord | None:
        current = self.project_list.currentItem()
        if not current:
            return None
        project_id = current.data(Qt.ItemDataRole.UserRole)
        return next((item for item in self.history.load() if item.id == project_id), None)

    def show_history_project(self, current=None, previous=None) -> None:
        project = self._selected_project()
        self.history_items.clear()
        if not project:
            return
        self.history_title.setText(project.title)
        self.history_meta.setText(
            f"{project.created_at.replace('T', ' ')[:19]}  ·  {len(project.items)} "
            + ("frames" if self.settings.interface_language == "en_US" else "张")
            + f"  ·  {project.output_dir}"
        )
        for index, history_item in enumerate(project.items):
            entry = QListWidgetItem(
                f"{Path(history_item.source).name}   ·   {self._tr(history_item.status)}"
            )
            entry.setData(Qt.ItemDataRole.UserRole, index)
            self.history_items.addItem(entry)
        if self.history_items.count():
            self.history_items.setCurrentRow(0)

    def show_history_item(self, current=None, previous=None) -> None:
        project = self._selected_project()
        item_widget = self.history_items.currentItem()
        if not project or not item_widget:
            return
        index = item_widget.data(Qt.ItemDataRole.UserRole)
        if not isinstance(index, int) or index >= len(project.items):
            return
        item = project.items[index]
        preview = Path(item.rendered_path or item.preview_path)
        if preview.exists():
            self._set_pixmap(self.history_preview, preview)
        else:
            self.history_preview.setPixmap(QPixmap())
            self.history_preview.setText(self._tr("项目预览已移动或不存在"))
        self.history_prompt.setPlainText(item.final_prompt or item.suggested_style)
        payload = {
            "diagnosis": item.diagnosis,
            "edit_plan": item.plan,
            "xmp": item.xmp_path,
            "rendered": item.rendered_path,
            "quality": item.quality_note,
            "error": item.error,
        }
        self.history_detail.setPlainText(json.dumps(payload, ensure_ascii=False, indent=2))

    def restore_project(self) -> None:
        project = self._selected_project()
        if not project:
            return
        self.files.clear()
        self.results.clear()
        self.style_by_path.clear()
        for item in project.items:
            source = Path(item.source)
            if not source.exists():
                continue
            row = len(self.files)
            self.files.append(source)
            result = ProcessResult(
                source=source,
                status="待确认",
                preview_path=Path(item.preview_path) if item.preview_path else None,
                diagnosis=Diagnosis.model_validate(item.diagnosis) if item.diagnosis else None,
                suggested_style=item.suggested_style,
                final_prompt=item.final_prompt,
                plan=EditPlan.model_validate(item.plan) if item.plan else None,
                xmp_path=Path(item.xmp_path) if item.xmp_path else None,
                rendered_path=Path(item.rendered_path) if item.rendered_path else None,
                quality_note=item.quality_note,
                error=item.error,
            )
            self.results[row] = result
            self.style_by_path[str(source)] = item.final_prompt or item.suggested_style
        self.output.setText(project.output_dir)
        self.refresh_table()
        self.switch_page(0)
        if self.files:
            self.table.selectRow(0)
        self.statusBar().showMessage(self._tr("项目已载回工作台 · 可以修改建议后再次执行"))

    def open_selected_history_output(self) -> None:
        project = self._selected_project()
        current = self.history_items.currentItem()
        if not project or not current:
            return
        item = project.items[current.data(Qt.ItemDataRole.UserRole)]
        target = Path(item.rendered_path or item.xmp_path or project.output_dir)
        if target.exists():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(target.resolve())))
        else:
            QMessageBox.information(self, self._tr("文件已移动"), self._tr("记录仍在，但对应的输出文件已不存在。"))


def apply_application_style(app: QApplication) -> None:
    app.setFont(QFont("Microsoft YaHei UI", 10))
    app.setStyleSheet(APP_STYLE)
