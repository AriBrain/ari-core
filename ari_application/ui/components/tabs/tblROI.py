"""
TblROI — results table for the user-uploaded atlas ROI TDP analysis.

Sibling of TblARI, but self-contained: this widget builds and owns its own
QTableWidget, so it can be dropped into a QTabWidget as one unit rather than
piggy-backing on initiate_tabs. Rows come from fileInfo[file_nr]['tblROI_df']
(produced by Metrics.compute_roi_tdps). Row selection routes through
Metrics.follow_roi_xyz to switch the orthoviews into the 'roi' overlay mode
and focus the crosshair on the selected ROI's centroid.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView,
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt


class TblROI(QWidget):
    """
    Read-only table of per-ROI TDP results. Selection wiring flips
    ui_params['overlay_mode'] to 'roi', records the selected label on
    ui_params['selected_roi_label'], and delegates crosshair movement +
    overlay refresh to Metrics.follow_roi_xyz.
    """

    COLUMNS = ['ROI', 'Label', 'Size (vox)', 'TDP', 'Centroid (vox)', 'Centroid (MNI)']

    def __init__(self, brain_nav):
        super().__init__()
        self.brain_nav = brain_nav
        self._container = None

    def init_table(self):
        """
        Build the tab contents. Returns the QWidget the QTabWidget owns.
        Called once from InitiateTabs.init_table.
        """
        self._container = QWidget()
        layout = QVBoxLayout()

        title = QLabel("ROI Analysis (User Atlas)")
        title.setFont(QFont('Arial', 14, QFont.Bold))
        title.setAlignment(Qt.AlignLeft)
        title.setStyleSheet("padding: 5px;")

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
            "Upload a user atlas and click Run ROI Analysis to populate this table."
        )
        placeholder.setTextAlignment(Qt.AlignCenter)
        self.table_widget.setItem(0, 0, placeholder)
        self.table_widget.setSpan(0, 0, 1, len(self.COLUMNS))

        self.table_widget.itemSelectionChanged.connect(self._on_row_selected)

        layout.addWidget(title)
        layout.addWidget(self.table_widget)
        self._container.setLayout(layout)
        return self._container

    def update_table(self, df):
        """
        Populate the table from a tblROI_df DataFrame. Called by
        InitiateTabs._on_atlas_run_clicked after Metrics.compute_roi_tdps.
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

    def _on_row_selected(self):
        """
        Translate the current selection to an ROI label and hand off to
        Metrics.follow_roi_xyz, which owns the crosshair-move + overlay-mode
        flip. Reading 'Label' from the row rather than tracking a separate
        index means the table can be re-sorted without breaking selection.
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
