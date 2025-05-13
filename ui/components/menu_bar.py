from PyQt5.QtWidgets import QAction, QDialog, QFormLayout, QLineEdit, QComboBox, QPushButton

class MenuBar:
    def __init__(self, brain_nav):
        self.brain_nav = brain_nav
        self.init_menu()

    def init_menu(self):
        menubar = self.brain_nav.menuBar()

        file_menu = menubar.addMenu('File')
        help_menu = menubar.addMenu('Help')

        analysis_settings_action = QAction('Analysis Settings', self.brain_nav)
        analysis_settings_action.triggered.connect(self.open_analysis_settings)
        file_menu.addAction(analysis_settings_action)

        help_menu_action = QAction('Help', self.brain_nav)
        help_menu.addAction(help_menu_action)


    def open_analysis_settings(self):       
        """
        Opens a settings dialog for configuring analysis parameters, allowing the user to adjust key options.
        
        This dialog provides the following adjustable settings:
        - **Significance Level (alpha):** A numeric input field to specify the alpha level for statistical significance.
        - **Connectivity Criterion:** A dropdown to select the connectivity criterion, with options of 6, 18, or 26.
        - **Local Test:** A dropdown to choose between 'Simes' and 'Robust variant of Simes' for local testing.
        - **Statistical Test:** A dropdown to select the type of test, with options for 'Two-sided test' or 'One-sided test'.
        
        After making selections, the user can:
        - Click "OK" to save the settings, which calls `save_analysis_settings`.
        - Click "Cancel" to close the dialog without saving changes.
        
        This function initiates the dialog window and manages the display and interactivity of the settings options.
        """

        dialog = QDialog(self)
        dialog.setWindowTitle('Analysis Settings')

        # Create a form layout for the settings
        layout = QFormLayout(dialog)

        # Significance Level input (alpha)
        self.alpha_edit = QLineEdit(str(self.brain_nav.input['alpha']))
        layout.addRow('Significance level:', self.alpha_edit)

        # Connectivity criterion dropdown
        self.conn_combo = QComboBox()
        self.conn_combo.addItems(['6', '18', '26'])
        self.conn_combo.setCurrentText(str(self.brain_nav.input['conn']))
        layout.addRow('Connectivity criterion:', self.conn_combo)

        # Local test dropdown
        self.local_test_combo = QComboBox()
        self.local_test_combo.addItems(['Simes', 'Robust variant of Simes'])
        self.local_test_combo.setCurrentText(self.brain_nav.input['simes'])
        layout.addRow('Local test:', self.local_test_combo)

        # Statistical test dropdown
        self.statistical_test_combo = QComboBox()
        self.statistical_test_combo.addItems(['Two-sided test', 'One-sided test'])

        # Set the current selection based on the existing input
        if self.brain_nav.input.get('twosidedTest', False):
            self.statistical_test_combo.setCurrentText('Two-sided test')
        elif self.brain_nav.input.get('onesidedTest', False):
            self.statistical_test_combo.setCurrentText('One-sided test')

        layout.addRow('Statistical test:', self.statistical_test_combo)

        # Add OK and Cancel buttons
        ok_button = QPushButton('OK')
        ok_button.clicked.connect(lambda: self.save_analysis_settings(dialog))
        layout.addWidget(ok_button)

        cancel_button = QPushButton('Cancel')
        cancel_button.clicked.connect(dialog.reject)
        layout.addWidget(cancel_button)

        dialog.setLayout(layout)
        dialog.exec_()

    
    def save_analysis_settings(self, dialog):
        """
        Saves the analysis settings input by the user and updates the configuration dictionary accordingly.
        
        This method collects user-provided settings from the `open_analysis_settings` dialog and stores them 
        in `self.input` with the following details:
        
        - **Significance Level (alpha):** Parses the user-entered text for alpha level and converts it to a float.
        - **Connectivity Criterion:** Sets the connectivity criterion as an integer based on the selected dropdown option.
        - **Local Test:** Stores the selected local test type (either 'Simes' or 'Robust variant of Simes').
        - **Statistical Test Flags:** Updates `twosidedTest` and `onesidedTest` flags in `self.input` based on the user's selection.
        - **Degrees of Freedom (tdf):** Sets a fixed value of 75 for the 'tdf' parameter.

        Once all settings are stored, the dialog is accepted to close.
        """

        # Save the user input to the self.input dictionary
        self.brain_nav.input['alpha'] = float(self.alpha_edit.text())
        self.brain_nav.input['conn'] = int(self.conn_combo.currentText())
        self.brain_nav.input['simes'] = self.local_test_combo.currentText()

        # Reset the test type flags
        self.brain_nav.input['twosidedTest'] = False
        self.brain_nav.input['onesidedTest'] = False

        # Update based on the selected test
        selected_test = self.statistical_test_combo.currentText()
        if selected_test == 'Two-sided test':
            self.brain_nav.input['twosidedTest'] = True
        elif selected_test == 'One-sided test':
            self.brain_nav.input['onesidedTest'] = True

        self.brain_nav.input['tdf'] = 75

        # Close the dialog
        dialog.accept()
