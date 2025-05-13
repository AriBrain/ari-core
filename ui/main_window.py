# **Standard Library Imports**
import sys
import os

# **Third-Party Library Imports**
import pyqtgraph as pg
from dotenv import load_dotenv

# **PyQt Imports**
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget, QHBoxLayout, QGridLayout,  QDesktopWidget, QSpacerItem, QSizePolicy, QListWidgetItem
)


# **Project-Specific Imports (Ordered by Functionality)**
from controllers.mouse_interactions import MouseInteractions
from models.nifti_loader import NiftiLoader
from models.metrics import Metrics
from models.image_processing import ImageProcessing
from orth_views.orth_view_setup import OrthViewSetup
from orth_views.orth_view_update import OrthViewUpdate
from analyses.ARI import pyARI
from resources.styles import Styles

from ui.components.left_side_bar import LeftSideBar, StatImageItem
from ui.components.tabs.tblARI import TblARI
from ui.components.ui_helpers import UIHelpers
from ui.components.upload_files import UploadFiles
from ui.components.three_d_viewer import ThreeDViewer
from ui.components.tabs.whole_brain_thresholding import WBTing
from ui.components.tabs.initiate_tabs import InitiateTabs
from ui.components.cluster_work_station import ClusterWorkStation
from ui.components.message_box import MessageLogger
from ui.components.orth_viewer_controls import OrthViewerControls
from ui.components.save_and_export import SaveAndExportTab
from ui.components.menu_bar import MenuBar

# from ui.start_window import StartWindow  # Import the StartWindow class


# Load enviornmental variables
load_dotenv()

