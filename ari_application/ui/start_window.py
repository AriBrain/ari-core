import nibabel as nib
import numpy as np
import matplotlib.pyplot as plt
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QFormLayout, QHBoxLayout, 
                             QLineEdit, QComboBox, QFileDialog, QLabel,  QGridLayout, QInputDialog)
from PyQt5.QtGui import QPalette, QBrush, QPixmap, QFont, QImage, QColor
from PyQt5.QtCore import Qt
import os
from ari_application.ui.main_window import BrainNav
import pickle


class StartWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Set the size of the window to be large
        self.setGeometry(100, 100, 1600, 800)

        # Set up the main layout (renamed to avoid conflict with layout() method)
        self.main_layout = QVBoxLayout(self)

        # Set degrees of freedom to none. Will be overwritten when t-map is detected/selected
        self.tdf = None

        # Create a container for the buttons with a gray background
        button_container = QWidget(self)
        button_container.setFixedSize(350, 300)  # Slightly bigger than the combined size of both buttons
        button_container.setStyleSheet("background-color: rgba(30, 30, 30, 240); border-radius: 15px;")  # Dark gray background with slight transparency and rounded corners

        # Create the New Project and Load Project buttons
        self.new_project_button = QPushButton('New Project', self)
        self.new_project_button.setFont(QFont('Arial', 24))  # Set font size for large buttons
        self.new_project_button.setFixedSize(300, 100)  # Set size for large buttons
        self.new_project_button.clicked.connect(self.open_new_project)
        self.new_project_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50; /* Green background */
                color: white;
                border-radius: 10px;
            }
            QPushButton:hover {
                background-color: #45a049; /* Darker green on hover */
            }
        """)

        self.load_project_button = QPushButton('Load Project', self)
        self.load_project_button.setFont(QFont('Arial', 24))  # Set font size for large buttons
        self.load_project_button.setFixedSize(300, 100)  # Set size for large buttons
        self.load_project_button.clicked.connect(self.load_project)
        self.load_project_button.setStyleSheet("""
            QPushButton {
                background-color: #008CBA; /* Blue background */
                color: white;
                border-radius: 10px;
            }
            QPushButton:hover {
                background-color: #007BB5; /* Darker blue on hover */
            }
        """)

        # Set up the layout for the buttons inside the container
        self.button_layout = QVBoxLayout(button_container)
        self.button_layout.addWidget(self.new_project_button, alignment=Qt.AlignCenter)
        self.button_layout.addWidget(self.load_project_button, alignment=Qt.AlignCenter)

        # Add the button container to the main layout
        self.main_layout.addStretch()
        self.main_layout.addWidget(button_container, alignment=Qt.AlignCenter)
        self.main_layout.addStretch()

        # Set the background image with slight transparency
        self.set_background_image(os.path.join(os.path.dirname(__file__), '..', 'public', 'logo_bw.png'))

        # Initialize placeholders for orthogonal views and header information
        self.sagittal_view = QLabel(self)
        self.coronal_view = QLabel(self)
        self.axial_view = QLabel(self)
        self.header_info = QLabel(self)

    def set_background_image(self, image_path):
        # Load the image
        oImage = QImage(image_path)

        # Scale the image to maintain aspect ratio while filling the screen
        sImage = oImage.scaled(self.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)

        # Apply slight transparency to the image
        for y in range(sImage.height()):
            for x in range(sImage.width()):
                color = QColor(sImage.pixel(x, y))
                alpha = 40  # Adjust this value to control visibility (0 = fully transparent, 255 = fully opaque)
                sImage.setPixelColor(x, y, QColor(color.red(), color.green(), color.blue(), alpha))

        # Set the scaled and processed image as the background
        palette = QPalette()
        palette.setBrush(QPalette.Window, QBrush(QPixmap.fromImage(sImage)))
        self.setPalette(palette)

    def open_new_project(self):
        # Remove the New Project and Load Project buttons
        self.new_project_button.setParent(None)
        self.load_project_button.setParent(None)

        # Clear the main layout completely
        while self.main_layout.count():
            item = self.main_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()  # Ensure widget is deleted properly
            else:
                del item

        # Reset the layout's properties (margins, spacing)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Slide the window to the left and show import options
        self.transition_to_import_data()

    def load_project(self):
        """Load a previously saved .ari project file and launch the main application."""
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Load Project", "", "ARIBrain Project (*.ari);;All Files (*)", options=options)

        if file_name:
            with open(file_name, "rb") as file:
                project_data = pickle.load(file)

            # Unpack saved data
            fileInfo             = project_data['fileInfo']
            atlasInfo            = project_data['atlasInfo']
            file_nr              = project_data['file_nr']
            file_nr_template     = project_data['file_nr_template']
            data_bg_index        = project_data['data_bg_index']
            aligned_statMapInfo  = project_data['aligned_statMapInfo']
            aligned_templateInfo = project_data['aligned_templateInfo']
            ui_params            = project_data['ui_params']
            templates            = project_data['templates']
            statmap_templates    = project_data['statmap_templates']
            ranges               = project_data['ranges']
            stat_image_names     = project_data.get('stat_image_names', [])
            template_names       = project_data.get('template_names', [])
            start_input          = project_data['start_input']

            # Pass all data into one dictionary
            data_package = {
                'fileInfo': fileInfo,
                'atlasInfo': atlasInfo,
                'file_nr': file_nr,
                'file_nr_template': file_nr_template,
                'data_bg_index': data_bg_index,
                'aligned_statMapInfo': aligned_statMapInfo,
                'aligned_templateInfo': aligned_templateInfo,
                'ui_params': ui_params,
                'templates': templates,
                'statmap_templates': statmap_templates,
                'ranges': ranges,
                'start_input': start_input,
                'stat_image_names': stat_image_names,
                'template_names': template_names
            }

            # Create and show the main window
            self.main_window = BrainNav(start_input, load_data=True, data2load=data_package)
            self.main_window.show()
            self.close()
            
    def transition_to_import_data(self):

        # Create the Import Data form
        form_layout = QFormLayout()

        # Add header label for "Load statistic file"
        header_label = QLabel("Load statistic file:")
        header_label.setFont(QFont('Arial', 12, QFont.Bold))
        form_layout.addRow(header_label)

        # Load statistic file with Browse button
        self.file_input = QLineEdit(self)
        self.file_input.setStyleSheet("background-color: white; color: black; padding: 5px; border: 1px solid gray;")

        browse_button = QPushButton('Browse', self)
        browse_button.clicked.connect(self.browse_file)
        browse_button.setStyleSheet("""
            QPushButton {
                background-color: #F5F5F5; /* Broken white */
                color: black;
                padding: 5px; 
                border: 1px 
                solid gray;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #A9A9A9; /* Dark grey on hover */
            }
        """)
        browse_button.setFixedWidth(50)
        file_layout = QHBoxLayout()
        file_layout.addWidget(self.file_input)
        file_layout.addWidget(browse_button)
        form_layout.addRow(file_layout)

        # File type dropdown menu
        # 1. Create a label widget with the text "Select File Type:".
        header_dropdown = QLabel("Select File Type:")
        # 2. Set the font for the label to Arial, size 12, and make it bold.
        header_dropdown.setFont(QFont('Arial', 12, QFont.Bold))
        # 3. Add the label to the form layout as a new row. This places the label in the layout.
        form_layout.addRow(header_dropdown)
        # 4. Create a combo box widget (drop-down menu) to allow the user to select the file type.
        self.file_type_combo = QComboBox(self)
        # 5. Add items (options) to the combo box: 'Select Map', 'z-map', 't-map', and 'p-map'.
        self.file_type_combo.addItems(['Select Map', 'z-map', 't-map', 'p-map'])
        # 6. Set the style of the combo box to have a white background with black text.
        #    Also, ensure that the dropdown items are highlighted with light grey when hovered over.
        # self.file_type_combo.setStyleSheet("""
        #     QComboBox {
        #         background-color: white; /* White background for the combo box */
        #         color: black; /* Black text */
        #         padding: 5px; /* Padding inside the combo box */
        #         border: 1px solid gray; /* Gray border around the combo box */
        #     }
        #     ComboBox QAbstractItemView::item {
        #         background-color: white; /* White background for dropdown items */
        #         color: black; /* Black text for dropdown items */
        #     }                               
        #     QComboBox QAbstractItemView::item:hover {
        #         selection-color: red;
        #         selection-background-color: blue;
        #         # padding: 5px; /* Padding inside the combo box */
        #         # border: 1px solid gray; /* Gray border around the combo box */
        #     }
        # """)
        self.file_type_combo.setStyleSheet("background-color: white; color: black; padding: 5px; border: 1px solid gray;")

        # 6. Connect the combo box change signal to a function
        self.file_type_combo.currentIndexChanged.connect(self.check_maptype)

        # 7. Add the combo box to the form layout as a new row. This places the combo box below the label.
        form_layout.addRow(self.file_type_combo)

        # Initialize the warning label
        self.warning_label = QLabel("")
        self.warning_label.setStyleSheet("color: red;")
        self.warning_label.hide()  # Keep it hidden initially
        form_layout.addRow(self.warning_label)

        self.file_type_combo.currentIndexChanged.connect(self.hide_warning_label)

        # Background dropdown menu
        header_background = QLabel("Select Background:")
        header_background.setFont(QFont('Arial', 12, QFont.Bold))
        form_layout.addRow(header_background)
        self.background_combo = QComboBox(self)
        self.background_combo.addItems(['Raw Data', 'MNI Template T1', 'MNI Template GM', 'Upload Template'])
        self.background_combo.setStyleSheet("background-color: white; color: black; padding: 5px; border: 1px solid gray;")
        form_layout.addRow(self.background_combo)

        # Create a container for the form and set its background
        form_container = QWidget(self)
        form_container.setFixedSize(350, 300)
        form_container.setStyleSheet("background-color: rgba(30, 30, 30, 240); border-radius: 15px;")
        form_container_layout = QVBoxLayout(form_container)
        form_container_layout.addLayout(form_layout)

        # Add the "Next" button to the form container
        next_button = QPushButton('Next', self)
        next_button.setFixedSize(60, 40)
        next_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50; /* Green background */
                color: white;
            }
            QPushButton:hover {
                background-color: #45a049; /* Darker green on hover */
            }
        """)
        next_button.clicked.connect(self.next_button_pressed)  

        form_container_layout.addStretch()
        form_container_layout.addWidget(next_button, alignment=Qt.AlignRight)

        # Create a container for the orthogonal views and set its background
        views_container = QWidget(self)
        views_container.setFixedSize(350, 350)  # Adjust size for 2x2 layout
        views_container.setStyleSheet("background-color: rgba(30, 30, 30, 240); border-radius: 15px;")

        # Create a grid layout for the orthogonal views inside the views container
        views_layout = QGridLayout(views_container)
        views_layout.addWidget(self.sagittal_view, 0, 0)  # Top-left
        views_layout.addWidget(self.coronal_view, 0, 1)   # Top-right
        views_layout.addWidget(self.axial_view, 1, 0)     # Bottom-left
        views_layout.addWidget(self.header_info, 1, 1)    # Bottom-right

        # Ensure the QLabel for header_info has a white background
        self.header_info.setStyleSheet("background-color: white; color: black; padding: 10px;")

        # Create a horizontal layout to hold both the form and views containers side by side
        container_layout = QHBoxLayout()
        container_layout.addWidget(form_container)
        container_layout.addWidget(views_container)
        container_layout.setSpacing(20)  # Adjust the spacing between the containers as needed

        # Create a wrapper container to center the two containers together
        wrapper_container = QWidget(self)
        wrapper_container_layout = QHBoxLayout(wrapper_container)
        wrapper_container_layout.addStretch()
        wrapper_container_layout.addLayout(container_layout)
        wrapper_container_layout.addStretch()

        # Add the wrapper container to the main layout, centered
        self.main_layout.addStretch()  # Add stretch to push content to vertical center
        self.main_layout.addWidget(wrapper_container)
        self.main_layout.addStretch()  # Add stretch to push content to vertical center
        
    def browse_file(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(self, "Select NIfTI File", "", "NIfTI Files (*.nii *.nii.gz);;All Files (*)", options=options)

        if file_path:
            if not file_path.endswith('.nii'):
                self.file_input.setText("Invalid file type. Please select a .nii file.")
                return
            try:
                data = nib.load(file_path)
                self.file_input.setText(file_path)
                self.display_orthogonal_views(data)
                
                # Determine the map type and update the combo box
                # map_type = self.check_file_type(file_path)
                # index = self.file_type_combo.findText(map_type, Qt.MatchFixedString)
                # if index >= 0:
                #     self.file_type_combo.setCurrentIndex(index)
                self.update_menu_selection(file_path)

            except Exception as e:
                self.file_input.setText(f"Error loading file: {str(e)}")

        
    def update_menu_selection(self, file_path):
        # Determine the file type and set menu_selection
        type, menu_selection = self.check_file_type(file_path)
        self.file_type = type

        # Set the combo box to the determined menu_selection
        self.file_type_combo.setCurrentText(menu_selection)

        # If menu_selection is 'Select Map Type', show the warning message
        if menu_selection == 'Select Map Type':
            self.warning_label.setText("Unable to determine file type. Select a map type")
            self.warning_label.show()
        else:
            # Clear the warning message if a valid type is determined
            self.warning_label.hide()
    
    def check_file_type(self,file_path):
        data = nib.load(file_path)
        header = data.header

        # Set type based on intent_code
        intent_code = header.get_intent()[0]
        type = None
        if intent_code != 0:
            if intent_code == 't test':
                type = 't'
            elif intent_code == 'f test':
                type = 'f'
            elif intent_code == 'z score':
                type = 'z'
            elif intent_code == 'p-value':
                type = 'p'
            else:
                type = 'None'
            print(f"Determined intent_code: {type}")
        else:
            # Determine type based on description
            descrip = header['descrip'].tostring().decode('utf-8')
            print(descrip)
            if "SPM{T" in descrip:
                type = 't'
            print(f"Determined descrip: {type}")

        # Set the menu selection based on determined type
        if type == 't':
            menu_selection = 't-map'
            self.ask_for_degrees_of_freedom()
        elif type == 'z':
            menu_selection = 'z-map'
        elif type == 'p':
            menu_selection = 'p-map'
        else:
            menu_selection = 'Select Map Type'

        return type, menu_selection
    
    def hide_warning_label(self):
        # Hide the warning label if a valid selection is made
        if self.file_type_combo.currentText() != 'Select Map Type':
            self.warning_label.hide()


    def check_maptype(self):
        # Check if the selected item is "t-map"
        selected_item = self.file_type_combo.currentText()
        if selected_item == 't-map':
            # Trigger the degrees of freedom input dialog
            self.ask_for_degrees_of_freedom()

    def ask_for_degrees_of_freedom(self):
        # Open a dialog to ask the user for degrees of freedom
        df, ok = QInputDialog.getInt(self, "Degrees of Freedom", "Enter the degrees of freedom:", 1, 1, 100)
        if ok:
            self.tdf = df
            print(f"Degrees of Freedom: {df}")
        else:
            print("User cancelled the input")


    def display_orthogonal_views(self, img):
        data = img.get_fdata().T

        # Sagittal view
        self.plot_single_view(self.sagittal_view, data[data.shape[0] // 2, :, :], '')

        # Coronal view
        self.plot_single_view(self.coronal_view, data[:, data.shape[1] // 2, :], '')

        # Axial view
        self.plot_single_view(self.axial_view, data[:, :, data.shape[2] // 2], '')

        # Display relevant header information in the bottom-right QLabel
        header_info_text = f"Dims: {img.shape}\nVoxel Size: {img.header.get_zooms()}\nSpace: {img.get_data_dtype()}"
        self.header_info.setText(header_info_text)


    def plot_single_view(self, label, data_slice, title):
        fig, ax = plt.subplots(figsize=(2, 2))
        ax.imshow(data_slice, cmap='gray',  origin="lower")
        ax.set_title(title)
        ax.axis('off')

        # Update QLabel placeholder with the Matplotlib figure
        self.update_label_with_figure(label, ax)

    def update_label_with_figure(self, label, ax):
        # Convert Matplotlib figure to QPixmap and display in QLabel
        ax.figure.canvas.draw()
        width, height = ax.figure.canvas.get_width_height()
        # im = ax.figure.canvas.tostring_rgb()
        im = ax.figure.canvas.buffer_rgba()

        # image = QImage(im, width, height, QImage.Format_RGB888)
        image = QImage(im, width, height, QImage.Format_RGBA8888)
        pixmap = QPixmap.fromImage(image)
        label.setPixmap(pixmap.scaled(label.size(), Qt.KeepAspectRatio))

    def next_button_pressed(self):
        # Initiate start_input dictionary
        start_input = {}
         
        # Retrieve the path from the file input field
        start_input['data_dir'] = self.file_input.text()

        # Retrieve the selected file type from the combo box
        start_input['map_type'] = self.file_type_combo.currentText()
        start_input['file_type'] = self.file_type
        start_input['tdf'] = self.tdf

        # We always have the same template dir (there are the default templates)
        start_input['template_dir'] = os.path.join(os.path.dirname(__file__), '..', 'public/templates')
        start_input['template_mask_fp'] = os.path.join(os.path.dirname(__file__), '..', 'public/template_masks' ,'mni_template_icbm152_inmask.nii')


        # Define the fileype in case auto detection returned None. 
        # Here we use the manual selection to evaluate.
        # if start_input['file_type'] == 'None':
        # Remove the filetype check, because while filetype might already be succesfully determined,  the user might still want 
        # overwrite the filetype for some reason.
        if start_input['map_type'] == 't-map':
            start_input['file_type'] = 't'
        elif start_input['map_type'] == 'z-map':
            start_input['file_type'] = 'z'
        elif start_input['map_type'] ==  'p-map':
            start_input['file_type'] = 'p'

        # Retrieve the selected background template option from the combo box
        background_selection = self.background_combo.currentText()
        if background_selection == 'Raw Data':
            start_input['show_template'] = 'raw_data'
            
        elif  background_selection == 'MNI Template T1':
            start_input['show_template'] = 'mni_icbm152_t1.nii'

        elif  background_selection == 'MNI Template GM':
            start_input['show_template'] = 'mni_icbm152_gm.nii'

        elif background_selection == 'Upload Template':
            start_input['show_template'] = 'user_template'
      
        # Instantiate the main window and pass the start_input dictionary
        self.main_window = BrainNav(start_input)

        self.main_window.show()

        # Close the current start window
        self.close()
        
        # Run ARI analysis immediately on the NEXT button click
        self.main_window.ARI.runARI()

# def set_dark_mode(app): 
#     """Apply a dark mode palette to the application."""
#     dark_palette = QPalette()

#     # Base colors for the dark theme
#     dark_palette.setColor(QPalette.Window, QColor(53, 53, 53))
#     dark_palette.setColor(QPalette.WindowText, Qt.white)
#     dark_palette.setColor(QPalette.Base, QColor(35, 35, 35))
#     dark_palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
#     dark_palette.setColor(QPalette.ToolTipBase, Qt.white)
#     dark_palette.setColor(QPalette.ToolTipText, Qt.white)
#     dark_palette.setColor(QPalette.Text, Qt.white)
#     dark_palette.setColor(QPalette.Button, QColor(53, 53, 53))
#     dark_palette.setColor(QPalette.ButtonText, Qt.white)
#     dark_palette.setColor(QPalette.BrightText, Qt.red)
    
#     # The highlight color (for selected items in tables, lists, etc.)
#     dark_palette.setColor(QPalette.Highlight, QColor(142, 45, 197).lighter())
#     dark_palette.setColor(QPalette.HighlightedText, Qt.black)

#     # Apply the dark palette to the application
#     app.setPalette(dark_palette)
            

if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    
    # app = QApplication(sys.argv)
    # window = StartWindow()
    # window.show()
    # sys.exit(app.exec_())

     # Create the application
    app = QApplication(sys.argv)

    # Apply dark mode
    # set_dark_mode(app)

    # Create and show the StartWindow
    window = StartWindow()
    window.show()

    # Execute the application
    sys.exit(app.exec_())