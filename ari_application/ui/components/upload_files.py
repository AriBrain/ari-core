from PyQt5.QtWidgets import QFileDialog
from ari_application.error_handling.ErrorHandler import ErrorHandler

class UploadFiles:
    """
    A utility class for managing file uploads in the BrainNav application.

    Provides dialog-based routines for uploading statistical images, template files,
    and user atlases. Ensures correct integration of loaded files into the main 
    application state, updating both UI and back-end structures. Includes robust 
    error handling and optional logging for traceability.

    Parameters
    ----------
    BrainNav : BrainNav
        Reference to the main application controller.
    config : dict, optional
        Configuration dictionary for custom settings.
    logger : logging.Logger, optional
        Logger instance for capturing events; a default is used if not provided.

    Attributes
    ----------
    brain_nav : BrainNav
        Reference to the parent application, used to coordinate file integration.
    config : dict
        Optional settings for upload routines.
    logger : logging.Logger
        Logger used for informational and error messages.
    error_handler : ErrorHandler
        Handler for exception capture and user-friendly error reporting.

    Methods
    -------
    upload_stat_image():
        Launches a dialog to select and load a new NIfTI statistical image file.

    upload_template_dialog():
        Launches a dialog to select and load a new NIfTI template file.

    upload_atlas_dialog():
        Placeholder for user-defined atlas upload functionality (to be implemented).
    """
    
    def __init__(self, BrainNav, config=None, logger=None):
        """
        Initialize the UploadFiles class.

        :param brain_nav: Instance of the BrainNav class.
        :param config: Optional configuration dictionary.
        :param logger: Optional logger instance.
        """
        self.brain_nav = BrainNav
        self.config = config if config else {}
        self.logger = logger if logger else self._setup_default_logger()
        self.error_handler = ErrorHandler(log_file='upload_files_errors.log')

    def _setup_default_logger(self):
        """
        Set up a default logger if none is provided.
        """
        import logging
        logger = logging.getLogger('UploadFiles')
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        return logger

    # def upload_dialog(self):
    def upload_stat_image(self):
        """
        Handle the file upload process.
        """
        options = QFileDialog.Options()
        # options |= QFileDialog.DontUseNativeDialog
        file_path, _ = QFileDialog.getOpenFileName(self.brain_nav, "Upload NIfTI File", "",
                                                   "NIfTI Files (*.nii *.nii.gz);;All Files (*)",
                                                   options=options)
        if file_path:
            self.logger.info(f"File selected: {file_path}")
            try:
               
                # Ensure the 'last_thresholding_method' key exists before assigning
                if 'last_thresholding_method' not in self.brain_nav.fileInfo[self.brain_nav.file_nr]:
                    self.brain_nav.fileInfo[self.brain_nav.file_nr]['last_thresholding_method'] = ""

                self.brain_nav.fileInfo[self.brain_nav.file_nr]['last_thresholding_method'] = self.brain_nav.initiate_tabs.thresholding_dropdown.currentText()

                self.brain_nav.file_nr +=1 # add one to the current file counter so that loading works 
                self.brain_nav.nifti_loader.load_overlay(file_path)
                self.brain_nav.nifti_loader.load_data_as_bg(file_path)
                self.brain_nav.left_side_bar.switch_rawData_template()
                self.brain_nav.left_side_bar.add_statmap_to_list(file_path)
                self.brain_nav.tblARI.clear_table()

                
                # New statmap is loaded, so we need to run ARI
                self.brain_nav.ARI.runARI()
                
                # if sender == self.brain_nav.upload_button:
                #     self.brain_nav.nifti_loader.load_bg(file_path)
                # elif sender == self.brain_nav.stat_images_set_button:
                #     self.brain_nav.nifti_loader.load_overlay(file_path)
            except Exception as e:
                self.brain_nav.file_nr -= 1
                self.error_handler.handle_exception(e)  # Use ErrorHandler to handle the exception

    def upload_template_dialog(self):
        """
        Handle the template upload process.
        """
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(self.brain_nav, "Upload Template File", "",
                                                   "NIfTI Files (*.nii *.nii.gz);;All Files (*)",
                                                   options=options)
        if file_path:
            self.logger.info(f"Template file selected: {file_path}")
            try:
                self.brain_nav.file_nr_template += 1  # increment template file counter
                self.brain_nav.left_side_bar.add_template_to_list(file_path)
                self.brain_nav.nifti_loader.load_bg(file_path)
            except Exception as e:
                self.brain_nav.file_nr_template -= 1
                self.error_handler.handle_exception(e)

    def upload_atlas_dialog(self):
        # here upload user atlas routine needs to be defined. 
        pass