class BrainNav(QMainWindow):
    def __init__(self, start_input, load_data=False, data2load=None):
        super().__init__()
        print(f"PYDEVD_WARN_EVALUATION_TIMEOUT = {os.getenv('PYDEVD_WARN_EVALUATION_TIMEOUT')}")
        # BrainNav.__init__(self, start_input)  [Main Application Initialization]
        # ├── Stores start_input dictionary
        # ├── Initializes Core Components
        # │   ├── self.orth_view_setup (OrthViewSetup)
        # │   ├── self.mouse_interactions (MouseInteractions)
        # │   ├── self.orth_view_update (OrthViewUpdate)
        # │   ├── self.metrics (Metrics)
        # │   ├── self.nifti_loader (NiftiLoader)
        # │   ├── self.upload_files (UploadFiles)
        # │   ├── self.image_processing (ImageProcessing)
        # │   ├── self.ARI (pyARI)
        # │
        # ├── Sets Default Parameters (alpha, threshold, etc.)
        # ├── Loads NIfTI overlay (self.nifti_loader.load_overlay)
        # ├── Sets Window Properties (Title, Screen Size)
        # │
        # ├── Creates Main Layout
        # │   ├── self.central_widget (QWidget)  [Root Widget]
        # │   ├── self.main_layout (QHBoxLayout)  [Main Horizontal Layout]
        # │
        # ├── Initializes UI Components
        # │   ├── self.init_panes()  [Creates left_container & right_container]
        # │   │   ├── Calls `init_panes()`
        # │   │   │   ├── Creates slice_layout (QGridLayout) [2×2 grid for slices]
        # │   │   │   ├── Creates left_container (QWidget)
        # │   │   │   ├── Creates right_container (QWidget)
        # │   │   │   └── Creates `outer_layout` (QHBoxLayout) and sets as central widget
        # │   │
        # │   ├── self.init_sidebar()  [Creates Sidebar (Stat Images, Templates, Atlas)]
        # │   ├── self.init_menu()  [Creates Menu Bar]
        # │
        # ├── Loads Background Image (self.nifti_loader.load_bg)
        # └── Finalizes UI Setup

        # Store the start_input dictionary
        self.start_input = start_input
        self.main_window = self  # Store reference to the main window

        # set root directory
        self.root_dir = os.path.dirname(__file__)

        # === Default Parameters === #
        self.default_alpha = 60  
        self.alpha = 0.6         
        self.default_threshold = 75
        self.threshold = 75

        # === Default Input Settings === #
        # These maybe be changed by the user in teh settings menu bar
        self.input = {
            'simes': 'Simes',
            'conn': 18,
            'alpha': 0.05,
            'twosidedTest': True,
            'tdf': start_input['tdf']
        }

        # Initialize orientation labels for orthviews
        self.orientation_labels = {
            'axial': [],
            'sagittal': [],
            'coronal': []
        }

        self.nifti_loader       = NiftiLoader(self)

        # If user started new project - i.e. does not a load an existing project
        if load_data == False:
            self.fileInfo = {}
            self.atlasInfo = {}
            self.file_nr = 0  
            self.file_nr_template = 0
            self.templates = {}
            self.statmap_templates = {}
            # self.statmaps = {}
            self.aligned_statMapInfo = {}
            self.aligned_templateInfo = {}

            key = (self.file_nr, self.file_nr_template)
            self.aligned_statMapInfo[key] = {}
            self.aligned_templateInfo[key] = {}

            # === UI Parameters === #
            self.ui_params = {
                'selected_row': [],
                'selected_cluster_id': [],
                'gradmap': True,
                '3d_brain_data' : None
            }

            # Load Nifti Overlay (Ensures Data is Loaded)
            self.nifti_loader.load_overlay(start_input['data_dir'])

            # Load Background Image
            file_path = start_input['template_dir']
            self.nifti_loader.load_bg(file_path)

            # Initialize the stat_image_items list to store item widgets
            self.stat_image_items = []

            # Initialize 3D crosshair position
            self.sagittal_slice = 0  # Initialize the sagittal slice index
            self.coronal_slice  = 0  # Initialize the coronal slice index
            self.axial_slice    = 0  # Initialize the axial slice index
        
        # If user loaded existing project allocate the data to the class variables
        else:
            self.fileInfo               = data2load['fileInfo']
            self.atlasInfo              = data2load['atlasInfo']
            self.file_nr                = data2load['file_nr']
            self.file_nr_template       = data2load['file_nr_template']
            self.data_bg_index          = data2load['data_bg_index']
            self.templates              = data2load['templates']
            self.statmap_templates      = data2load['statmap_templates']
            self.ui_params              = data2load['ui_params']
            self.aligned_statMapInfo    = data2load['aligned_statMapInfo']
            self.aligned_templateInfo   = data2load['aligned_templateInfo']
            self.stat_image_items       = [] # This is not saved in the pickle file but needed when handling more than one statmap sessions        

            self.sagittal_dim = 0
            self.coronal_dim  = 1
            self.axial_dim    = 2

            tmpdata                 = self.templates[self.file_nr_template]['data'] 
            self.sagittal_slice     = tmpdata.shape[ self.sagittal_dim ] // 2
            self.coronal_slice      = tmpdata.shape[ self.coronal_dim ] // 2 
            self.axial_slice        = tmpdata.shape[ self.axial_dim ] // 2 

            self.ranges = data2load['ranges']

            # self.update_table(self.fileInfo[self.file_nr]['tblARI_df'])
            # self.metrics.update_overlay_image(self.file_nr, cluster_label=None)
            # self.metrics.show_metrics()

        # === Initialize Core Functionalities === #
        self.orth_view_setup    = OrthViewSetup(self)
        self.mouse_interactions = MouseInteractions(self)
        self.orth_view_update   = OrthViewUpdate(self)
        self.metrics            = Metrics(self)
        self.upload_files       = UploadFiles(self)
        self.image_processing   = ImageProcessing(self)
        self.ARI                = pyARI(self)

        # === Initialize UI Components === #
        self.tblARI             = TblARI(self)
        self.UIHelp             = UIHelpers(self)
        self.threeDviewer       = ThreeDViewer(self)
        self.WBTing             = WBTing(self)
        self.save_export        = SaveAndExportTab(self)
        self.initiate_tabs      = InitiateTabs(self)
        self.cluster_ws         = ClusterWorkStation(self)
        self.message_box        = MessageLogger(self)
        self.left_side_bar      = LeftSideBar(self)
        self.orth_view_controls = OrthViewerControls(self)
        self.menu_bar           = MenuBar(self)

        if load_data:
            # Restore stat image widgets from saved names
            self.stat_image_items.clear()
            self.left_side_bar.stat_images_list.clear()
            for name in data2load.get('stat_image_names', []):
                item_widget = StatImageItem(name)
                item = QListWidgetItem(self.left_side_bar.stat_images_list)
                item.setSizeHint(item_widget.sizeHint())
                self.left_side_bar.stat_images_list.setItemWidget(item, item_widget)
                self.stat_image_items.append(item_widget)

            # Restore template list from saved names
            self.left_side_bar.template_list.clear()
            for name in data2load.get('template_names', []):
                self.left_side_bar.template_list.addItem(name)
            self.left_side_bar.template_list.setCurrentRow(self.file_nr_template)

        # show default metrics
        self.metrics.show_metrics()

 

        # === Set Window Properties === #
        self.setWindowTitle("ARIBrain")
        screen_resolution = QDesktopWidget().screenGeometry()
        self.setGeometry(0, 0, screen_resolution.width(), screen_resolution.height())

        # === Central Widget & Layout === #
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)            

        # Connect signals from the left side bar to the upload_files methods
        self.left_side_bar.stat_image_add_clicked.connect(self.upload_files.upload_stat_image)
        self.left_side_bar.template_add_clicked.connect(self.upload_files.upload_template_dialog)
        self.left_side_bar.atlas_add_clicked.connect(self.upload_files.upload_atlas_dialog)

        self.init_panes()       # Creates left_container & right_container contained in outer_layout 
        self.menu_bar.init_menu()        # Creates menu bar

        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(10)

        # Ensure Central Widget Uses Main Layout
        self.central_widget.setLayout(self.main_layout)

        # For tracking mouse movement
        self._dragging = False  # Flag to track if the mouse is being dragged
        self._last_pos = None  # Variable to store the last mouse position

        self._right_dragging = False
        self._right_last_pos = None

        self._mouse_pressed = False  # Flag to differentiate single click and dra

        self.cluster_tab_blink_timer = QTimer(self)
        self.cluster_tab_blink_timer.timeout.connect(self.tblARI.blink_cluster_tab_title)

        self.cluster_tab_blink_state = False  # Track state of the cluster tab title

        # === NOW safe to update views ===
        if load_data:
            self.tblARI.update_table(self.fileInfo[self.file_nr]['tblARI_df'])
            self.metrics.update_overlay_image(self.file_nr, cluster_label=None)
            self.metrics.show_metrics()
            self.orth_view_setup.setup_viewer()
  



    def init_panes(self):
        # outer_layout (QHBoxLayout)  [Main layout]
        # ├── left_container (QWidget)  [Contains slices]
        # │   └── slice_layout (QGridLayout)  [2×2 grid for slices and metrics]
        # │       ├── sag_layout (QVBoxLayout)  [Sagittal slice]
        # │       │   ├── orth_title_style('Sagittal Slice') (QLabel)
        # │       │   └── sagittal_view (pg.ImageView)
        # │       │
        # │       ├── cor_layout (QVBoxLayout)  [Coronal slice]
        # │       │   ├── orth_title_style('Coronal Slice') (QLabel)
        # │       │   └── coronal_view (pg.ImageView)
        # │       │
        # │       ├── ax_layout (QVBoxLayout)  [Axial slice]
        # │       │   ├── orth_title_style('Axial Slice') (QLabel)
        # │       │   └── axial_view (pg.ImageView)
        # │       │
        # │       ├── metrics_layout (QVBoxLayout)  [Metrics and controls]
        # │       │   ├── orth_title_style('Metrics') (QLabel)
        # │       │   ├── metrics_container_layout (QVBoxLayout)
        # │       │   │   ├── metrics_label (QLabel)  [Displays data metrics]
        # │       │   │   ├── sliders_group_box (QGroupBox)  ["Controls"]
        # │       │   │   │   └── sliders_layout (QVBoxLayout)
        # │       │   │   │       ├── transparency_control_layout (QVBoxLayout)
        # │       │   │   │       │   ├── overlay_transparency_label (QLabel)  ["Overlay Transparency"]
        # │       │   │   │       │   ├── slider_reset_layout (QHBoxLayout)
        # │       │   │   │       │   │   ├── alpha_slider (QSlider)  [Range: 0-100, Default: self.default_alpha]
        # │       │   │   │       │   │   └── reset_button (QPushButton)  ["Reset View"]
        # │       │   │   │       │
        # │       │   │   │       └── transparency_control_layout added to sliders_layout
        # │       │   │   ├── sliders_group_box added to metrics_container_layout
        # │       │   ├── metrics_container_layout added to metrics_layout
        # │
        # ├── right_container (QWidget)  [Contains table and cluster controls]
        # │   └── right_layout (QVBoxLayout)
        # │       ├── table_widget (QTableWidget)  [Displays cluster data]
        # │       ├── work_station_container (QWidget)  [Cluster work station]
        # │       └── container_widget (QWidget)  [Cluster controls]
        # │
        # └── outer_layout set as central widget
        
        # Create the grid layout for the slices
        self.slice_layout = QGridLayout()
        self.slice_layout.setSpacing(5)

        # Create the three ImageViews
        self.axial_view = pg.ImageView()
        self.sagittal_view = pg.ImageView()
        self.coronal_view = pg.ImageView()

        # self.axial_view.getView().invertY(True)
        # self.sagittal_view.getView().invertY(True)
        # self.coronal_view.getView().invertY(True)


        for view in [self.axial_view, self.sagittal_view, self.coronal_view]:
            view.ui.histogram.hide()  
            view.ui.roiBtn.hide()
            view.ui.menuBtn.hide()
            view.setFixedSize(400, 400)
            view.setStyleSheet(" ".join(Styles.orth_view_styling))

        # ---------------------------
        #  Create each "tile" layout
        # ---------------------------

        # 1) Sagittal tile
        sag_layout = QVBoxLayout()
        sag_layout.addWidget(Styles.orth_title_style('Sagittal Slice', 400, 35))
        sag_layout.addWidget(self.sagittal_view)

        # 2) Coronal tile
        cor_layout = QVBoxLayout()
        cor_layout.addWidget(Styles.orth_title_style('Coronal Slice', 400, 35))
        cor_layout.addWidget(self.coronal_view)

        # 3) Axial tile
        ax_layout = QVBoxLayout()
        ax_layout.addWidget(Styles.orth_title_style('Axial Slice', 400, 35))
        ax_layout.addWidget(self.axial_view)

        # 4) “Metrics” tile (title + metrics label + slider + reset button)
        cluster_viewer_layout = QVBoxLayout()
        # metrics_layout.addWidget(Styles.orth_title_style('Metrics', 400, 35))
        cluster_viewer_layout.addWidget(Styles.cluster_viewer_title_style('3D Cluster Viewer', 400, 35))

        # -- A container for the metrics label + the sliders group
        self.cluster_viewer_container = QVBoxLayout()

        self.threeDviewer.init_3d_cluster_viewer()

        cluster_viewer_layout.addLayout(self.cluster_viewer_container)

        # -------------------------------------
        #  Place all four tiles into a 2×2 grid
        # -------------------------------------
        self.slice_layout.addLayout(sag_layout, 0, 0)
        self.slice_layout.addLayout(cor_layout, 0, 1)

        # **Add Vertical Spacer**
        vertical_spacer = QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.slice_layout.addItem(vertical_spacer, 1, 0, 1, 2)  # Row 1, spanning both columns

        self.slice_layout.addLayout(ax_layout, 2, 0)
        self.slice_layout.addLayout(cluster_viewer_layout, 2, 1)

        # -------------------------------------
        #  Create a button panel to control some aspects of the viewers.
        # -------------------------------------

        # Initiate the viewer controls, this will generate viewer_control_container
        # Then we can add it to the slice layout
        self.viewer_control_container = self.orth_view_controls.init_viewer_controls()

        # Add the container to the slice layout
        self.slice_layout.addWidget(self.viewer_control_container, 3, 0, 1, 2)  # Span two columns

        # Initialize other panels and get their container widgets
        self.table_container = self.initiate_tabs.init_table()           # Table widget
        self.initiate_tabs.thresholding_dropdown_clicked.connect(self.WBTing.update_threshold_option)


        self.work_station_container = self.cluster_ws.init_work_station()    # Work station container widget and slider groupset
        self.message_log_container = self.message_box.init_message_box()     # Message box init
        # self.init_cluster_edit_buttons()  # Cluster controls container

        # -----------------------------
        # Left Column: Slices Layout
        # -----------------------------
        # (Assuming your slice_layout already has the four tiles.)
        self.left_container = QWidget()
        self.left_container.setLayout(self.slice_layout)

        # -----------------------------
        # Right Column: Additional Elements (vertical stack)
        # -----------------------------
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(10)
        right_layout.setAlignment(Qt.AlignTop)
        right_layout.addWidget(self.table_container, alignment=Qt.AlignTop)
        right_layout.addWidget(self.work_station_container, alignment=Qt.AlignTop)
        right_layout.addWidget(self.message_log_container, alignment=Qt.AlignTop)

        self.right_container = QWidget()
        self.right_container.setLayout(right_layout)

        # -----------------------------
        # Outer Layout: Place Left and Right Columns Side by Side
        # -----------------------------
        outer_layout = QHBoxLayout()
        outer_layout.setContentsMargins(10, 10, 10, 10)
        outer_layout.setSpacing(10)

        # **First add sidebar (self.left_panel_container)**
        outer_layout.addWidget(self.left_side_bar.left_panel_container, alignment=Qt.AlignLeft)
        
        # **Then add the main panes (self.left_container)**
        outer_layout.addWidget(self.left_container, alignment=Qt.AlignTop)

        # **Finally, add right panel**
        outer_layout.addWidget(self.right_container, alignment=Qt.AlignTop)

        # Set the outer layout as the central widget's layout
        self.central_widget.setLayout(outer_layout)


        # Install the MouseInteractions event filter for each view.
        # This ensures that the eventFilter method in the MouseInteractions class will handle mouse events for these views.
        # The eventFilter method processes various mouse interactions like clicks, drags, zooms, and scrolls.
        # By passing self.mouse_interactions, we are connecting the MouseInteractions instance created earlier in BrainNav
        # to handle events from the corresponding views' scenes.
        self.axial_view.getView().scene().installEventFilter(self.mouse_interactions)
        self.sagittal_view.getView().scene().installEventFilter(self.mouse_interactions)
        self.coronal_view.getView().scene().installEventFilter(self.mouse_interactions)

        # Connect mouse click events to a function
        self.axial_view.getView().scene().sigMouseClicked.connect(lambda evt: self.mouse_interactions.on_mouse_click(evt, 'axial'))
        self.sagittal_view.getView().scene().sigMouseClicked.connect(lambda evt: self.mouse_interactions.on_mouse_click(evt, 'sagittal'))
        self.coronal_view.getView().scene().sigMouseClicked.connect(lambda evt: self.mouse_interactions.on_mouse_click(evt, 'coronal'))

        # Crosshairs
        self.crosshair_pen = pg.mkPen('r', width=2)
        self.axial_crosshair_h = pg.InfiniteLine(angle=0, pen=self.crosshair_pen)
        self.axial_crosshair_v = pg.InfiniteLine(angle=90, pen=self.crosshair_pen)
        self.sagittal_crosshair_h = pg.InfiniteLine(angle=0, pen=self.crosshair_pen)
        self.sagittal_crosshair_v = pg.InfiniteLine(angle=90, pen=self.crosshair_pen)
        self.coronal_crosshair_h = pg.InfiniteLine(angle=0, pen=self.crosshair_pen)
        self.coronal_crosshair_v = pg.InfiniteLine(angle=90, pen=self.crosshair_pen)

        self.axial_view.addItem(self.axial_crosshair_h)
        self.axial_view.addItem(self.axial_crosshair_v)
        self.sagittal_view.addItem(self.sagittal_crosshair_h)
        self.sagittal_view.addItem(self.sagittal_crosshair_v)
        self.coronal_view.addItem(self.coronal_crosshair_h)
        self.coronal_view.addItem(self.coronal_crosshair_v)



if __name__ == '__main__':
    app = QApplication(sys.argv)
    viewer = BrainNav()
    viewer.show()
    sys.exit(app.exec_())
