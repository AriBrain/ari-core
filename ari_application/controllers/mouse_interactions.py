
### controllers/mouse_interactions.py

"""
MouseInteractions class handles all mouse-related events and interactions 
for the BrainViewer application.

This class processes mouse events such as clicks, drags, pans, and zooms. 
It updates the view slices,
crosshair positions, and manages zoom and pan functionalities across 
the axial, sagittal, and coronal views.

"""

from PyQt5.QtCore import QEvent, Qt, QObject
from PyQt5.QtWidgets import QApplication, QMenu, QAction, QTableWidgetItem
from ari_application.models.metrics import Metrics


class MouseInteractions(QObject):


    def __init__(self, BrainNav):
        """
        Initialize the MouseInteractions with a reference to the BrainViewer instance.

        :param brain_nav: Instance of the BrainViewer class.
        """
        super().__init__()  # Initialize the QObject part
        self.brain_nav = BrainNav

    def eventFilter(self, source, event):
        """
        Filter and handle mouse events.

        :param source: The source of the event.
        :param event: The event to be processed.
        :return: True if the event was handled, False otherwise.
        """
        # If the left mouse button is pressed, start dragging
        if event.type() == QEvent.GraphicsSceneMousePress and event.button() == Qt.LeftButton:
            self.brain_nav._dragging = True
            self.brain_nav._mouse_pressed = True
            self.brain_nav._last_pos = event.scenePos()
            return True

        # If the left mouse button is released, stop dragging and handle as a click if applicable
        elif event.type() == QEvent.GraphicsSceneMouseRelease and event.button() == Qt.LeftButton:
            self.brain_nav._dragging = False
            if self.brain_nav._mouse_pressed:
                self.on_mouse_click(event, source)
            self.brain_nav._mouse_pressed = False
            return True

        # Handle mouse movement while dragging
        elif event.type() == QEvent.GraphicsSceneMouseMove and self.brain_nav._dragging:
            self.handle_drag(event.scenePos(), source)
            self.brain_nav._mouse_pressed = False
            return True
        
            # If the right mouse button is pressed, show the context menu
        elif event.type() == QEvent.GraphicsSceneMousePress and event.button() == Qt.RightButton:
            self.show_context_menu(event, source)
            return True

        # If the right mouse button is pressed, start panning
        elif event.type() == QEvent.GraphicsSceneMousePress and event.button() == Qt.RightButton:
            self.brain_nav._right_dragging = True
            self.brain_nav._right_last_pos = event.scenePos()
            return True

        # If the right mouse button is released, stop panning
        elif event.type() == QEvent.GraphicsSceneMouseRelease and event.button() == Qt.RightButton:
            self.brain_nav._right_dragging = False
            return True

        # Handle mouse movement while panning
        elif event.type() == QEvent.GraphicsSceneMouseMove and self.brain_nav._right_dragging:
            self.handle_pan(event.scenePos(), source)
            return True

        # Handle mouse wheel events for zooming or scrolling
        elif event.type() == QEvent.GraphicsSceneWheel:
            if QApplication.keyboardModifiers() == Qt.ControlModifier:
                self.handle_zoom(event, source)
            else:
                self.handle_scroll(event, source)
            return True

        # Pass the event to the base class if not handled
        return super(type(self.brain_nav), self.brain_nav).eventFilter(source, event)

    def on_mouse_click(self, event, source):
        """
        Handle mouse click events to update the crosshair and slices.

        :param event: The mouse event.
        :param source: The source of the event.
        """
        pos = event.scenePos()
       
        # Print source and each view's scene for debugging
        # print("Source:", source)
        # print("Axial view scene:", self.brain_nav.axial_view.getView().scene())
        # print("Sagittal view scene:", self.brain_nav.sagittal_view.getView().scene())
        # print("Coronal view scene:", self.brain_nav.coronal_view.getView().scene())

        # Determine which view was clicked (axial, sagittal, or coronal)
        if source is self.brain_nav.axial_view.getView().scene():
            view_type = 'axial'
        elif source is self.brain_nav.sagittal_view.getView().scene():
            view_type = 'sagittal'
        elif source is self.brain_nav.coronal_view.getView().scene():
            view_type = 'coronal'
       
        # Map the click position to the appropriate slice coordinates
        if view_type == 'coronal':
            # print(f"Mouse Click detected on {view_type}")
            mapped_pos = self.brain_nav.coronal_view.getView().mapSceneToView(pos)
            x, y = int(mapped_pos.x()), int(mapped_pos.y())
            self.brain_nav.axial_slice = y
            self.brain_nav.sagittal_slice = x
        elif view_type == 'sagittal':
            # print(f"Mouse Click detected on {view_type}")
            mapped_pos = self.brain_nav.sagittal_view.getView().mapSceneToView(pos)
            x, y = int(mapped_pos.x()), int(mapped_pos.y())
            self.brain_nav.axial_slice = y
            self.brain_nav.coronal_slice = x
        elif view_type == 'axial':
            # print(f"Mouse Click detected on {view_type}"
            mapped_pos = self.brain_nav.axial_view.getView().mapSceneToView(pos)
            x, y = int(mapped_pos.x()), int(mapped_pos.y())
            self.brain_nav.sagittal_slice = x
            self.brain_nav.coronal_slice = y

        # Update the crosshairs and slices based on the new positions
        self.brain_nav.orth_view_update.update_slices()
        self.brain_nav.orth_view_update.update_crosshairs()
        # self.brain_nav.metrics.show_metrics(self.brain_nav)
        self.brain_nav.metrics.show_metrics()
        self.brain_nav.UIHelp.update_ui_xyz()

    def handle_zoom(self, event, source):
        """
        Handle zoom events to zoom in/out on the views.

        :param event: The mouse wheel event.
        :param source: The source of the event.
        """
        # Determine the zoom direction
        delta = -event.delta()
        zoom_factor = 1.1 if delta > 0 else 0.9

        # Apply zoom to all views
        for i, view in enumerate([self.brain_nav.axial_view, self.brain_nav.sagittal_view, self.brain_nav.coronal_view]):
            # Get the current view range (visible area) of the view
            view_range = view.getView().viewRange()

            # Get the position of the mouse in the scene and map it to view coordinates
            mouse_pos = event.scenePos()
            mapped_pos = view.getView().mapSceneToView(mouse_pos)
            mouse_x = mapped_pos.x()
            mouse_y = mapped_pos.y()

            # Ensure the mouse coordinates are within the bounds of the current view range
            mouse_x = min(max(mouse_x, view_range[0][0]), view_range[0][1])
            mouse_y = min(max(mouse_y, view_range[1][0]), view_range[1][1])

            # Calculate the new ranges centered around the mouse position
            new_x_range = (mouse_x - (mouse_x - view_range[0][0]) * zoom_factor, 
                        mouse_x + (view_range[0][1] - mouse_x) * zoom_factor)
            new_y_range = (mouse_y - (mouse_y - view_range[1][0]) * zoom_factor, 
                        mouse_y + (view_range[1][1] - mouse_y) * zoom_factor)
            
            # Set the new range for the view, centered around the mouse position
            view.getView().setRange(xRange=new_x_range, yRange=new_y_range, padding=0)

        # Update the stored ranges after zooming
        self.brain_nav.orth_view_update.get_ranges()

        # Ensure the event is fully consumed to prevent default behavior
        event.accept()

    def handle_drag(self, pos, source):
        """
        Handle drag events to move the crosshair and update slices.

        :param pos: The current position of the mouse.
        :param source: The source of the event.
        """
        if self.brain_nav._last_pos is None:
            return
        # Calculate the change in position since the last recorded mouse position
        delta = pos - self.brain_nav._last_pos
        if delta.manhattanLength() > 0:
            self.brain_nav._last_pos = pos
            self.brain_nav.orth_view_update.move_crosshair_and_slices(pos, source)

    # def handle_scroll(self, event, source):
    #     """
    #     Handle scroll events to change slices.

    #     :param event: The mouse wheel event.
    #     :param source: The source of the event.

    #         # Context

    #     # e.g: self.axial_slice = min(max(self.axial_slice + steps, 0), self.data.shape[2] - 1)

    #     # Theselines of code are used to update the current axial slice index (self.axial_slice) when the user 
    #     # scrolls the mouse wheel over the axial view.

    #     # Components

    #     # 	1.	self.axial_slice + steps:
    #     # 	•	self.axial_slice: This is the current index of the axial slice.
    #     # 	•	steps: This is the amount to change the slice index, determined by the scroll direction and magnitude. 
    #     #       Typically, steps is calculated based on the mouse wheel movement (delta // 120).
    #     # 	2.	max(self.axial_slice + steps, 0):
    #     # 	•	This ensures that the new slice index does not go below 0, which is the minimum valid index for the slices. 
    #     #       The max function returns the greater of self.axial_slice + steps and 0.
    #     # 	•	If self.axial_slice + steps is negative (e.g., scrolling up when already at the first slice), this
    #     #       expression ensures the slice index is clamped to 0, preventing underflow.
    #     # 	3.	min(..., self.data.shape[2] - 1):
    #     # 	•	self.data.shape[2] gives the total number of slices along the axial dimension.
    #     # 	•	self.data.shape[2] - 1 is the index of the last axial slice (since array indices start at 0).
    #     # 	•	The min function ensures that the new slice index does not exceed the last slice index. It 
    #     #       returns the smaller of the computed slice index and the last valid slice index.
    #     """
    #     # Determine the scroll direction and steps
    #     delta = event.delta()
    #     steps = delta // 120

    #     # Update the current slice index based on the scroll direction
    #     if source == self.brain_nav.axial_view.getView().scene():
    #         self.brain_nav.axial_slice = min(max(self.brain_nav.axial_slice + steps, 0), self.brain_nav.data.shape[2] - 1)
    #     elif source == self.brain_nav.sagittal_view.getView().scene():
    #         self.brain_nav.sagittal_slice = min(max(self.brain_nav.sagittal_slice + steps, 0), self.brain_nav.data.shape[0] - 1)
    #     elif source == self.brain_nav.coronal_view.getView().scene():
    #         self.brain_nav.coronal_slice = min(max(self.brain_nav.coronal_slice + steps, 0), self.brain_nav.data.shape[1] - 1)

    #     # Ensure the event is fully consumed to prevent default behavior
    #     event.accept()

    #     # Update crosshairs and slices based on the new slice indices
    #     self.brain_nav.orth_view_update.update_crosshairs()
    #     self.brain_nav.orth_view_update.update_slices()
    #     self.brain_nav.metrics.show_metrics(self.brain_nav)

    def handle_scroll(self, event, source):
        """
        Handle scroll events to change slices.

        :param event: The mouse wheel event.
        :param source: The source of the event.

            # Context

        # e.g: self.axial_slice = min(max(self.axial_slice + steps, 0), self.data.shape[2] - 1)

        # Theselines of code are used to update the current axial slice index (self.axial_slice) when the user 
        # scrolls the mouse wheel over the axial view.

        # Components

        # 	1.	self.axial_slice + steps:
        # 	•	self.axial_slice: This is the current index of the axial slice.
        # 	•	steps: This is the amount to change the slice index, determined by the scroll direction and magnitude. 
        #       Typically, steps is calculated based on the mouse wheel movement (delta // 120).
        # 	2.	max(self.axial_slice + steps, 0):
        # 	•	This ensures that the new slice index does not go below 0, which is the minimum valid index for the slices. 
        #       The max function returns the greater of self.axial_slice + steps and 0.
        # 	•	If self.axial_slice + steps is negative (e.g., scrolling up when already at the first slice), this
        #       expression ensures the slice index is clamped to 0, preventing underflow.
        # 	3.	min(..., self.data.shape[2] - 1):
        # 	•	self.data.shape[2] gives the total number of slices along the axial dimension.
        # 	•	self.data.shape[2] - 1 is the index of the last axial slice (since array indices start at 0).
        # 	•	The min function ensures that the new slice index does not exceed the last slice index. It 
        #       returns the smaller of the computed slice index and the last valid slice index.
        """
        # Determine the scroll direction and steps
        delta = event.delta()
        steps = delta // 120  # Typically, each step is 120 units

        template_data = self.brain_nav.templates[self.brain_nav.file_nr_template]['data']

        # Update the current slice index based on the scroll direction
        if source == self.brain_nav.axial_view.getView().scene():
            # Scroll through axial slices
            self.brain_nav.axial_slice = min(max(self.brain_nav.axial_slice + steps, 0), template_data.shape[2] - 1)
        elif source == self.brain_nav.sagittal_view.getView().scene():
            # Scroll through sagittal slices
            self.brain_nav.sagittal_slice = min(max(self.brain_nav.sagittal_slice + steps, 0), template_data.data.shape[0] - 1)
        elif source == self.brain_nav.coronal_view.getView().scene():
            # Scroll through coronal slices
            self.brain_nav.coronal_slice = min(max(self.brain_nav.coronal_slice + steps, 0), template_data.data.shape[1] - 1)

        # Ensure the event is fully consumed to prevent default behavior
        event.accept()

        # Update crosshairs and slices based on the new slice indices
        self.brain_nav.orth_view_update.update_crosshairs()
        self.brain_nav.orth_view_update.update_slices()
        self.brain_nav.metrics.show_metrics()
        self.brain_nav.UIHelp.update_ui_xyz()

    def handle_pan(self, pos, source):
        """
        Handle pan events to move the view based on the mouse position.

        :param pos: The current position of the mouse.
        :param source: The source of the event.
        """
        if self.brain_nav._right_last_pos is None:
            return
        
        # Calculate the change in position since the last recorded mouse position
        delta = pos - self.brain_nav._right_last_pos

        # Iterate over the three views (axial, sagittal, coronal)
        for i, view in enumerate([self.brain_nav.axial_view, self.brain_nav.sagittal_view, self.brain_nav.coronal_view]):
            # Get the view box of the current view
            view_box = view.getView()
            # Get the current visible range of the view box
            view_range = view_box.viewRange()
            # Extract the current x (horizontal) range
            x_range = view_range[0]
            # Extract the current y (vertical) range
            y_range = view_range[1]
            # Calculate the new x range by subtracting the delta.x() from both ends of the current x range
            new_x_range = (x_range[0] - delta.x(), x_range[1] - delta.x())
            # Calculate the new y range by subtracting the delta.y() from both ends of the current y range
            new_y_range = (y_range[0] - delta.y(), y_range[1] - delta.y())
            # Set the new range for the view box, effectively panning the view by the delta amount
            view_box.setRange(xRange=new_x_range, yRange=new_y_range, padding=0)
        
        # Update the last recorded position for the next movement calculation
        self.brain_nav._right_last_pos = pos

        # Update the stored ranges after panning
        self.brain_nav.orth_view_update.get_ranges()

    def show_context_menu(self, event, source):
        """
        Show a context menu when right-clicking on the view.
        
        :param event: The mouse event.
        :param source: The source of the event.
        """
        menu = QMenu()

        # Add the "Select Cluster" action
        select_action_LM = QAction("Select Cluster (Local Minimum)", self.brain_nav)
        select_action_LM.triggered.connect(lambda: self.select_cluster_LM(event, source))
        menu.addAction(select_action_LM)

        select_action_xyz = QAction("Select Cluster (xyz)", self.brain_nav)
        select_action_xyz.triggered.connect(lambda: self.select_cluster_xyz(event, source))
        menu.addAction(select_action_xyz)

        # Show the menu at the position of the right-click
        menu.exec_(event.screenPos())


    def select_cluster_xyz(self, event, source):
        """
        Select the cluster based on the crosshair position and update the tables.
        
        :param event: The mouse event.
        :param source: The source of the event (axial, sagittal, coronal).
        """
        file_nr = self.brain_nav.file_nr
        file_nr_template = self.brain_nav.file_nr_template
        data_table = self.brain_nav.fileInfo[file_nr]['tblARI_df']

        x_ui = self.brain_nav.sagittal_slice 
        y_ui = self.brain_nav.coronal_slice
        z_ui = self.brain_nav.axial_slice

        # x_raw, y_raw, z_raw  = self.brain_nav.fileInfo[file_nr]['mapped_coordinate_matrix_C'][x_ui, y_ui, z_ui]
        x_raw, y_raw, z_raw  = self.brain_nav.aligned_templateInfo[(file_nr, file_nr_template)]['mapped_coordinate_matrix_C'][x_ui, y_ui, z_ui]

        cluster_id = self.brain_nav.fileInfo[file_nr]['img_clus'][x_raw, y_raw, z_raw]

        # row_number      = int(data_table[data_table['Cluster'] == cluster_id].index[0])
        # row_number      = data_table.reset_index(drop=True).index[data_table['Cluster'] == cluster_id][0]
        row_number      = data_table.reset_index(drop=True).index[data_table['Unique ID'] == cluster_id][0]
        cluster_data    = data_table[data_table['Cluster']==cluster_id]

        # Communicate back to main UI and update work station
        self.brain_nav.ui_params['selected_row'] = row_number
        self.brain_nav.ui_params['selected_cluster_id'] = cluster_id

        # updated information in workstation
        self.brain_nav.cluster_ws.update_work_station(self.brain_nav.ui_params['selected_row'])

        # Change hilight on selected row in stats table accordingly
        self.brain_nav.tblARI.reset_highlight()

        # Now update the overlay maps to highlight the selected cluster
        self.brain_nav.orth_view_update.add_overlay_with_transparency(selected_cluster_id=cluster_id)

        # Update 3d viewer
        self.brain_nav.threeDviewer.update_cluster_3d_view(cluster_id)

        # update xyz spinboxes 
        self.brain_nav.UIHelp.update_ui_xyz()


    def select_cluster_LM(self, event, source):
        """
        Select the local minimum of the cluster based on the crosshair position 
        and update the tables and view.

        Parameters:
            event: The mouse event.
            source: The source of the event (axial, sagittal, coronal).
        """
        file_nr = self.brain_nav.file_nr
        file_nr_template = self.brain_nav.file_nr_template
        data_table = self.brain_nav.fileInfo[file_nr]['tblARI_df']

        # Get the current crosshair position in UI space
        x_ui = self.brain_nav.sagittal_slice
        y_ui = self.brain_nav.coronal_slice
        z_ui = self.brain_nav.axial_slice

        # Map the UI coordinates to native space
        # x_raw, y_raw, z_raw = self.brain_nav.fileInfo[file_nr]['mapped_coordinate_matrix_C'][x_ui, y_ui, z_ui]
        x_raw, y_raw, z_raw  = self.brain_nav.aligned_templateInfo[(file_nr, file_nr_template)]['mapped_coordinate_matrix_C'][x_ui, y_ui, z_ui]


        # Determine the cluster ID from the image cluster map
        cluster_id = self.brain_nav.fileInfo[file_nr]['img_clus'][x_raw, y_raw, z_raw]

        # Check if the cluster ID exists in the data table
        if cluster_id in data_table['Unique ID'].values:
            # Get the row corresponding to the selected cluster
            row_number = data_table.reset_index(drop=True).index[data_table['Unique ID'] == cluster_id][0]

            # Move crosshair to position
            # Metrics.follow_cluster_xyz(self, row_number)
            self.brain_nav.metrics.follow_cluster_xyz(row_number)

            # updated information in workstation
            self.brain_nav.cluster_ws.update_work_station(row_number)

            # Change hilight on selected row in stats table accordingly
            self.brain_nav.tblARI.reset_highlight()

            # Update 3d viewer
            self.brain_nav.threeDviewer.update_cluster_3d_view(cluster_id)

            # # Now update the overlay maps to highlight the selected cluster
            # self.brain_nav.orth_view_update.add_overlay_with_transparency(selected_cluster_id=cluster_id)