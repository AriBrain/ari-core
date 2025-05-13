# === Qt Widgets & Core ===
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QSlider, QLineEdit
)

# === Project-Specific ===
from resources.styles import Styles  # For button and slider styling

class WBTing(QWidget):
    """
    WBTing (Whole Brain Thresholding Interface) manages the UI elements and thresholding logic 
    for global statistical map filtering using either TDP-based or Z-score based thresholds.

    Core Responsibilities:
    -----------------------
    - Create and manage a dedicated control panel for adjusting the whole-brain threshold.
    - Synchronize user input from a slider, buttons, or text field to update cluster overlays and metrics.
    - Handle switching between thresholding modes (TDP-based vs Z-score based), including reloading previous settings.
    - Communicate updates to other modules such as Metrics, TblARI, and the overlay engine.
    - Provide UI feedback via a log message box and enforce valid value ranges.

    Features:
    ---------
    - Fine-grained threshold adjustment using buttons (±0.01), slider, or direct numeric input.
    - Dynamic min/max slider bounds depending on loaded data and selected thresholding method.
    - Styled, modular Qt widgets grouped into responsive containers.
    - Interactive and non-intrusive feedback system to guide user input.

    Key UI Components:
    ------------------
    - `threshold_slider1`: Horizontal slider for thresholding.
    - `tdp_textbox1`: Manual input field for threshold value.
    - `minus_button1`, `plus_button1`: Stepwise adjusters.
    - `reset_button2`: Applies entered threshold value.
    - `threshold_container1`: The final widget container to be placed into the UI.

    This class provides a clean and user-friendly interface for threshold control, forming 
    a central part of the cluster filtering pipeline in the BrainNav application.
    """

    def __init__(self, BrainNav):
        super().__init__()  # Initialize the QWidget

        self.brain_nav = BrainNav

        # Optional: assign commonly accessed properties for brevity
        # self.fileInfo   = self.brain_nav.fileInfo
        self.file_nr    = self.brain_nav.file_nr
        self.ui_params  = self.brain_nav.ui_params
        # self.metrics    = self.brain_nav.metrics

    @property
    def fileInfo(self):
        return self.brain_nav.fileInfo
    
    @property
    def metrics(self):
        return self.brain_nav.metrics
    

    def whole_brain_tdp_slider(self):
        """
        Initializes and constructs the UI elements for the Whole Brain Thresholding (TDP-based) control group.

        This method creates a visual threshold controller consisting of:
        - A horizontal slider for adjusting the threshold value between `mintdp` and 1.0.
        - A `+` and `-` button for incremental adjustments (±0.01).
        - A text input box for manually entering the threshold value.
        - A `Run` button to apply the threshold defined in the text box.

        The components are grouped into:
        - A **right container** with the minus button, slider, and plus button.
        - A **left container** with the TDP text box and Run button.
        - Both containers are horizontally aligned in `threshold_layout1` and embedded in a main QWidget (`threshold_container1`).

        Features:
        ---------
        - Signals are connected to the `update_threshold_label` function to update cluster overlays and metrics.
        - The slider uses a default value of 0.75 and operates in steps of 0.01.
        - The lower bound `mintdp` is updated dynamically by the ARI analysis.

        Attributes Created:
        -------------------
        - `self.mintdp` (float): Lower bound for the TDP threshold slider.
        - `self.threshold_slider1` (QSlider): Slider for TDP adjustment.
        - `self.tdp_textbox1` (QLineEdit): Text input for direct threshold entry.
        - `self.minus_button1` (QPushButton): Decreases threshold by 0.01.
        - `self.plus_button1` (QPushButton): Increases threshold by 0.01.
        - `self.reset_button2` (QPushButton): Applies threshold from the text box.
        - `self.left_container` (QWidget): Holds textbox and run button.
        - `self.right_container` (QWidget): Holds slider and increment buttons.
        - `self.threshold_container1` (QWidget): Final container used in the layout.

        Notes:
        ------
        - The styling of each component follows dark theme conventions for visual consistency.
        - This method is typically called during UI initialization to populate the thresholding tab.
        """
        # First Control Group (Whole Brain Threshold)
        self.mintdp = 0.0  # Initial lower bound (updated dynamically)

        # Minus Button
        self.minus_button1 = QPushButton('-')
        self.minus_button1.setCursor(Qt.PointingHandCursor)
        self.minus_button1.setStyleSheet(Styles.minus_button_styling)
        self.minus_button1.setFixedSize(40, 40)
        self.minus_button1.clicked.connect(lambda: self.update_threshold_label(value=-0.01))

        # Plus Button
        self.plus_button1 = QPushButton('+')
        self.plus_button1.setCursor(Qt.PointingHandCursor)
        self.plus_button1.setStyleSheet(Styles.plus_button_styling)
        self.plus_button1.setFixedSize(40, 40)
        self.plus_button1.clicked.connect(lambda: self.update_threshold_label(value=0.01))

        # Threshold Slider
        self.threshold_slider1 = QSlider(Qt.Horizontal)
        self.threshold_slider1.setRange(int(self.mintdp * 100), 100)
        self.threshold_slider1.setValue(75)
        self.threshold_slider1.setSingleStep(1)
        self.threshold_slider1.setTickInterval(10)
        self.threshold_slider1.setTickPosition(QSlider.TicksBelow)
        self.threshold_slider1.setCursor(Qt.PointingHandCursor)
        self.threshold_slider1.setFixedSize(200, 40)
        self.threshold_slider1.setTracking(False)  # Prevents updates while hovering
        self.threshold_slider1.valueChanged.connect(self.update_threshold_label)
        self.threshold_slider1.setStyleSheet(Styles.cluster_slider_styling)

        # TDP Textbox (larger, bold, different color)
        self.tdp_textbox1 = QLineEdit("0.75")
        self.tdp_textbox1.setFixedWidth(80)  # Increased width
        self.tdp_textbox1.setAlignment(Qt.AlignCenter)

        # Parent set overrides this stylesheet. Leave it for now.
        font = QFont("Arial", 20, QFont.Bold)
        self.tdp_textbox1.setFont(font)
        self.tdp_textbox1.setStyleSheet("""
            QLineEdit { 
                font-size: 20px; 
                font-weight: bold; 
                color: white; 
                background-color: #1e2b38; 
                # background-color: #091c13;
                border-radius: 5px; 
                padding: 5px;
            }
        """)
        self.tdp_textbox1.returnPressed.connect(lambda: self.update_threshold_label(float(self.tdp_textbox1.text())))

        # Run Button (spaced slightly to the right)
        self.reset_button2 = QPushButton('Run')
        self.reset_button2.setCursor(Qt.PointingHandCursor)
        self.reset_button2.setStyleSheet(Styles.runARI_button_styling)
        self.reset_button2.setFixedSize(80, 40)
        self.reset_button2.clicked.connect(lambda: self.update_threshold_label(float(self.tdp_textbox1.text())))

         # **Left Layout (Textbox + Run Button)**
        self.left_container = QWidget()
        left_layout = QHBoxLayout()
        left_layout.addWidget(self.tdp_textbox1)
        left_layout.addSpacing(15)
        left_layout.addWidget(self.reset_button2)
        left_layout.setAlignment(Qt.AlignLeft)  # Align to the left
        # self.left_container.setLayout(left_layout)

        # **Right Layout (Slider + Buttons)**
        self.right_container = QWidget()
        right_layout = QHBoxLayout()
        right_layout.addWidget(self.minus_button1)
        right_layout.addWidget(self.threshold_slider1)
        right_layout.addWidget(self.plus_button1)
        right_layout.setAlignment(Qt.AlignRight)  # Align to the right
        # self.right_container.setLayout(right_layout)

        # Create separate containers for styling
        self.left_container = QWidget()
        self.left_container.setAttribute(Qt.WA_StyledBackground, True)
        self.left_container.setStyleSheet("background-color: #091c13; border-radius: 10px; padding: 5px;")
        self.left_container.setLayout(left_layout)

        self.right_container = QWidget()
        self.right_container.setAttribute(Qt.WA_StyledBackground, True)
        self.right_container.setStyleSheet("background-color: #091c13; border-radius: 10px; padding: 5px;")
        self.right_container.setLayout(right_layout)

        # Combine both containers into a horizontal layout
        self.threshold_layout1 = QHBoxLayout()
        self.threshold_layout1.addWidget(self.right_container)
        self.threshold_layout1.addSpacing(80)  # Adjust spacing between groups
        self.threshold_layout1.addWidget(self.left_container)
        self.threshold_layout1.setAlignment(Qt.AlignLeft)

        # Main container
        self.threshold_container1 = QWidget()
        self.threshold_container1.setLayout(self.threshold_layout1)

        return self.threshold_container1  # Return the main container for use in the UI

    # **Function to Update Advisory Text**
    def update_threshold_option(self):
        """
        Updates the UI elements and internal state based on the selected whole brain thresholding method.

        This function dynamically adjusts the slider range, text box values, cluster table, and overlay 
        depending on whether "TDP-based" or "Z-score based" thresholding is selected. It ensures that the 
        user is presented with the appropriate controls and data for the chosen method.

        - For "TDP-based" thresholding:
            - Slider range is set based on the minimum TDP (`mintdp`) to 1.
            - If a previous TDP threshold exists, the slider and text box are set to that value.
            - The table and overlay are updated based on the last computed TDP-based cluster list.
            - A message indicating the current TDP threshold is logged to the message box.

        - For "Z-score based" thresholding:
            - Slider range is set based on `zmin` and `zmax` stored in the fileInfo.
            - If a previous Z-score threshold exists, the slider and text box are set to that value.
            - The table and overlay are updated based on the last computed Z-score based cluster list.
            - A message indicating the current Z-score threshold is logged to the message box.

        Signals for the slider and textbox are temporarily blocked to prevent unwanted triggers during initialization.
        Any selected cluster from the previous thresholding method is cleared when switching methods.

        Attributes Accessed:
            self.file_nr (int): Index of the currently active file.
            self.fileInfo (dict): Dictionary storing file-specific data, including thresholds and cluster lists.
            self.metrics (Metrics): Instance of the Metrics class for updating overlays and cluster tables.
            self.ui_params (dict): UI state parameters, including selected cluster ID.

        Messages Logged:
            - Whole Brain TDP value when TDP-based thresholding is selected.
            - Whole Brain Z-score value when Z-score based thresholding is selected.

        """
        file_nr = self.file_nr

        # Get currently selected threshold option from the dropdown
        selected_option     = self.brain_nav.initiate_tabs.thresholding_dropdown.currentText()
        
        # Update the advisory text based on the selected option
        self.brain_nav.initiate_tabs.advisory_text.setText(self.brain_nav.initiate_tabs.advisory_messages.get(selected_option, ""))

        # Block signals to prevent triggering the valueChanged signal
        self.threshold_slider1.blockSignals(True)
        self.tdp_textbox1.blockSignals(True)

        # Update slider configuration depending on selection
        if selected_option == "TDP-based":
            self.threshold_slider1.setRange(int(self.mintdp * 100), 100)
           
            if 'tdp_threshold' in self.fileInfo[file_nr]:
                tdpthresh = self.fileInfo[file_nr]['tdp_threshold']
                
                self.threshold_slider1.setValue(int(tdpthresh*100))
                self.tdp_textbox1.setText(str(tdpthresh))

                # get most recent whole brain tdp clustermap and use it to reinstate the UI elements
                # Recompute table data
                clusterlist = self.fileInfo[file_nr]['tdp_whole_brain_clusterlist']
                ord_clusterlist, _, tblARI_df, _ = self.metrics.prepare_tblARI(clusterlist)
                _, _, tblARI_df = self.brain_nav.metrics.update_clust_img(ord_clusterlist, tblARI_df)
                self.brain_nav.tblARI.update_table(tblARI_df)

                # Restore overlay
                self.metrics.update_overlay_image(file_nr, cluster_label = None)

                # Send the current tdp to the message box
                self.brain_nav.message_box.log_message(f"<span style='color: white;'>Whole Brain TDP = {tdpthresh:.2f}</span>")

            else:        
                self.threshold_slider1.setValue(75)
                self.tdp_textbox1.setText("0.75")

        elif selected_option == "Z-score based":
            zmin = self.fileInfo[file_nr]['zmin'] 
            zmax = self.fileInfo[file_nr]['zmax'] 
            
            self.threshold_slider1.setRange(int(zmin*100), int(zmax*100)) 

            if 'zscore_threshold' in self.fileInfo[self.file_nr]:
                zthresh = self.fileInfo[self.file_nr]['zscore_threshold']

                self.threshold_slider1.setValue(int(zthresh*100))
                self.tdp_textbox1.setText(str(zthresh))

                # get most recent whole brain zscore threshold clustermap and use it to reinstate the UI elements
                # Recompute table data
                clusterlist = self.fileInfo[self.file_nr]['zscore_whole_brain_clusterlist']
                tblARI_raw = self.fileInfo[self.file_nr]['tblARI_raw']

                ord_clusterlist, _, tblARI_df, _ = self.metrics.prepare_tblARI(clusterlist)
                _, _, tblARI_df = self.metrics.update_clust_img(ord_clusterlist, tblARI_df)
                
                # Create a mapping from Cluster to Active Proportion
                tdp_mapping = dict(zip(tblARI_raw['Cluster'], tblARI_raw['Active Proportion'].round(2)))
                
                # Update TDP column directly (inplace), using the mapping
                tblARI_df['TDP'] = tblARI_df['Cluster'].map(tdp_mapping)
                self.brain_nav.tblARI.update_table(tblARI_df)

                # Restore overlay
                self.metrics.update_overlay_image(file_nr, cluster_label = None)
                
                # Send the current tdp to the message box
                self.brain_nav.message_box.log_message(f"<span style='color: white;'>Whole Brain Z-score = {zthresh:.2f}</span>")

            else:        
                self.threshold_slider1.setValue(int(zmin*100))  # Example initial value
                self.tdp_textbox1.setText(str(zmin))  # Example initial Z-score text
                

        # Unblock signals after updating
        self.threshold_slider1.blockSignals(False)
        self.tdp_textbox1.blockSignals(False)

        # Remove selected cluster if any
        self.ui_params['selected_cluster_id'] = None

    def update_tdp_bounds(self):
        """
        Update the lower bound of the TDP slider when ARI finishes.
        """
        file_nr         = self.file_nr  # Get the current file index
        cluster_slider  = self.brain_nav.cluster_ws.cluster_slider

        if 'mintdp' in self.fileInfo[file_nr]:  # Check if ARI has computed mintdp
            self.mintdp = self.fileInfo[file_nr]['mintdp']
            print('mintdp updated:' + str(self.mintdp))
        else:
            self.mintdp = 0.0  # Default to 0 if not available

        # Update the slider range dynamically
        cluster_slider.setRange(int(self.mintdp * 100), 100)

        # Ensure the current slider value is still within bounds
        current_value = cluster_slider.value() / 100
        if current_value < self.mintdp:
            cluster_slider.setValue(int(self.mintdp * 100))  # Reset to min if out of range

        # Update the text box display
        self.brain_nav.cluster_ws.tdp_textbox.setText(f"{cluster_slider.value() / 100:.2f}")
    

    def update_threshold_label(self, value):
        """
        Updates the threshold label, slider, and textbox values, and applies the selected threshold to the current statistical map.

        This function is called when the user interacts with:
        - The slider (threshold_slider1)
        - The text input box (tdp_textbox1)
        - The increment/decrement buttons (plus_button1, minus_button1)
        - The reset button (reset_button2)

        The update flow is as follows:
        - Determines the selected thresholding method ("TDP-based" or "Z-score based") from the dropdown.
        - Retrieves the current threshold value and the UI element that triggered the update.
        - Checks the updated value against the allowed bounds (TDP range or Z-score range).
        - If the new value is out of bounds, it is clamped to the nearest valid value and a warning message is logged to the message box.
        - Updates both the slider and textbox to reflect the validated threshold value.
        - Finally, it updates the cluster overlay and table using the `control_threshold` method in the `Metrics` class.

        Parameters:
            value (float): The new threshold value or adjustment (depending on the sender).

        UI Components Updated:
            - `tdp_textbox1`: Text input for the threshold value.
            - `threshold_slider1`: Slider for adjusting the threshold.
            - Message log receives warnings and updates.

        Thresholding Modes:
            - TDP-based: Threshold value represents a True Discovery Proportion (0 to 1).
            - Z-score based: Threshold value represents a statistical Z-score (range depends on the loaded data).

        Attributes Accessed:
            - self.fileInfo: Stores per-file data, including previously computed clusters and thresholds.
            - self.metrics: Instance of the Metrics class for handling cluster computation and visualization updates.

        Warning Messages:
            - Logged when the user tries to exceed the allowed threshold range.
            - Example: "Warning: Lower limit reached at 0.25, increase threshold value."

        Notes:
            - Signal blocking is used to prevent recursive updates between slider and textbox.
            - Handles both absolute value updates (textbox/slider) and incremental updates (buttons).

        """
        selected_option =  self.brain_nav.initiate_tabs.thresholding_dropdown.currentText()
        sender = self.sender()  # Get the object that emitted the signal
        
        multiplier = 100  # Multiplier to convert between slider and textbox values

        current_threshold = float(self.tdp_textbox1.text())

        # Check if updated value is still within bounds, if not don't update and send message
        # Determine bounds based on selected thresholding method
        if selected_option == "TDP-based":
            min_bound = self.fileInfo[self.file_nr]['mintdp']
            max_bound = 1.0
        elif selected_option == "Z-score based":
            min_bound = self.fileInfo[self.file_nr]['zmin']
            max_bound = self.fileInfo[self.file_nr]['zmax']
        else:
            # Fallback if some other thresholding option is introduced
            min_bound, max_bound = 0.0, 1.0  

        if sender == self.minus_button1 or sender == self.plus_button1:
            check_value = current_threshold + value
        elif sender == self.tdp_textbox1 or sender == self.reset_button2:
            check_value = value 
        elif sender == self.threshold_slider1: #or sender == self.reset_button2:
            check_value = value / multiplier
        # this is included for re computing the cluster map when switching beteween templates.
        # in this case there is no ui element sender, we just call it from reset template. in main_window.py
        else:
            check_value = value / multiplier

        # Check bounds — if outside, log message and return
        if check_value < min_bound:
            if sender == self.minus_button1 or sender == self.plus_button1:
                value = 0
            elif sender == self.tdp_textbox1: 
                value = min_bound
            elif sender == self.threshold_slider1: #or sender == self.reset_button2:
                value = min_bound 

            self.brain_nav.message_box.log_message(
                f"<span style='color: orange; font-weight: bold;'>"
                f"Warning: Lower limit reached at {min_bound:.2f}, increase threshold value."
                f"</span>"
            )
        if check_value > max_bound:
            if sender == self.minus_button1 or sender == self.plus_button1:
                value = 0
            elif sender == self.tdp_textbox1: 
                value = max_bound
            elif sender == self.threshold_slider1: #or sender == self.reset_button2:
                value = max_bound 
            self.brain_nav.message_box.log_message(
                f"<span style='color: orange; font-weight: bold;'>"
                f"Warning: Upper limit reached at {max_bound:.2f}, decrease threshold value."
                f"</span>"
            )
 
        # Block signals to prevent auto updates and infinite loops
        self.threshold_slider1.blockSignals(True)
        self.tdp_textbox1.blockSignals(True)

        # Update the other UI elements and covnert value accordingly.
        if sender == self.minus_button1 or sender == self.plus_button1:
            value = current_threshold + value
            self.threshold_slider1.setValue(int(value * multiplier))
            self.tdp_textbox1.setText(f"{value:.2f}")
        elif sender == self.tdp_textbox1 or sender == self.reset_button2:
            value = value 
            self.threshold_slider1.setValue(int(value * multiplier))
        elif sender == self.threshold_slider1: #or sender == self.reset_button2:
            value = value / multiplier
            self.tdp_textbox1.setText(f"{value:.2f}")

        # Unblock signals after updating
        self.threshold_slider1.blockSignals(False)
        self.tdp_textbox1.blockSignals(False)

        # Send message to user
        if selected_option == "TDP-based":
            self.brain_nav.message_box.log_message(f"<span style='color: white;'>Whole Brain TDP = {value:.2f}</span>")

            # Update threshold value in fileINFO and apply the new threshold value to the metrics
            self.fileInfo[self.file_nr]['tdp_threshold'] = value
            self.metrics.control_threshold(thresholding_method = "tdp", threshold_value = value)
        elif selected_option == "Z-score based":
            self.brain_nav.message_box.log_message(f"<span style='color: white;'>Whole Brain Z-score = {value:.2f}</span>")

            # Update threshold value in fileINFO and apply the new threshold value to the metrics
            self.fileInfo[self.file_nr]['zscore_threshold'] = value
            self.metrics.control_threshold(thresholding_method = "zscore", threshold_value = value)

    
    def reset_threshold_slider(self, selected_option):
        """
        Reset the threshold slider and text box to the stored threshold value from self.fileInfo.
        Also resets the slider range (min/max) based on the stored thresholding mode.
        """

        multiplier = 100  # For scaling between float threshold and int slider
        thresholding_dropdown = self.brain_nav.initiate_tabs.thresholding_dropdown

        # Determine which value and range to use based on selected method
        if selected_option == "TDP-based":
            value = self.fileInfo[self.file_nr].get('tdp_threshold', 0.0)
            min_bound = self.fileInfo[self.file_nr].get('mintdp', 0.0)
            max_bound = 1.0
        elif selected_option == "Z-score based":
            value = self.fileInfo[self.file_nr].get('zscore_threshold', 0.0)
            min_bound = self.fileInfo[self.file_nr].get('zmin', -10.0)
            max_bound = self.fileInfo[self.file_nr].get('zmax', 10.0)
        else:
            self.brain_nav.message_box.log_message("Unknown thresholding method selected.")
            return
        
        self.brain_nav.initiate_tabs.advisory_text.setText(self.brain_nav.initiate_tabs.advisory_messages.get(selected_option, ""))

        # Block signals during UI update
        self.threshold_slider1.blockSignals(True)
        self.tdp_textbox1.blockSignals(True)
        thresholding_dropdown.blockSignals(True)

        # Reset slider range
        self.threshold_slider1.setMinimum(int(min_bound * multiplier))
        self.threshold_slider1.setMaximum(int(max_bound * multiplier))
        self.threshold_slider1.setValue(int(value * multiplier))
        self.tdp_textbox1.setText(f"{value:.2f}")
        thresholding_dropdown.setCurrentText(selected_option)

        # Unblock signals
        self.threshold_slider1.blockSignals(False)
        self.tdp_textbox1.blockSignals(False)
        thresholding_dropdown.blockSignals(False)

        # Log user message
        label = "TDP" if selected_option == "TDP-based" else "Z-score"
        self.brain_nav.message_box.log_message(f"<span style='color: white;'>Threshold reverted to stored {label} = {value:.2f}</span>")
 


    def reset_threshold(self):
        """
        Resets the threshold setting and clears associated visual indicators.
        
        Triggered by the 'Reset' button, this method allows users to revert threshold settings
        to the default starting point. It accomplishes the following:
        
        - **Slider and Label Reset:** Retrieves the current slider value and updates the threshold label
          accordingly to reflect this starting threshold.
        - **Highlight Clearing:** Clears any highlights applied to table rows, providing a clean slate for cluster display.
        - **Removed Clusters Reset:** Empties the `removed_clusters` list to clear any previously flagged clusters,
          ensuring no clusters are highlighted as removed in the table.
        """
        # Retrieve the current value of the slider
        value = self.threshold_slider1.value()

        # Update the label and threshold logic with the current slider value
        self.update_threshold_label(value)

        # Clear all row background colors
        self.brain_nav.tblARI.clear_all_highlights()

    
