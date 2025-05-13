
import numpy as np
from PyQt5.QtWidgets import QWidget, QTableWidgetItem
from PyQt5.QtGui import QColor, QBrush
from PyQt5.QtCore import QTimer, Qt

class TblARI(QWidget):
    """
    TblARI manages the cluster summary table within the BrainNav interface.

    Core Responsibilities:
    - Populate the cluster table (`tblARI_df`) and keep it synchronized with internal state
    - React to row selections by updating related UI components: slice views, crosshairs, metrics, and 3D viewer
    - Maintain and reset visual highlights to reflect the current cluster state
    - Handle coordinate translation between voxel space and UI space
    - Support blinking behavior to draw attention to the 'Cluster Analysis' tab

    This component acts as the central interface for user interaction with cluster data, 
    serving as both a data renderer and trigger for deeper cluster-level UI updates.
    """
    def __init__(self, brain_nav):
        super().__init__()
        self.brain_nav = brain_nav

        # self.cluster_tab_blink_timer = QTimer(self)
        # self.cluster_tab_blink_timer.timeout.connect(self.blink_cluster_tab_title)
        # self.cluster_tab_blink_state = False

        # self.tab_widget = None  # Set externally if needed

    @property
    def fileInfo(self):
        return self.brain_nav.fileInfo
    
    @property
    def table_widget(self):
        return self.brain_nav.initiate_tabs.table_widget


    def update_table(self, tblARI_df, selected_clus=None):
        """
        Update the QTableWidget with the new data from tblARI_df.
        This method should be called whenever tblARI_df is updated.
        """
        # table_widget = self.brain_nav.initiate_tabs.table_widget
        ui_params = self.brain_nav.ui_params

        # block dsignal to widget to prevent it from triggering on_row_selected()
        self.table_widget.blockSignals(True)
        
        # Clear the table
        self.table_widget.clearContents()

        # Set the number of rows based on the data size, limiting to 10 rows
        num_rows = len(tblARI_df)
        self.table_widget.setRowCount(num_rows)

        # Populate the table with data from tblARI_df
        for i in range(num_rows):
            for j, value in enumerate(tblARI_df.iloc[i]):
                item = QTableWidgetItem(str(value))
                self.table_widget.setItem(i, j, item)
        self.table_widget.blockSignals(False)

        # In accept_cluster_changes (Accept button) selected cluster nr is passed in order to 
        # redifine the selected row nr (in tabel) here. This is then passed with updating the workstation
        # accordingly. 
        if selected_clus:
            selected_row_new = tblARI_df[tblARI_df['Unique ID'] == selected_clus].index[0]
            ui_params['selected_row'] = selected_row_new

        # tdp_item = self.fileInfo[self.file_nr]['tblARI_df'].iloc[selected_row_new].TDP
        # new_tdp = max(0.0, min(tdp_item, 1.0))  # Ensure it's within range
        # self.update_tdp_ui(new_tdp)  # Use a dedicated function to update UI elements

        
        # Update the work station with the selected row's data if it exists
        # selected_row = self.table_widget.currentRow()
        # self.ui_params.get('selected_row', -1)
        if isinstance(ui_params['selected_row'], (int, np.integer)) and ui_params['selected_cluster_id'] in tblARI_df['Unique ID'].values:
            selected_row= tblARI_df[tblARI_df['Unique ID'] == ui_params['selected_cluster_id']].index[0]

            self.brain_nav.cluster_ws.update_work_station(selected_row)
        else:
            self.brain_nav.cluster_ws.clear_work_station()
        
        # self.table_widget.itemSelectionChanged.connect(self.update_cluster_3d_view) #needs cluster ID


        # Change hilight on selected row in stats table accordingly
        # self.reset_highlight()
        self.brain_nav.cluster_tab_blink_timer.start(200)  # Every 500ms
        QTimer.singleShot(3000, self.stop_blinking_cluster_tab_title)  # Stop after 3 seconds

    def blink_cluster_tab_title(self):
        """Toggles the 'Cluster Analysis' tab title between normal and highlighted."""

        if self.brain_nav.cluster_tab_blink_state:
            self.brain_nav.initiate_tabs.tab_widget.tabBar().setTabTextColor(1, QColor("orange"))
        else:
            self.brain_nav.initiate_tabs.tab_widget.tabBar().setTabTextColor(1, QColor("white"))  # Reset to default color

        self.brain_nav.cluster_tab_blink_state = not self.brain_nav.cluster_tab_blink_state

    def stop_blinking_cluster_tab_title(self):

        self.brain_nav.cluster_tab_blink_timer.stop()

        self.brain_nav.initiate_tabs.tab_widget.setTabText(1, "Cluster Analysis")  # Reset to normal
        self.brain_nav.initiate_tabs.tab_widget.tabBar().setTabTextColor(1, QColor("white"))


    def clear_table(self):
        """
        Clears the contents of the table widget and resets row count.
        This is used to reset the table when no data is available.
        """
        self.brain_nav.initiate_tabs.table_widget.blockSignals(True)
        self.brain_nav.initiate_tabs.table_widget.clearContents()
        self.brain_nav.initiate_tabs.table_widget.setRowCount(0)

        # Optional: clear headers too if you want a fully blank slate
        # self.table_widget.setColumnCount(0)

        self.brain_nav.initiate_tabs.table_widget.blockSignals(False)

    def on_row_selected(self):
        file_nr = self.brain_nav.file_nr

        # Get the selected row
        selected_row = self.brain_nav.initiate_tabs.table_widget.currentRow()

        # Set it in UI parameters dict
        # Cast to numpy.int64 because the evaluation in update_table() expects this data type
        # Other specifications of row number are based on the table (numpy dataframe)
        self.brain_nav.ui_params['selected_row'] = np.int64(selected_row)

        # Highlight the selected row
        # self.highlight_selected_row(selected_row)
        
        # Reset the TDP value in the UI when a new row is selected
        if selected_row >= 0:  # Ensure that a row is selected
            # Get the TDP value from the table (assuming TDP is in the 4th column)
            tdp_item = self.fileInfo[file_nr]['tblARI_df'].iloc[selected_row].TDP
            # if tdp_item:
            try:
                # new_tdp = float(tdp_item.text())  # Convert text to float
                new_tdp = max(0.0, min(tdp_item, 1.0))  # Ensure it's within range
                self.brain_nav.UIHelp.update_tdp_ui(new_tdp)  # Use a dedicated function to update UI elements
            except ValueError:
                print("Warning: Invalid TDP value in table.")  # Debugging message
            
            # Highlight the selected row
            self.highlight_selected_row(selected_row)
            
            # Update the work station accordingly
            self.brain_nav.cluster_ws.update_work_station(selected_row)

            # Extract the voxel coordinates (x, y, z) from the selected row
            voxel_coords_item = self.table_widget.item(selected_row, 5)  # Assuming "Vox (x, y, z)" is the 6th column

            if voxel_coords_item:
                # Convert the string "(x, y, z)" into a tuple of integers
                voxel_coords_str = voxel_coords_item.text().strip("()")
                voxel_coords = tuple(map(int, voxel_coords_str.split(',')))
                
                # print(f"Selected voxel coordinates: {voxel_coords}")
                
                # Map from native space to UI space coordinates
                # x_raw, y_raw, z_raw  = self.fileInfo[self.file_nr]['mapped_coordinate_matrix_F'][voxel_coords[0], voxel_coords[1], voxel_coords[2]]
                # x_ui, y_ui, z_ui  = self.fileInfo[self.file_nr]['inverse_mapped_matrix_F'][voxel_coords[0], voxel_coords[1], voxel_coords[2]]
                x_ui, y_ui, z_ui  = self.brain_nav.aligned_statMapInfo[(file_nr, self.brain_nav.file_nr_template)]['inverse_mapped_matrix_F'][voxel_coords[0], voxel_coords[1], voxel_coords[2]]    
                # print(f"Selected voxel coordinates in UI space: {x_raw}, {y_raw}, {z_raw}")

                # Update the slice indices
                self.brain_nav.sagittal_slice = x_ui
                self.brain_nav.coronal_slice  = y_ui
                self.brain_nav.axial_slice    = z_ui
                
                # Get unique cluster ID
                cluster_id = int(self.table_widget.item(selected_row, 1).text())
                self.brain_nav.ui_params['selected_cluster_id'] = cluster_id

                # Update UI; slices, crosshair, metrics, 3dviewer and xyz spinboxes
                self.brain_nav.orth_view_update.update_slices(selected_cluster_id=cluster_id)
                self.brain_nav.orth_view_update.update_crosshairs()
                self.brain_nav.metrics.show_metrics()
                self.brain_nav.threeDviewer.update_cluster_3d_view(cluster_id)
                self.brain_nav.UIHelp.update_ui_xyz()
       
    def highlight_selected_row(self, selected_row=None, removed_clusters=False, reinstated_clusters=None):
        """
        Highlights the selected row and any specified clusters with distinct colors.
        
        :param selected_row: Row index to highlight with green.
        :param removed_clusters: If True, highlights clusters marked as removed in red.
        :param reinstated_clusters: List of cluster IDs to highlight in light blue if reinstated.
        """
        # Define highlight colors
        light_green = QColor(27, 122, 65)    # RGB for light green
        highlight_red = QColor(237, 100, 90) # RGB for red
        light_blue = QColor(166, 182, 227)   # RGB for light blue

        # Clear all row background colors
        self.clear_all_highlights()

        # Highlight the selected row
        if selected_row is not None:
            for col in range(self.table_widget.columnCount()):
                item = self.table_widget.item(selected_row, col)
                if item is not None:
                    item.setBackground(QBrush(light_green))

  
    def reset_highlight(self):
        """
        Reapply highlight to the previously selected row if it exists in ui_params.
        """
        # selected_row = self.ui_params.get('selected_row', -1)

        selected_row = -1

        file_nr = self.brain_nav.file_nr

        # Access the current cluster table that is displayed in the UI
        # Check if 'tblARI_df' exists and 'selected_cluster_id' is valid
        if 'tblARI_df' in self.fileInfo[file_nr] and self.brain_nav.ui_params['selected_cluster_id']:
            tblARI_df = self.brain_nav.fileInfo[file_nr]['tblARI_df']
            
            # Proceed only if 'selected_cluster_id' is in 'Unique ID' column
            if self.brain_nav.ui_params['selected_cluster_id'] in tblARI_df['Unique ID'].values:
                selected_row= tblARI_df[tblARI_df['Unique ID'] == self.brain_nav.ui_params['selected_cluster_id']].index[0]
            else:
                self.clear_all_highlights()
        
        # If selected_row is an int and greater then 0. This will ignore the empty list cases
        # which happen when no row is selected. This is because reset_highlight is also called from 
        # control_threshold in Metrics. It's possible that no cluster has been selected but users will 
        # change the threshold slider. 
        if isinstance(selected_row, (int, np.integer)) and selected_row >= 0:
            self.highlight_selected_row(selected_row)

    def clear_all_highlights(self):
        """
        Clears all custom background colors in the table.
        """
        for row in range(self.table_widget.rowCount()):
            for col in range(self.table_widget.columnCount()):
                item = self.table_widget.item(row, col)
                if item is not None:
                    item.setBackground(QBrush(Qt.black))  # Reset to default color
    

