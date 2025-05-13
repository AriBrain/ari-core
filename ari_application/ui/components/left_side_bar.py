from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, 
    QPushButton, QMessageBox,  QListWidgetItem
)
from PyQt5.QtCore import Qt, pyqtSignal

from ari_application.resources.styles import Styles  # Adjust path if needed

import os


class LeftSideBar(QWidget):
    """
    LeftSideBar manages the vertical control panel on the left-hand side of the BrainNav UI.

    This component provides interactive lists and buttons to manage core resources for analysis:
    - Statistical Images
    - Template Images
    - Anatomical Atlases

    Signals:
    --------
    - `stat_image_add_clicked`: Emitted when the "Add" button for statistical images is clicked.
    - `template_add_clicked`: Emitted when the "Add" button for templates is clicked.
    - `atlas_add_clicked`: Emitted when the "Add" button for atlases is clicked.

    Features:
    ---------
    - Upload and select statistical images, templates, and atlas files.
    - Switch and configure the selected statistical map and template.
    - Automatically prompt users when cluster maps are missing or thresholding hasn't been performed.
    - Updates viewer components (metrics, 3D view, orthogonal slices) based on selection.
    - Shows ARI status for each statistical image using a custom `StatImageItem` widget.

    Key Widgets:
    ------------
    - `stat_images_list`, `template_list`: `QListWidget` instances displaying file items.
    - `stat_images_upload_button`, `template_upload_button`, `atlas_upload_button`: "Add" buttons for each resource type.
    - `stat_images_set_button`, `template_set_button`: "Set" buttons to activate selected files.
    - `left_panel_container`: The top-level container widget holding the entire sidebar layout.

    Integration:
    ------------
    - Communicates with `BrainNav` to update metrics, cluster overlays, templates, and coordinate mappings.
    - Makes use of `StatImageItem` widgets to represent file entries visually, including ARI completion indicators.

    Notes:
    ------
    - Atlas support is minimal and currently shows a single entry (AAL2).
    - This class expects `self.templates`, `self.statmap_templates`, `self.data_bg_index`, and `self.file_nr` to be defined externally.
    - All file additions, selections, and UI refresh logic is routed through this sidebar for consistency.
    """

    # Define the button signals
    stat_image_add_clicked = pyqtSignal()
    template_add_clicked = pyqtSignal()
    atlas_add_clicked = pyqtSignal()


    def __init__(self, BrainNav):
        super().__init__() # Initialize the QWidget
        
        self.brain_nav = BrainNav

        self.init_sidebar()

    def init_sidebar(self):
        left_panel_layout = QVBoxLayout()

        # === Statistical Images Section === #
        stat_images_layout = QVBoxLayout()
        stat_images_label = QLabel("Statistical Images")
        self.stat_images_list = QListWidget()
        self.stat_images_list.setStyleSheet(" ".join(Styles.left_box_styling))
        self.stat_images_list.setMaximumWidth(150)

        self.stat_images_upload_button = QPushButton("Add")
        self.stat_images_upload_button.setStyleSheet(Styles.overlay_button_styling)
        self.stat_images_upload_button.setCursor(Qt.PointingHandCursor)
        # self.stat_images_upload_button.clicked.connect(self.upload_files.upload_dialog)
        self.stat_images_upload_button.clicked.connect(self.stat_image_add_clicked.emit)

        self.stat_images_set_button = QPushButton("Set")
        self.stat_images_set_button.setStyleSheet(Styles.overlay_button_styling)
        self.stat_images_set_button.setCursor(Qt.PointingHandCursor)
        self.stat_images_set_button.clicked.connect(self.set_selected_item)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.stat_images_upload_button, alignment=Qt.AlignLeft)
        button_layout.addWidget(self.stat_images_set_button, alignment=Qt.AlignRight)

        stat_images_layout.addWidget(stat_images_label)
        stat_images_layout.addWidget(self.stat_images_list)
        stat_images_layout.addLayout(button_layout)

        self.add_statmap_to_list(self.brain_nav.start_input['data_dir'])

        left_panel_layout.addLayout(stat_images_layout)

        # === Template Section === #
        template_layout = QVBoxLayout()
        template_label = QLabel("Template")
        self.template_list = QListWidget()
        self.template_list.setStyleSheet(" ".join(Styles.left_box_styling))
        self.template_list.setMaximumWidth(150)

        self.template_upload_button = QPushButton("Add")
        self.template_upload_button.setStyleSheet(Styles.overlay_button_styling)
        self.template_upload_button.setCursor(Qt.PointingHandCursor)
        # self.template_upload_button.clicked.connect(self.upload_files.upload_template_dialog)
        self.template_upload_button.clicked.connect(self.template_add_clicked.emit)

        self.template_set_button = QPushButton("Set")
        self.template_set_button.setStyleSheet(Styles.overlay_button_styling)
        self.template_set_button.setCursor(Qt.PointingHandCursor)
        self.template_set_button.clicked.connect(self.set_selected_template)

        template_button_layout = QHBoxLayout()
        template_button_layout.addWidget(self.template_upload_button, alignment=Qt.AlignLeft)
        template_button_layout.addWidget(self.template_set_button, alignment=Qt.AlignRight)

        template_layout.addWidget(template_label)
        template_layout.addWidget(self.template_list)
        template_layout.addLayout(template_button_layout)

        for file_info in self.brain_nav.templates.values():
            self.template_list.addItem(file_info['filename'])   
        self.template_list.setCurrentRow(self.brain_nav.file_nr_template)

        left_panel_layout.addLayout(template_layout)

        # === Atlas Section === #
        atlas_layout = QVBoxLayout()
        atlas_label = QLabel("Atlas")
        atlas_list = QListWidget()
        atlas_list.setStyleSheet(" ".join(Styles.left_box_styling))
        atlas_list.setMaximumWidth(150)

        self.atlas_upload_button = QPushButton("Add")
        self.atlas_upload_button.setStyleSheet(Styles.overlay_button_styling)
        self.atlas_upload_button.setCursor(Qt.PointingHandCursor)
        # atlas_upload_button.clicked.connect(self.upload_files.upload_dialog)
        self.atlas_upload_button.clicked.connect(self.atlas_add_clicked.emit)


        atlas_layout.addWidget(atlas_label)
        atlas_layout.addWidget(atlas_list)
        atlas_layout.addWidget(self.atlas_upload_button, alignment=Qt.AlignRight)

        atlas_list.addItem('AAL2')

        left_panel_layout.addLayout(atlas_layout)
        left_panel_layout.addStretch()

        self.left_panel_container = QWidget()
        self.left_panel_container.setLayout(left_panel_layout)



    def set_selected_item(self):
        """
        Sets the selected statistical image and updates related UI components.
        
        This method retrieves the selected item from `stat_images_list`, updates the internal
        file index (`self.file_nr`), and displays relevant information and metrics for the selection.
        
        Functionality:
        - **Selection Retrieval:** Fetches the currently selected item in `stat_images_list` and sets `self.file_nr`
          to the corresponding row index.
        - **Item Display:** Prints the file name of the selected item for debugging or informational purposes.
        - **Metrics Display and Viewer Setup:** Calls `Metrics.show_metrics` to display metrics associated with
          the selected item and `OrthViewSetup.setup_viewer` to configure the viewer accordingly.
        - **Empty Selection Handling:** Prints a message if no item is selected.
        """
        prev_file_nr        = self.brain_nav.file_nr
        fileInfo            = self.brain_nav.fileInfo
        file_nr             = self.brain_nav.file_nr
        file_nr_template    = self.brain_nav.file_nr_template

        selected_items = self.stat_images_list.selectedItems()
        if selected_items:

            # store last selected thresholding method with conditional check, brain_nav.file_nr has not been updated yet
            if 'last_thresholding_method' in fileInfo[file_nr]:
                fileInfo[file_nr]['last_thresholding_method'] = self.brain_nav.initiate_tabs.thresholding_dropdown.currentText()
            else:
                fileInfo[file_nr]['last_thresholding_method'] = "TDP-based"

            selected_item = selected_items[0]
            
            # Get the index of the selected item in the list, file_nr is now updated
            file_nr = self.stat_images_list.row(selected_item)
            self.brain_nav.file_nr = file_nr
            
            self.switch_rawData_template()  # updates: template list with the selected statmap

            # It's possbile that the user has changed to a template for which the the overla data was not computed beyond the gradient map.
            gradmap = self.brain_nav.aligned_statMapInfo.get((file_nr, file_nr_template), {}).get('gradmap_flag', None)
            clusterlist_exists = 'clusterlist' in fileInfo[file_nr]

            if gradmap is True and clusterlist_exists:
                self.brain_nav.message_box.log_message("<span style='color: orange;'>Warning: No clustermap computed for selected template, do you want to do this now?</span>")
                print("\033[38;5;214m"  # Orange terminal output
                      "Warning: No clustermap computed for selected template, do you want to compute it now?\033[0m")
                
                # Show dialog asking user whether to proceed
                dialog = QMessageBox(self.brain_nav)
                dialog.setWindowTitle("No clustermap found for selected template image")
                dialog.setText("No clustermap computed for selected template. Do you want to compute it now?")
                dialog.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
                dialog.setDefaultButton(QMessageBox.Ok)
                
                response = dialog.exec_()
                
                if response == QMessageBox.Ok:
                    self.set_selected_template()
                else:
                    self.brain_nav.file_nr = prev_file_nr
                    return

            if gradmap is True and not clusterlist_exists:
                # Show dialog with three options: Compute, Review, Cancel
                dialog = QMessageBox(self)
                dialog.setWindowTitle("No thresholding performed")
                dialog.setText("No thresholding has been done for this statistical map.\n"
                            "Would you like to compute it now, or review the gradient map first?")
                compute_button = dialog.addButton("Compute", QMessageBox.AcceptRole)
                review_button = dialog.addButton("Review Gradient Map", QMessageBox.ActionRole)
                cancel_button = dialog.addButton(QMessageBox.Cancel)

                dialog.setDefaultButton(compute_button)
                dialog.exec_()

                clicked_button = dialog.clickedButton()
                
                if clicked_button == compute_button:
                    self.brain_nav.WBTing.update_threshold_label(float(self.brain_nav.WBTing.tdp_textbox1.text()))
                elif clicked_button == review_button:
                    self.brain_nav.orth_view_setup.setup_viewer()
                    return
                elif clicked_button == cancel_button:
                    return

            item_widget = self.stat_images_list.itemWidget(selected_item)
            print(f"Selected item: {item_widget.file_name_label.text()}")

            # update the file_nr in the brain_nav object to the selected one
            # self.brain_nav.file_nr = file_nr

            # # Display metrics and set up the viewer
            self.brain_nav.tblARI.clear_table()          # clear the table
            self.brain_nav.UIHelp.refresh_ui()           # updated: ari table, 3dviewer, metrics, orthoview
            self.brain_nav.UIHelp.update_ui_xyz()        # updates: spinboxes    
            self.brain_nav.cluster_ws.update_work_station(selected_row=None)  # updates: workstation table and cluster tdp slider and box - requires selected row
            

            # set the whole brain tresholdslider to the selected statmap (this is in sunch with the table etc.)
            method = self.brain_nav.fileInfo[self.brain_nav.file_nr].get('last_thresholding_method')
            if method is not None:
                self.brain_nav.WBTing.reset_threshold_slider(method)

            self.brain_nav.message_box.log_message(f"<span style='color: white;'>Selected Map: {item_widget.file_name_label.text()}</span>")
        else:
            print("No item selected")


    def switch_rawData_template(self):
        """
        Updates the statMap template name in the template list UI to match its filename.

        Assumes statMap entry is located at `self.data_bg_index` (an integer key).
        """
        # change the templates entry of the statmap to the currently selected one
        statmap_index = self.brain_nav.data_bg_index        
        self.brain_nav.templates[statmap_index] = self.brain_nav.statmap_templates[self.brain_nav.file_nr]

        # update the name in the UI list
        statmap_name = self.brain_nav.templates[statmap_index]['filename']
        self.template_list.item(statmap_index).setText(statmap_name)

    def set_selected_template(self):
        """
        Handles the selection of a new template from the template list.

        When a user selects a template, this function:
        - Retrieves the selected template's index.
        - Clears the current 3D scene.
        - Reinitializes the orthogonal viewer.
        - Recomputes and updates the table containing cluster metrics.
        - Restores the last selected cluster overlay (if any).
        - Updates the 3D cluster view and displays associated metrics.
        """

        # Get the selected item(s) from the template list
        selected_items = self.template_list.selectedItems()

        if selected_items:
            # Keep the xyz of the previous template ui space
            xprev, yprev, zprev = self.brain_nav.sagittal_slice, self.brain_nav.coronal_slice, self.brain_nav.axial_slice
            xyz_prev = (xprev, yprev, zprev)

            # Get cluster id based on currenty xyz position. If no clusterID return None.
            # this will retrieve a cluster even if not selected. Might not be ideal here
            # clusID = self.get_selected_cluster_id()

            if self.brain_nav.ui_params['selected_cluster_id']:
                clusID = self.brain_nav.ui_params['selected_cluster_id']
            else:
                clusID = None

            # Pick the first selected item
            selected_item = selected_items[0]

            # save previous template index
            file_nr_template_prev = self.brain_nav.file_nr_template
            
            # Save the index of the newly selected template
            self.brain_nav.file_nr_template = self.template_list.row(selected_item)

            # Clear the 3D view scene to prepare for new cluster display
            self.brain_nav.threeDviewer.cluster_3d_view.clear()

            # Reinitialize the orthogonal viewer with correct UI, slices, and 3D view
            self.brain_nav.orth_view_setup.setup_viewer()

            # Load the list of clusters for the selected template
            try:
                clusterlist = self.brain_nav.fileInfo[self.brain_nav.file_nr]['clusterlist']
            except KeyError:
                clusterlist = None

            # Compute and sort cluster metrics for the cluster list
            ord_clusterlist, _, tblARI_df, _ = self.brain_nav.metrics.prepare_tblARI(clusterlist)

            # Update the cluster image and table with computed metrics
            _, _, tblARI_df = self.brain_nav.metrics.update_clust_img(ord_clusterlist, tblARI_df)

            # Update the GUI table with new cluster metrics
            self.brain_nav.tblARI.update_table(tblARI_df)

            # Remap the xyz coordinates from old to new template ui space
            self.brain_nav.UIHelp.remap_ui_xyz(self.brain_nav.file_nr, xyz_prev, file_nr_template_prev, self.brain_nav.file_nr_template)

            # Update the overlay image to match the selected cluster/template
            self.brain_nav.metrics.update_overlay_image(self.brain_nav.file_nr, clusID)

            self.brain_nav.orth_view_update.update_crosshairs()

            if clusID is not None:
                # Reset any previously highlighted cluster
                self.brain_nav.tblARI.reset_highlight()

            #     # Find the row in the table corresponding to the selected cluster
            #     selected_row = tblARI_df[tblARI_df['Unique ID'] == clusID].index[0]

            #     # Center the view and metrics on the selected cluster
            #     self.metrics.follow_cluster_xyz(selected_row) # also calls show_metrics

            # Show the cluster metrics in the UI
            self.brain_nav.metrics.show_metrics()

            # Render the selected cluster in the 3D view
            self.brain_nav.threeDviewer.update_cluster_3d_view(clusLabel=clusID)
            
            # set the gragmap_flag for this data and template combination to false. 
            self.brain_nav.aligned_statMapInfo[(self.brain_nav.file_nr, self.brain_nav.file_nr_template)]['gradmap_flag'] = False

        # self.log_message(f"<span style='color: white;'>Selected Template: {item_widget.file_name_label.text()}</span>")


    def add_template_to_list(self, file_path):
        """Add a new template to the template list widget."""
        item_name = os.path.basename(file_path)
        item = QListWidgetItem(f"{item_name}")
        self.template_list.addItem(item)
        self.template_list.setCurrentItem(item)

    def add_statmap_to_list(self, full_path):
        # Add items with custom widgets
        base_name = os.path.basename(full_path)
        base_dir = os.path.basename(os.path.dirname(full_path))

        # item_widget = StatImageItem(f"{base_dir}/{base_name}")
        item_widget = StatImageItem(f"{base_name}")
        item = QListWidgetItem(self.stat_images_list)
        item.setSizeHint(item_widget.sizeHint())
        self.stat_images_list.setItemWidget(item, item_widget)
        self.brain_nav.stat_image_items.append(item_widget)  # Store reference

    def update_ari_status(self, completed=False):
        for item in self.brain_nav.stat_image_items:
            item.update_ari_status(completed)

    

