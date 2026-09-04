import numpy as np
import pyqtgraph as pg
from matplotlib.colors import ListedColormap
from pyqtgraph import TextItem

class OrthViewUpdate:
    def __init__(self, BrainNaV):
        """

        The OrthViewUpdate class handles the updating of orthogonal views (axial, sagittal, coronal)
        for the BrainNav application. It includes methods to get and set the display ranges of these views,
        update the displayed image slices, and manage the crosshair positions within each view. This class
        ensures that the views are synchronized and correctly display the current state of the brain
        image data.
        """

        # Initialize the OrthViewUpdate with a reference to the BrainNav instance.
        # :param brain_nav: Instance of the BrainNav class.
        self.brain_nav = BrainNaV

        self.axial_overlay_item = None
        self.sagittal_overlay_item = None
        self.coronal_overlay_item = None
        # Extra ImageItems for the selected-ROI border (heatmap/categorical
        # selection highlight replaces the old dim-others approach).
        self.axial_contour_item = None
        self.sagittal_contour_item = None
        self.coronal_contour_item = None

    def get_ranges(self):
        """
        Get the current display range for each orthogonal view (axial, sagittal, coronal).
        This method retrieves the view range for each view and updates the ranges array accordingly.
        """
        # Loop through each view (axial, sagittal, coronal) using an enumeration to get both index and view.
        for i, view in enumerate([self.brain_nav.axial_view, self.brain_nav.sagittal_view, self.brain_nav.coronal_view]):
            # Get the current view range for the current view.
            view_range = view.getView().viewRange()

            # Update the ranges array for the current view.
            # view_range[0] contains the horizontal range (x_min and x_max).
            # view_range[1] contains the vertical range (y_min and y_max).
            self.brain_nav.ranges[i, :2] = view_range[0]  # Set x_min and x_max.
            self.brain_nav.ranges[i, 2:] = view_range[1]  # Set y_min and y_max.

    def set_ranges(self):
        """
        Set the display range for each orthogonal view (axial, sagittal, coronal).
        This method updates the view range for each view to ensure the image is displayed correctly.
        """
        file_nr_template = self.brain_nav.file_nr_template
        template_data_shape = self.brain_nav.templates[file_nr_template]['data'].shape

        # Loop through each view (axial, sagittal, coronal) using an enumeration to get both index and view.
        for i, view in enumerate([self.brain_nav.axial_view, self.brain_nav.sagittal_view, self.brain_nav.coronal_view]):
            # # Set the view range for the current view.
            # # xRange is set using the first two values in the ranges array for the current view.
            # # yRange is set using the last two values in the ranges array for the current view.
            # view.getView().setRange(
            #     xRange=(self.brain_nav.ranges[i, 0], self.brain_nav.ranges[i, 1]),  # Set the horizontal range.
            #     yRange=(self.brain_nav.ranges[i, 2], self.brain_nav.ranges[i, 3]),  # Set the vertical range.
            #     padding=0  # No additional padding around the displayed image.
            # )
            
            # Extract xRange and yRange
            x_min, x_max = self.brain_nav.ranges[i, 0], self.brain_nav.ranges[i, 1]
            y_min, y_max = self.brain_nav.ranges[i, 2], self.brain_nav.ranges[i, 3]

            # Handle NaNs: Replace with min/max valid values
            if np.isnan(x_min) or np.isnan(x_max):
                x_min, x_max = 0, template_data_shape[0]  # Default full width
            if np.isnan(y_min) or np.isnan(y_max):
                y_min, y_max = 0, template_data_shape[1]  # Default full height

            # Set the view range while ensuring valid values
            view.getView().setRange(
                xRange=(x_min, x_max),
                yRange=(y_min, y_max),
                padding=0
            )

    def update_slices(self, selected_cluster_id=None):
        """
        Update the displayed slices for each orthogonal view (axial, sagittal, coronal).
        This method updates the image data shown in each view and sets the appropriate view ranges.
        This function operates on data which is the first (background image) loaded. It does not apply 
        to the analysed data. 
        """
        # # Retrieve the current image data and its mask
        # data    = self.brain_nav.data
        # tmp_mask= (data != 0)

        #  # Create a masked version of the data where voxels outside the mask become NaN.
        # # (If your display logic prefers another “blank” value, you can change np.nan accordingly.)
        # masked_data = np.where(tmp_mask, data, np.nan)

        # Retrieve the current image data and its mask
        # data = self.brain_nav.fileInfo[self.brain_nav.file_nr]['r_template_image'].get_fdata()    
        file_nr = self.brain_nav.file_nr
        file_nr_template = self.brain_nav.file_nr_template
        data = self.brain_nav.aligned_templateInfo[(file_nr, file_nr_template)]['r_template_image'].get_fdata()   

        tmp_mask = (data != 0) & np.isfinite(data)  # Ensure valid (non-zero, finite) voxels

        # Replace invalid values (NaNs, -inf) with zero (or another placeholder)
        data = np.nan_to_num(data, nan=0.0, neginf=0)

        # Create a masked version of the data where invalid voxels become NaNdsd
        masked_data = np.where(tmp_mask, data, np.nan)
        
        # Check if the data is in C-order or F-order - should always be C-order as it is forced in rotate method
        # Update the views using the masked data.
        if data.flags['C_CONTIGUOUS']:
            # # For C-contiguous data:
            # self.brain_nav.axial_view.setImage(masked_data[:, :, self.brain_nav.axial_slice])
            # self.brain_nav.sagittal_view.setImage(masked_data[self.brain_nav.sagittal_slice, :, :])
            # self.brain_nav.coronal_view.setImage(masked_data[:, self.brain_nav.coronal_slice, :])

            # Ensure slice indices are within bounds
            axial_slice = min(self.brain_nav.axial_slice, masked_data.shape[2] - 1)
            sagittal_slice = min(self.brain_nav.sagittal_slice, masked_data.shape[0] - 1)
            coronal_slice = min(self.brain_nav.coronal_slice, masked_data.shape[1] - 1)

            # For C-contiguous data:
            self.brain_nav.axial_view.setImage(masked_data[:, :, axial_slice])
            self.brain_nav.sagittal_view.setImage(masked_data[sagittal_slice, :, :])
            self.brain_nav.coronal_view.setImage(masked_data[:, coronal_slice, :])

        elif data.flags['F_CONTIGUOUS']:
            # For F-contiguous data:
            self.brain_nav.axial_view.setImage(masked_data[self.brain_nav.axial_slice, :, :])
            self.brain_nav.sagittal_view.setImage(masked_data[:, :, self.brain_nav.sagittal_slice])
            self.brain_nav.coronal_view.setImage(masked_data[:, self.brain_nav.coronal_slice, :])

        # Set the ranges for the views
        # This ensures that the view ranges are updated to reflect any changes in the displayed slices.
        self.set_ranges()

        # Overlay images if overlay data is present
        # Use dict.get to safely access the nested structure
        # statmap_entry = self.brain_nav.statmaps.get(self.brain_nav.file_nr, {})
        statmap_entry = self.brain_nav.aligned_statMapInfo.get((self.brain_nav.file_nr, self.brain_nav.file_nr_template), {})

        # Three overlay modes — cluster (the original ARI overlay), atlas
        # (verification view for the user-uploaded atlas), and roi (post-
        # analysis selection view, lands in step 5). See
        # docs/ATLAS_TDP_PLAN.md §4.3.
        overlay_mode = self.brain_nav.ui_params.get('overlay_mode', 'cluster')

        if overlay_mode in ('atlas', 'roi') and self._has_user_atlas_for_active_view():
            self.add_atlas_overlay(
                highlight_label=self.brain_nav.ui_params.get('selected_roi_label')
                if overlay_mode == 'roi' else None
            )
        elif 'overlay_data' in statmap_entry:
            # Clear any leftover atlas contour items before drawing the
            # cluster overlay — add_overlay_with_transparency doesn't know
            # about them.
            self._clear_atlas_contours()
            self.add_overlay_with_transparency(selected_cluster_id)
            # self.update_crosshairs()
        else:
            # Full cleanup — atlas overlay + contour + cluster overlay items.
            self._clear_atlas_contours()
            # Remove existing overlay items if they exist
            if self.axial_overlay_item:
                self.brain_nav.axial_view.removeItem(self.axial_overlay_item)
            if self.sagittal_overlay_item:
                self.brain_nav.sagittal_view.removeItem(self.sagittal_overlay_item)
            if self.coronal_overlay_item:
                self.brain_nav.coronal_view.removeItem(self.coronal_overlay_item)
        
        # Add orientation labels
        self.add_orientation_labels()

    
    def update_crosshairs(self):
        file_nr_template = self.brain_nav.file_nr_template

        template_data_shape = self.brain_nav.templates[file_nr_template]['data'].shape

        # Clamp slices to valid range
        self.brain_nav.axial_slice = min(self.brain_nav.axial_slice, template_data_shape[2] - 1)
        self.brain_nav.sagittal_slice = min(self.brain_nav.sagittal_slice, template_data_shape[0] - 1)
        self.brain_nav.coronal_slice = min(self.brain_nav.coronal_slice, template_data_shape[1] - 1)
        
        # print("Updating crosshairs")

        # Update the crosshair positions in the coronal view
        # The coronal view shows slices along the y-axis (anterior-posterior) and z-axis (superior-inferior)
        # Setting the horizontal (h) crosshair to the axial_slice (z-axis) ensures that the horizontal line moves up and down correctly
        # Setting the vertical (v) crosshair to the sagittal_slice (x-axis) ensures that the vertical line moves left and right correctly
        self.brain_nav.coronal_crosshair_h.setPos(self.brain_nav.axial_slice + 0.5)
        self.brain_nav.coronal_crosshair_v.setPos(self.brain_nav.sagittal_slice + 0.5)

        # Update the crosshair positions in the sagittal view
        # The sagittal view shows slices along the x-axis (left-right) and z-axis (superior-inferior)
        # Setting the horizontal (h) crosshair to the axial_slice (z-axis) ensures that the horizontal line moves up and down correctly
        # Setting the vertical (v) crosshair to the coronal_slice (y-axis) ensures that the vertical line moves left and right correctly
        self.brain_nav.sagittal_crosshair_h.setPos(self.brain_nav.axial_slice + 0.5)
        self.brain_nav.sagittal_crosshair_v.setPos(self.brain_nav.coronal_slice + 0.5)

        # Update the crosshair positions in the axial view
        # The axial view shows slices along the x-axis (left-right) and y-axis (anterior-posterior)
        # Setting the horizontal (h) crosshair to the coronal_slice (y-axis) ensures that the horizontal line moves up and down correctly
        # Setting the vertical (v) crosshair to the sagittal_slice (x-axis) ensures that the vertical line moves left and right correctly
        self.brain_nav.axial_crosshair_h.setPos(self.brain_nav.coronal_slice + 0.5)
        self.brain_nav.axial_crosshair_v.setPos(self.brain_nav.sagittal_slice + 0.5)


    def move_crosshair_and_slices(self, pos, source):
        """
        Move crosshair and update slices based on the current mouse position.

        This method is responsible for updating the position of the crosshair and 
        the corresponding slices in the BrainNav application when the mouse is moved.
        It maps the current mouse position to the appropriate coordinates in the view 
        and updates the sagittal and coronal slices accordingly. These are in turn 
        used by the update slices and cross hair methods called at the end.

        Parameters:
        pos (QPointF): The current position of the mouse in the scene coordinates.
        source (QGraphicsScene): The source of the event, which determines which view 
                                (axial, sagittal, or coronal) the mouse event originated from.

        Operations:
        - Check if the source of the event is the axial, saggital or coronal view's scene.
        - Map the mouse position from the scene coordinates to the orthview  coordinates.
        - Convert the mapped position to integer values representing the x and y coordinates.
        - Update the sagittal_slice with the x coordinate.
        - Update the coronal_slice with the y coordinate.

        Called by handle_drag(self, pos, source) from mouse_interaction class

        Example Usage:
        When the mouse is moved within the axial view, this method will be called 
        to update the crosshair position and the corresponding sagittal and coronal slices.
        If the mouse position in the axial view is at (120, 150), the sagittal_slice 
        will be updated to 120 and the coronal_slice will be updated to 150.
        """
        if source is self.brain_nav.axial_view.getView().scene():
            # Map the mouse position to the axial view coordinates
            mapped_pos = self.brain_nav.axial_view.getView().mapSceneToView(pos)
            x, y = int(mapped_pos.x()), int(mapped_pos.y())
            self.brain_nav.sagittal_slice = x
            self.brain_nav.coronal_slice = y
        elif source is self.brain_nav.sagittal_view.getView().scene():
            # Map the mouse position to the sagittal view coordinates
            mapped_pos = self.brain_nav.sagittal_view.getView().mapSceneToView(pos)
            x, y = int(mapped_pos.x()), int(mapped_pos.y())
            self.brain_nav.axial_slice = y
            self.brain_nav.coronal_slice = x
        elif source is self.brain_nav.coronal_view.getView().scene():
            # Map the mouse position to the coronal view coordinates
            mapped_pos = self.brain_nav.coronal_view.getView().mapSceneToView(pos)
            x, y = int(mapped_pos.x()), int(mapped_pos.y())
            self.brain_nav.axial_slice = y
            self.brain_nav.sagittal_slice = x

        # Update the crosshairs and slices based on the new positions
        # self.brain_nav.metrics.show_metrics(self.brain_nav)
        self.brain_nav.metrics.show_metrics()
        
        # here we set it always to TRUE. This is now ok because we are loading the gradmap upon landing on the main_window. 
        # it works and does not interfere with other types of displaying the data. We can use it as a flag to display the gradmap.
        self.update_slices() 
        self.update_crosshairs()
        self.brain_nav.UIHelp.update_ui_xyz()


    def add_overlay_with_transparency(self, selected_cluster_id=None):
        """
        Add the overlay data to the views with transparency.
        This method uses the stable cluster LUT for consistent visualization.
        """

        if selected_cluster_id is not None:
            selected_cluster_id -= 1

        file_nr = self.brain_nav.file_nr

        # Retrieve the selected cluster ID and gradmap flag
        # gradmap = self.brain_nav.ui_params['gradmap']
        gradmap = self.brain_nav.aligned_statMapInfo[(file_nr, self.brain_nav.file_nr_template)]['gradmap_flag']
        # gradmap = self.brain_nav.fileInfo[file_nr]['gradmap_flag']

        # Remove existing overlay items
        if self.axial_overlay_item:
            self.brain_nav.axial_view.removeItem(self.axial_overlay_item)
        if self.sagittal_overlay_item:
            self.brain_nav.sagittal_view.removeItem(self.sagittal_overlay_item)
        if self.coronal_overlay_item:
            self.brain_nav.coronal_view.removeItem(self.coronal_overlay_item)

        # overlay = self.brain_nav.statmaps[file_nr]['overlay_data']  # Precomputed overlay data
        overlay = self.brain_nav.aligned_statMapInfo[(self.brain_nav.file_nr, self.brain_nav.file_nr_template)]['overlay_data']  

        
        # Create a masked version of the data where voxels outside the mask become NaN.
        # (If your display logic prefers another “blank” value, you can change np.nan accordingly.)
        # Retrieve the current image data and its mask
        tmp_mask= (overlay != 0)
        overlay = np.where(tmp_mask, overlay, np.nan)
        
        alpha = self.brain_nav.alpha  # Retrieve transparency level

        if 'img_clus' in self.brain_nav.fileInfo[self.brain_nav.file_nr] and self.brain_nav.fileInfo[self.brain_nav.file_nr]['img_clus'] is not None:
            
            # Replace all zeros with NaNs (optional, based on your overlay data)
            # overlay = np.where(overlay == 0, np.nan, overlay)

            # Generate LUT based on stable LM_ids_count
            custom_lut_large = self.brain_nav.fileInfo[file_nr]['custom_lut']

            # Index custom_lut using the integer cluster IDs
            # custom_lut = custom_lut_large[all_cluster_ids_int, :]
            custom_lut = custom_lut_large 

            # Adjust the transparency of non-selected clusters
            if selected_cluster_id is not None and overlay is not None:
                # selected_cluster_id += 1
                
                # Iterate through the LUT and apply transparency
                for i in range(custom_lut.shape[0]):
                    #  range(1, len(lut))
                    if i == selected_cluster_id:
                        # custom_lut[i, 3] = int(alpha * 255)  # Full opacity for the selected cluster
                        custom_lut[i, 3] = 255  # Full opacity for the selected cluster

                    else:
                        # custom_lut[i, 3] = int(0.6 * alpha * 255)  # Reduced opacity for non-selected clusters
                        custom_lut[i, 3] = int(0.4 * 255)  # Reduced opacity for non-selected clusters
            else:
                # Apply the same alpha to all clusters if no cluster is selected
                custom_lut[:, 3] = int(alpha * 255)
                #  custom_lut[:, 3] = np.where(np.arange(lut.shape[0]), int(alpha * 255), 0)

            # update the alpha column with currently selected alpha value
            # custom_lut[:, 3] = int(alpha * 255)

            # Define the background row
            # background = np.array([0, 0, 0, 0], dtype=custom_lut.dtype)

            # # Insert the background row at the first position (index 0)
            # custom_lut = np.insert(custom_lut, 0, background, axis=0)

        else:           
            # overlay = np.where(overlay == 0, np.nan, overlay)
            custom_lut = OrthViewUpdate.create_custom_lut(self, colormap='rainbow', alpha=alpha)
            
        # Define the background row
        background = np.array([0, 0, 0, 0], dtype=custom_lut.dtype)
        # Insert the background row at the first position (index 0)
        custom_lut = np.insert(custom_lut, 0, background, axis=0)

        template_data = self.brain_nav.templates[self.brain_nav.file_nr_template]['data'] 

        if template_data.flags['C_CONTIGUOUS']:
            

            if selected_cluster_id is not None or gradmap == False:
                axial_data      = np.take(custom_lut, np.nan_to_num(overlay[:, :, self.brain_nav.axial_slice], nan=0).astype(int), axis=0)
                sagittal_data   = np.take(custom_lut, np.nan_to_num(overlay[self.brain_nav.sagittal_slice, :, :], nan=0).astype(int), axis=0)
                coronal_data    = np.take(custom_lut, np.nan_to_num(overlay[:, self.brain_nav.coronal_slice, :], nan=0).astype(int), axis=0)

                # Create ImageItems with pre-mapped color data (with RGBA values)
                self.axial_overlay_item = pg.ImageItem(axial_data)
                self.sagittal_overlay_item = pg.ImageItem(sagittal_data)
                self.coronal_overlay_item = pg.ImageItem(coronal_data)
            elif gradmap == True: 
                 # Use LUT for each slice if no selected cluster is specified
                # Axial slice
                self.axial_overlay_item = pg.ImageItem(overlay[:, :, self.brain_nav.axial_slice], lut=custom_lut)
                # Sagittal slice
                self.sagittal_overlay_item = pg.ImageItem(overlay[self.brain_nav.sagittal_slice, :, :], lut=custom_lut)
                # Coronal slice
                self.coronal_overlay_item = pg.ImageItem(overlay[:, self.brain_nav.coronal_slice, :], lut=custom_lut)


        elif template_data.flags['F_CONTIGUOUS']:

            if selected_cluster_id is not None:
                # For F-order, adjust the slices for each view
                axial_data = np.take(custom_lut, np.nan_to_num(overlay[self.brain_nav.axial_slice, :, :], nan=0).astype(int), axis=0)
                sagittal_data = np.take(custom_lut, np.nan_to_num(overlay[:, :, self.brain_nav.sagittal_slice], nan=0).astype(int), axis=0)
                coronal_data = np.take(custom_lut, np.nan_to_num(overlay[:, self.brain_nav.coronal_slice, :], nan=0).astype(int), axis=0)

                # Create ImageItems with pre-mapped color data (with RGBA values)
                self.axial_overlay_item = pg.ImageItem(axial_data)
                self.sagittal_overlay_item = pg.ImageItem(sagittal_data)
                self.coronal_overlay_item = pg.ImageItem(coronal_data)

            else:
                # Use LUT for each slice if no selected cluster is specified
                self.axial_overlay_item = pg.ImageItem(overlay[self.brain_nav.axial_slice, :, :], lut=custom_lut)
                self.sagittal_overlay_item = pg.ImageItem(overlay[:, :, self.brain_nav.sagittal_slice], lut=custom_lut)
                self.coronal_overlay_item = pg.ImageItem(overlay[:, self.brain_nav.coronal_slice, :], lut=custom_lut)

        # Add the overlay items to the views
        self.brain_nav.axial_view.addItem(self.axial_overlay_item)
        self.brain_nav.sagittal_view.addItem(self.sagittal_overlay_item)
        self.brain_nav.coronal_view.addItem(self.coronal_overlay_item)
            
    def _active_atlas_key(self):
        """
        Returns the userAtlasInfo key for the currently selected template,
        matching the keying convention used by atlasInfo (int file_nr_template
        for normal templates, ('data_as_template', file_nr) for the
        statmap-as-template case). Returns None when the data-as-template
        index has been set but the user is viewing it.
        """
        file_nr = self.brain_nav.file_nr
        file_nr_template = self.brain_nav.file_nr_template
        data_bg_index = getattr(self.brain_nav, 'data_bg_index', None)
        if data_bg_index is not None and file_nr_template == data_bg_index:
            return ('data_as_template', file_nr)
        return file_nr_template

    def _has_user_atlas_for_active_view(self):
        key = self._active_atlas_key()
        return key in self.brain_nav.userAtlasInfo

    def add_atlas_overlay(self, highlight_label=None):
        """
        Render the user-uploaded atlas as a coloured overlay over the current
        template. LUT choice depends on ui_params['atlas_colour_mode']:
        'categorical' uses the fixed HSV palette, 'heatmap' uses the viridis
        LUT built from per-ROI TDPs by Metrics._build_atlas_tdp_lut.

        When highlight_label is set (the 'roi' overlay mode), a bright cyan
        1-voxel contour is drawn on top of the selected ROI in each slice —
        replacing the old dim-others approach so heatmap comparisons across
        ROIs remain readable while the selection stays identifiable.
        """
        # Drop any previous overlay + contour items so we don't stack.
        self._remove_atlas_overlay_items()

        atlas_entry = self.brain_nav.userAtlasInfo[self._active_atlas_key()]
        atlas_vol = atlas_entry['data']

        # Pick the LUT the current colour mode calls for. Fall back to the
        # categorical LUT if heatmap was requested but tdp_lut hasn't been
        # built yet (analysis not run).
        mode = self.brain_nav.ui_params.get('atlas_colour_mode', 'categorical')
        if mode == 'heatmap' and atlas_entry.get('tdp_lut') is not None:
            lut = atlas_entry['tdp_lut'].copy()
        else:
            lut = atlas_entry['lut'].copy()

        # Apply the live opacity from the orthview alpha slider. The LUT
        # bakes in the alpha at load time, so without this the atlas overlay
        # ignores later slider moves. Only ROI rows (alpha > 0) are touched,
        # keeping the background row transparent. No dim-highlight rewrite:
        # selection is signalled by the contour overlay instead.
        roi_rows = lut[:, 3] > 0
        slider_alpha = int(self.brain_nav.alpha * 255)
        lut[roi_rows, 3] = slider_alpha

        template_data = self.brain_nav.templates[self.brain_nav.file_nr_template]['data']

        if template_data.flags['C_CONTIGUOUS']:
            axial_slice = atlas_vol[:, :, self.brain_nav.axial_slice].astype(int)
            sagittal_slice = atlas_vol[self.brain_nav.sagittal_slice, :, :].astype(int)
            coronal_slice = atlas_vol[:, self.brain_nav.coronal_slice, :].astype(int)
        else:
            axial_slice = atlas_vol[self.brain_nav.axial_slice, :, :].astype(int)
            sagittal_slice = atlas_vol[:, :, self.brain_nav.sagittal_slice].astype(int)
            coronal_slice = atlas_vol[:, self.brain_nav.coronal_slice, :].astype(int)

        # Clamp to LUT range — defensive, in case the atlas has a stray label
        # outside what _build_atlas_lut sized for.
        max_idx = lut.shape[0] - 1
        axial_slice = np.clip(axial_slice, 0, max_idx)
        sagittal_slice = np.clip(sagittal_slice, 0, max_idx)
        coronal_slice = np.clip(coronal_slice, 0, max_idx)

        self.axial_overlay_item = pg.ImageItem(np.take(lut, axial_slice, axis=0))
        self.sagittal_overlay_item = pg.ImageItem(np.take(lut, sagittal_slice, axis=0))
        self.coronal_overlay_item = pg.ImageItem(np.take(lut, coronal_slice, axis=0))

        self.brain_nav.axial_view.addItem(self.axial_overlay_item)
        self.brain_nav.sagittal_view.addItem(self.sagittal_overlay_item)
        self.brain_nav.coronal_view.addItem(self.coronal_overlay_item)

        # Contour highlight for the selected ROI, if any.
        if highlight_label is not None and 0 < highlight_label <= max_idx:
            self._add_atlas_contour(
                axial_slice, sagittal_slice, coronal_slice, int(highlight_label),
            )

    def _clear_atlas_contours(self):
        """Drop the three per-view contour ImageItems (no-op if absent)."""
        for attr, view_attr in [
            ('axial_contour_item', 'axial_view'),
            ('sagittal_contour_item', 'sagittal_view'),
            ('coronal_contour_item', 'coronal_view'),
        ]:
            item = getattr(self, attr)
            if item is not None:
                getattr(self.brain_nav, view_attr).removeItem(item)
                setattr(self, attr, None)

    def _remove_atlas_overlay_items(self):
        for attr, view_attr in [
            ('axial_overlay_item', 'axial_view'),
            ('sagittal_overlay_item', 'sagittal_view'),
            ('coronal_overlay_item', 'coronal_view'),
            ('axial_contour_item', 'axial_view'),
            ('sagittal_contour_item', 'sagittal_view'),
            ('coronal_contour_item', 'coronal_view'),
        ]:
            item = getattr(self, attr)
            if item is not None:
                getattr(self.brain_nav, view_attr).removeItem(item)
                setattr(self, attr, None)

    def _add_atlas_contour(self, axial_slice, sagittal_slice, coronal_slice, label):
        """
        Draw a 1-voxel bright-cyan border around the selected ROI on each
        slice. Border = ROI - eroded(ROI), computed per slice with scipy.
        Cheap (three small binary_erosion calls per slice update) and
        legible over both categorical and heatmap-coloured overlays.
        """
        from scipy.ndimage import binary_erosion

        # RGBA — bright cyan, fully opaque. Chosen to contrast with viridis
        # (yellow-through-purple) and with the categorical HSV palette.
        border_rgba = np.array([0, 255, 255, 255], dtype=np.uint8)

        def contour_image(slice_2d):
            roi = (slice_2d == label)
            if not roi.any():
                return None
            border = roi & ~binary_erosion(roi)
            if not border.any():
                return None
            img = np.zeros((*slice_2d.shape, 4), dtype=np.uint8)
            img[border] = border_rgba
            return img

        axial_img = contour_image(axial_slice)
        sagittal_img = contour_image(sagittal_slice)
        coronal_img = contour_image(coronal_slice)

        if axial_img is not None:
            self.axial_contour_item = pg.ImageItem(axial_img)
            self.brain_nav.axial_view.addItem(self.axial_contour_item)
        if sagittal_img is not None:
            self.sagittal_contour_item = pg.ImageItem(sagittal_img)
            self.brain_nav.sagittal_view.addItem(self.sagittal_contour_item)
        if coronal_img is not None:
            self.coronal_contour_item = pg.ImageItem(coronal_img)
            self.brain_nav.coronal_view.addItem(self.coronal_contour_item)

    def create_custom_lut(self, colormap='hot', alpha=0.5, selected_cluster_id=None, overlay=None):
        """
        Create a custom LUT (Lookup Table) with transparency for non-cluster voxels.
        
        :param colormap: Name of the colormap to use.
        :param alpha: Transparency level for cluster voxels.
        :param threshold_value: Threshold value to identify cluster voxels.
        :return: A custom LUT with transparency.
        """
        if isinstance(colormap, str):
            # If colormap is a string, use it to get the LUT from matplotlib
            lut = pg.colormap.get(colormap, source='matplotlib').getLookupTable(alpha=False)
        elif isinstance(colormap, ListedColormap):
            # If colormap is a ListedColormap, use its colors directly
            lut = (colormap(np.linspace(0, 1, colormap.N))[:, :3] * 255).astype(np.uint8)
            
        # Extend LUT to include alpha values
        custom_lut = np.zeros((lut.shape[0], 4), dtype=lut.dtype)
        custom_lut[:, :3] = lut
        
        # Update the alpha channel (transparency) of the custom look-up table (LUT)
        # np.where(condition, x, y)
        	# •	condition: An array-like object containing boolean values. It determines where to select elements from x or y.
            # •	x: Values to select when the condition is True.
            # •	y: Values to select when the condition is False.
            
        # `custom_lut[:, 3]` accesses the alpha channel of the custom LUT, assuming the LUT is in RGBA format.
        # `np.arange(lut.shape[0])` generates an array of indices from 0 to the number of entries in the LUT.
        # `np.where` is used to apply a condition across these indices:
        #    - If the index is greater than or equal to `threshold_value`, the alpha value is set to `int(alpha * 255)`.
        #      This makes the corresponding LUT entries semi-transparent or opaque depending on the `alpha` value.
        #    - If the index is less than `threshold_value`, the alpha value is set to 0, making those entries fully transparent.
        # The result is an updated alpha channel for the LUT where only values above the threshold are visible.
        # custom_lut[:, 3] = np.where(np.arange(lut.shape[0]) >= threshold_value, int(alpha * 255), 0)

    
        # Adjust the transparency of non-selected clusters
        if selected_cluster_id is not None and overlay is not None:
            # selected_cluster_id += 1
            
            # Iterate through the LUT and apply transparency
            for i in range(lut.shape[0]):
                #  range(1, len(lut))
                if i == selected_cluster_id:
                    # custom_lut[i, 3] = int(alpha * 255)  # Full opacity for the selected cluster
                    custom_lut[i, 3] = 255  # Full opacity for the selected cluster

                else:
                    # custom_lut[i, 3] = int(0.6 * alpha * 255)  # Reduced opacity for non-selected clusters
                    custom_lut[i, 3] = int(0.4 * 255)  # Reduced opacity for non-selected clusters
        else:
            # Apply the same alpha to all clusters if no cluster is selected
            custom_lut[:, 3] = int(alpha * 255)
            #  custom_lut[:, 3] = np.where(np.arange(lut.shape[0]), int(alpha * 255), 0)


        # custom_lut[:, 3] = np.where(np.arange(lut.shape[0]), int(alpha * 255), 0)
        
        return custom_lut

    def add_orientation_labels(self):
        """
        Dynamically add anatomical orientation labels (L/R, A/P, I/S) to each orthogonal view
        based on the NIfTI sform matrix.

        This method uses the sform affine stored in the loaded NIfTI file to determine 
        the physical orientation of the three voxel axes. Using nibabel's `aff2axcodes`, 
        it extracts the **positive direction** codes for each axis, such as ('R', 'A', 'S') 
        for Right-Anterior-Superior. These codes describe the direction in which each voxel 
        axis increases.

        Since `aff2axcodes` returns only one side of each anatomical pair, we use a 
        mapping dictionary to determine the **opposite** direction labels. For example,
        'R' is opposite to 'L', 'A' is opposite to 'P', and 'S' is opposite to 'I'.

        •	In voxel space: axes are ordered as (X, Y, Z) → typically (L-R, A-P, I-S)
            aff2axcodes(sform) gives you the positive direction of increasing voxel index per axis.
            On screen, the y-axis increases downward, so “top of the image” ≠ higher voxel index, 
            which leads to flipped logic for vertical axes (A/P, S/I).
            Therefore: invert labels on the vertical axis of the display.

        The labels are then placed as follows:

        - **Axial view**: Shows plane orthogonal to axis 2 → X=axis 0 (L/R), Y=axis 1 (A/P)
        - **Sagittal view**: Shows plane orthogonal to axis 0 → X=axis 1 (P/A), Y=axis 2 (I/S)
        - **Coronal view**: Shows plane orthogonal to axis 1 → X=axis 0 (L/R), Y=axis 2 (I/S)

        In each view, the appropriate orientation labels are added just outside the image 
        boundaries using pixel offsets. This ensures correct anatomical interpretation of 
        the displayed slices, regardless of the underlying orientation of the data.

        This function requires that the sform matrix has been extracted and stored in:
            self.brain_nav.fileInfo[self.brain_nav.file_nr]['sform']
        """
        import nibabel as nib

        def create_label(text, pos):
            label = TextItem(text, anchor=(0.5, 0.5), color="white")
            label.setPos(*pos)
            return label

        # Remove previous orientation labels if they exist
        if not hasattr(self, 'orientation_labels'):
            self.orientation_labels = {'axial': [], 'sagittal': [], 'coronal': []}
        else:
            for label in self.orientation_labels['axial']:
                self.brain_nav.axial_view.getView().removeItem(label)
            for label in self.orientation_labels['sagittal']:
                self.brain_nav.sagittal_view.getView().removeItem(label)
            for label in self.orientation_labels['coronal']:
                self.brain_nav.coronal_view.getView().removeItem(label)
            self.orientation_labels = {'axial': [], 'sagittal': [], 'coronal': []}

        offset = -5  # pixels outside the data bounds

        sform = self.brain_nav.fileInfo[self.brain_nav.file_nr]['sform']
        axcodes = nib.aff2axcodes(sform)  # e.g. ('R', 'A', 'S')

        # Define opposite directions
        opposites = {'L': 'R', 'R': 'L', 'A': 'P', 'P': 'A', 'I': 'S', 'S': 'I'}

        # ---------------------------------------------------------------
        # Derive the DISPLAY volume's axis directions by composing the
        # exact transform chain the rendered data went through, instead of
        # assuming the canonical axes survive it (they don't — the y-flip
        # in rotate_volume previously mirrored A/P on the sagittal view's
        # horizontal axis while the axial view's two inversions happened
        # to cancel).
        #
        # Chain (see transpose_image / rotate_volume in image_processing):
        #   canonical (axcodes, e.g. R, A, S)
        #   1. .T                    -> axes reversed:            (2, 1, 0)
        #   2. rot90(k=1, axes=(2,0)) = flip(axis 0) + swap 0<->2
        #   3. flip(axis 1)
        #
        # Tracking (direction, sign) triples through those steps yields the
        # per-axis positive direction of the array that setImage receives.
        # ---------------------------------------------------------------
        def _display_axcodes(canonical):
            # (code, flipped?) per axis, starting canonical: axis i -> code i
            axes = [(canonical[0], False), (canonical[1], False), (canonical[2], False)]
            axes = axes[::-1]                       # 1. transpose (.T)
            axes[0] = (axes[0][0], not axes[0][1])  # 2a. rot90: flip axis 0
            axes[0], axes[2] = axes[2], axes[0]     # 2b. rot90: swap axes 0<->2
            axes[1] = (axes[1][0], not axes[1][1])  # 3. y-flip (rotate_volume)
            # Resolve flips into the opposite letter.
            return tuple(opposites[c] if flipped else c for c, flipped in axes)

        # Positive direction of each DISPLAY axis, e.g. ('R', 'P', 'I') for
        # RAS input. Rendering: pyqtgraph col-major (array axis 0 -> screen
        # x, axis 1 -> screen y) with ImageView's default invertY, so screen
        # y increases DOWNWARD. Hence for any displayed 2D slice:
        #   right edge  = positive direction of its screen-x axis
        #   bottom edge = positive direction of its screen-y axis
        disp = _display_axcodes(axcodes)

        # Axial slice [:, :, z]: screen-x = display axis 0, screen-y = axis 1
        shape = self.brain_nav.axial_view.image.shape
        x_len, y_len = shape[0], shape[1]
        vbox = self.brain_nav.axial_view.getView()
        label = create_label(opposites[disp[0]], (-offset, y_len / 2))         # left edge
        vbox.addItem(label)
        self.orientation_labels['axial'].append(label)
        label = create_label(disp[0], (x_len + offset, y_len / 2))             # right edge
        vbox.addItem(label)
        self.orientation_labels['axial'].append(label)
        label = create_label(opposites[disp[1]], (x_len / 2, -offset))         # top edge
        vbox.addItem(label)
        self.orientation_labels['axial'].append(label)
        label = create_label(disp[1], (x_len / 2, y_len + offset))             # bottom edge
        vbox.addItem(label)
        self.orientation_labels['axial'].append(label)

        # Sagittal slice [x, :, :]: screen-x = display axis 1, screen-y = axis 2
        shape = self.brain_nav.sagittal_view.image.shape
        x_len, y_len = shape[0], shape[1]
        vbox = self.brain_nav.sagittal_view.getView()
        label = create_label(opposites[disp[1]], (-offset, y_len / 2))         # left edge
        vbox.addItem(label)
        self.orientation_labels['sagittal'].append(label)
        label = create_label(disp[1], (x_len + offset, y_len / 2))             # right edge
        vbox.addItem(label)
        self.orientation_labels['sagittal'].append(label)
        label = create_label(opposites[disp[2]], (x_len / 2, -offset))         # top edge
        vbox.addItem(label)
        self.orientation_labels['sagittal'].append(label)
        label = create_label(disp[2], (x_len / 2, y_len + offset))             # bottom edge
        vbox.addItem(label)
        self.orientation_labels['sagittal'].append(label)

        # Coronal slice [:, y, :]: screen-x = display axis 0, screen-y = axis 2
        shape = self.brain_nav.coronal_view.image.shape
        x_len, y_len = shape[0], shape[1]
        vbox = self.brain_nav.coronal_view.getView()
        label = create_label(opposites[disp[0]], (-offset, y_len / 2))         # left edge
        vbox.addItem(label)
        self.orientation_labels['coronal'].append(label)
        label = create_label(disp[0], (x_len + offset, y_len / 2))             # right edge
        vbox.addItem(label)
        self.orientation_labels['coronal'].append(label)
        label = create_label(opposites[disp[2]], (x_len / 2, -offset))         # top edge
        vbox.addItem(label)
        self.orientation_labels['coronal'].append(label)
        label = create_label(disp[2], (x_len / 2, y_len + offset))             # bottom edge
        vbox.addItem(label)
        self.orientation_labels['coronal'].append(label)
