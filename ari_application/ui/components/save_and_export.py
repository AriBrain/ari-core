from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QFileDialog
from PyQt5.QtCore import Qt, QBuffer
from PyQt5.QtGui import QFont, QTextDocument
from PyQt5.QtPrintSupport import QPrinter
import pickle
import base64
import nibabel as nib  # Required for handling NIfTI files

class SaveAndExportTab(QWidget):
    """
    A modular class that encapsulates the functionality of the 'Save & Export' tab 
    within the ARIBrain application.

    This class provides UI components and logic for saving the current application state,
    loading a previously saved project, and exporting results including:
    - Cluster statistics tables (as CSV)
    - Cluster maps (as NIfTI .nii.gz files)
    - 3D visualizations (as PNG)
    - A complete HTML report with interactive cluster tables and orthogonal views
    - A stylized PDF summary of the cluster statistics table

    The class depends on the main application (`brain_nav`) for access to relevant 
    data structures such as fileInfo, statmaps, thresholds, and UI elements.

    Attributes:
        brain_nav (QMainWindow): Reference to the main application window to access 
                                 shared state and invoke refresh/logging operations.

    Methods:
        init_save_and_export_tab(): Initializes the tab UI and connects button signals.
        save_project(): Serializes and saves the current session state to a .ari file.
        load_project(): Loads a previously saved .ari file and restores state.
        export_results(): Coordinates full export of statistics, maps, visuals, and reports.
        export_all_tables_to_csv(): Saves CSV versions of cluster tables for each session.
        export_all_cluster_maps(): Saves updated cluster maps as NIfTI images.
        export_3d_visualization(): Captures and saves a snapshot of the 3D cluster viewer.
        html_report(): Generates and writes a styled, multi-tab HTML report with cluster info.
        save_html_table_as_pdf(): Renders the HTML table to a styled PDF document.
        grab_views_for_file(): Captures orthogonal views as inline PNGs for reports.
    """
    
    def __init__(self, brain_nav):
        super().__init__()
        self.brain_nav = brain_nav

    @property
    def fileInfo(self):
        return self.brain_nav.fileInfo

    def init_save_and_export_tab(self):
        """Initialize the Save & Export tab with buttons for saving, loading, and exporting."""

        self.save_export_tab = QWidget()
        self.save_export_layout = QVBoxLayout()

        # Save Project Button
        self.save_project_button = QPushButton("Save Project")
        self.save_project_button.setFont(QFont('Arial', 24, QFont.Bold))
        self.save_project_button.setFixedSize(200, 100)
        self.save_project_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50; /* Green background */
                color: white;
                border-radius: 10px;
            }
            QPushButton:hover {
                background-color: #45a049; /* Darker green on hover */
            }
        """)
        self.save_project_button.clicked.connect(self.save_project)

        # Load Project Button
        self.load_project_button = QPushButton("Load Project")
        self.load_project_button.setFont(QFont('Arial', 24, QFont.Bold))
        self.load_project_button.setFixedSize(200, 100)
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
        self.load_project_button.clicked.connect(self.load_project)

        # Export Results Button
        self.export_results_button = QPushButton("Export Results")
        self.export_results_button.setFont(QFont('Arial', 24, QFont.Bold))
        self.export_results_button.setFixedSize(200, 100)
        self.export_results_button.setStyleSheet("""
            QPushButton {
                background-color: #d6a35c; /* Blue background */
                color: white;
                border-radius: 10px;
            }
            QPushButton:hover {
                background-color: #007BB5; /* Darker blue on hover */
            }
        """)
        self.export_results_button.clicked.connect(self.export_results)

        # Add buttons to layout
        # Add buttons to layout with alignment
        self.save_export_layout.addWidget(self.save_project_button, alignment=Qt.AlignHCenter)
        self.save_export_layout.addWidget(self.load_project_button, alignment=Qt.AlignHCenter)
        self.save_export_layout.addWidget(self.export_results_button, alignment=Qt.AlignHCenter)
        self.save_export_tab.setLayout(self.save_export_layout)

        return self.save_export_tab

    def save_project(self):
        """Save the current project state to a .ari file."""
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getSaveFileName(
            self, "Save Project", "", "ARIBrain Project (*.ari);;All Files (*)", options=options)

        if file_name:
            if not file_name.endswith(".ari"):
                file_name += ".ari"

            # Slim per-file copies: strip session-only heavyweights that are
            # lazily recomputable — 'hom' (the Hommel object, rebuilt on the
            # first ROI run) and 'atlas_on_analysis_grid' (rebuilt when the
            # atlas is re-aligned at load). Shallow copies only; the arrays
            # we keep are shared, not duplicated.
            slim_fileInfo = {
                fn: {k: v for k, v in info.items()
                     if k not in ('hom', 'atlas_on_analysis_grid')}
                for fn, info in self.brain_nav.fileInfo.items()
            }

            # User atlas: save only what's needed to re-align at load time —
            # the aligned volumes (~35MB per background) are deliberately NOT
            # pickled to keep .ari files small. The codebook is saved because
            # it may come from a user-uploaded file that no longer sits next
            # to the atlas; TDPs are rebuilt from tblROI_df (in fileInfo).
            user_atlas_meta = None
            sample_entry = next(iter(self.brain_nav.userAtlasInfo.values()), None)
            if sample_entry is not None:
                user_atlas_meta = {
                    'full_path': sample_entry.get('full_path'),
                    'filename': sample_entry.get('filename'),
                    'codebook': sample_entry.get('codebook'),
                }

            project_data = {
                'version': 2,
                'fileInfo': slim_fileInfo,
                'atlasInfo': self.brain_nav.atlasInfo,
                'user_atlas': user_atlas_meta,
                'file_nr': self.brain_nav.file_nr,
                'file_nr_template': self.brain_nav.file_nr_template,
                'data_bg_index': self.brain_nav.data_bg_index,
                'ui_params': self.brain_nav.ui_params,
                'aligned_templateInfo': self.brain_nav.aligned_templateInfo,
                'aligned_statMapInfo': self.brain_nav.aligned_statMapInfo,
                'statmap_templates': self.brain_nav.statmap_templates,
                'start_input': self.brain_nav.start_input,
                'templates': self.brain_nav.templates,
                'template_names': [self.brain_nav.left_side_bar.template_list.item(i).text()
                                for i in range(self.brain_nav.left_side_bar.template_list.count())],
                'stat_image_names': [w.file_name_label.text() for w in self.brain_nav.stat_image_items],
                'ranges': self.brain_nav.ranges
            }

            with open(file_name, "wb") as file:
                pickle.dump(project_data, file)

            self.brain_nav.message_box.log_message(f"<span style='color: green;'>Project saved: {file_name}</span>")

    def load_project(self):
        """Load a previously saved .ari project file."""
        from PyQt5.QtWidgets import  QListWidgetItem
        from ui.components.left_side_bar import StatImageItem

        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Load Project", "", "ARIBrain Project (*.ari);;All Files (*)", options=options)

        if file_name:
            with open(file_name, "rb") as file:
                project_data = pickle.load(file)

            self.brain_nav.fileInfo             = project_data['fileInfo']

            self.brain_nav.atlasInfo            = project_data['atlasInfo']
            self.brain_nav.file_nr              = project_data['file_nr']
            self.brain_nav.file_nr_template     = project_data['file_nr_template']
            self.brain_nav.data_bg_index        = project_data['data_bg_index']
            self.brain_nav.ui_params            = project_data['ui_params']
            self.brain_nav.aligned_statMapInfo  = project_data['aligned_statMapInfo']
            self.brain_nav.aligned_templateInfo = project_data['aligned_templateInfo']
            # self.brain_nav.stat_image_items     = [] # This is not saved in the pickle file but needed when handling more than one statmap sessions
            self.brain_nav.templates            = project_data['templates']
            self.brain_nav.statmap_templates    = project_data['statmap_templates']
            self.brain_nav.start_input          = project_data['start_input']
            self.brain_nav.ranges               = project_data['ranges']

            # Restore stat image widgets from names
            self.brain_nav.stat_image_items.clear()
            self.brain_nav.left_side_bar.stat_images_list.clear()
            for name in project_data.get('stat_image_names', []):
                item_widget = StatImageItem(name)
                item = QListWidgetItem(self.brain_nav.left_side_bar.stat_images_list)
                item.setSizeHint(item_widget.sizeHint())
                self.brain_nav.left_side_bar.stat_images_list.setItemWidget(item, item_widget)
                self.brain_nav.stat_image_items.append(item_widget)

            # Restore template names
            self.brain_nav.left_side_bar.template_list.clear()
            for name in project_data.get('template_names', []):
                self.brain_nav.left_side_bar.template_list.addItem(name)
            self.brain_nav.left_side_bar.template_list.setCurrentRow(self.brain_nav.file_nr_template)


            # Re-establish (or clear) the user-atlas session state. Always
            # called — also when the loaded project has no atlas — so a
            # lingering in-session atlas from before the load is cleared.
            self.restore_user_atlas_state(project_data.get('user_atlas'))

            self.brain_nav.UIHelp.refresh_ui()
            self.brain_nav.message_box.log_message(f"<span style='color: green;'>Project loaded: {file_name}</span>")

    def restore_user_atlas_state(self, user_atlas_meta):
        """
        Rebuild the user-atlas session state from the slim metadata saved in
        a .ari project: re-align the atlas from its saved path (the aligned
        volumes are deliberately not pickled to keep project files small),
        re-apply the saved codebook, and rebuild the TDP LUT/range from the
        persisted tblROI_df. Ends by syncing the ROI tab UI either way.

        Shared by both load paths (in-app load_project and the StartWindow →
        BrainNav(load_data=True) route).
        """
        import os as _os

        bn = self.brain_nav
        bn.userAtlasInfo = {}

        if user_atlas_meta:
            path = user_atlas_meta.get('full_path')
            if path and _os.path.exists(path):
                ok = bn.nifti_loader.load_user_atlas(path)
                if ok:
                    # The saved codebook wins over whatever the loader
                    # re-parsed from a sidecar — the user may have uploaded a
                    # custom codebook file during the original session.
                    saved_cb = user_atlas_meta.get('codebook')
                    if saved_cb:
                        for entry in bn.userAtlasInfo.values():
                            entry['codebook'] = saved_cb

                    # Rebuild TDP artifacts for the active statmap from the
                    # persisted results table (TDPs are template-invariant,
                    # so Label -> TDP from tblROI_df is the full state).
                    tbl = bn.fileInfo.get(bn.file_nr, {}).get('tblROI_df')
                    if (
                        tbl is not None and not getattr(tbl, 'empty', True)
                        and 'Label' in tbl.columns and 'TDP' in tbl.columns
                    ):
                        atlas_key = bn.metrics._resolve_atlas_key(
                            bn.file_nr, bn.file_nr_template
                        )
                        entry = bn.userAtlasInfo.get(atlas_key)
                        if entry is not None:
                            entry['tdps_per_roi'] = {
                                int(l): float(t)
                                for l, t in zip(tbl['Label'], tbl['TDP'])
                            }
                            tdp_lut, tdp_range = bn.metrics._build_atlas_tdp_lut(entry)
                            entry['tdp_lut'] = tdp_lut
                            entry['tdp_range'] = tdp_range
            else:
                bn.message_box.log_message(
                    f"<span style='color: orange;'>Saved atlas not found at "
                    f"{path} — ROI overlays unavailable. Re-upload the atlas "
                    f"to restore them; the ROI results table is still shown."
                    f"</span>"
                )

        # Sync the ROI tab (buttons, count, table, colour toggle) with
        # whatever state we ended up in.
        bn.tblROI.restore_from_session()



    def export_results(self):
        """Export statistics table, cluster map (.nii.gz), and 3D visualization as a .png."""
        options = QFileDialog.Options()
        dir_name = QFileDialog.getExistingDirectory(self, "Select Export Directory", options=options)

        if dir_name:
            # Export statistics table as CSV
            # table_path = f"{dir_name}/statistics_table.csv"
            # self.export_table_to_csv(table_path)
            table_path = f"{dir_name}"
            self.export_all_tables_to_csv(table_path)

            # Export cluster map as NIfTI
            cluster_map_path = f"{dir_name}"
            # self.export_cluster_map(cluster_map_path)
            self.export_all_cluster_maps(cluster_map_path)

            # Export atlas-based (ROI) results, if any session computed them:
            # per-statmap ROI table CSVs plus label + TDP NIfTI maps on the
            # same grid/affine as the cluster maps.
            self.export_all_roi_tables_to_csv(dir_name)
            self.export_all_roi_maps(dir_name)

            # Export 3D visualization as PNG
            visualization_path = f"{dir_name}/3d_cluster_view.png"
            self.export_3d_visualization(visualization_path)

            html_path = f"{dir_name}/full_report.html"
            tbl_text_html = self.html_report(html_path)

            pdf_table_path = f"{dir_name}/ARI_report_table.pdf"
            self.save_html_table_as_pdf(tbl_text_html,pdf_table_path)

            self.brain_nav.message_box.log_message(f"<span style='color: green;'>All results succesfully exported to: {dir_name} 😊</span>")

    # def export_table_to_csv(self, file_path):
    #     """Exports the statistics table as a CSV file."""
        
    #     df = self.fileInfo[self.file_nr]['tblARI_df']
    #     df.to_csv(file_path, index=False)
    #     self.log_message(f"Statistics table saved: {file_path}")

    def export_all_tables_to_csv(self, output_dir):
        """Export cluster statistics tables for all file_nr entries in fileInfo."""
        from os.path import join

        for i, file_nr in enumerate(self.fileInfo):
            try:
                df = self.fileInfo[file_nr]['tblARI_df']
                file_path = join(output_dir, f"cluster_table_{i+1}.csv")
                df.to_csv(file_path, index=False)
                self.brain_nav.message_box.log_message(f"Statistics table saved: {file_path}")

            except KeyError as e:
                self.brain_nav.message_box.log_message(f"<span style='color: orange;'>Skipping file_nr {file_nr}: missing field {e}</span>")

    def export_all_roi_tables_to_csv(self, output_dir):
        """
        Export the ROI TDP tables (atlas-based analysis) for every statmap
        that has one. Mirrors export_all_tables_to_csv; statmaps without ROI
        results are silently skipped — the atlas workflow is optional.
        """
        from os.path import join

        for i, file_nr in enumerate(self.fileInfo):
            df = self.fileInfo[file_nr].get('tblROI_df')
            if df is None or getattr(df, 'empty', True):
                continue
            fn = self.fileInfo[file_nr].get('filename', f'file{file_nr}')
            file_path = join(output_dir, f"roi_table_{fn}_{i+1}.csv")
            df.to_csv(file_path, index=False)
            self.brain_nav.message_box.log_message(f"ROI table saved: {file_path}")

    def export_all_roi_maps(self, output_dir):
        """
        Export two NIfTI maps per statmap with ROI results, both on the
        statmap's native grid/affine (same convention as the exported
        cluster maps, so all outputs overlay directly):

          roi_atlas_map_*.nii.gz  — integer ROI labels, matching the 'Label'
                                    column of the roi_table CSV
          roi_tdp_map_*.nii.gz    — each ROI's voxels valued by its TDP
                                    (float32; 0 = background / unscored)

        Uses fileInfo['atlas_on_analysis_grid'] (the analysis-grid atlas);
        transposed back to canonical orientation for saving, exactly like the
        img_clus export.
        """
        from os.path import join

        for i, file_nr in enumerate(self.fileInfo):
            info = self.fileInfo[file_nr]
            atlas_grid = info.get('atlas_on_analysis_grid')
            df = info.get('tblROI_df')
            if atlas_grid is None or df is None or getattr(df, 'empty', True):
                continue

            fn = info.get('filename', f'file{file_nr}')
            atlas_canonical = atlas_grid.T.copy()  # analysis grid -> canonical

            # 1) Label map
            atlas_image = nib.Nifti1Image(
                atlas_canonical,
                affine=info['affine'],
                header=info['header'],
            )
            label_path = join(output_dir, f"roi_atlas_map_{fn}_{i+1}.nii.gz")
            nib.save(atlas_image, label_path)
            self.brain_nav.message_box.log_message(f"ROI atlas map saved: {label_path}")

            # 2) TDP map — derived from the persisted results table so it
            # works even right after a project load.
            import numpy as np
            tdp_map = np.zeros(atlas_canonical.shape, dtype=np.float32)
            for label, tdp in zip(df['Label'], df['TDP']):
                tdp_map[atlas_canonical == int(label)] = float(tdp)

            tdp_image = nib.Nifti1Image(
                tdp_map,
                affine=info['affine'],
                header=info['header'],
            )
            tdp_path = join(output_dir, f"roi_tdp_map_{fn}_{i+1}.nii.gz")
            nib.save(tdp_image, tdp_path)
            self.brain_nav.message_box.log_message(f"ROI TDP map saved: {tdp_path}")

    def save_html_table_as_pdf(self, html_string, output_path="ARI_report_table.pdf"):
        document = QTextDocument()
        document.setHtml(html_string)
        document.setDefaultFont(QFont("Times New Roman", 12))  # Set default font and size

        printer = QPrinter()
        printer.setOutputFormat(QPrinter.PdfFormat)
        printer.setOutputFileName(output_path)
        printer.setPageMargins(15, 15, 15, 15, QPrinter.Millimeter)

        document.print_(printer)
        self.brain_nav.message_box.log_message(f"HTML tabel saved as PDF: {output_path}")


    # def export_cluster_map(self, file_path):
    #     """Exports the cluster map as a NIfTI file."""
    #     file_nr = self.file_nr
    #     img_clus = self.fileInfo[file_nr]['img_clus'].T.copy()  # <--- Safe copy

    #     # Change unique cluster IDs in img_clus to 1 to n
    #     uIDs = self.fileInfo[file_nr]['tblARI_df']['Unique ID']
    #     cIDs = self.fileInfo[file_nr]['tblARI_df']['Cluster']

    #     for i, uID in enumerate(uIDs):
    #         img_clus[img_clus == uID] = cIDs[i]

    #     cluster_image = nib.Nifti1Image(
    #         img_clus,
    #         affine=self.fileInfo[file_nr]['affine'],
    #         header=self.fileInfo[file_nr]['header']
    #     )

    #     nib.save(cluster_image, file_path)
    #     self.log_message(f"Cluster map saved: {file_path}")

    def export_all_cluster_maps(self, output_dir):
        """Export cluster maps for all file_nr entries in fileInfo."""
        from os.path import join

        for i, file_nr in enumerate(self.fileInfo):
            try:
                img_clus = self.fileInfo[file_nr]['img_clus'].T.copy()  # Safe copy
                fn = self.fileInfo[file_nr]['filename']
                uIDs = self.fileInfo[file_nr]['tblARI_df']['Unique ID']
                cIDs = self.fileInfo[file_nr]['tblARI_df']['Cluster']

                for j, uID in enumerate(uIDs):
                    img_clus[img_clus == uID] = cIDs[j]

                cluster_image = nib.Nifti1Image(
                    img_clus,
                    affine=self.fileInfo[file_nr]['affine'],
                    header=self.fileInfo[file_nr]['header']
                )

                file_path = join(output_dir, f"cluster_map_{fn}_{i+1}.nii.gz")
                nib.save(cluster_image, file_path)
                self.brain_nav.message_box.log_message(f"Cluster map saved: {file_path}")

            except KeyError as e:
                self.brain_nav.message_box.log_message(f"<span style='color: orange;'>Skipping file_nr {file_nr}: missing field {e}</span>")

    def export_3d_visualization(self, file_path):
        """Saves a PNG screenshot of the 3D cluster visualization."""
        self.brain_nav.threeDviewer.cluster_3d_view.screenshot(file_path)
        self.brain_nav.message_box.log_message(f"3D visualization saved: {file_path}")

    def html_report(self, path='full_report.html'):
        """
        Export the cluster statistics DataFrame to an APA-styled HTML file.

        Parameters:
        - df (pd.DataFrame): The DataFrame containing the statistics.
        - path (str): File path to write the HTML output to.
        """
        from PyQt5.QtCore import QBuffer
        import base64

        file_nr = self.brain_nav.file_nr

        initial_message = self.fileInfo[file_nr]['init_message']
        last_set_z = "N/A"
        last_set_tdp = "N/A"
        if 'tdp_threshold' in self.fileInfo[file_nr]:
            last_set_tdp =  self.fileInfo[file_nr]['tdp_threshold']
        if 'z_threshold' in self.fileInfo[file_nr]:
            last_set_z =  self.fileInfo[file_nr]['z_threshold']

        # Summary statistics table
        Report_text = f"""
            <h1 style='color:#2c3e50;'>ARI Brain Report</h1>

            <p style='font-size:14px; line-height:1.6; color:#2d3436;'>
            Welcome to the <b>ARI Brain Report</b>. This report presents the results of your most recent cluster-based statistical inference.
            It includes:
            <ul style='margin-top: 0;'>
                <li>The full statistical cluster table as it was at the moment of saving,</li>
                <li>A preview of the selected cluster map on the anatomical template,</li>
                <li>And a snapshot of the 3D viewer showing the <i>last selected cluster</i>.</li>
            </ul>
            </p>

            <p style='font-size:14px; line-height:1.6; color:#2d3436;'>
            The results shown below reflect your current analysis settings at the time of export.
            These include thresholding values, template reference, and other configuration parameters.
            </p>

            <h2 style='color:#34495e;'>Analysis Settings</h2>

            <p style='font-size:14px; line-height:1.6; color:#2d3436;'>
            {self.fileInfo[self.brain_nav.file_nr]['init_message']}<br>
            <b>Currently applied thresholds:</b><br>
            {f"TDP threshold: <code>{last_set_tdp}</code><br>" if 'last_set_tdp' in locals() else ""}
            {f"Z-score threshold: <code>{last_set_z}</code><br>" if 'last_set_z' in locals() else ""}
            </p>
        """

        tbl_text = """
        <div style="margin-top: 40px; margin-bottom: 20px;">
            <h2 style="margin-bottom: 10px;">Table Explanation</h2>
            <p style="font-size: 15px; line-height: 1.6;">
                The table below summarizes the statistical properties of each identified cluster at the time of report export. 
                Each row represents one cluster, ordered by its statistical significance.
            </p>
            <p style="font-size: 15px; line-height: 1.6;">
                <b>Cluster Nr</b> corresponds to the cluster label in the downloaded cluster map (e.g., Cluster 23 here refers to the region 
                marked as 23 in the exported NIfTI file). This mapping allows for direct visual and spatial correspondence between the 
                report and the brain image.
            </p>
            <p style="font-size: 15px; line-height: 1.6;">
                The listed <b>MNI coordinates (x, y, z)</b> point to the local minimum within each cluster — the voxel with the most extreme 
                statistic. Corresponding anatomical <b>region labels</b> are estimated based on this voxel's location using an atlas lookup.
            </p>
        </div>
        """

        styles = """
        <style>
            table {
                border-collapse: collapse;
                width: 100%;
                font-family: "Arial", sans-serif;
                font-size: 14px;
            }
            th {
                border-bottom: 2px solid black;
                text-align: center;
                padding: 8px;
            }
            td {
                border-bottom: 1px solid #ddd;
                text-align: center;
                padding: 8px;
            }
            td:first-child {
                text-align: left;
            }
            caption {
                caption-side: top;
                font-weight: bold;
                text-align: left;
                margin-bottom: 10px;
            }
        </style>
        """

        
        # # ARI table
        # df = self.fileInfo[self.file_nr]['tblARI_df']
        # html = df.to_html(index=False, float_format="%.2f", classes="dataframe", border=0)
        # html_with_style = f"{styles}<caption>ARI Cluster Table</caption>{html}"

        tab_buttons = ""
        tab_contents = ""

        # Remember the live view state — the snapshot grabs below mutate
        # file_nr and overlay_mode; we restore both at the end of the report.
        _orig_file_nr = self.brain_nav.file_nr
        _orig_overlay_mode = self.brain_nav.ui_params.get('overlay_mode', 'cluster')

        for idx, info in self.fileInfo.items():
            if 'tblARI_df' not in info:
                continue

            df = info['tblARI_df']
            label = f"File {info['filename']}"
            safe_id = f"tab_{idx}"

            tab_buttons += f"<button class='tablink' onclick=\"openTab(event, '{safe_id}')\">{label}</button>\n"

            table_html = df.to_html(index=False, float_format="%.2f", classes="dataframe", border=0)

            # Force the cluster overlay for these snapshots so the images
            # match the tables they sit under, regardless of which analysis
            # view was active when the user clicked Export.
            sag_img, cor_img, ax_img = self.grab_views_for_file(idx, overlay_mode='cluster')

            tab_contents += f"""
            <div id="{safe_id}" class="tabcontent" style="display: none;">
                <caption style="caption-side: top; font-weight: bold; text-align: left; margin-bottom: 10px;">
                    ARI Cluster Table: {label}
                </caption>
                {table_html}
                <div class="image-gallery" style="margin-top: 30px;">
                    <div><h3>Sagittal Slice</h3><img src="{sag_img}" /></div>
                    <div><h3>Coronal Slice</h3><img src="{cor_img}" /></div>
                    <div><h3>Axial Slice</h3><img src="{ax_img}" /></div>
                </div>
            </div>
            """

        # === ROI (user atlas) section — only when a session computed ROI TDPs ===
        roi_section = ""
        roi_blocks = ""
        has_atlas_overlay = bool(self.brain_nav.userAtlasInfo)
        for idx, info in self.fileInfo.items():
            roi_df = info.get('tblROI_df')
            if roi_df is None or getattr(roi_df, 'empty', True):
                continue
            roi_table_html = roi_df.to_html(
                index=False, float_format="%.3f", classes="dataframe", border=0
            )

            # Atlas-overlay snapshots below the table, keeping image and
            # numbers in one context (mirrors the cluster tabs). All ROIs
            # visible, coloured by the session's current colour mode
            # (categorical or TDP heatmap). If an ROI is selected, grab in
            # 'roi' mode instead so the renderer draws its cyan contour —
            # the outline appears in every statmap's snapshot since the
            # atlas (and therefore the region) is shared across them.
            # Skipped when the atlas overlay isn't available (e.g. loaded
            # project whose atlas file moved).
            roi_gallery = ""
            if has_atlas_overlay:
                selected_label = self.brain_nav.ui_params.get('selected_roi_label')
                snap_mode = 'roi' if selected_label is not None else 'atlas'
                sag_img, cor_img, ax_img = self.grab_views_for_file(idx, overlay_mode=snap_mode)

                selection_note = ""
                if selected_label is not None:
                    atlas_entry = next(iter(self.brain_nav.userAtlasInfo.values()), {})
                    roi_name = (atlas_entry.get('codebook') or {}).get(
                        int(selected_label), f"ROI {int(selected_label)}"
                    )
                    selection_note = (
                        f"<p style='font-size: 13px; color: #2d3436;'>"
                        f"Outlined region: <b>{roi_name}</b> "
                        f"(label {int(selected_label)})</p>"
                    )

                roi_gallery = f"""
                <div class="image-gallery" style="margin-top: 30px;">
                    <div><h3>Sagittal Slice</h3><img src="{sag_img}" /></div>
                    <div><h3>Coronal Slice</h3><img src="{cor_img}" /></div>
                    <div><h3>Axial Slice</h3><img src="{ax_img}" /></div>
                </div>
                {selection_note}
                """

            roi_blocks += f"""
            <div style="margin-top: 25px;">
                <h3 style="color:#34495e;">File: {info.get('filename', idx)}</h3>
                {roi_table_html}
                {roi_gallery}
            </div>
            """

        if roi_blocks:
            atlas_entry = next(iter(self.brain_nav.userAtlasInfo.values()), {})
            atlas_name = atlas_entry.get('filename', 'user atlas')
            n_rois = len(atlas_entry.get('codebook') or {})
            tdp_range = atlas_entry.get('tdp_range')
            range_note = (
                f" TDP heatmap range at export: [{tdp_range[0]:.3f}, {tdp_range[1]:.3f}]."
                if tdp_range else ""
            )
            roi_section = f"""
            <div style="margin-top: 40px; margin-bottom: 20px;">
                <h2 style="color:#34495e;">ROI Analysis (User Atlas)</h2>
                <p style="font-size: 15px; line-height: 1.6;">
                    Atlas-based TDP results computed with atlas
                    <code>{atlas_name}</code> ({n_rois} regions).{range_note}
                </p>
                <p style="font-size: 15px; line-height: 1.6;">
                    Each row is one atlas region. <b>Label</b> matches the
                    integer values in the exported <code>roi_atlas_map</code>
                    NIfTI, and the exported <code>roi_tdp_map</code> carries
                    each region's TDP as the voxel value. <b>TDP</b> is a
                    simultaneous lower bound on the proportion of truly active
                    voxels in the region (All-Resolutions Inference), computed
                    on the statistical map's own grid — values are independent
                    of the displayed template.
                </p>
                {roi_blocks}
            </div>
            """

        # All snapshots taken — restore the view the user actually had before
        # the export started mutating file_nr / overlay_mode.
        self.brain_nav.file_nr = _orig_file_nr
        self.brain_nav.ui_params['overlay_mode'] = _orig_overlay_mode
        self.brain_nav.orth_view_update.update_slices()

        # === Grab Snapshots of Orthogonal Views ===
        def grab_widget_snapshot(widget):
            return widget.grab()

        def pixmap_to_base64(pixmap):
            buffer = QBuffer()
            buffer.open(QBuffer.ReadWrite)
            pixmap.save(buffer, "PNG")
            img_bytes = buffer.data()
            base64_str = base64.b64encode(img_bytes).decode("utf-8")
            return f"data:image/png;base64,{base64_str}"


        sag_pixmap = grab_widget_snapshot(self.brain_nav.sagittal_view)
        cor_pixmap = grab_widget_snapshot(self.brain_nav.coronal_view)
        ax_pixmap  = grab_widget_snapshot(self.brain_nav.axial_view)

        sag_img = pixmap_to_base64(sag_pixmap)
        cor_img = pixmap_to_base64(cor_pixmap)
        ax_img  = pixmap_to_base64(ax_pixmap)

        full_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
        <meta charset="UTF-8">
        <title>ARI Brain Report</title>
        {styles}
        <style>
            body {{
                background-color: #fdfdfd;
            }}
            .centered-container {{
                width: 50%;
                margin: 0 auto;
            }}
            .image-gallery {{
                display: flex;
                justify-content: space-between;
                flex-wrap: wrap;
                gap: 10px;
                margin-top: 30px;
            }}
            .image-gallery div {{
                flex: 1 1 30%;
                text-align: center;
            }}
            .image-gallery img {{
                width: 100%;
                height: auto;
                border: 1px solid #ccc;
                border-radius: 5px;
            }}
            .tab {{
                overflow: hidden;
                border-bottom: 1px solid #ccc;
                margin-bottom: 20px;
            }}
            .tab button {{
                background-color: #ecf0f1;
                border: none;
                outline: none;
                cursor: pointer;
                padding: 10px 16px;
                transition: 0.3s;
                font-size: 14px;
                margin-right: 4px;
                border-radius: 5px 5px 0 0;
            }}
            .tab button:hover {{
                background-color: #dcdde1;
            }}
            .tab button.active {{
                background-color: #bdc3c7;
            }}
            .tabcontent {{
                display: none;
                padding: 10px;
                border-top: none;
            }}
        </style>
        <script>
            function openTab(evt, tabName) {{
                var i, tabcontent, tablinks;

                tabcontent = document.getElementsByClassName("tabcontent");
                for (i = 0; i < tabcontent.length; i++) {{
                    tabcontent[i].style.display = "none";
                }}

                tablinks = document.getElementsByClassName("tablink");
                for (i = 0; i < tablinks.length; i++) {{
                    tablinks[i].classList.remove("active");
                }}

                document.getElementById(tabName).style.display = "block";
                evt.currentTarget.classList.add("active");
            }}

            // Auto-open first tab
            window.onload = function() {{
                let first = document.getElementsByClassName('tablink')[0];
                if (first) first.click();
            }};
        </script>
        </head>
        <body>
        <div class="centered-container">
            {Report_text}
            {tbl_text}
            <div style="margin-top: 40px; margin-bottom: 20px;">
                <h2>Cluster Tables</h2>
                <div class="tab">
                    {tab_buttons}
                </div>
                {tab_contents}
            </div>
            {roi_section}
        </div>
        </body>
        </html>
        """

        # Write to file
        with open(path, "w") as f:
            f.write(full_html)

        self.brain_nav.message_box.log_message(f"HTML Report exported to {path}")

        html_with_style = f"{styles}<caption>ARI Cluster Table</caption>{table_html}"

        return html_with_style



    # helper function for html report
    def grab_views_for_file(self, file_nr, overlay_mode=None):
        """
        Temporarily switch to a statmap (and optionally force an overlay
        mode) so the orthviews render its context, then grab the three views
        as base64 PNGs.

        overlay_mode: 'cluster' for the cluster-table snapshots, 'atlas' for
        the ROI-section snapshots. Forcing it here matters — without it the
        snapshot would show whatever overlay happened to be active in the
        session (e.g. atlas overlays under the cluster tables when exporting
        from the ROI tab). Callers are responsible for restoring the
        original file_nr / overlay_mode when the report is done.
        """
        self.brain_nav.file_nr = file_nr  # temporarily switch to this file
        if overlay_mode is not None:
            self.brain_nav.ui_params['overlay_mode'] = overlay_mode
        # self.brain_nav.orth_view_setup.set_initial_ranges()
        self.brain_nav.orth_view_update.update_slices()

        # Grab pixmaps from views
        def to_b64(pixmap):
            buffer = QBuffer()
            buffer.open(QBuffer.ReadWrite)
            pixmap.save(buffer, "PNG")
            return f"data:image/png;base64,{base64.b64encode(buffer.data()).decode('utf-8')}"

        sag_img = to_b64(self.brain_nav.sagittal_view.grab())
        cor_img = to_b64(self.brain_nav.coronal_view.grab())
        ax_img  = to_b64(self.brain_nav.axial_view.grab())

        return sag_img, cor_img, ax_img
