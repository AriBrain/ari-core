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
    QAbstractItemView,
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
        Build the tab contents: explainer -> operating panel -> table.
        Returns the container widget for QTabWidget.addTab.
        """
        self._container = QWidget()
        outer = QVBoxLayout()

        title = QLabel("ROI Analysis (User Atlas)")
        title.setFont(QFont('Arial', 14, QFont.Bold))
        title.setAlignment(Qt.AlignLeft)
        title.setStyleSheet("padding: 5px;")

        explainer = QTextEdit()
        explainer.setReadOnly(True)
        # HTML so the warning can be bolded inline.
        explainer.setHtml(_ROI_ANALYSIS_EXPLAINER)
        # A bit taller than the old 60px so the appended standard-space
        # warning isn't clipped.
        explainer.setFixedHeight(120)

        outer.addWidget(title)
        outer.addWidget(explainer)
        outer.addLayout(self._build_operating_panel())
        outer.addWidget(self._build_table())

        self._container.setLayout(outer)
        return self._container

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
        row.addStretch()
        row.addWidget(self.atlas_run_button)
        return row

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
            return
        self.update_table(df)

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
