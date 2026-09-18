"""
TblROI — the ROI Analysis tab: operating panel + results table.

Owns the full atlas-based ROI TDP workflow UI: the explainer text at the
top, the Upload Atlas / Upload Codebook / Run buttons plus an ROI-count
readout, and the results table beneath. Row selection routes through
Metrics.follow_roi_xyz to switch the orthoviews into the 'roi' overlay
mode and focus the crosshair on the selected ROI's centroid.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTextEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QComboBox, QToolButton,
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt

import pandas as pd

from ari_application.resources.styles import Styles


# Explainer shown above the operating panel. Moved out of the thresholding
# dropdown's advisory_messages — ROI TDP isn't a thresholding method, so
# describing it under the thresholding dropdown was a category error.
_ROI_ANALYSIS_EXPLAINER = (
    "ROI Analysis assigns a TDP (True Discovery Proportion) value to each "
    "region in a user-supplied anatomical atlas, using the ARI framework "
    "instead of forming data-driven clusters. Upload an atlas NIfTI (integer "
    "labels), optionally attach a codebook <code>.txt</code> mapping labels "
    "to names, then Run to compute per-ROI TDPs."
    "<br><br>"
    "<b>Important:</b> the atlas and the statistical map must be in the "
    "<b>same standard space</b> (e.g. MNI, or Talairach). Alignment is "
    "header-based (no image registration is performed), so native/scanner-"
    "space data will produce misplaced ROIs and unreliable TDPs."
)


class TblROI(QWidget):
    """
    Read-only ROI results table with an operating panel above it. See
    docs/ATLAS_TDP_PLAN.md for the overall design; the atlas loader lives
    in NiftiLoader, the TDP math in Metrics.compute_roi_tdps, and the
    row-selection follow-up in Metrics.follow_roi_xyz.
    """

    COLUMNS = ['ROI', 'Label', 'Size (vox)', 'TDP', 'Centroid (vox)', 'Centroid (MNI)']

    def __init__(self, brain_nav):
        super().__init__()
        self.brain_nav = brain_nav
        self._container = None

    def init_table(self):
        """
        Build the tab contents:
            title -> collapsible explainer -> operating panel
                  -> crosshair readout -> results table.

        Vertical budget: the explainer collapses to a 24px header once an
        atlas is loaded (it is first-run guidance, not a working surface),
        which more than pays for the 30px crosshair strip. The table is the
        only expanding widget, so it absorbs the difference — nothing else
        compresses and nothing is pushed out of the tab.

        Returns the container widget for QTabWidget.addTab.
        """
        self._container = QWidget()
        outer = QVBoxLayout()

        title = QLabel("ROI Analysis (User Atlas)")
        title.setFont(QFont('Arial', 14, QFont.Bold))
        title.setAlignment(Qt.AlignLeft)
        title.setStyleSheet("padding: 5px;")

        outer.addWidget(title)
        outer.addLayout(self._build_explainer())
        outer.addLayout(self._build_operating_panel())
        outer.addWidget(self._build_crosshair_readout())
        outer.addWidget(self._build_table())

        self._container.setLayout(outer)
        return self._container

    # ------------------------------------------------------------------
    # Collapsible explainer
    # ------------------------------------------------------------------

    def _build_explainer(self):
        """
        The standing explanation, behind a disclosure header.

        It matters exactly once — before the first atlas upload — but it was
        holding 120px permanently, on the most vertically constrained tab in
        the app. Expanded by default so a first-time user still reads it;
        collapsed automatically once an atlas loads, and re-openable any time.
        """
        box = QVBoxLayout()
        box.setSpacing(2)
        box.setContentsMargins(0, 0, 0, 0)

        self.explainer_toggle = QToolButton()
        self.explainer_toggle.setText("About ROI analysis")
        self.explainer_toggle.setCheckable(True)
        self.explainer_toggle.setChecked(True)
        self.explainer_toggle.setArrowType(Qt.DownArrow)
        self.explainer_toggle.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.explainer_toggle.setCursor(Qt.PointingHandCursor)
        self.explainer_toggle.setStyleSheet("""
            QToolButton {
                border: none;
                color: #9aa0a6;
                font-size: 11pt;
                padding: 2px 4px;
                text-align: left;
            }
            QToolButton:hover { color: #dddddd; }
        """)
        self.explainer_toggle.toggled.connect(self._on_explainer_toggled)

        self.explainer = QTextEdit()
        self.explainer.setReadOnly(True)
        # HTML so the warning can be bolded inline.
        self.explainer.setHtml(_ROI_ANALYSIS_EXPLAINER)
        # A bit taller than the old 60px so the appended standard-space
        # warning isn't clipped.
        self.explainer.setFixedHeight(120)

        box.addWidget(self.explainer_toggle)
        box.addWidget(self.explainer)
        return box

    def _on_explainer_toggled(self, expanded):
        self.explainer.setVisible(expanded)
        self.explainer_toggle.setArrowType(
            Qt.DownArrow if expanded else Qt.RightArrow
        )

    def collapse_explainer(self):
        """
        Fold the explainer away — called once an atlas is loaded, when the
        guidance has served its purpose and the table wants the height.
        No-op if the user already collapsed it.
        """
        if getattr(self, 'explainer_toggle', None) is not None:
            self.explainer_toggle.setChecked(False)

    # ------------------------------------------------------------------
    # Crosshair readout
    # ------------------------------------------------------------------

    def _build_crosshair_readout(self):
        """
        Single-line live readout of the ROI under the crosshair: name, label,
        TDP and MNI position.

        The workstation metrics panel can't serve this: it lives inside the
        Whole Brain TDP tab's layout, so it is off-screen whenever the user is
        on this tab — which is precisely when they are navigating an atlas.
        Fixed height so it can never wrap and push the table down.
        """
        self.crosshair_readout = QLabel()
        self.crosshair_readout.setTextFormat(Qt.RichText)
        self.crosshair_readout.setFixedHeight(30)
        self.crosshair_readout.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        self.crosshair_readout.setStyleSheet("""
            QLabel {
                background-color: #111;
                color: #dddddd;
                padding: 2px 10px;
                border-radius: 6px;
                border: 1px solid #444;
                font-size: 11pt;
            }
        """)
        self._set_crosshair_placeholder()
        return self.crosshair_readout

    def _set_crosshair_placeholder(self, text="Upload an atlas to inspect regions under the crosshair"):
        self.crosshair_readout.setText(
            f"<span style='color:#777;'>{text}</span>"
        )

    def update_crosshair_readout(self):
        """
        Refresh the readout for the current crosshair position. Driven from
        Metrics.show_metrics, which already runs on every crosshair move, so
        the line tracks mouse drags without a second signal path.

        Shows the ROI's TDP for the ACTIVE statmap (results are per-statmap),
        and an em-dash when the analysis hasn't been run for it yet. In TDP
        heatmap mode the value is tinted with the same viridis colour the
        overlay uses, so the number and the region on screen read as one
        thing.
        """
        if getattr(self, 'crosshair_readout', None) is None:
            return

        bn = self.brain_nav
        atlas_key = bn.orth_view_update._active_atlas_key()
        entry = bn.userAtlasInfo.get(atlas_key)
        if entry is None:
            self._set_crosshair_placeholder()
            return

        atlas = entry['data']
        x, y, z = bn.sagittal_slice, bn.coronal_slice, bn.axial_slice
        if not (0 <= x < atlas.shape[0]
                and 0 <= y < atlas.shape[1]
                and 0 <= z < atlas.shape[2]):
            self._set_crosshair_placeholder("Crosshair is outside the atlas volume")
            return

        label = int(atlas[x, y, z])
        if label <= 0:
            self._set_crosshair_placeholder("No ROI at the crosshair")
            return

        name = (entry.get('codebook') or {}).get(label, f"ROI {label}")
        info = bn.fileInfo.get(bn.file_nr, {})
        tdp = (info.get('roi_tdps') or {}).get(label)

        if tdp is None:
            tdp_html = "<span style='color:#777;'>&mdash;</span>"
        else:
            colour = '#dddddd'
            lut = info.get('roi_tdp_lut')
            if (
                bn.ui_params.get('atlas_colour_mode') == 'heatmap'
                and lut is not None and label < lut.shape[0]
            ):
                r, g, b = (int(c) for c in lut[label][:3])
                colour = f"#{r:02x}{g:02x}{b:02x}"
            tdp_html = f"<b style='color:{colour};'>{tdp:.3f}</b>"

        mni_html = ""
        rtr_affine = bn.aligned_templateInfo.get(
            (bn.file_nr, bn.file_nr_template), {}
        ).get('rtr_template_affine')
        if rtr_affine is not None:
            import numpy as np
            mni = bn.metrics.xyz2MNI(np.array([x, y, z]), rtr_affine)
            mni_html = (
                "<span style='color:#888;'>&nbsp;&nbsp;MNI</span> "
                f"({int(mni[0])}, {int(mni[1])}, {int(mni[2])})"
            )

        self.crosshair_readout.setText(
            f"<span style='color:#888;'>Crosshair &rarr;</span> "
            f"<b>{name}</b> "
            f"<span style='color:#888;'>(label {label})</span>"
            f"<span style='color:#888;'>&nbsp;&nbsp;TDP</span> {tdp_html}"
            f"{mni_html}"
        )

    # ------------------------------------------------------------------
    # Operating panel: Upload Atlas / Upload Codebook / ROI count / Run
    # ------------------------------------------------------------------

    def _build_operating_panel(self):
        """
        Horizontal row above the table with the three action buttons and a
        read-only ROI-count display. The Run button uses the same green
        Styles.runARI_button_styling as the whole-brain thresholding Run
        button; the count display mirrors tdp_textbox1's look for visual
        parity with the other tab.
        """
        row = QHBoxLayout()

        self.atlas_upload_button = QPushButton("Upload Atlas")
        self.atlas_upload_button.setCursor(Qt.PointingHandCursor)
        self.atlas_upload_button.setStyleSheet(Styles.atlas_button_styling)
        self.atlas_upload_button.clicked.connect(self._on_atlas_upload_clicked)

        self.atlas_codebook_button = QPushButton("Upload Codebook")
        self.atlas_codebook_button.setCursor(Qt.PointingHandCursor)
        self.atlas_codebook_button.setStyleSheet(Styles.atlas_button_styling)
        self.atlas_codebook_button.setEnabled(False)
        self.atlas_codebook_button.setToolTip(
            "Attach or replace the ROI-name codebook for the loaded atlas."
        )
        self.atlas_codebook_button.clicked.connect(
            self._on_atlas_codebook_upload_clicked
        )

        # ROI count readout — replaces the whole-brain threshold value slot.
        # Read-only QLineEdit styled like tdp_textbox1 so the two tabs feel
        # like the same product.
        roi_count_label = QLabel("ROIs loaded:")
        self.roi_count_display = QLineEdit("—")
        self.roi_count_display.setReadOnly(True)
        self.roi_count_display.setFixedWidth(80)
        self.roi_count_display.setAlignment(Qt.AlignCenter)
        font = QFont()
        font.setPointSize(12)
        font.setBold(True)
        self.roi_count_display.setFont(font)
        self.roi_count_display.setStyleSheet("""
            QLineEdit {
                background-color: #1a1a1a;
                color: #dddddd;
                border: 1px solid #444;
                border-radius: 5px;
                padding: 2px;
            }
        """)

        # Colour-mode toggle. Categorical is the default; Heatmap uses viridis
        # coloured by per-ROI TDP (auto-ranged) and requires the analysis to
        # have run. Disabled until then. Label omitted to keep the panel
        # within the tab's horizontal budget — the combo items themselves
        # ("Categorical" / "TDP heatmap") explain what it does, and the
        # tooltip carries the fuller description.
        self.colour_mode_selector = QComboBox()
        self.colour_mode_selector.addItems(["Categorical", "TDP heatmap"])
        self.colour_mode_selector.setEnabled(False)
        self.colour_mode_selector.setToolTip(
            "Categorical: fixed HSV palette per ROI.\n"
            "TDP heatmap: viridis coloured by TDP (auto-ranged across ROIs)."
        )
        self.colour_mode_selector.currentIndexChanged.connect(
            self._on_colour_mode_changed
        )

        # Green Run button — matches Styles.runARI_button_styling used on the
        # Whole Brain TDP tab. Disabled until an atlas is loaded.
        self.atlas_run_button = QPushButton("Run")
        self.atlas_run_button.setCursor(Qt.PointingHandCursor)
        self.atlas_run_button.setStyleSheet(Styles.runARI_button_styling)
        self.atlas_run_button.setEnabled(False)
        self.atlas_run_button.clicked.connect(self._on_atlas_run_clicked)

        row.addWidget(self.atlas_upload_button)
        row.addWidget(self.atlas_codebook_button)
        row.addSpacing(12)
        row.addWidget(roi_count_label)
        row.addWidget(self.roi_count_display)
        row.addSpacing(12)
        row.addWidget(self.colour_mode_selector)
        row.addStretch()
        row.addWidget(self.atlas_run_button)
        return row

    def _on_colour_mode_changed(self, index):
        """
        Update ui_params and refresh the orthviews + 3D so the swap is
        instant. Uses the QComboBox text, not the index, so reordering the
        combo later won't break the mapping.
        """
        mode = 'heatmap' if self.colour_mode_selector.currentText() == 'TDP heatmap' else 'categorical'
        self.brain_nav.ui_params['atlas_colour_mode'] = mode
        self.brain_nav.orth_view_update.update_slices()
        self.update_crosshair_readout()
        selected = self.brain_nav.ui_params.get('selected_roi_label')
        if selected is not None:
            self.brain_nav.threeDviewer.update_cluster_3d_view(int(selected))

    def set_roi_count(self, n):
        """
        Called by UploadFiles.upload_atlas_dialog after a successful load
        (and by upload_codebook_dialog if the label set changes). Passing
        None resets the display to the em-dash placeholder.
        """
        self.roi_count_display.setText("—" if n is None else str(int(n)))

    # ------------------------------------------------------------------
    # Table
    # ------------------------------------------------------------------

    def _build_table(self):
        self.table_widget = QTableWidget(self._container)
        self.table_widget.setColumnCount(len(self.COLUMNS))
        self.table_widget.setHorizontalHeaderLabels(self.COLUMNS)
        self.table_widget.verticalHeader().setVisible(False)
        self.table_widget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table_widget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_widget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table_widget.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)

        header = self.table_widget.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        header.setSectionResizeMode(0, QHeaderView.Stretch)            # ROI name
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)   # Label
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)   # Size
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)   # TDP
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)   # Centroid (vox)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)   # Centroid (MNI)

        # Placeholder while no analysis has run — keeps the empty tab from
        # looking broken.
        self.table_widget.setRowCount(1)
        placeholder = QTableWidgetItem(
            "Upload a user atlas and click Run to populate this table."
        )
        placeholder.setTextAlignment(Qt.AlignCenter)
        self.table_widget.setItem(0, 0, placeholder)
        self.table_widget.setSpan(0, 0, 1, len(self.COLUMNS))

        self.table_widget.itemSelectionChanged.connect(self._on_row_selected)
        return self.table_widget

    def update_table(self, df):
        """
        Populate the table from a tblROI_df DataFrame. Called by
        _on_atlas_run_clicked after Metrics.compute_roi_tdps, and by
        UploadFiles.upload_codebook_dialog after a codebook swap.
        """
        # Block selection signals during the rewrite so we don't fire
        # follow_roi_xyz on every setItem.
        self.table_widget.blockSignals(True)
        self.table_widget.clearContents()
        self.table_widget.clearSpans()
        self.table_widget.setRowCount(len(df))

        for r in range(len(df)):
            row = df.iloc[r]
            for c, col in enumerate(self.COLUMNS):
                # A compute_roi_tdps run before the centroid columns landed
                # would have a narrower DataFrame; render 'N/A' rather than
                # KeyError on those older rows.
                value = row[col] if col in df.columns else 'N/A'
                item = QTableWidgetItem(str(value))
                if col in ('Label', 'Size (vox)', 'TDP'):
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                elif col in ('Centroid (vox)', 'Centroid (MNI)'):
                    item.setTextAlignment(Qt.AlignCenter)
                self.table_widget.setItem(r, c, item)

        self.table_widget.blockSignals(False)

    def clear_table(self):
        self.table_widget.blockSignals(True)
        self.table_widget.clearContents()
        self.table_widget.clearSpans()
        self.table_widget.setRowCount(0)
        self.table_widget.blockSignals(False)

    def populate_from_codebook(self, codebook):
        """
        Render the codebook (label -> name mapping) as an empty-analysis
        table: one row per ROI with the name and label filled in, the
        numeric columns showing em-dashes. Called after atlas / codebook
        upload so the user can preview which regions will be analysed
        before clicking Run. compute_roi_tdps overwrites these rows via
        update_table with the real TDPs + centroids once the analysis
        completes.
        """
        if not codebook:
            return
        rows = [
            {
                'ROI': name,
                'Label': int(label),
                'Size (vox)': '—',
                'TDP': '—',
                'Centroid (vox)': '—',
                'Centroid (MNI)': '—',
            }
            for label, name in sorted(codebook.items(), key=lambda kv: int(kv[0]))
        ]
        self.update_table(pd.DataFrame(rows))

    def show_placeholder(self):
        """Reset the table to the pre-analysis single-row hint."""
        self.table_widget.blockSignals(True)
        self.table_widget.clearContents()
        self.table_widget.clearSpans()
        self.table_widget.setRowCount(1)
        placeholder = QTableWidgetItem(
            "Upload a user atlas and click Run to populate this table."
        )
        placeholder.setTextAlignment(Qt.AlignCenter)
        self.table_widget.setItem(0, 0, placeholder)
        self.table_widget.setSpan(0, 0, 1, len(self.COLUMNS))
        self.table_widget.blockSignals(False)

    def restore_from_session(self):
        """
        Sync the whole ROI operating panel with the current session state —
        called after a .ari project load (or an atlas restore failure) so the
        tab reflects reality: buttons enabled only when an atlas is loaded,
        count readout, table contents (results if present, codebook preview
        otherwise, placeholder when there's no atlas at all), and the colour
        toggle synced to ui_params without re-triggering renders.
        """
        bn = self.brain_nav
        has_atlas = bool(bn.userAtlasInfo)

        self.atlas_codebook_button.setEnabled(has_atlas)
        self.atlas_run_button.setEnabled(has_atlas)

        if has_atlas:
            # Guidance already served; give the height to the table.
            self.collapse_explainer()
        self.update_crosshair_readout()

        if not has_atlas:
            self.set_roi_count(None)
            self.colour_mode_selector.blockSignals(True)
            self.colour_mode_selector.setCurrentText('Categorical')
            self.colour_mode_selector.blockSignals(False)
            self.colour_mode_selector.setEnabled(False)
            self.show_placeholder()
            return

        sample = next(iter(bn.userAtlasInfo.values()))
        self.set_roi_count(len(sample.get('codebook') or {}))

        tbl = bn.fileInfo.get(bn.file_nr, {}).get('tblROI_df')
        if tbl is not None and not getattr(tbl, 'empty', True):
            self.update_table(tbl)
        else:
            self.populate_from_codebook(sample.get('codebook') or {})

        # Heatmap toggle only when THIS statmap has a TDP LUT (analysis was
        # run for it and its artifacts were rebuilt on load). Checking the
        # active statmap rather than "any atlas entry" keeps the toggle honest
        # when one map has been analysed and another hasn't.
        has_heat = (
            bn.fileInfo.get(bn.file_nr, {}).get('roi_tdp_lut') is not None
        )
        self.colour_mode_selector.blockSignals(True)
        mode = bn.ui_params.get('atlas_colour_mode', 'categorical')
        if not has_heat and mode == 'heatmap':
            # Saved mode can't be honoured without a LUT — fall back.
            bn.ui_params['atlas_colour_mode'] = 'categorical'
            mode = 'categorical'
        self.colour_mode_selector.setCurrentText(
            'TDP heatmap' if mode == 'heatmap' else 'Categorical'
        )
        self.colour_mode_selector.blockSignals(False)
        self.colour_mode_selector.setEnabled(has_heat)

    def sync_to_active_statmap(self):
        """
        Re-point the whole ROI tab at the statmap that is now active.

        ROI results are per-statmap (fileInfo['tblROI_df'] / 'roi_tdps'), but
        the atlas itself is shared, so switching maps must swap the table and
        the heatmap LUT without unloading the atlas. When the incoming map has
        no results yet we also drop the ROI selection and fall back to the
        verification overlay — keeping a selection whose TDP belongs to the
        previous map is how stale numbers used to end up on screen.

        Called by LeftSideBar.set_selected_statmap.
        """
        bn = self.brain_nav
        if not bn.userAtlasInfo:
            return

        self.restore_from_session()

        has_results = bn.fileInfo.get(bn.file_nr, {}).get('roi_tdps') is not None
        if not has_results:
            bn.ui_params['selected_roi_label'] = None
            if bn.ui_params.get('overlay_mode') == 'roi':
                bn.ui_params['overlay_mode'] = 'atlas'

        # Re-render only if the orthviews are actually showing the atlas;
        # in cluster mode the caller's own refresh already did the work.
        if bn.ui_params.get('overlay_mode') in ('atlas', 'roi'):
            bn.orth_view_update.update_slices()
            selected = bn.ui_params.get('selected_roi_label')
            bn.threeDviewer.update_cluster_3d_view(
                int(selected) if selected is not None else None
            )
        self.update_crosshair_readout()

    def select_roi_row(self, roi_label):
        """
        Highlight and scroll to the row for a given ROI label, without
        re-triggering _on_row_selected. Called by Metrics.follow_roi_xyz so a
        crosshair-based ROI pick keeps the table in sync, mirroring the
        cluster-analysis flow. No-op if the table isn't populated with that
        label yet (e.g. Run hasn't been clicked).
        """
        label_col = self.COLUMNS.index('Label')
        target_row = None
        for r in range(self.table_widget.rowCount()):
            item = self.table_widget.item(r, label_col)
            if item is None:
                continue
            text = item.text().strip()
            if text.lstrip('-').isdigit() and int(text) == int(roi_label):
                target_row = r
                break
        if target_row is None:
            return

        # Block signals so the programmatic selection doesn't bounce back
        # into follow_roi_xyz.
        self.table_widget.blockSignals(True)
        self.table_widget.selectRow(target_row)
        self.table_widget.scrollToItem(
            self.table_widget.item(target_row, 0),
            QAbstractItemView.PositionAtCenter,
        )
        self.table_widget.blockSignals(False)

    # ------------------------------------------------------------------
    # Button handlers (moved here from InitiateTabs — this widget owns
    # them because it owns the buttons now).
    # ------------------------------------------------------------------

    def _on_atlas_upload_clicked(self):
        """
        Hand off to UploadFiles.upload_atlas_dialog, which runs the file
        picker + loader and flips the orthoviews into atlas-overlay
        verification mode on success.
        """
        self.brain_nav.upload_files.upload_atlas_dialog()

    def _on_atlas_codebook_upload_clicked(self):
        """
        Hand off to UploadFiles.upload_codebook_dialog. The dialog replaces
        the codebook in-place and re-renders this table if it's already
        populated.
        """
        self.brain_nav.upload_files.upload_codebook_dialog()

    def _on_atlas_run_clicked(self):
        """
        Compute per-ROI TDPs for the active user atlas and populate the
        results table. No tab-switch needed anymore — the Run button is on
        this tab, so the user is already looking at the destination.
        """
        df = self.brain_nav.metrics.compute_roi_tdps(
            self.brain_nav.file_nr,
            self.brain_nav.file_nr_template,
        )
        if df is None or df.empty:
            # Cancelled, or nothing overlapped the data. Fall back to what the
            # session legitimately holds for this statmap — restore_from_session
            # shows the stored results if the run was cancelled, or the codebook
            # preview if the run genuinely produced none — rather than leaving
            # another run's numbers on screen implying they belong to this one.
            self.restore_from_session()
            return
        self.update_table(df)
        # tdp_lut is built inside compute_roi_tdps, so the heatmap option
        # is now meaningful — enable the toggle.
        self.colour_mode_selector.setEnabled(True)

    def _on_row_selected(self):
        """
        Translate the current selection to an ROI label and hand off to
        Metrics.follow_roi_xyz, which owns the crosshair-move + overlay-mode
        flip + 3D refresh. Reading 'Label' from the row rather than tracking
        a separate index means the table can be re-sorted without breaking
        selection.
        """
        selected_rows = self.table_widget.selectionModel().selectedRows()
        if not selected_rows:
            return

        row = selected_rows[0].row()
        label_item = self.table_widget.item(row, self.COLUMNS.index('Label'))
        if label_item is None or not label_item.text().strip().lstrip('-').isdigit():
            return

        try:
            label = int(label_item.text())
        except ValueError:
            return

        self.brain_nav.metrics.follow_roi_xyz(label)
