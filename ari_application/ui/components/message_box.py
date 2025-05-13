import re
import datetime

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QTextCursor
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit
)

class MessageLogger(QWidget):
    """
    MessageLogger handles the creation, display, and management of a custom message log box 
    within the BrainNav UI.

    It provides:
    - A styled message log container that can be docked or undocked (floating window)
    - A toggle button to switch between docked and floating states
    - A log method to append HTML-formatted messages with timestamped info and custom formatting
    - An initializer to populate the message box with session details

    This component helps provide feedback to users during interaction and logs key events 
    (such as threshold changes, cluster info, and data loading) in a persistent visual space.
    """

    def __init__(self, brain_nav):
        super().__init__()
        self.brain_nav = brain_nav


    def init_message_box(self):
        """
        Creates a modern, sleek message box with improved styling.
        """
        # --- New: Create a separate container for the Message Log ---
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
        # Set tooltip text and delay
        self.toggle_dock_button.setToolTip("Undock")
        self.toggle_dock_button.setToolTipDuration(300)  # 1000 ms = 1 second delay
        
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

        return self.message_log_container


    def toggle_message_box_dock(self):
        """
        Toggles the message log between docked (embedded in the message_log_container) and 
        floating (a top-level window) states.
        """
        print("toggle_message_box_dock called. is_message_box_floating:", self.is_message_box_floating)
        
        if not self.is_message_box_floating:
            # Undock: Remove from the container and make it a top-level window
            try:
                self.message_log_container.layout().removeWidget(self.message_box)
                print("Removed message_box from message_log_container.")
            except Exception as e:
                print("Error removing widget:", e)

            self.message_box.setParent(None)  # Detach from parent
            # Make it a floating window
            self.message_box.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)
            self.message_box.show()
            self.message_box.raise_()
            
            self.toggle_dock_button.setText("⧉")  # Update button
            self.is_message_box_floating = True
            print("Undocked: state updated to floating.")
        
        else:
            # Redock: Reattach it back to the message_log_container
            print("Redocking: Hiding floating message_box.")
            self.message_box.hide()
            
            self.message_box.setParent(self.message_log_container)  # Reparent it
            self.message_box.setWindowFlags(Qt.Widget)  # Restore normal widget behavior
            self.message_box.show()

            # Explicitly **reconnect** the button to avoid losing it
            self.toggle_dock_button.clicked.disconnect()
            self.toggle_dock_button.clicked.connect(self.toggle_message_box_dock)

            self.message_log_container.layout().addWidget(self.message_box)  # Add back to layout
            
            self.toggle_dock_button.setText("⧉")  # Update button
            self.is_message_box_floating = False
            print("Redocked: state updated to docked.")
                
    def log_message(self, message):
        """
        Append a message to the persistent message box. Each new line of the message is prefixed with "> ".
        """
        # Use regex to split on <br> tags, preserving content structure
        lines = re.split(r'<br\s*/?>', message)

        # Filter out empty lines and add "> " prefix
        formatted_lines = [f"> {line.strip()}" for line in lines if line.strip()]

        # Join lines back together with HTML line breaks
        formatted_message = "<br>".join(formatted_lines)

        # Get the current content (in HTML) and append the new message with a line break.
        current_text = self.message_text.toHtml()
        new_text = current_text + formatted_message + "<br>"
        self.message_text.setHtml(new_text)

        # Move the cursor to the end so that the latest message is visible
        self.message_text.moveCursor(QTextCursor.End)

    
    def initiate_first_message(self):
        import datetime
        file_nr = self.brain_nav.file_nr

        # Get current system timestamp
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Retrieve map type and data directory
        map_info = self.brain_nav.start_input
        data_dir = map_info.get('data_dir', 'Unknown')
        map_type = map_info.get('map_type', 'Unknown')
        template = map_info.get('template_dir', 'Unknown')
        mintdp = f"{self.brain_nav.fileInfo[file_nr]['mintdp']:.3f}"

        # Retrieve initial analysis settings
        analysis_settings = self.brain_nav.input

        # Format settings as a readable string
        analysis_settings_str = ", ".join(f"{key}: {value}" for key, value in analysis_settings.items())

        # Construct log message
        init_message = (
            f"<b>Session started at:</b> {timestamp}<br>"
             f"<b>Uploaded map type:</b> {map_type} with min TDP of: {mintdp}<br>"
            f"<b>Template:</b> {template}<br>"
            f"<b>Data directory:</b> {data_dir}<br>"
            f"<b>Analysis settings:</b> {analysis_settings_str}"
        )

        self.brain_nav.fileInfo[file_nr]['init_message'] = init_message

        # Log the message
        self.log_message(init_message)