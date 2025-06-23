
# === Required Imports ===
from PyQt5.QtWidgets import (
    QWidget, QGroupBox, QTableWidget, QTableWidgetItem, QPushButton,
    QSlider, QLineEdit, QVBoxLayout, QHBoxLayout, QHeaderView
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from ari_application.resources.styles import Styles


# === ClusterWorkStation Class ===
class ClusterWorkStation(QWidget):
    """
    ClusterWorkStation is a QWidget-based UI component for visualizing and manipulating a single 
    selected brain cluster within the BrainNav application.

    Features:
    - Displays detailed cluster properties in a dedicated work station table
    - Allows interactive adjustment of the TDP threshold 
      using plus/minus buttons, a slider, and a text box
    - Includes buttons for stepping through cluster state history
    - Dynamically updates UI elements to reflect the currently selected cluster
    - Provides warnings for non-editable clusters (e.g., TDP = 0)
    - Integrated with the main BrainNav logic and metrics pipeline

    This tool is designed to let users explore and tweak the characteristics of a cluster 
    after selection, offering fine-grained control and visual feedback for parameter tuning.
    """
    
    def __init__(self, brain_nav):

        super().__init__()
        self.brain_nav = brain_nav


    def init_work_station(self):
        # Create GroupBox for Work Station
        self.work_station_groupbox = QGroupBox("Selected Cluster Work Station")
        self.work_station_groupbox.setFont(QFont('Arial', 12, QFont.Bold))  # Set group box title font
        self.work_station_groupbox.setStyleSheet(
            "QGroupBox { color: white; border: 1px solid gray; border-radius: 5px; margin-top: 10px; padding: 10px; }"
        )

        # Create the work station table widget
        self.work_station_table = QTableWidget(self)
        self.work_station_table.setColumnCount(7)  # Same number of columns as the main table
        self.work_station_table.setHorizontalHeaderLabels([
            "Cluster", "Unique ID", "Size", "TDP", "max(Z)", "Vox", "MNI"
        ])
        self.work_station_table.verticalHeader().setVisible(False)  # Hide row headers
        self.work_station_table.setRowCount(1)  # Set it to one row to show the selected data

        # Turn off scroll
        self.work_station_table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # Set the table's header to resize according to contents
        header = self.work_station_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)

        # Set custom styles for the work station table
        self.work_station_table.setStyleSheet(Styles.work_station_table_styling)

        # Calculate the height based on the row height and the header height
        row_height = self.work_station_table.rowHeight(0)
        header_height = self.work_station_table.horizontalHeader().height()

        # Set the fixed height to include the header and one row
        total_height = row_height + header_height + 10
        self.work_station_table.setFixedHeight(total_height)

        # Create a vertical layout for the groupbox
        work_station_layout = QVBoxLayout()
        work_station_layout.addWidget(self.work_station_table)  # Add the table inside the group box

        # Initialize the slider group set 
        self.init_cluster_edit_buttons()
        work_station_layout.addWidget(self.button_container)

        # Create a vertical layout container to hold both sets of controls
        # self.cluster_controls_container = QVBoxLayout()
        # self.cluster_controls_container.setSpacing(10)  # Adjust spacing between groups
        # self.cluster_controls_container.addWidget(self.button_container)

        # Set layout for the GroupBox
        self.work_station_groupbox.setLayout(work_station_layout)

        # Create a QWidget to hold the groupbox
        self.work_station_container = QWidget()
        container_layout = QVBoxLayout()
        container_layout.addWidget(self.work_station_groupbox)
        self.work_station_container.setLayout(container_layout)

        return self.work_station_container  # Return the container with the group box

    def init_cluster_edit_buttons(self):
        """
        Initialize buttons and sliders for cluster-focused and whole-brain TDP threshold adjustment.
        Layout: Two rows stacked vertically, each containing [Minus Button] [Slider] [Plus Button] [Editable Text Box]
        """

        # First Control Group (Whole Brain Threshold)
        self.mintdp = 0.0  # Initial lower bound (updated dynamically)

        # Second Control Group (Cluster TDP Threshold)
        self.minus_button = QPushButton('-')
        self.minus_button.setCursor(Qt.PointingHandCursor)
        self.minus_button.setStyleSheet(Styles.minus_button_styling)
        self.minus_button.setFixedSize(40, 40)
        self.minus_button.clicked.connect(lambda: self.adjust_tdp(-0.01))

        self.plus_button = QPushButton('+')
        self.plus_button.setCursor(Qt.PointingHandCursor)
        self.plus_button.setStyleSheet(Styles.plus_button_styling)
        self.plus_button.setFixedSize(40, 40)
        self.plus_button.clicked.connect(lambda: self.adjust_tdp(0.01))

        self.cluster_slider = QSlider(Qt.Horizontal)
        self.cluster_slider.setRange(int(self.mintdp * 100), 100)
        self.cluster_slider.setValue(50)
        self.cluster_slider.setSingleStep(1)
        self.cluster_slider.setTickInterval(10)
        self.cluster_slider.setTickPosition(QSlider.TicksBelow)
        self.cluster_slider.setCursor(Qt.PointingHandCursor)
        self.cluster_slider.setFixedSize(200, 40)
        self.cluster_slider.setTracking(False)  # Prevents updates while hovering
        self.cluster_slider.valueChanged.connect(self.update_tdp_from_slider)
        self.cluster_slider.setStyleSheet(Styles.cluster_slider_styling)

        self.tdp_textbox = QLineEdit("0.50")
        self.tdp_textbox.setFixedWidth(50)
        self.tdp_textbox.setAlignment(Qt.AlignCenter)
        self.tdp_textbox.setStyleSheet("QLineEdit { font-size: 14px; }")
        self.tdp_textbox.returnPressed.connect(self.update_tdp_from_text)

        self.prev_state_button = QPushButton('↺')
        self.prev_state_button.setCursor(Qt.PointingHandCursor)
        self.prev_state_button.setStyleSheet(Styles.reset_button2_styling)
        self.prev_state_button.setFixedSize(60, 40)
        self.prev_state_button.clicked.connect(lambda: self.brain_nav.metrics.state_history())

        self.next_state_button = QPushButton('↻')
        self.next_state_button.setCursor(Qt.PointingHandCursor)
        self.next_state_button.setStyleSheet(Styles.reset_button2_styling)
        self.next_state_button.setFixedSize(60, 40)
        self.next_state_button.clicked.connect(lambda: self.brain_nav.metrics.state_history())

        # Layout for second control set
        self.button_layout = QHBoxLayout()
        self.button_layout.addWidget(self.minus_button)
        self.button_layout.addWidget(self.cluster_slider)
        self.button_layout.addWidget(self.plus_button)
        self.button_layout.addWidget(self.tdp_textbox)
        self.button_layout.addWidget(self.prev_state_button)
        self.button_layout.addWidget(self.next_state_button)
        self.button_layout.setSpacing(10)

        self.button_container = QWidget()
        self.button_container.setAttribute(Qt.WA_StyledBackground, True)
        self.button_container.setStyleSheet("background-color: #091c13; border-radius: 10px;")
        self.button_container.setLayout(self.button_layout)

        # Add both containers to the vertical layout
        # self.cluster_controls_container.addWidget(self.threshold_container1)
        # self.cluster_controls_container.addWidget(self.button_container)

    
    def update_work_station(self, selected_row=None):
        """
        Update the work_station_table based on the currently selected row.

        If selected_row is None, fill all fields with 'N/A'.
        """
        table_widget = self.brain_nav.tblARI.table_widget
        headers = [table_widget.horizontalHeaderItem(column).text() for column in range(table_widget.columnCount())]
        tdp_value = None

        for column in range(table_widget.columnCount()):
            if selected_row is None:
                # Fill with N/A if no row is selected
                item = QTableWidgetItem(" ")
            else:
                selected_item = table_widget.item(selected_row, column)
                item = QTableWidgetItem(selected_item.text()) if selected_item else QTableWidgetItem(" ")

                if headers[column] in ["Vox (x, y, z)", "MNI (x, y, z)"]:
                    font = QFont("Arial", 11)
                    item.setFont(font)

                if headers[column] == "TDP" and selected_item is not None:
                    try:
                        tdp_value = float(selected_item.text())
                    except ValueError:
                        print(f"Warning: TDP value '{selected_item.text()}' could not be converted to float.")

            self.work_station_table.setItem(0, column, item)

        if selected_row is not None and tdp_value is not None:
            self.brain_nav.UIHelp.update_tdp_ui(tdp_value)
        elif selected_row is not None:
            print("Warning: No TDP value found in selected row.")

    def clear_work_station(self):
        """
        Clear the contents of the work_station_table and reset it to its default state.
        This method is called when there is no selected row or cluster.
        """
        # Get the number of rows and columns in the work_station_table
        row_count = self.work_station_table.rowCount()
        column_count = self.work_station_table.columnCount()

        # Iterate over all cells and clear their contents
        for row in range(row_count):
            for column in range(column_count):
                self.work_station_table.setItem(row, column, None)

        # Optionally, set default placeholders or labels for the work station
        # Example: Add a placeholder to indicate the table is empty
        placeholder_item = QTableWidgetItem("Lost")
        placeholder_item.setTextAlignment(Qt.AlignCenter)  # Center align the placeholder text
        # font = QFont("Arial", 8, QFont.italic)
        # placeholder_item.setFont(font)

        # Add placeholder to the first cell if the table has at least one row and column
        if row_count > 0 and column_count > 0:
            self.work_station_table.setItem(0, 0, placeholder_item)

        self.tdp_textbox.blockSignals(False)
    

        # self.apply_tdp_threshold(new_tdp)  # Apply the threshold change
    def update_tdp_from_slider(self):
        """ Update TDP value when slider is moved. """
        new_tdp = round(self.cluster_slider.value() / 100, 2)
        self.set_tdp(new_tdp)

    def update_tdp_from_text(self):
        """ Update TDP value when manually entered in the text box. """
        try:
            new_tdp = float(self.tdp_textbox.text())
            self.set_tdp(new_tdp)
        except ValueError:
            print("[DEBUG]")
            invalid_text = self.tdp_textbox.text()
            print(f"[DEBUG] Invalid float entered in TDP textbox: '{invalid_text}'")
            # Reset to the current slider value if input is invalid
            self.tdp_textbox.setText(f"{self.cluster_slider.value() / 100:.2f}")

    def adjust_tdp(self, step):
        """ Adjust TDP threshold using + / - buttons. """
        try:
            # Get the current value from the text box (since it should be the latest displayed value)
            current_tdp = float(self.tdp_textbox.text())
        except ValueError:
            # Fallback to the internal tdp_value if parsing fails
            current_tdp = self.tdp_value

        # Calculate the new TDP value by adding the step and rounding
        new_tdp = round(current_tdp + step, 2)
        # Ensure the new value is within bounds (mintdp to 1.0)
        new_tdp = max(self.mintdp, min(new_tdp, 1.0))
        
        # Update the centralized TDP state and UI elements
        self.set_tdp(new_tdp)

    def set_tdp(self, new_tdp):
        """
        Centralized method to update the cluster TDP value.
        - new_tdp: float between self.mintdp and 1.0.
        This method updates the internal TDP state, updates the slider and text box,
        and then calls the metrics change function to update the selected cluster.
        """

        # --- Check if current cluster has TDP = 0 ---
        selected_cluster_id = self.brain_nav.ui_params.get('selected_cluster_id')
        tblARI_df = self.brain_nav.fileInfo[self.brain_nav.file_nr].get('tblARI_df')

        if selected_cluster_id is not None and tblARI_df is not None:
            # Find the row for the selected cluster
            selected_row = tblARI_df[tblARI_df['Unique ID'] == selected_cluster_id]

            if not selected_row.empty:
                cluster_tdp = selected_row['TDP'].values[0]

                if cluster_tdp == 0:
                    warning_message = (
                        "<span style='color: orange; font-weight: bold;'>"
                        f"Warning: Cluster {selected_cluster_id} has TDP = 0. "
                        "TDP adjustment is not possible."
                        "</span>"
                    )
                    self.brain_nav.message_box.log_message(warning_message)

                    print("\033[38;5;214m"  # Orange terminal output
                        f"Warning: Cluster {selected_cluster_id} has TDP = 0. "
                        "TDP adjustment is not possible.\033[0m")

                    # Optionally reset slider or textbox if desired (optional)
                    # self.tdp_textbox.setText(f"{self.cluster_slider.value() / 100:.2f}")
                    return  # Do not proceed with TDP update

        # Ensure the new TDP is within the allowed range.
        new_tdp = max(self.brain_nav.fileInfo[self.brain_nav.file_nr]['mintdp'], min(new_tdp, 1.0))

        # Now apply the TDP change to the selected cluster.
        self.brain_nav.metrics.change_cluster_size(new_tdp)