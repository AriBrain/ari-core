import re
import sys
import logging
import datetime
import traceback
from html import escape as _html_escape
from pathlib import Path
from typing import Optional

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QTextCursor
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit
)


# Color per level. Plain hex; rendered via inline <span>.
_LEVEL_COLOR = {
    'DEBUG': '#888888',
    'INFO':  '#dddddd',
    'WARN':  '#ffa500',
    'ERROR': '#ff6464',
}

_LEVEL_LOGLEVEL = {
    'DEBUG': logging.DEBUG,
    'INFO':  logging.INFO,
    'WARN':  logging.WARNING,
    'ERROR': logging.ERROR,
}


class MessageLogger(QWidget):
    """
    User-facing log surface for BrainNav.

    Provides four levels — info / warn / error / debug — each rendered with a
    timestamped, color-coded tag in the in-app log box, and mirrored to a
    rotating-friendly file logger at ~/.aribrain/aribrain.log.

    Messages emitted before init_message_box() runs (i.e. during subsystem
    construction) are buffered and flushed when the widget becomes available.

    The most-recently-constructed instance is registered as MessageLogger._active
    so that the global sys.excepthook installed by main.py can route uncaught
    exceptions into the UI.
    """

    _active: Optional['MessageLogger'] = None

    def __init__(self, brain_nav):
        super().__init__()
        self.brain_nav = brain_nav

        # Messages logged before init_message_box() runs are buffered.
        self._pending: list[str] = []
        self._widget_ready = False

        # Re-entrancy guard so a failure inside rendering doesn't recurse.
        self._rendering = False

        # Show DEBUG entries in the UI? File logger always records them.
        self.debug_enabled = False

        self._file_logger = self._setup_file_logger()

        MessageLogger._active = self

    # ------------------------------------------------------------------
    # Public level API
    # ------------------------------------------------------------------

    def info(self, message: str, *, html: bool = False) -> None:
        self._emit('INFO', message, html=html)

    def warn(self, message: str, *, html: bool = False) -> None:
        self._emit('WARN', message, html=html)

    def error(self, message: str, *, exc_info=None, html: bool = False) -> None:
        """
        Log an error. `exc_info` may be True (use sys.exc_info()) or a
        (type, value, tb) tuple — when present, the traceback is appended in the
        UI and written to the file log.
        """
        tb_text = None
        if exc_info is True:
            exc_info = sys.exc_info()
        if exc_info and exc_info[0] is not None:
            tb_text = ''.join(traceback.format_exception(*exc_info))
        self._emit('ERROR', message, html=html, traceback_text=tb_text)

    def debug(self, message: str, *, html: bool = False) -> None:
        self._emit('DEBUG', message, html=html)

    def set_debug_enabled(self, enabled: bool) -> None:
        self.debug_enabled = bool(enabled)

    @classmethod
    def get_active(cls) -> Optional['MessageLogger']:
        return cls._active

    # ------------------------------------------------------------------
    # Backwards-compat shim. New code should call .info() directly.
    # ------------------------------------------------------------------

    def log_message(self, message: str) -> None:
        self._emit('INFO', message, html=True)

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def _emit(self, level: str, message: str, *, html: bool = False,
              traceback_text: Optional[str] = None) -> None:
        # File log first — always, regardless of UI readiness.
        plain = self._strip_html(message) if html else message
        self._log_to_file(level, plain, traceback_text)

        if level == 'DEBUG' and not self.debug_enabled:
            return

        body = message if html else _html_escape(message).replace('\n', '<br>')
        color = _LEVEL_COLOR.get(level, '#dddddd')
        ts = datetime.datetime.now().strftime('%H:%M:%S')

        row = (
            f"<span style='color: #888888;'>[{ts}]</span> "
            f"<span style='color: {color}; font-weight: bold;'>[{level}]</span> "
            f"<span style='color: {color};'>{body}</span>"
        )

        if traceback_text:
            row += (
                f"<pre style='color: {color}; margin: 2px 0 6px 24px;"
                f" font-family: Consolas, monospace; font-size: 10pt;'>"
                f"{_html_escape(traceback_text)}</pre>"
            )

        if not self._widget_ready:
            self._pending.append(row)
            return

        self._append_to_widget(row)

    def _append_to_widget(self, row_html: str) -> None:
        if self._rendering:
            return
        self._rendering = True
        try:
            lines = re.split(r'<br\s*/?>', row_html)
            formatted = [f"> {line.strip()}" for line in lines if line.strip()]
            out = "<br>".join(formatted)
            current = self.message_text.toHtml()
            self.message_text.setHtml(current + out + "<br>")
            self.message_text.moveCursor(QTextCursor.End)
        finally:
            self._rendering = False

    def _flush_pending(self) -> None:
        for row in self._pending:
            self._append_to_widget(row)
        self._pending.clear()

    # ------------------------------------------------------------------
    # File logger
    # ------------------------------------------------------------------

    def _setup_file_logger(self) -> logging.Logger:
        logger = logging.getLogger('ari_application.message_log')
        if not logger.handlers:
            try:
                log_dir = Path.home() / '.aribrain'
                log_dir.mkdir(exist_ok=True)
                handler = logging.FileHandler(log_dir / 'aribrain.log', encoding='utf-8')
            except Exception:
                handler = logging.StreamHandler(sys.stderr)
            handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S',
            ))
            logger.addHandler(handler)
            logger.setLevel(logging.DEBUG)
            logger.propagate = False
        return logger

    def _log_to_file(self, level: str, message: str,
                     traceback_text: Optional[str] = None) -> None:
        full = message if not traceback_text else f"{message}\n{traceback_text}"
        self._file_logger.log(_LEVEL_LOGLEVEL.get(level, logging.INFO), full)

    @staticmethod
    def _strip_html(s: str) -> str:
        return re.sub(r'<[^>]+>', '', s)

    # ------------------------------------------------------------------
    # Widget construction
    # ------------------------------------------------------------------

    def init_message_box(self):
        """
        Creates a modern, sleek message box with improved styling.
        """
        self.message_log_container = QWidget()
        message_log_layout = QVBoxLayout()
        message_log_layout.setContentsMargins(0, 0, 0, 0)
        message_log_layout.setSpacing(10)

        # Store original parent for redocking
        self.original_parent = None

        # Main message box widget (initially docked)
        self.message_box = QWidget()
        self.message_box.setStyleSheet("""
            QWidget {
                background-color: rgba(26, 26, 26, 200);  /* Slight transparency */
                border: 2px solid rgba(136, 136, 136, 180);
                border-radius: 12px;
                padding: 10px;
            }
        """)

        # Title bar
        title_bar = QWidget()
        title_bar_layout = QHBoxLayout()
        title_bar_layout.setContentsMargins(8, 4, 8, 4)
        title_bar_layout.setSpacing(5)

        title_label = QLabel("📩 Message Log")
        title_label.setStyleSheet("""
            color: white;
            font-size: 13pt;
            font-weight: bold;
            padding: 4px;
            border: 0px
        """)

        # Toggle button: 🗖 (undock), 🗗 (dock)
        self.toggle_dock_button = QPushButton("⧉")
        self.toggle_dock_button.setStyleSheet("""
            QPushButton {
                background: none;
                border: none;
                color: white;
                font-size: 16px;
                font-weight: bold;
                padding: 4px;
            }
            QPushButton:hover {
                color: #00ff99;  /* Neon hover effect */
            }
        """)
        self.toggle_dock_button.setFixedSize(30, 25)
        self.toggle_dock_button.setToolTip("Undock")
        self.toggle_dock_button.setToolTipDuration(300)

        self.toggle_dock_button.clicked.connect(self.toggle_message_box_dock)

        title_bar_layout.addWidget(title_label)
        title_bar_layout.addStretch()
        title_bar_layout.addWidget(self.toggle_dock_button)
        title_bar.setLayout(title_bar_layout)
        title_bar.setStyleSheet("""
            background-color: rgba(25, 25, 25, 220);
            border-top-left-radius: 12px;
            border-top-right-radius: 12px;
            padding: 5px;
        """)

        # Message text area
        self.message_text = QTextEdit()
        self.message_text.setReadOnly(True)
        self.message_text.setStyleSheet("""
            QTextEdit {
                background-color: rgba(15, 15, 15, 230);
                color: #dddddd;
                border: none;
                font-family: Consolas, "Courier New", monospace;
                font-size: 12pt;
                padding: 6px;
                border-bottom-left-radius: 12px;
                border-bottom-right-radius: 12px;
            }
        """)
        self.message_text.setMinimumHeight(120)

        # Main layout inside the message box
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(title_bar)
        layout.addWidget(self.message_text)
        self.message_box.setLayout(layout)

        # Track floating state
        self.is_message_box_floating = False

        message_log_layout.addWidget(self.message_box)
        self.message_log_container.setLayout(message_log_layout)

        self._widget_ready = True
        self._flush_pending()

        return self.message_log_container

    def toggle_message_box_dock(self):
        """
        Toggles the message log between docked (embedded in the message_log_container) and
        floating (a top-level window) states.
        """
        if not self.is_message_box_floating:
            # Undock: Remove from the container and make it a top-level window
            try:
                self.message_log_container.layout().removeWidget(self.message_box)
            except Exception:
                self.error("Failed to undock message log", exc_info=True)

            self.message_box.setParent(None)
            self.message_box.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)
            self.message_box.show()
            self.message_box.raise_()

            self.toggle_dock_button.setText("⧉")
            self.is_message_box_floating = True

        else:
            # Redock: Reattach it back to the message_log_container
            self.message_box.hide()

            self.message_box.setParent(self.message_log_container)
            self.message_box.setWindowFlags(Qt.Widget)
            self.message_box.show()

            # Explicitly reconnect the button to avoid losing it
            self.toggle_dock_button.clicked.disconnect()
            self.toggle_dock_button.clicked.connect(self.toggle_message_box_dock)

            self.message_log_container.layout().addWidget(self.message_box)

            self.toggle_dock_button.setText("⧉")
            self.is_message_box_floating = False

    def initiate_first_message(self):
        file_nr = self.brain_nav.file_nr

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        map_info = self.brain_nav.start_input
        data_dir = map_info.get('data_dir', 'Unknown')
        map_type = map_info.get('map_type', 'Unknown')
        template = map_info.get('template_dir', 'Unknown')
        mintdp = f"{self.brain_nav.fileInfo[file_nr]['mintdp']:.3f}"

        analysis_settings = self.brain_nav.input
        analysis_settings_str = ", ".join(
            f"{key}: {value}" for key, value in analysis_settings.items()
        )

        init_message = (
            f"<b>Session started at:</b> {timestamp}<br>"
            f"<b>Uploaded map type:</b> {map_type} with min TDP of: {mintdp}<br>"
            f"<b>Template:</b> {template}<br>"
            f"<b>Data directory:</b> {data_dir}<br>"
            f"<b>Analysis settings:</b> {analysis_settings_str}"
        )

        self.brain_nav.fileInfo[file_nr]['init_message'] = init_message

        self.info(init_message, html=True)
