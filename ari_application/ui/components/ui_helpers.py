
import numpy as np

class UIHelpers:
    """
    A utility class that manages UI-related updates and spatial coordinate transformations
    for the BrainNav application.

    This class is primarily responsible for synchronizing crosshair slice positions with MNI
    coordinates, updating TDP threshold UI elements, and retrieving cluster IDs based on
    current UI space coordinates. It also includes functionality to remap coordinates when
    switching between different brain templates.

    Attributes
    ----------
    brain_nav : BrainNav
        Reference to the main application controller, giving access to shared state and components.

    Properties
    ----------
    fileInfo : dict
        Shortcut to `brain_nav.fileInfo`, containing per-file analysis data.

    Methods
    -------
    update_ui_xyz():
        Updates the MNI coordinate spinboxes in the UI based on the current crosshair location.

    update_tdp_ui(new_tdp):
        Sets the TDP slider and text box to a given value without triggering signal-based updates.

    get_selected_cluster_id():
        Retrieves the cluster ID at the current crosshair voxel location. Returns None if invalid.

    remap_ui_xyz(file_nr, xyz_prev, file_nr_template_prev, file_nr_template_new):
        Remaps crosshair positions between templates while preserving the anatomical location.
    """
      
    def __init__(self, brain_nav):
        super().__init__()
        self.brain_nav = brain_nav
    
    @property
    def fileInfo(self):
        return self.brain_nav.fileInfo

    def update_ui_xyz(self):
        """
        Updates the MNI coordinate spinboxes in the UI based on the current crosshair slice positions.

        This method retrieves the current voxel indices (sagittal, coronal, axial), 
        converts them to MNI space using the image's affine transformation, and updates 
        the MNI coordinate spinboxes accordingly. 

        Signals from the spinboxes are blocked during the update to avoid triggering 
        callbacks (e.g., user-driven updates to slices).

        Note:
        - The z-axis flip (from UI space to image space) is handled inside the 
          `xyz2MNI` method for consistency.
        """

        file_nr = self.brain_nav.file_nr
        file_nr_template = self.brain_nav.file_nr_template

        x, y, z = self.brain_nav.sagittal_slice, self.brain_nav.coronal_slice, self.brain_nav.axial_slice
        
        # We flip inside the method:
        xyzs = np.array([x, y, z])
        affine = self.brain_nav.aligned_templateInfo[(file_nr, file_nr_template)]['rtr_template_affine']
        # MNI_xyzs = self.metrics.xyz2MNI(xyzs, self.fileInfo[file_nr]['rtr_tamplate_affine'])
        MNI_xyzs = self.brain_nav.metrics.xyz2MNI(xyzs, affine)


        # Update spinboxes without triggering valueChanged
        for key, val in zip(['x', 'y', 'z'], MNI_xyzs):
            spinbox = self.brain_nav.orth_view_controls.mni_coord_boxes[key]
            spinbox.blockSignals(True)
            spinbox.setValue(val)
            spinbox.blockSignals(False)


    def update_tdp_ui(self, new_tdp):
        """ Update the TDP slider and text box while preventing recursive updates. """

        # Block signals to prevent triggering updates twice
        self.brain_nav.cluster_ws.cluster_slider.blockSignals(True)
        self.brain_nav.cluster_ws.tdp_textbox.blockSignals(True)

        # Update the UI elements
        self.brain_nav.cluster_ws.cluster_slider.setValue(int(new_tdp * 100))  # Convert to 0-100 scale
        self.brain_nav.cluster_ws.tdp_textbox.setText(f"{new_tdp:.2f}")  # Update the text box

        # Re-enable signals
        self.brain_nav.cluster_ws.cluster_slider.blockSignals(False)
        self.brain_nav.cluster_ws.tdp_textbox.blockSignals(False)


    def get_selected_cluster_id(self):
        """
        Returns the selected cluster ID based on crosshair position.
        
        :return: The selected cluster ID or None if no selection is made.
        """
        x_ui = self.brain_nav.sagittal_slice 
        y_ui = self.brain_nav.coronal_slice
        z_ui = self.brain_nav.axial_slice

        # x_raw, y_raw, z_raw  = self.brain_nav.fileInfo[file_nr]['mapped_coordinate_matrix_C'][x_ui, y_ui, z_ui]
        x_raw, y_raw, z_raw  = self.brain_nav.aligned_templateInfo[(self.brain_nav.file_nr, self.brain_nav.file_nr_template)]['mapped_coordinate_matrix_C'][x_ui, y_ui, z_ui]

        cluster_id = self.brain_nav.fileInfo[self.brain_nav.file_nr]['img_clus'][x_raw, y_raw, z_raw]

        if cluster_id is not None or cluster_id != 0:
            cluster_out = cluster_id
        else: 
            cluster_out = None

        return cluster_out
    
    def remap_ui_xyz(self, file_nr, xyz_prev, file_nr_template_prev, file_nr_template_new):
        
        # get the current coordinates of the crosshair in UI space
        x_ui = xyz_prev[0]
        y_ui = xyz_prev[1] 
        z_ui = xyz_prev[2]

        # map them to data space coordinates
        x_raw, y_raw, z_raw  = self.brain_nav.aligned_templateInfo[(file_nr, file_nr_template_prev)]['mapped_coordinate_matrix_C'][x_ui, y_ui, z_ui]

        # remap them to the new ui coordinates (linked to the newly set template)
        x_ui_new, y_ui_new, z_ui_new = self.brain_nav.aligned_statMapInfo[(file_nr, file_nr_template_new)]['inverse_mapped_matrix_C'][x_raw, y_raw, z_raw]

        # Update the slice indices
        self.brain_nav.sagittal_slice   = x_ui_new
        self.brain_nav.coronal_slice    = y_ui_new
        self.brain_nav.axial_slice      = z_ui_new


    def refresh_ui(self):
        """Refresh the UI after loading a project."""
        # Update table with reloaded data
        try: 
            self.brain_nav.tblARI.update_table(self.brain_nav.fileInfo[self.brain_nav.file_nr]['tblARI_df'])
        except:
            print("No table data to update")

        # Update 3D viewer
        self.brain_nav.threeDviewer.update_cluster_3d_view()

        # Update orthogonal slices
        # self.brain_nav.orth_view_setup.setup_viewer()

        self.brain_nav.orth_view_update.update_slices()

        # Show current metrics (coordinates, MNI, etc.)
        self.brain_nav.metrics.show_metrics()

        self.brain_nav.left_side_bar.update_ari_status()    # updates: ARI status in the list
    