class StatImageItem(QWidget):
    """
    Class: StatImageItem

    Description:
    This class represents a custom widget for displaying statistical image items in a list, with an associated ARI status. 
    The widget comprises a file name label and an ARI status label, arranged horizontally. 
    The ARI status label initially appears in grey, but can be updated to green when the ARI analysis is completed.
        
    Attributes:
    - file_name_label (QLabel): Displays the name of the statistical image file.
    - ari_label (QLabel): Displays the ARI status, which can be updated to indicate completion.

    Methods:
    - __init__(self, file_name): Initializes the widget with the provided file name and sets up the layout and styling.
    - update_ari_status(self, completed=False): Updates the color of the ARI label to green if the analysis is completed,
      otherwise keeps it grey.
    """
    def __init__(self, file_name):
        super().__init__()

        # Create a horizontal layout for the item
        layout = QHBoxLayout()
        layout.setContentsMargins(2, 2, 2, 2)  # Add 2px padding on all sides
        layout.setSpacing(0)  # Remove spacing between widgets

        # Style the widget itself to have rounded edges
        self.setStyleSheet("""
            background-color: #091c13;  # Set background color to match the list
            border-radius: 10px;         # Match the rounded border of the list
        """)

        # Create a label for the file name
        self.file_name_label = QLabel(file_name)
        self.file_name_label.setStyleSheet("color: white; border: none;")  # Set text color
        layout.addWidget(self.file_name_label, stretch=1)  # Allow file name to take more space

        # Create a label for the ARI status, initially grey with slight upper padding
        self.ari_label = QLabel("ARI")
        self.ari_label.setStyleSheet("""
            color: grey; 
            font-size: 10px; 
            border: none; 
            /*padding-top: 5px;   Add slight upper padding */
        """)
        layout.addWidget(self.ari_label, alignment=Qt.AlignRight)  # Push ARI label to the right

        # Set the layout for the widget
        self.setLayout(layout)

    def update_ari_status(self, completed=False):
        """Update the ARI status color."""
        if completed:
            self.ari_label.setStyleSheet("color: green; font-size: 10px; border: none; ")
        else:
            self.ari_label.setStyleSheet("color: grey; font-size: 10px; border: none; ")
    
