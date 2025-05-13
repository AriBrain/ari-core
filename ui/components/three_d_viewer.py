
  # --- Imports ---
import numpy as np
import pyvista as pv

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton
# from PyQt5.QtWidgets import QSizePolicy  # Uncomment if you use it

from pyvistaqt import QtInteractor

# If you have your custom Styles or BrainNav modules:
from resources.styles import Styles  # Replace with actual path

class ThreeDViewer(QWidget):
    """
    The ThreeDViewer class provides a dynamic 3D visualization interface for brain cluster data 
    using PyVista and Qt integration within the BrainNav application.

    Core Responsibilities:
    - Initializes a 3D QtInteractor viewer embedded within a styled QWidget container.
    - Renders anatomical brain templates and selected cluster overlays with transparency and custom coloring.
    - Offers interactive features such as camera reset, cluster view updates, and orientation control.
    - Supports toggling between docked and floating viewer modes for flexible UI integration.
    - Includes controls for pausing/resuming live updates to improve performance during static inspection.

    Key Features:
    - Faint full-brain rendering as spatial context for overlays
    - Cluster highlighting by label and color lookup
    - XYZ axis line rendering for orientation reference
    - Camera pose memory with smooth reinitialization
    - Floating undock mode and live update pause button

    This component is optimized for interactive anatomical exploration and integrates seamlessly 
    with the rest of the BrainNav pipeline, responding to UI signals and data updates in real-time.
    """

    def __init__(self, brain_nav):
        super().__init__()
        self.brain_nav = brain_nav

    def init_3d_cluster_viewer(self):
        # from vtkmodules.vtkInteractionStyle import vtkInteractorStyleTrackballActor

        self.cluster_3d_view = QtInteractor(self)
        # self.cluster_3d_view.interactor.SetInteractorStyle(vtkInteractorStyleTrackballActor())
        
        self.cluster_3d_view.setFixedSize(400, 400)
        self.cluster_3d_view.set_background('black')  # RGB for light grey
        self.cluster_3d_view.track_mouse_position()
        # self.cluster_3d_view.iren.interactor.AddObserver("MouseMoveEvent", self.custom_mouse_move)

        # Create a QWidget container for the 3D view
        self.cluster_3d_view_container = QWidget()
        self.cluster_3d_view_container.setLayout(QVBoxLayout())
        self.cluster_3d_view_container.layout().setContentsMargins(0, 0, 0, 0)
        self.cluster_3d_view_container.setFixedSize(400, 400)
        self.cluster_3d_view_container.layout().addWidget(self.cluster_3d_view)

        # Apply stylesheet to the container, NOT the 3D view
        self.cluster_3d_view_container.setStyleSheet(" ".join(Styles.orth_view_styling))
        self.cluster_3d_view_container.style().unpolish(self.cluster_3d_view_container)
        self.cluster_3d_view_container.style().polish(self.cluster_3d_view_container)
        self.cluster_3d_view_container.update()

         # Placeholder for when the 3D viewer is undocked
        self.empty_placeholder = QWidget()
        self.empty_placeholder.setStyleSheet("background-color: #1a1a1a;")  # Dark grey
        self.empty_placeholder.setMinimumSize(400, 400)

        # Add directly to the parent's layout
        self.brain_nav.cluster_viewer_container.addWidget(self.cluster_3d_view_container)
        
        # --- New 3D Viewer Docking Initialization ---
        self.is_3dviewer_floating_3d = False
        self.toggle_3dviewer_button = QPushButton("⧉")
        self.toggle_3dviewer_button.setFixedSize(30, 25)
        self.toggle_3dviewer_button.setStyleSheet("""
            QPushButton {
                background: none;
                border: none;
                color: white;
                font-size: 16px;
                font-weight: bold;
                padding: 4px;
            }
            QPushButton:hover {
                color: #00ff99;
            }
        """)
        self.toggle_3dviewer_button.setToolTip("Undock")
        self.toggle_3dviewer_button.setToolTipDuration(300)
        self.toggle_3dviewer_button.clicked.connect(self.toggle_3dviewer_dock)
        
        # --- New 3D Viewer Pause Button ---
        self.pause_3dviewer_button = QPushButton("⏸")
        self.pause_3dviewer_button.setFixedSize(30, 25)
        self.pause_3dviewer_button.setStyleSheet("""
            QPushButton {
                background: none;
                border: none;
                color: white;
                font-size: 16px;
                font-weight: bold;
                padding: 4px;
            }
            QPushButton:hover {
                color: #00ff99;
            }
        """)
        self.pause_3dviewer_button.setToolTip("Pause 3D updates")
        self.pause_3dviewer_button.setToolTipDuration(300)
        self.pause_3dviewer_button.clicked.connect(self.toggle_3dviewer_pause)
        
        # Add both buttons as children of the 3D view container
        self.toggle_3dviewer_button.setParent(self.cluster_3d_view_container)
        self.pause_3dviewer_button.setParent(self.cluster_3d_view_container)
        
        # Position buttons in the top-right corner with a margin of 5 pixels
        # Position undock button
        self.toggle_3dviewer_button.move(
            self.cluster_3d_view_container.width() - self.toggle_3dviewer_button.width() - 5,
            5
        )
        # Position pause button to the left of the undock button
        self.pause_3dviewer_button.move(
            self.cluster_3d_view_container.width() - self.toggle_3dviewer_button.width() - self.pause_3dviewer_button.width() - 10,
            5
        )
        
        self.toggle_3dviewer_button.raise_()
        self.pause_3dviewer_button.raise_()
        
        # Initialize 3D brain pause flag to False (3D rendering is active)
        if 'ui_params' in self.brain_nav.__dict__ and '3d_brain_pause' not in self.brain_nav.ui_params:
            self.brain_nav.ui_params['3d_brain_pause'] = False




    def update_cluster_3d_view(self, clusLabel=None):
        """Update the 3D cluster visualization in QtInteractor."""
        
        if self.brain_nav.ui_params['3d_brain_pause'] is True:
            return

        file_nr = self.brain_nav.file_nr
        file_nr_template = self.brain_nav.file_nr_template

        # Check if there's an existing camera state
        if self.cluster_3d_view.renderer.GetActors().GetNumberOfItems() > 0:
            camera = self.cluster_3d_view.camera
            position = camera.position
            focal_point = camera.focal_point
            view_angle = camera.view_angle
        else:
            position = None
        
        self.cluster_3d_view.clear()

        # If 3d_brain_data is filled, it means that 'template_mask_dir' was provided
        # which for now means that the MNI template was chosen. data is in the brai_nav instance
        # and is used to create the faint brain surface. Created in the load_bg (nifti_loader class) method.
        if self.brain_nav.templates[file_nr_template]['filename']== 'mni_icbm152_t1.nii':
            brain_data = self.brain_nav.ui_params['3d_brain_data']
        else:
            # brain_data = self.data.T  # this is raw data but not in alignment with the overlay
            # brain_data = self.fileInfo[self.file_nr]['r_template_image'].get_fdata()  
            brain_data = self.brain_nav.aligned_templateInfo[(file_nr, file_nr_template)]['r_template_image'].get_fdata()  
        
        # brain_data = np.transpose(brain_data, (2, 1, 0))

        # ----------------
        # Add Faint Full Brain Surface
        # ----------------
        brain_grid = pv.ImageData()
        brain_grid.dimensions = np.array(brain_data.shape) + 1
        brain_grid.origin = (0, 0, 0)
        brain_grid.spacing = (1, 1, 1)

        # Add anatomical data
        brain_grid.cell_data["intensity"] = brain_data.flatten(order="F")

        # Threshold to get outer brain surface (tweak 0.1 based on actual data)
        brain_surface = brain_grid.threshold(0.1)

        # Add semi-transparent brain surface for reference
        self.cluster_3d_view.add_mesh(brain_surface, color="white", opacity=0.05)

        # ----------------
        # Set up xyz axes
        # ----------------
        dims = brain_grid.dimensions
        center = (dims[0] / 2, dims[1] / 2, dims[2] / 2)
        lengths = (dims[0], dims[1], dims[2])
            
        if clusLabel:
            # overlay_data = self.statmaps[self.file_nr]['overlay_data'].T
            overlay_data = self.brain_nav.aligned_statMapInfo[(file_nr,file_nr_template)]['overlay_data'].T

    
            # transpose the data to match the PyVista format
            overlay_data = np.transpose(overlay_data, (2, 1, 0))

            # ----------------
            # Determine Cluster Color
            # ----------------
            lut = self.brain_nav.fileInfo[file_nr]['custom_lut']
            lut = lut[:, :3]
            
            # Define the background row
            background = np.array([0, 0, 0], dtype=lut.dtype)

            # Insert the background row at the first position (index 0)
            lut = np.insert(lut, 0, background, axis=0)
            
            # Map cluster ID to its RGBA color
            clusColor = np.take(lut, clusLabel, axis=0)
            
            # ----------------
            # Add Cluster Voxels
            # ----------------
            grid = pv.ImageData()
            grid.dimensions = np.array(overlay_data.shape) + 1
            grid.origin = (0, 0, 0)
            grid.spacing = (1, 1, 1)

            voxel_data = np.zeros(overlay_data.shape, dtype=np.uint8)
            voxel_data[overlay_data == clusLabel] = 1
            grid.cell_data["cluster"] = voxel_data.flatten(order="F")

            # Add cluster voxels in cluster color
            self.cluster_3d_view.add_mesh(grid.threshold(0.5), color=clusColor, opacity=0.7)


        # Add XYZ axes lines
        self.add_axes_lines(self.cluster_3d_view, center, lengths)

        # ----------------
        # Finalize View
        # ----------------
        # self.cluster_3d_view.reset_camera()
        # self.cluster_3d_view.camera.up = (0, 0, 0)  # Z-axis points up (superior)
        # Slight zoom-in (adjust the factor as needed, e.g., 1.2 means zoom in by 20%)
        # self.cluster_3d_view.camera.zoom(1.2)

        # Restore camera if available, otherwise reset
        if position is not None:
            self.cluster_3d_view.camera.position = position
            self.cluster_3d_view.camera.focal_point = focal_point
            self.cluster_3d_view.camera.view_angle = view_angle
        else:
            self.cluster_3d_view.reset_camera()

            center = np.array([brain_data.shape[0] / 2, brain_data.shape[1] / 2, brain_data.shape[2] / 2])
            camera_position = np.array([-200, center[1], center[2]])  

            # Apply a pitch, yaw, and roll
            camera_position = self.rotate_point(camera_position, center, 0, 'x')  
            camera_position = self.rotate_point(camera_position, center, -90, 'y')  
            camera_position = self.rotate_point(camera_position, center, 90, 'z')  

            # Set camera
            self.cluster_3d_view.camera_position = [camera_position, center, (0, 0, 1)]  # Keep Z-up

            # self.cluster_3d_view.camera.up = (-1, 0, 2)
            self.cluster_3d_view.camera.zoom(0.9)

        self.cluster_3d_view.update()

    def toggle_3dviewer_pause(self):
        """
        Toggles the 3D viewer between paused and active states.
        When paused, the 3D viewer won't update, improving performance during exploration.
        """
        # Toggle the pause state
        self.brain_nav.ui_params['3d_brain_pause'] = not self.brain_nav.ui_params['3d_brain_pause']
        
        # Update button appearance based on state
        if self.brain_nav.ui_params['3d_brain_pause']:
            self.pause_3dviewer_button.setText("▶")  # Play symbol
            self.pause_3dviewer_button.setToolTip("Resume 3D updates")
            self.brain_nav.message_box.log_message("3D viewer updates paused")
        else:
            self.pause_3dviewer_button.setText("⏸")  # Pause symbol
            self.pause_3dviewer_button.setToolTip("Pause 3D updates")
            self.brain_nav.message_box.log_message("3D viewer updates resumed")
            # Update the 3D view immediately when resuming
            self.update_cluster_3d_view()

    
    #
    def toggle_3dviewer_dock(self):
        """
        Toggles the 3D viewer between docked (embedded in the metrics container) and 
        floating (a top-level window) states.
        """
        print("toggle_3dviewer_dock called. is_3dviewer_floating_3d:", self.is_3dviewer_floating_3d)
        
        if not self.is_3dviewer_floating_3d:
            # Undock: Remove the 3D viewer container from its parent layout and make it a top-level window.
            try:
                self.brain_nav.cluster_viewer_container.removeWidget(self.cluster_3d_view_container)
                print("Removed cluster_3d_view_container from metrics_container_layout.")
            except Exception as e:
                print("Error removing widget:", e)

            # Put a dark placeholder in that spot so the tile doesn't collapse
            self.brain_nav.cluster_viewer_container.addWidget(self.empty_placeholder)
            
            self.cluster_3d_view_container.setParent(None)  # Detach from parent
            self.cluster_3d_view_container.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)
            
            # Remove fixed size to allow resizing: set a minimum size and an expanding size policy.
            # self.cluster_3d_view_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            self.cluster_3d_view_container.setFixedSize(800, 800)

            self.cluster_3d_view.setFixedSize(800, 800)
            # self.cluster_3d_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            
            self.cluster_3d_view_container.show()
            self.cluster_3d_view_container.raise_()
            
            self.toggle_3dviewer_button.setText("⧉")  # Update button text or icon
            self.is_3dviewer_floating_3d = True

            # reset the buttons to the right corner of the undocked view
            self.toggle_3dviewer_button.move(
                self.cluster_3d_view_container.width() - self.toggle_3dviewer_button.width() - 5, 5)
            self.pause_3dviewer_button.move(
                self.cluster_3d_view_container.width() - self.toggle_3dviewer_button.width() - self.pause_3dviewer_button.width() - 10, 5)
            
            self.toggle_3dviewer_button.raise_()
            self.pause_3dviewer_button.raise_()
            
            print("Undocked: 3D viewer state updated to floating.")
        
        else:
            print("Redocking: Hiding floating 3D viewer container.")

            # Redock: Remove placeholder from layout
            self.brain_nav.cluster_viewer_container.removeWidget(self.empty_placeholder)
            self.empty_placeholder.setParent(None)

            # Redock: Reattach the 3D viewer container back to the metrics container.
            self.cluster_3d_view_container.hide()
            
            self.cluster_3d_view_container.setParent(self.brain_nav.cluster_viewer_container.parentWidget())
            self.cluster_3d_view_container.setWindowFlags(Qt.Widget)  # Restore normal widget behavior
            
            # Optionally restore fixed size for the docked state:
            self.cluster_3d_view_container.setFixedSize(400, 400)
            self.cluster_3d_view.setFixedSize(400, 400)
            
            self.cluster_3d_view_container.show()
            
            # Re-add the 3D viewer container back to the metrics container layout.
            self.brain_nav.cluster_viewer_container.addWidget(self.cluster_3d_view_container)
            
            self.toggle_3dviewer_button.setText("⧉")  # Update button text or icon
            self.is_3dviewer_floating_3d = False

            # reset the buttons to the right corner of the redocked view
            self.toggle_3dviewer_button.move(
                self.cluster_3d_view_container.width() - self.toggle_3dviewer_button.width() - 5, 5)
            self.pause_3dviewer_button.move(
                self.cluster_3d_view_container.width() - self.toggle_3dviewer_button.width() - self.pause_3dviewer_button.width() - 10, 5)
            
            self.toggle_3dviewer_button.raise_()
            self.pause_3dviewer_button.raise_()

            print("Redocked: 3D viewer state updated to docked.")

    @staticmethod
    def add_axes_lines(viewer, center, lengths):
        "Helper function to add XYZ axes lines to the 3d viewer."

        x_length, y_length, z_length = lengths

        x_line = pv.Line((0, center[1], center[2]), (x_length, center[1], center[2]))
        viewer.add_mesh(x_line, color='red', line_width=2)

        y_line = pv.Line((center[0], 0, center[2]), (center[0], y_length, center[2]))
        viewer.add_mesh(y_line, color='green', line_width=2)

        z_line = pv.Line((center[0], center[1], 0), (center[0], center[1], z_length))
        viewer.add_mesh(z_line, color='blue', line_width=2)

    @staticmethod
    def rotate_point(point, center, angle_degrees, axis='x'):
        """ Rotate point around a center by angle along given axis 
        Helper function for 3d visualization."""

        angle = np.radians(angle_degrees)
        rotation_matrix = np.eye(3)

        if axis == 'x':
            rotation_matrix = np.array([
                [1, 0, 0],
                [0, np.cos(angle), -np.sin(angle)],
                [0, np.sin(angle), np.cos(angle)]
            ])
        elif axis == 'y':
            rotation_matrix = np.array([
                [np.cos(angle), 0, np.sin(angle)],
                [0, 1, 0],
                [-np.sin(angle), 0, np.cos(angle)]
            ])
        elif axis == 'z':
            rotation_matrix = np.array([
                [np.cos(angle), -np.sin(angle), 0],
                [np.sin(angle), np.cos(angle), 0],
                [0, 0, 1]
            ])

        offset = point - center
        rotated_offset = rotation_matrix @ offset
        return center + rotated_offset
    
  
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
        camera_position = self.rotate_point(camera_position, center, xdegree, 'x')  
        camera_position = self.rotate_point(camera_position, center, ydegree, 'y')  
        camera_position = self.rotate_point(camera_position, center, zdegree, 'z') 

         # Set camera
        self.cluster_3d_view.camera_position = [camera_position, center, up_vector]  # Keep Z-up

        # self.cluster_3d_view.camera.up = (-1, 0, 2)
        # self.cluster_3d_view.camera.zoom(0.9)

        # update the view
        self.cluster_3d_view.update()