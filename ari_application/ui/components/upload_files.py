import os

from PyQt5.QtWidgets import QFileDialog, QMessageBox


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
                self.brain_nav.message_box.error(
                    f"Failed to upload statistical image: {e}", exc_info=True
                )

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
                self.brain_nav.message_box.error(
                    f"Failed to upload template: {e}", exc_info=True
                )

    def upload_codebook_dialog(self):
        """
        Pick a codebook `.txt` in AAL2 format and swap in the parsed names.
        Only meaningful once a user atlas is loaded; the atlas section's
        Upload Codebook button is gated on that. If a TblROI is already
        populated, we re-render it in place with the new names — TDPs and
        centroids are unaffected by a name change so no recompute needed.
        """
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(
            self.brain_nav, "Upload Codebook File", "",
            "Text Files (*.txt);;All Files (*)",
            options=options,
        )
        if not file_path:
            return

        self.logger.info(f"Codebook file selected: {file_path}")
        try:
            ok = self.brain_nav.nifti_loader.load_user_codebook(file_path)
        except Exception as e:
            # ErrorHandler was removed on main (983bde7) — the leveled
            # MessageLogger owns error reporting now.
            self.brain_nav.message_box.error(
                f"Failed to load codebook: {e}", exc_info=True
            )
            return

        if not ok:
            return

        # Refresh the ROI table with the new names.
        file_nr = self.brain_nav.file_nr
        atlas_key = self.brain_nav.metrics._resolve_atlas_key(
            file_nr, self.brain_nav.file_nr_template,
        )
        new_codebook = self.brain_nav.userAtlasInfo[atlas_key]['codebook']
        tbl = self.brain_nav.fileInfo.get(file_nr, {}).get('tblROI_df')
        if tbl is not None and not tbl.empty:
            # An analysis has been run; keep TDPs and centroids, just rewrite
            # the ROI-name column via Label -> new name.
            tbl['ROI'] = tbl['Label'].map(
                lambda lbl: new_codebook.get(int(lbl), f"ROI {int(lbl)}")
            )
            self.brain_nav.tblROI.update_table(tbl)
        else:
            # No analysis yet — refresh the codebook-only preview so the
            # renamed regions show up in the table right away.
            self.brain_nav.tblROI.populate_from_codebook(new_codebook)

    def upload_atlas_dialog(self):
        """
        Pick a user atlas NIfTI, hand off to NiftiLoader.load_user_atlas, and
        on success flip the orthoviews into 'atlas' overlay mode so the user
        can visually verify alignment before running ROI TDPs.
        """
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(
            self.brain_nav, "Upload Atlas File", "",
            "NIfTI Files (*.nii *.nii.gz);;All Files (*)",
            options=options,
        )
        if not file_path:
            return

        self.logger.info(f"Atlas file selected: {file_path}")
        try:
            ok = self.brain_nav.nifti_loader.load_user_atlas(file_path)
        except Exception as e:
            # ErrorHandler was removed on main (983bde7) — the leveled
            # MessageLogger owns error reporting now.
            self.brain_nav.message_box.error(
                f"Failed to load atlas: {e}", exc_info=True
            )
            return

        if not ok:
            return

        # Switch the overlay layer to the atlas for verification. Enable the
        # Run + Upload Codebook buttons (they live on TblROI, which owns
        # the whole atlas operating panel) and update the ROI-count readout.
        self.brain_nav.ui_params['overlay_mode'] = 'atlas'
        self.brain_nav.tblROI.atlas_run_button.setEnabled(True)
        self.brain_nav.tblROI.atlas_codebook_button.setEnabled(True)
        # The explainer has served its purpose — hand its height to the table.
        self.brain_nav.tblROI.collapse_explainer()
        # The sidebar's Atlas section lists the loaded atlases; keep it honest.
        self.brain_nav.left_side_bar.refresh_atlas_list()

        # ROI count = number of distinct labels in the codebook (auto-filled
        # to include every non-zero label in the atlas, whether or not the
        # sidecar named it).
        sample_entry = next(iter(self.brain_nav.userAtlasInfo.values()), None)
        if sample_entry is not None:
            self.brain_nav.tblROI.set_roi_count(len(sample_entry['codebook']))
            # Show the ROI list right away with placeholder TDP/centroid
            # columns; compute_roi_tdps overwrites these when Run is clicked.
            self.brain_nav.tblROI.populate_from_codebook(sample_entry['codebook'])

        self.brain_nav.orth_view_update.update_slices()

    # ------------------------------------------------------------------
    # Analysis mask
    # ------------------------------------------------------------------

    def upload_mask_dialog(self):
        """
        Pick a brain-mask NIfTI and re-analyse the active statistical map with
        it. The mask is also remembered in the sidebar's Analysis Mask
        section, so it can be applied to other statmaps with one click.

        The R ARIbrain app offered the same thing (menu2.R, "uncheck to
        import the brain mask").
        """
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(
            self.brain_nav, "Upload Analysis Mask", "",
            "NIfTI Files (*.nii *.nii.gz);;All Files (*)",
            options=options,
        )
        if not file_path:
            return

        self.logger.info(f"Mask file selected: {file_path}")
        file_nr = self.brain_nav.file_nr
        try:
            mask, notes = self.brain_nav.nifti_loader.load_user_mask(file_path, file_nr)
        except Exception as e:
            self.brain_nav.message_box.error(f"Failed to load mask: {e}", exc_info=True)
            return

        if mask is None:
            self.brain_nav.message_box.error(notes)
            return
        for note in notes:
            self.brain_nav.message_box.info(note)

        source = {
            'kind': 'user',
            'full_path': file_path,
            'filename': os.path.basename(file_path),
        }
        # Listed even if the user declines to apply it now.
        self._remember_mask(source)
        self.brain_nav.left_side_bar.refresh_mask_list()
        self.apply_mask_and_rerun(source, user_mask=mask)

    def apply_mask_and_rerun(self, source, user_mask=None):
        """
        Re-analyse the ACTIVE statmap with `source` as its analysis mask.
        Shared by mask upload and by clicking a row in the sidebar's Analysis
        Mask section.

        The mask decides every downstream result, so this is a full re-run:
        the statmap is reset to its just-loaded state (cluster table, ROI
        results and the cached Hommel object all go), then ARI runs exactly
        as for a newly uploaded statmap. Other statmaps are not touched.

        Returns True if the re-run happened.
        """
        bn = self.brain_nav
        file_nr = bn.file_nr
        info = bn.fileInfo[file_nr]

        if source.get('kind') == 'user' and user_mask is None:
            # A mask remembered from another statmap: bring it onto this
            # statmap's grid, which may differ.
            try:
                user_mask, notes = bn.nifti_loader.load_user_mask(source['full_path'], file_nr)
            except Exception as e:
                bn.message_box.error(f"Failed to load mask: {e}", exc_info=True)
                return False
            if user_mask is None:
                bn.message_box.error(notes)
                return False
            for note in notes:
                bn.message_box.info(note)

        if not self._confirm_mask_change(info, source):
            return False

        if not bn.nifti_loader.apply_analysis_mask(file_nr, source, user_mask):
            return False

        # Selections referred to clusters / ROIs computed with the old mask.
        bn.ui_params['selected_cluster_id'] = []
        bn.ui_params['selected_row'] = []
        bn.ui_params['selected_roi_label'] = None
        if bn.ui_params.get('overlay_mode') == 'roi':
            bn.ui_params['overlay_mode'] = 'atlas'

        # Same sequence as upload_stat_image.
        bn.tblARI.clear_table()
        bn.ARI.runARI()

        bn.tblROI.sync_to_active_statmap()
        bn.left_side_bar.refresh_mask_list()
        return True

    def _confirm_mask_change(self, info, source):
        """
        Ask before re-running. Always asked, not only when results would be
        lost: it is also where the user learns the mask applies to this one
        statmap rather than to every loaded map.
        """
        desc = self.brain_nav.nifti_loader.describe_mask_source(source)
        name = info.get('filename', 'this statistical map')

        lost = []
        if info.get('tblARI_df') is not None:
            lost.append("its cluster table")
        roi = info.get('tblROI_df')
        if roi is not None and not getattr(roi, 'empty', True):
            lost.append("its ROI results")
        lost_text = (" " + " and ".join(lost).capitalize() + " will be cleared.") if lost else ""

        answer = QMessageBox.question(
            self.brain_nav,
            "Change analysis mask",
            f"Analyse {name} with the {desc}?\n\n"
            f"ARI will be re-run for this statistical map only.{lost_text}",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes,
        )
        return answer == QMessageBox.Yes

    def _remember_mask(self, source):
        """Add an uploaded mask to the session list, once per file."""
        masks = self.brain_nav.userMasks
        if not any(m.get('full_path') == source['full_path'] for m in masks):
            masks.append(dict(source))
