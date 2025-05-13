
from PyQt5.QtGui import QFont

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTabWidget, QComboBox, QTextEdit, 
    QSizePolicy, QSpacerItem, QTableWidget, QHeaderView, QGraphicsDropShadowEffect
)
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtCore import Qt, pyqtSignal

class InitiateTabs(QWidget):
    """
    InitiateTabs is responsible for setting up and managing the primary tabbed UI structure 
    in the BrainNav application. It includes controls for whole-brain thresholding, cluster analysis, 
    and saving/exporting project data.

    Core Responsibilities:
    -----------------------
    - Initialize the main UI layout and container holding all tab views.
    - Create and populate three main tabs:
        1. Whole Brain TDP Thresholding
        2. Cluster Analysis Table
        3. Save & Export Controls
    - Manage dynamic UI elements like thresholding method selection, advisory messages, and 
      data metrics display.
    - Connect dropdowns and table events to application logic through PyQt signals and slots.

    Features:
    ---------
    - A dropdown (`thresholding_dropdown`) for selecting thresholding strategies (TDP, Z-score, etc.).
    - Advisory text box that updates based on selected thresholding method.
    - Integration with WBTing for threshold slider controls and cluster overlay logic.
    - A metrics display widget with modern styling and optional shadow effects.
    - A full-featured table for visualizing cluster data, including highlighting and row selection.
    - Support for external tabs like project export and custom maps.

    Key Attributes:
    ---------------
    - `tab_widget`: The QTabWidget managing all content tabs.
    - `table_widget`: QTableWidget displaying cluster statistics.
    - `thresholding_dropdown_clicked`: Signal emitted when the dropdown selection changes.
    - `advisory_text`: QTextEdit displaying user guidance.
    - `metrics_label`: QLabel showing real-time metadata and ARI analysis summaries.

    Notes:
    ------
    - This class forms the main interface surface for user interaction after uploading data.
    - UI elements are styled using dark theme conventions to match the overall application design.
    """

    # Define the button signals
    thresholding_dropdown_clicked = pyqtSignal()

    def __init__(self, BrainNav):
        super().__init__() # Initialize the QWidget

        self.brain_nav = BrainNav

        self.init_table()

    def init_table(self):
        # Create the main container for the tabs
        self.table_container = QWidget()
        table_layout = QVBoxLayout()

        # Create the tab widget
        self.tab_widget = QTabWidget()

        # -----------------------
        # Tab 1: Whole Brain TDP 
        # -----------------------
        whole_brain_tab = QWidget()
        whole_brain_layout = QVBoxLayout()


        # **Dropdown for thresholding options**
        self.thresholding_dropdown = QComboBox()
        self.thresholding_dropdown.addItems([
            "TDP-based", "Z-score based", "Anatomical Atlas", "User-specified cluster map"
        ])
        # self.thresholding_dropdown.currentIndexChanged.connect(self.update_threshold_option)
        self.thresholding_dropdown.currentIndexChanged.connect(self.thresholding_dropdown_clicked.emit)

        # **Advisory Text Box**
        self.advisory_text = QTextEdit()
        self.advisory_text.setReadOnly(True)

        # **Define Advisory Text for Each Option**
        self.advisory_messages = {
            "TDP-based": ("Applying a TDP threshold is equivalent to using different test statistic thresholds for cluster generation. "
                        "Each created cluster has the TDP not below the given threshold. "
                        "Note that you can adjust thresholds afterward. Navigate to the cluster tab for cluster analysis."),
            
            "Z-score based": ("Applying a test statistic threshold leads to conventional supra-threshold clusters. "
                            "Use the z-score option if you want to replicate results from a standard analysis. "
                            "Note that you can adjust thresholds afterward. Navigate to the cluster tab for cluster analysis."),

            "Anatomical Atlas": ("This method assigns a TDP value to each anatomical region instead of using thresholding to define clusters. "),

            "User-specified cluster map": ("Instead of defining clusters through thresholding, this method assigns a TDP value to predefined"
                                           "regions in your custom cluster map." )
        }

        # **Set Default Advisory Text**
        self.advisory_text.setText(self.advisory_messages["TDP-based"])
        
        self.advisory_text.setFixedHeight(60)

        # Initiate the whole brain tdp slider. 
        self.threshold_container1 = self.brain_nav.WBTing.whole_brain_tdp_slider() # -> self.threshold_container1

        # # **Atlas selection dropdown or file selection**
        # self.atlas_dropdown = QComboBox()
        # self.atlas_dropdown.addItems(["Atlas A", "Atlas B", "Atlas C"])  # Placeholder values
        # self.atlas_dropdown.setVisible(False)  # Initially hidden

        # self.cluster_map_button = QPushButton("Select Cluster Map")
        # self.cluster_map_button.setCursor(Qt.PointingHandCursor)
        # self.cluster_map_button.clicked.connect(self.select_cluster_map)
        # self.cluster_map_button.setVisible(False)  # Initially hidden

        # **Layout Configuration**
        threshold_layout = QHBoxLayout()
        threshold_layout.addWidget(QLabel("Thresholding Method:"))
        threshold_layout.addWidget(self.thresholding_dropdown)

        # Set layout alignment to top
        whole_brain_layout.setAlignment(Qt.AlignTop)

        # Ensure elements don't stretch unnecessarily
        self.thresholding_dropdown.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.threshold_container1.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.advisory_text.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)  # Allow width expansion

        whole_brain_layout.addLayout(threshold_layout)
        whole_brain_layout.addWidget(self.advisory_text)
        whole_brain_layout.addWidget(self.threshold_container1)
        whole_brain_layout.addSpacing(10)  # Adds a little space before the next elements

        self.init_metrics_container()  # Initialize the metrics container layout

        # And add the container layout (metrics label + group box) into the tile
        whole_brain_layout.addLayout(self.metrics_container_layout)

        # **Add a spacer to push everything to the top**
        spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        whole_brain_layout.addItem(spacer)
        

        whole_brain_tab.setLayout(whole_brain_layout)

        # -----------------------
        # Tab 2: Cluster Analysis (Table)
        # -----------------------
        cluster_tab = QWidget()
        cluster_layout = QVBoxLayout()

        cluster_title = QLabel("Cluster Statistics")
        cluster_title.setFont(QFont('Arial', 14, QFont.Bold))
        cluster_title.setAlignment(Qt.AlignLeft)
        cluster_title.setStyleSheet("padding: 5px;")

        self.table_widget = QTableWidget(self)
        self.table_widget.setColumnCount(8)
        self.table_widget.setHorizontalHeaderLabels([
            "Cluster", "Unique ID", "Size", "TDP", "max(Z)", "Vox (x, y, z)", "MNI (x, y, z)", "Region"
        ])
        
        # Hide the xyzV column (assuming it's column index 5)
        self.table_widget.setColumnHidden(5, True)

        self.table_widget.verticalHeader().setVisible(False)
        self.table_widget.setRowCount(20)

        # Enable scrolling
        self.table_widget.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)

        # Set the table's header to resize according to contents
        header = self.table_widget.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Cluster ID
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)  # Region
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)  # Region

        # Connect the row selection signal to the slot
        self.table_widget.itemSelectionChanged.connect(self.brain_nav.tblARI.on_row_selected)

        # Add title and table to the cluster analysis tab
        cluster_layout.addWidget(cluster_title)
        cluster_layout.addWidget(self.table_widget)
        cluster_tab.setLayout(cluster_layout)

        # -----------------------
        # Tab 3: Save & Export Project
        # -----------------------

        self.save_export_tab = self.brain_nav.save_export.init_save_and_export_tab()

        # -----------------------
        # Add tabs to tab widget
        # -----------------------
        self.tab_widget.addTab(whole_brain_tab, "Whole Brain TDP")
        self.tab_widget.addTab(cluster_tab, "Cluster Analysis")
        self.tab_widget.addTab(self.save_export_tab, "Save/Load and Export")

        # Set the height of the entire container (including tabs)
        half_height = self.brain_nav.height() // 2
        self.table_container.setFixedHeight(half_height)

        # Add the tab widget to the main layout
        table_layout.addWidget(self.tab_widget)

        # Set layout for the container widget
        self.table_container.setLayout(table_layout)

        return self.table_container


    def init_metrics_container(self):
        # Create the metrics layout
        self.metrics_container_layout = QVBoxLayout()

        # Create the label
        self.metrics_label = QLabel()
        self.metrics_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.metrics_label.setWordWrap(True)  # Allow multiline wrapping

        # Create a title label
        self.metrics_title = QLabel("Data Information")
        self.metrics_title.setAlignment(Qt.AlignLeft)
        title_font = QFont("Open Sans", 12, QFont.Bold)
        self.metrics_title.setFont(title_font)
        self.metrics_title.setStyleSheet("""
            QLabel {
                color: #ffffff;
                padding-bottom: 8px;
                margin-left: 2px;
            }
        """)

        # Set a more modern/larger font
        modern_font = QFont("Open Sans", 12)
        modern_font.setStyleStrategy(QFont.PreferAntialias)
        self.metrics_label.setFont(modern_font)

        # Optional: Add a drop shadow for a subtle glow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(12)          # Spread of the shadow
        shadow.setOffset(0, 2)            # Horizontal, vertical offset
        shadow.setColor(QColor(0, 0, 0, 180))
        self.metrics_label.setGraphicsEffect(shadow)

        # Update stylesheet for background, spacing, etc.
        self.metrics_label.setStyleSheet("""
            QLabel {
                background-color: #111;        /* Dark grey background */
                color: #fff;                   /* White text */
                padding: 15px;                 /* More padding for space around text */
                border-radius: 8px;            /* Slightly rounded corners */
                border: 1px solid #444;        /* Subtle border */
                font-size: 14pt;               /* Larger font size (override if needed) */
                line-height: 150%;             /* Increase vertical spacing between lines */
                letter-spacing: 0.5px;         /* Subtle spacing between letters */
            }
        """)

        # Remove or adjust any fixed size so it can expand if needed
        # self.metrics_label.setFixedSize(400, 100)  # Remove this line
        self.metrics_label.setMinimumSize(400, 120)  # Example: let it grow vertically

        # Add label to layout
        # self.metrics_container_layout.addWidget(self.metrics_title)
        self.metrics_container_layout.addWidget(self.metrics_label)

        # # Finally, show default metrics
        # self.brain_nav.metrics.show_metrics()