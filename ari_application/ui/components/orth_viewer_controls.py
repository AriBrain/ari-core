
import numpy as np

from PyQt5.QtWidgets import (
    QWidget, QGroupBox, QVBoxLayout, QHBoxLayout, QLabel, QSlider,
    QPushButton, QDoubleSpinBox, QWidget
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from ari_application.resources.styles import Styles 


class OrthViewerControls(QWidget):

    def __init__(self, brain_nav):
        super().__init__()
        self.brain_nav = brain_nav


    def init_viewer_controls(self):
        # Create the main viewer control container
        # self.viewer_control_container = QGroupBox("") #Viewer Controls
        self.viewer_control_container = QWidget()  
        self.viewer_control_layout = QHBoxLayout()  # Set horizontal layout
        self.viewer_control_container.setStyleSheet(Styles.controls_panel_styling)
        
        # self.viewer_control_container.setStyleSheet("""
        #     QGroupBox {
        #         border: 1px solid grey;
        #         border-radius: 5px;
        #         margin-top: 5px;
        #         padding: 2px;
        #         background-color: #1e2120;
        #     }
        #     QGroupBox::title {
        #         subcontrol-origin: margin;
        #         subcontrol-position: top center;
        #         padding: 5px;
        #         color: white;
        #         font-weight: normal;
        #     }
        # """)

        # Main layout for the control panel
        self.viewer_control_layout = QHBoxLayout()

        # -----------------------------------
        # Left Box: Orthogonal Controls
        # -----------------------------------
        self.orthogonal_control_box = QGroupBox("Orthogonal Controls")
        # self.orthogonal_control_box.setStyleSheet("font-weight: normal; color: white;")
        self.orthogonal_control_layout = QVBoxLayout()  # Change to horizontal layout

        self.overlay_transparency_label = QLabel("Overlay Transparency")
        self.overlay_transparency_label.setFont(QFont('Arial', 9))
        self.overlay_transparency_label.setAlignment(Qt.AlignLeft)

        self.alpha_slider = QSlider(Qt.Horizontal)
        self.alpha_slider.setRange(0, 100)
        self.alpha_slider.setValue(self.brain_nav.default_alpha)
        self.alpha_slider.valueChanged.connect(self.brain_nav.metrics.control_transparency)
        self.alpha_slider.setFixedSize(200, 25)
        self.alpha_slider.setStyleSheet(Styles.cluster_slider_styling)

        self.reset_button = QPushButton('Reset View')
        self.reset_button.setStyleSheet(Styles.reset_button_styling)
        self.reset_button.setCursor(Qt.PointingHandCursor)
        self.reset_button.clicked.connect(self.brain_nav.orth_view_setup.setup_viewer)
        self.reset_button.setFixedSize(100, 25)

        # Row layout for slider + reset button
        self.top_controls_layout = QHBoxLayout()
        self.top_controls_layout.addWidget(self.alpha_slider)
        self.top_controls_layout.addWidget(self.reset_button)

        # --- MNI Coordinate Display Boxes ---
        self.coord_x = QDoubleSpinBox()
        self.coord_y = QDoubleSpinBox()
        self.coord_z = QDoubleSpinBox()

        for box in [self.coord_x, self.coord_y, self.coord_z]:
            box.setDecimals(0)
            box.setRange(-200.0, 200.0)
            box.setFixedWidth(70)
            box.setStyleSheet("QDoubleSpinBox { background-color: #222; color: #0f0; }")

        self.coord_x.valueChanged.connect(lambda val: self.handle_user_coord_change())
        self.coord_y.valueChanged.connect(lambda val: self.handle_user_coord_change())
        self.coord_z.valueChanged.connect(lambda val: self.handle_user_coord_change())
        # self.coord_x.editingFinished.connect(self.handle_user_coord_change)
        # self.coord_y.editingFinished.connect(self.handle_user_coord_change)
        # self.coord_z.editingFinished.connect(self.handle_user_coord_change)

        # Labels
        x_label = QLabel("X:")
        y_label = QLabel("Y:")
        z_label = QLabel("Z:")

        for label in [x_label, y_label, z_label]:
            label.setStyleSheet("color: white; font-weight: bold;")

        # Layout to hold the coordinate spinboxes
        self.coord_layout = QHBoxLayout()
        self.coord_layout.setSpacing(6)
        self.coord_layout.addWidget(x_label)
        self.coord_layout.addWidget(self.coord_x)
        self.coord_layout.addWidget(y_label)
        self.coord_layout.addWidget(self.coord_y)
        self.coord_layout.addWidget(z_label)
        self.coord_layout.addWidget(self.coord_z)

        # Add elements to the orthogonal control layout
        # self.orthogonal_control_layout.addWidget(self.overlay_transparency_label)
        # self.orthogonal_control_layout.addWidget(self.alpha_slider)
        # self.orthogonal_control_layout.addWidget(self.reset_button)  # Move reset button to the right
        
        # Add top controls row to the main vertical layout
        self.orthogonal_control_layout.addLayout(self.top_controls_layout)
        self.orthogonal_control_layout.addLayout(self.coord_layout)

        # Set layout for the orthogonal control box
        self.orthogonal_control_box.setLayout(self.orthogonal_control_layout)

        # Initiate xyz ui boxes in orth controls.
        self.mni_coord_boxes = {
            'x': self.coord_x,
            'y': self.coord_y,
            'z': self.coord_z
        }

        # -----------------------------------
        # Right Box: 3D Controls
        # -----------------------------------
        self.three_d_control_box = QGroupBox("3D Controls")
        # self.three_d_control_box.setStyleSheet("font-weight: normal; color: white; subcontrol-position: top left;")
        self.three_d_control_layout = QVBoxLayout()

        # Create a horizontal layout for titles
        self.title_layout = QHBoxLayout()

        sagittal_label = QLabel("Sagittal")
        sagittal_label.setAlignment(Qt.AlignCenter)
        coronal_label = QLabel("Coronal")
        coronal_label.setAlignment(Qt.AlignCenter)
        axial_label = QLabel("Axial")
        axial_label.setAlignment(Qt.AlignCenter)

        self.title_layout.addWidget(sagittal_label)
        self.title_layout.addWidget(coronal_label)
        self.title_layout.addWidget(axial_label)

        # Create a horizontal layout for buttons
        self.button_layout = QHBoxLayout()

        # Sagittal buttons
        self.sagittal_left_button = QPushButton("Left")
        self.sagittal_right_button = QPushButton("Right")
        self.sagittal_left_button.clicked.connect(self.set_3d_brain_orientation)
        self.sagittal_right_button.clicked.connect(self.set_3d_brain_orientation)

        sagittal_layout = QHBoxLayout()
        sagittal_layout.addWidget(self.sagittal_left_button)
        sagittal_layout.addWidget(self.sagittal_right_button)

        # Coronal buttons
        self.coronal_ant_button = QPushButton("Ant.")
        self.coronal_post_button = QPushButton("Post.")
        self.coronal_ant_button.clicked.connect(self.set_3d_brain_orientation)
        self.coronal_post_button.clicked.connect(self.set_3d_brain_orientation)

        coronal_layout = QHBoxLayout()
        coronal_layout.addWidget(self.coronal_ant_button)
        coronal_layout.addWidget(self.coronal_post_button)

        # Axial buttons
        self.axial_supp_button = QPushButton("Supp.")
        self.axial_inf_button = QPushButton("Inf.")
        self.axial_supp_button.clicked.connect(self.set_3d_brain_orientation)
        self.axial_inf_button.clicked.connect(self.set_3d_brain_orientation)

        axial_layout = QHBoxLayout()
        axial_layout.addWidget(self.axial_supp_button)
        axial_layout.addWidget(self.axial_inf_button)

        # Add the button layouts directly below their respective titles
        self.button_layout.addLayout(sagittal_layout)
        self.button_layout.addLayout(coronal_layout)
        self.button_layout.addLayout(axial_layout)

        # Add title and buttons to 3D control layout
        self.three_d_control_layout.addLayout(self.title_layout)
        self.three_d_control_layout.addLayout(self.button_layout)

        # Set layout for 3D control box
        self.three_d_control_box.setLayout(self.three_d_control_layout)

        # -----------------------------------
        # Add Both Control Boxes to the Viewer Control Layout
        # -----------------------------------
        self.viewer_control_layout.addWidget(self.orthogonal_control_box, 1)  # Set equal space
        self.viewer_control_layout.addWidget(self.three_d_control_box, 1)

        # Apply the layout to the QWidget container
        self.viewer_control_container.setLayout(self.viewer_control_layout)

        return self.viewer_control_container

  
    def set_3d_brain_orientation(self):
        """
        Sets the 3D orientation of the brain visualization based on the selected view.

        This method reorients the full brain anatomical data and positions the 3D camera so that the
        visualization correctly reflects the desired anatomical perspective (e.g., sagittal left/right,
        coronal anterior/posterior, or axial superior/inferior).

        The process is as follows:
        1. Data Reorientation:
            - The raw brain data is first transposed via `self.data.T` and then further reordered
            using `np.transpose(brain_data, (2, 1, 0))`. These operations correct the native axis
            ordering of the data to match the expected (X, Y, Z) configuration. In effect, the first
            operation reverses the order of axes (e.g., from (X, Y, Z) to (Z, Y, X) if using a simple
            transpose on a 3D array), and the second operation re-permutes them to yield a final order
            that properly aligns with the anatomical directions.
        
        2. Camera Setup:
            - The center of the volume is computed from the dimensions of the reoriented data.
            - A default camera position is defined (typically starting from one side of the brain).
            - Depending on which view button is pressed (sagittal left/right, coronal anterior/posterior,
            or axial superior/inferior), the camera position is overridden, and specific rotation angles
            (pitch, yaw, roll) are applied. Additionally, the up vector is adjusted to correct for any
            vertical inversion in the view.
        
        3. Rotation Application:
            - The helper function `rotate_point` is used in sequence (for x, then y, then z rotations)
            to rotate the camera position about the volume center.
            - Finally, the computed camera position, center, and adjusted up vector are passed to the
            3D viewer’s camera configuration.

        Returns:
            None
        """
        # If 3d_brain_data is filled, it means that 'template_mask_dir' was provided
        # which for now means that the MNI template was chosen. data is in the brai_nav instance
        # and is used to create the faint brain surface. Created in the load_bg (nifti_loader class) method.
        if self.brain_nav.ui_params['3d_brain_data'] is not None:
            brain_data = self.brain_nav.ui_params['3d_brain_data']
        else:
            # brain_data = self.data.T  # this is raw data but not in alignment with the overlay
            brain_data = self.brain_nav.fileInfo[self.brain_nav.file_nr]['r_template_image'].get_fdata()  
        
        # brain_data = np.transpose(brain_data, (2, 1, 0))
        
        center = np.array([brain_data.shape[0] / 2, brain_data.shape[1] / 2, brain_data.shape[2] / 2])
        
        # Padding to keep the brain at a nice distance from the camera
        padding_x = 50  # adjust this as needed (in voxel units or mm depending on scale)
        padding_y = 0
        padding_z = 50

        # Axis-aligned distances from center to edge + padding
        x_dist = (brain_data.shape[0]) + padding_x
        y_dist = (brain_data.shape[1]) + padding_y
        z_dist = (brain_data.shape[2]) + padding_z

        # Default camera position (can be overridden below)
        camera_position = np.array([-x_dist, center[1], center[2]])

        sender = self.sender()


        if sender == self.sagittal_left_button:
            camera_position = np.array([-x_dist, center[1], center[2]])
            xdegree, ydegree, zdegree = 0, 0, 0
            up_vector = (0, 0, -1)

        elif sender == self.sagittal_right_button:
            camera_position = np.array([x_dist +(x_dist * 0.8), center[1], center[2]])
            xdegree, ydegree, zdegree = 0, 0, 0
            up_vector = (0, 0, -1)

        elif sender == self.coronal_ant_button:
            camera_position = np.array([center[0], -y_dist, center[2]])
            xdegree, ydegree, zdegree = 0, 0, 0
            up_vector = (0, 0, -1)

        elif sender == self.coronal_post_button:
            camera_position = np.array([center[0], y_dist + (y_dist * 1.1), center[2]])
            xdegree, ydegree, zdegree = 0, 0, 0
            up_vector = (0, 0, -1)

        elif sender == self.axial_supp_button:
            camera_position = np.array([-z_dist, center[1], center[2]])
            xdegree, ydegree, zdegree = 0, -90, 90
            up_vector = (0, 0, 1)

        elif sender == self.axial_inf_button:
            camera_position = np.array([-z_dist, center[1], center[2]])
            xdegree, ydegree, zdegree = 0, 90, 90
            up_vector = (0, 0, 1)


        # Apply a pitch, yaw, and roll
        camera_position = self.brain_nav.threeDviewer.rotate_point(camera_position, center, xdegree, 'x')  
        camera_position = self.brain_nav.threeDviewer.rotate_point(camera_position, center, ydegree, 'y')  
        camera_position = self.brain_nav.threeDviewer.rotate_point(camera_position, center, zdegree, 'z') 

         # Set camera
        self.brain_nav.threeDviewer.cluster_3d_view.camera_position = [camera_position, center, up_vector]  # Keep Z-up

        # self.cluster_3d_view.camera.up = (-1, 0, 2)
        # self.cluster_3d_view.camera.zoom(0.9)

        # update the view
        self.brain_nav.threeDviewer.cluster_3d_view.update()


    
    def handle_user_coord_change(self):
        """
        Triggered only when the user manually edits the MNI coordinate spinboxes.
        Updates the UI (crosshairs, slices) based on the new coordinate.
        """
        self.file_nr = self.brain_nav.file_nr
        self.file_nr_template = self.brain_nav.fileInfo[self.file_nr]['template_file_nr']


        # Ensure data and affine are initialized (not the case on initiation)
        if (not hasattr(self, "templates") or
            not (self.file_nr, self.file_nr_template) in self.brain_nav.aligned_templateInfo or
            'rtr_template_affine' not in self.brain_nav.aligned_templateInfo[(self.file_nr, self.file_nr_template)] or
            not hasattr(self, "ranges") or
            'data' not in self.templates[self.file_nr_template]):

            print("Data not initialized yet. Ignoring user input.")
            return
        
        data = self.brain_nav.templates[self.file_nr_template]['data']

        x = self.coord_x.value()
        y = self.coord_y.value()
        z = self.coord_z.value()

        # Convert MNI back to voxel space
        # affine = self.fileInfo[self.file_nr]['rtr_tamplate_affine']
        affine = self.brain_nav.aligned_templateInfo[(self.file_nr, self.file_nr_template)]['rtr_template_affine']
        inv_affine = np.linalg.inv(affine)
        voxel_xyz = inv_affine @ np.array([x, y, z, 1])
        voxel_xyz = np.floor(voxel_xyz[:3]).astype(int)

        sagittal, coronal, z_ui = voxel_xyz[0], voxel_xyz[1], data.shape[2] - 1 - voxel_xyz[2]

        self.brain_nav.sagittal_slice = np.clip(sagittal, 0, data.shape[0] - 1)
        self.brain_nav.coronal_slice = np.clip(coronal, 0, data.shape[1] - 1)
        self.brain_nav.axial_slice = np.clip(z_ui, 0, data.shape[2] - 1)

        self.brain_nav.orth_view_update.update_slices()
        self.brain_nav.orth_view_update.update_crosshairs()
    
