from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget,
    QPushButton, QMessageBox, QListWidgetItem, QApplication, QToolButton,
    QAbstractItemView, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QSize
from PyQt5.QtGui import QPainter, QFontMetrics, QColor, QFont

from ari_application.resources.styles import Styles  # Adjust path if needed
from ari_application.models.nifti_loader import (
    NiftiLoader, AUTO_MASK_SOURCE, LEGACY_MASK_SOURCE,
)

import os
from contextlib import contextmanager


# --------------------------------------------------------------------------
# Palette for the rail. Kept local rather than pushed into Styles because
# these are structural to the sidebar's row/section idiom, not shared chrome.
# --------------------------------------------------------------------------
_RAIL_BG        = "#0b1f16"
_SECTION_BG     = "#122b1f"   # expanded section body, one step up from the rail
_ROW_ACTIVE_BG  = "#163c2a"
_ACCENT         = "#7fd1a8"
_TEXT           = "#dfe6e2"
_TEXT_DIM       = "#8a9a92"
_ROW_HEIGHT     = 26
_RAIL_WIDTH     = 210
_MAX_VISIBLE_ROWS = 8   # scroll beyond this instead of growing the rail


class ElidedLabel(QLabel):
    """
    QLabel that paints its text elided in the middle but keeps text()
    returning the full string.

    That distinction matters: save_project harvests statmap names via
    StatImageItem.file_name_label.text(), so an elided widget that also
    reported elided text would write "sub-01_zstat...nback.nii.gz" into the
    .ari file and break the reload. The full name also becomes the tooltip,
    which is how the user reads a name that doesn't fit.
    """

    def __init__(self, text='', colour=_TEXT, mode=Qt.ElideMiddle,
                 display=None, parent=None):
        super().__init__(text, parent)
        self._mode = mode
        self._colour = QColor(colour)
        self._display = display
        self.setToolTip(text)
        self.setMinimumWidth(40)

    def setText(self, text, display=None):
        super().setText(text)
        self._display = display
        self.setToolTip(text)

    def setColour(self, colour):
        self._colour = QColor(colour)
        self.update()

    def minimumSizeHint(self):
        return QSize(40, super().minimumSizeHint().height())

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setPen(self._colour)
        painter.setFont(self.font())
        elided = QFontMetrics(self.font()).elidedText(
            self._display or self.text(), self._mode, self.width()
        )
        painter.drawText(self.rect(), int(self.alignment()), elided)


class ResourceRow(QWidget):
    """
    One row in the rail: an activation dot, a middle-elided name, and an
    optional right-hand badge ("ARI", "raw data", "built-in", "user").

    The dot is the answer to "which one is actually loaded?" — the old rail
    had only a selection highlight, so a selected-but-not-Set row looked
    identical to the live one.
    """

    def __init__(self, name, badge=None, badge_colour=_TEXT_DIM, show_dot=True):
        super().__init__()
        self._active = False
        self._show_dot = show_dot

        layout = QHBoxLayout()
        layout.setContentsMargins(6, 0, 6, 0)
        layout.setSpacing(6)

        self.dot = QLabel("\u25cb" if show_dot else "")
        # 14, not 10: the hollow circle is wider than the filled one and was
        # being clipped on its right side, rendering as a "C".
        self.dot.setFixedWidth(14)
        self.dot.setAlignment(Qt.AlignCenter)
        self.dot.setStyleSheet(f"color: {_TEXT_DIM}; border: none; background: transparent;")
        layout.addWidget(self.dot)

        # text() keeps the full filename (save_project reads it); only the
        # painted string is shortened.
        self.file_name_label = ElidedLabel(name, display=self._stem(name))
        self.file_name_label.setStyleSheet("border: none; background: transparent;")
        layout.addWidget(self.file_name_label, stretch=1)

        self.badge_label = QLabel(badge or "")
        badge_font = QFont()
        badge_font.setPointSize(9)
        self.badge_label.setFont(badge_font)
        self._badge_colour = badge_colour
        self.badge_label.setStyleSheet(
            f"color: {badge_colour}; border: none; background: transparent;"
        )
        layout.addWidget(self.badge_label, alignment=Qt.AlignRight)

        self.setLayout(layout)
        self.setFixedHeight(_ROW_HEIGHT)
        # Opaque: the QListWidgetItem still carries its own text (save_project
        # and the template restore read item(i).text()), and a transparent row
        # would let that text paint through underneath this one. A plain
        # QWidget ignores a stylesheet background unless WA_StyledBackground
        # is set, so both flags are needed, not either one.
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setAutoFillBackground(True)
        self._apply_style()

    @staticmethod
    def _stem(name):
        """Filename without the NIfTI extension — the extension is noise in a
        narrow rail and identical on every row."""
        for ext in ('.nii.gz', '.nii'):
            if name.endswith(ext):
                return name[:-len(ext)]
        return name

    def set_active(self, active):
        self._active = bool(active)
        self._apply_style()

    def set_badge(self, text, colour=None):
        self.badge_label.setText(text or "")
        if colour is not None:
            self._badge_colour = colour
        self.badge_label.setStyleSheet(
            f"color: {self._badge_colour}; border: none; background: transparent;"
        )

    def set_name(self, name):
        self.file_name_label.setText(name, display=self._stem(name))

    def _apply_style(self):
        if self._show_dot:
            self.dot.setText("\u25cf" if self._active else "\u25cb")
            self.dot.setStyleSheet(
                f"color: {_ACCENT if self._active else _TEXT_DIM};"
                " border: none; background: transparent;"
            )
        self.file_name_label.setColour(_TEXT if self._active else _TEXT_DIM)
        bg = _ROW_ACTIVE_BG if self._active else _SECTION_BG
        self.setStyleSheet(f"background-color: {bg}; border-radius: 4px;")


class ResourceList(QListWidget):
    """
    QListWidget restyled for the rail and sized to its contents.

    Deliberately still a QListWidget: main_window and save_and_export drive
    these lists directly (clear / addItem / setItemWidget / setCurrentRow /
    item(i).text()), and a bespoke widget would have meant touching all of
    those call sites. The visual change is rows-as-widgets plus a height that
    follows the row count instead of a fixed empty box.

    `row_factory` lets the template and atlas sections get a ResourceRow for
    plain addItem(str) calls while the item keeps its text for save_project.
    """

    def __init__(self, row_factory=None):
        super().__init__()
        self._row_factory = row_factory
        self.setFrameShape(QListWidget.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setFocusPolicy(Qt.NoFocus)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(f"""
            QListWidget {{
                background-color: {_SECTION_BG};
                border: none;
                outline: none;
                padding: 0px;
            }}
            QListWidget::item {{ border: none; padding: 0px; }}
            QListWidget::item:selected {{ background: transparent; }}
        """)
        self.model().rowsInserted.connect(self._schedule_sync)
        self.model().rowsRemoved.connect(self._schedule_sync)
        self.model().modelReset.connect(self._schedule_sync)
        self._sync_height()

    # -- keep item text intact while giving plain items a row widget --------
    def addItem(self, item):
        super().addItem(item)
        if self._row_factory is not None:
            idx = self.count() - 1
            list_item = self.item(idx)
            widget = self._row_factory(list_item.text(), idx)
            if widget is not None:
                list_item.setSizeHint(widget.sizeHint())
                self.setItemWidget(list_item, widget)
        self._schedule_sync()

    def setItemWidget(self, item, widget):
        super().setItemWidget(item, widget)
        self._schedule_sync()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._fit_rows()

    def _fit_rows(self):
        """
        Pin every item to the viewport width. Callers set an item's sizeHint
        from its widget's own sizeHint, which for a long filename is wider
        than the rail — the row then overflowed and was clipped, taking the
        badge with it. The name elides to whatever width is actually here.
        """
        w = self.viewport().width()
        if w <= 0:
            return
        for i in range(self.count()):
            item = self.item(i)
            if item.sizeHint().width() != w or item.sizeHint().height() != _ROW_HEIGHT:
                item.setSizeHint(QSize(w, _ROW_HEIGHT))

    def _schedule_sync(self, *args):
        # Deferred: callers routinely add the QListWidgetItem first and set
        # its widget (and therefore its real height) a line later.
        QTimer.singleShot(0, self._sync_height)

    def _sync_height(self):
        self._fit_rows()
        n = self.count()
        visible = min(max(n, 1), _MAX_VISIBLE_ROWS)
        self.setFixedHeight(visible * _ROW_HEIGHT + 4)

    def rows(self):
        """Every row widget currently installed, in order."""
        return [self.itemWidget(self.item(i)) for i in range(self.count())]

    def set_row_name(self, index, name):
        """
        Rename an existing row, updating BOTH the item's text and the row
        widget on top of it.

        Renaming in place has one caller — the raw-data background entry,
        which re-points at whichever statmap is active — and it is easy to
        get half right: the item carries the name that save_project reads
        back, while the widget carries the name the user sees. Setting only
        the item leaves a correct .ari file next to a stale label on screen.
        """
        item = self.item(index)
        if item is None:
            return
        item.setText(name)
        widget = self.itemWidget(item)
        if widget is not None:
            widget.set_name(name)


class Section(QWidget):
    """
    A collapsible titled group: header (disclosure arrow, title, count, '+')
    over a ResourceList. Replaces the old fixed-height bordered box, which
    reserved the same space whether it held one entry or ten.
    """

    def __init__(self, title, resource_list, on_add=None, add_tooltip=""):
        super().__init__()
        self.list = resource_list

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QHBoxLayout()
        header.setContentsMargins(6, 3, 6, 3)
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(4)

        self.toggle = QToolButton()
        self.toggle.setText(title)
        self.toggle.setCheckable(True)
        self.toggle.setChecked(True)
        self.toggle.setArrowType(Qt.DownArrow)
        self.toggle.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.toggle.setCursor(Qt.PointingHandCursor)
        self.toggle.setStyleSheet(f"""
            QToolButton {{
                border: none;
                color: {_TEXT_DIM};
                font-size: 10px;
                font-weight: bold;
                padding: 2px 0px;
                text-align: left;
            }}
            QToolButton:hover {{ color: {_TEXT}; }}
        """)
        self.toggle.toggled.connect(self._on_toggled)

        self.count_label = QLabel("0")
        self.count_label.setStyleSheet(
            f"color: {_TEXT_DIM}; font-size: 10px; border: none;"
        )

        self.add_button = QPushButton("+")
        self.add_button.setFixedSize(18, 18)
        self.add_button.setCursor(Qt.PointingHandCursor)
        self.add_button.setToolTip(add_tooltip)
        self.add_button.setStyleSheet(f"""
            QPushButton {{
                border: 1px solid {_TEXT_DIM};
                border-radius: 4px;
                background-color: transparent;
                color: {_TEXT_DIM};
                font-size: 12px;
                font-weight: bold;
                padding: 0px;
            }}
            QPushButton:hover {{
                border-color: {_ACCENT};
                color: {_ACCENT};
            }}
        """)
        if on_add is not None:
            self.add_button.clicked.connect(on_add)

        header.addWidget(self.toggle, stretch=1)
        header.addWidget(self.count_label)
        header.addWidget(self.add_button)

        # Header and body are separate widgets so the expanded state can be
        # signalled by a filled, rounded panel rather than by the arrow
        # direction alone. Collapsed, the header sits flat on the rail; open,
        # header and body join into one raised card.
        self.header_widget = QWidget()
        self.header_widget.setAttribute(Qt.WA_StyledBackground, True)
        self.header_widget.setLayout(header)

        self.body = QWidget()
        self.body.setAttribute(Qt.WA_StyledBackground, True)
        body_layout = QVBoxLayout()
        body_layout.setContentsMargins(2, 2, 2, 4)
        body_layout.setSpacing(0)
        body_layout.addWidget(self.list)
        self.body.setLayout(body_layout)

        layout.addWidget(self.header_widget)
        layout.addWidget(self.body)
        self.setLayout(layout)
        self._apply_expanded_style(True)

        # Take exactly the height we ask for. With the default Preferred
        # policy the rail's spare vertical space was shared out among the
        # three sections, which then padded it between their own header and
        # list — a one-row section rendered with its single row floating in
        # the middle of a tall empty box. All slack belongs to the stretch at
        # the bottom of the rail.
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)

        self.list.model().rowsInserted.connect(self.refresh_count)
        self.list.model().rowsRemoved.connect(self.refresh_count)
        self.list.model().modelReset.connect(self.refresh_count)
        self.refresh_count()

    def _on_toggled(self, expanded):
        self.body.setVisible(expanded)
        self.toggle.setArrowType(Qt.DownArrow if expanded else Qt.RightArrow)
        self._apply_expanded_style(expanded)

    def _apply_expanded_style(self, expanded):
        """
        Expanded: header and body form one raised, rounded card in
        _SECTION_BG, with the header squared off at the bottom so the two
        read as a single block. Collapsed: the header goes flat and
        transparent and sits directly on the rail.
        """
        if expanded:
            self.header_widget.setStyleSheet(f'''
                QWidget {{
                    background-color: {_SECTION_BG};
                    border-top-left-radius: 6px;
                    border-top-right-radius: 6px;
                }}
            ''')
            self.body.setStyleSheet(f'''
                QWidget {{
                    background-color: {_SECTION_BG};
                    border-bottom-left-radius: 6px;
                    border-bottom-right-radius: 6px;
                }}
            ''')
        else:
            self.header_widget.setStyleSheet(
                "QWidget { background-color: transparent; border-radius: 6px; }"
            )
            self.body.setStyleSheet("QWidget { background: transparent; }")

    def refresh_count(self, *args):
        self.count_label.setText(str(self.list.count()))




class LeftSideBar(QWidget):
    """
    LeftSideBar manages the vertical control panel on the left-hand side of the BrainNav UI.

    This component provides interactive lists and buttons to manage core resources for analysis:
    - Statistical Images
    - Template Images
    - Anatomical Atlases

    Signals:
    --------
    - `stat_image_add_clicked`: Emitted when the "Add" button for statistical images is clicked.
    - `template_add_clicked`: Emitted when the "Add" button for templates is clicked.
    - `atlas_add_clicked`: Emitted when the "Add" button for atlases is clicked.

    Features:
    ---------
    - Upload and select statistical images, templates, and atlas files.
    - Switch and configure the selected statistical map and template.
    - Automatically prompt users when cluster maps are missing or thresholding hasn't been performed.
    - Updates viewer components (metrics, 3D view, orthogonal slices) based on selection.
    - Shows ARI status for each statistical image using a custom `StatImageItem` widget.

    Key Widgets:
    ------------
    - `stat_images_list`, `template_list`: `QListWidget` instances displaying file items.
    - `stat_images_upload_button`, `template_upload_button`, `atlas_upload_button`: the '+' buttons in each section header.
    - Activation is a single click on a row; the '\u25cf' marker shows what is
      live. The old select-then-"Set" pair is gone.
    - `left_panel_container`: The top-level container widget holding the entire sidebar layout.

    Integration:
    ------------
    - Communicates with `BrainNav` to update metrics, cluster overlays, templates, and coordinate mappings.
    - Makes use of `StatImageItem` widgets to represent file entries visually, including ARI completion indicators.

    Notes:
    ------
    - The Atlas section lists the bundled AAL2 plus the user atlas once one
      is loaded; call refresh_atlas_list() after an atlas upload or a project
      load to keep it in sync.
    - This class expects `self.templates`, `self.statmap_templates`, `self.data_bg_index`, and `self.file_nr` to be defined externally.
    - All file additions, selections, and UI refresh logic is routed through this sidebar for consistency.
    """

    # Define the button signals
    stat_image_add_clicked = pyqtSignal()
    template_add_clicked = pyqtSignal()
    atlas_add_clicked = pyqtSignal()
    mask_add_clicked = pyqtSignal()


    def __init__(self, BrainNav):
        super().__init__() # Initialize the QWidget
        
        self.brain_nav = BrainNav

        self.init_sidebar()

    def init_sidebar(self):
        """
        Build the rail: three collapsible sections, each sized to its
        contents, each with a '+' in its header.

        Replaces three fixed-height bordered boxes that reserved ~200px
        apiece regardless of how many entries they held, truncated every
        filename at 148px behind a horizontal scrollbar, and hid the ARI
        badge off the right edge as a result.
        """
        left_panel_layout = QVBoxLayout()
        left_panel_layout.setContentsMargins(4, 4, 4, 4)
        left_panel_layout.setSpacing(10)

        # === Statistical Images ===========================================
        # Rows are built by callers as StatImageItem, so no row_factory here.
        self.stat_images_list = ResourceList()
        self.stat_images_list.itemClicked.connect(self._on_stat_row_clicked)

        self.stat_images_section = Section(
            "STATISTICAL IMAGES", self.stat_images_list,
            on_add=self.stat_image_add_clicked.emit,
            add_tooltip="Add a statistical map",
        )
        self.stat_images_upload_button = self.stat_images_section.add_button

        self.add_statmap_to_list(self.brain_nav.start_input['data_dir'])
        left_panel_layout.addWidget(self.stat_images_section)

        # === Templates =====================================================
        self.template_list = ResourceList(row_factory=self._make_template_row)
        self.template_list.itemClicked.connect(self._on_template_row_clicked)

        self.template_section = Section(
            "TEMPLATE", self.template_list,
            on_add=self.template_add_clicked.emit,
            add_tooltip="Add a background template",
        )
        self.template_upload_button = self.template_section.add_button

        for file_info in self.brain_nav.templates.values():
            self.template_list.addItem(file_info['filename'])
        self.template_list.setCurrentRow(self.brain_nav.file_nr_template)

        left_panel_layout.addWidget(self.template_section)

        # === Atlas =========================================================
        # No activation dots: AAL2 and a user atlas are both live at once —
        # AAL2 feeds the crosshair region readout, the user atlas drives the
        # ROI overlay — so a radio marker would misrepresent the state. The
        # badge carries the meaning instead.
        self.atlas_list = ResourceList(row_factory=self._make_atlas_row)
        self.atlas_list.itemClicked.connect(self._on_atlas_row_clicked)

        self.atlas_section = Section(
            "ATLAS", self.atlas_list,
            on_add=self.atlas_add_clicked.emit,
            add_tooltip="Upload an ROI atlas for ROI analysis",
        )
        self.atlas_upload_button = self.atlas_section.add_button

        left_panel_layout.addWidget(self.atlas_section)
        self.refresh_atlas_list()

        # === Analysis mask =================================================
        # Dots here, unlike the atlas section: exactly one mask applies to the
        # active statmap at a time. The dot follows the ACTIVE statmap, so it
        # moves when you switch maps if they use different masks.
        self._mask_sources = []
        self.mask_list = ResourceList(row_factory=self._make_mask_row)
        self.mask_list.itemClicked.connect(self._on_mask_row_clicked)

        self.mask_section = Section(
            "ANALYSIS MASK", self.mask_list,
            on_add=self.mask_add_clicked.emit,
            add_tooltip="Upload a brain mask for the selected statistical map",
        )
        self.mask_upload_button = self.mask_section.add_button

        left_panel_layout.addWidget(self.mask_section)
        self.refresh_mask_list()

        left_panel_layout.addStretch()

        self.left_panel_container = QWidget()
        self.left_panel_container.setLayout(left_panel_layout)
        self.left_panel_container.setFixedWidth(_RAIL_WIDTH)
        self.left_panel_container.setStyleSheet(
            f"background-color: {_RAIL_BG}; border-radius: 8px;"
        )

        QTimer.singleShot(0, self.refresh_markers)

    # ----------------------------------------------------------------------
    # Row factories
    # ----------------------------------------------------------------------

    def _make_template_row(self, name, index):
        """
        Template row. The statmap-as-background entry gets a 'raw data' badge
        — it used to appear as an unexplained third filename in the list.
        """
        badge = ""
        if index == getattr(self.brain_nav, 'data_bg_index', None):
            badge = "raw data"
        row = ResourceRow(name, badge=badge)
        row.set_active(index == self.brain_nav.file_nr_template)
        return row

    def _make_atlas_row(self, name, index):
        badge = "built-in" if index == 0 else "user"
        colour = _TEXT_DIM if index == 0 else _ACCENT
        return ResourceRow(name, badge=badge, badge_colour=colour, show_dot=False)

    def _make_mask_row(self, name, index):
        source = self._mask_sources[index]
        kind = source.get('kind')
        if kind == 'auto':
            row = ResourceRow(name, badge="auto")
            row.setToolTip(
                "Default: every voxel that is neither NaN nor exactly zero "
                "(the R ARIbrain rule)."
            )
        elif kind == 'legacy':
            row = ResourceRow(name, badge="legacy", badge_colour=_TEXT_DIM)
            row.setToolTip(
                "How projects saved before the mask fix were analysed: every "
                "non-NaN voxel, including the empty space around the brain. "
                "Click 'Non-zero voxels' to re-analyse this map with the default."
            )
        else:
            row = ResourceRow(name, badge="user", badge_colour=_ACCENT)
            row.setToolTip(source.get('full_path', name))
        return row

    @staticmethod
    def _same_mask(a, b):
        if a.get('kind') != b.get('kind'):
            return False
        return a.get('kind') != 'user' or a.get('full_path') == b.get('full_path')

    def refresh_mask_list(self):
        """
        Re-list the analysis masks: the automatic rule, every uploaded mask,
        and a 'legacy' entry while any loaded statmap still uses the old
        non-NaN-only mask (projects saved before the mask fix).

        Uploaded masks come from the session list and from the statmaps
        themselves, so a reopened project shows the masks it was analysed
        with even though the upload happened in an earlier session.
        """
        if not hasattr(self, 'mask_list'):
            return
        bn = self.brain_nav
        statmap_sources = [NiftiLoader.mask_source_of(info)
                           for info in bn.fileInfo.values()]

        sources = [dict(AUTO_MASK_SOURCE)]
        for src in list(getattr(bn, 'userMasks', [])) + statmap_sources:
            if src.get('kind') == 'user' and not any(
                    self._same_mask(src, s) for s in sources):
                sources.append(dict(src))
        if any(src.get('kind') == 'legacy' for src in statmap_sources):
            sources.append(dict(LEGACY_MASK_SOURCE))

        labels = {'auto': "Non-zero voxels", 'legacy': "All non-NaN voxels"}
        self._mask_sources = sources
        self.mask_list.clear()
        for src in sources:
            self.mask_list.addItem(labels.get(src['kind'], src.get('filename', 'mask')))
        self.refresh_markers()

    def _on_mask_row_clicked(self, item):
        """
        Re-analyse the active statmap with the clicked mask (after a
        confirmation — it is a full ARI re-run). Clicking the mask already in
        use does nothing.
        """
        index = self.mask_list.row(item)
        if not 0 <= index < len(self._mask_sources):
            return
        source = self._mask_sources[index]
        bn = self.brain_nav
        active = NiftiLoader.mask_source_of(bn.fileInfo.get(bn.file_nr, {}))
        if self._same_mask(source, active):
            return
        if source.get('kind') == 'legacy':
            # Listed so an old project's state is visible, not as something
            # to choose for new analyses.
            bn.message_box.info(
                "The legacy mask is listed because a loaded project was "
                "analysed with it. Choose 'Non-zero voxels' or an uploaded "
                "mask to re-analyse."
            )
            self.refresh_markers()
            return
        bn.upload_files.apply_mask_and_rerun(source)
        self.refresh_markers()

    def refresh_atlas_list(self):
        """
        Re-list the atlases: the bundled AAL2 plus the user atlas when one is
        loaded. The old rail hardcoded a single 'AAL2' entry that never
        changed, so after uploading an atlas the section was simply wrong.

        Called on init, after an atlas upload, and after a project load.
        """
        if not hasattr(self, 'atlas_list'):
            return
        self.atlas_list.clear()
        self.atlas_list.addItem('AAL2')

        user_atlas = getattr(self.brain_nav, 'userAtlasInfo', None)
        if user_atlas:
            entry = next(iter(user_atlas.values()))
            self.atlas_list.addItem(entry.get('filename', 'user atlas'))

    # ----------------------------------------------------------------------
    # Activation — single click, guarded
    # ----------------------------------------------------------------------

    def _on_stat_row_clicked(self, item):
        """
        Single click activates. Re-clicking the live map is a no-op: a statmap
        switch re-runs thresholding lookups and can raise a modal prompt, so
        it is not something to repeat by accident.
        """
        if self.stat_images_list.row(item) == self.brain_nav.file_nr:
            return
        with self._busy():
            self.set_selected_item()
        self.refresh_markers()

    def _on_template_row_clicked(self, item):
        """Single click activates; re-clicking the live template is a no-op."""
        if self.template_list.row(item) == self.brain_nav.file_nr_template:
            return
        with self._busy():
            self.set_selected_template()
        self.refresh_markers()

    def _on_atlas_row_clicked(self, item):
        """
        Atlas rows aren't activated — both atlases are live at once. Clicking
        the user atlas jumps to the ROI Analysis tab, which is the only place
        it can actually be worked with.
        """
        if self.atlas_list.row(item) == 0:
            return
        tabs = getattr(self.brain_nav, 'initiate_tabs', None)
        if tabs is not None and hasattr(tabs, 'roi_analysis_tab_index'):
            tabs.tab_widget.setCurrentIndex(tabs.roi_analysis_tab_index)

    @contextmanager
    def _busy(self):
        """
        Wait cursor and a frozen rail for the duration of a switch. Both
        switches do real work (resampling, table rebuilds, 3D re-render);
        without this the rail stays clickable and a second click can land
        mid-switch.
        """
        QApplication.setOverrideCursor(Qt.WaitCursor)
        self.stat_images_list.setEnabled(False)
        self.template_list.setEnabled(False)
        try:
            yield
        finally:
            self.stat_images_list.setEnabled(True)
            self.template_list.setEnabled(True)
            QApplication.restoreOverrideCursor()

    def refresh_markers(self):
        """
        Repaint the activation dots from the authoritative state on BrainNav,
        rather than trusting the list's own selection. Safe to call at any
        time; cheap.
        """
        for i, row in enumerate(self.stat_images_list.rows()):
            if row is not None:
                row.set_active(i == self.brain_nav.file_nr)

        data_bg_index = getattr(self.brain_nav, 'data_bg_index', None)
        for i, row in enumerate(self.template_list.rows()):
            if row is None:
                continue
            row.set_active(i == self.brain_nav.file_nr_template)
            row.set_badge("raw data" if i == data_bg_index else "")

        # Analysis mask: the one used by the active statmap.
        if hasattr(self, 'mask_list'):
            active = NiftiLoader.mask_source_of(
                self.brain_nav.fileInfo.get(self.brain_nav.file_nr, {})
            )
            for i, row in enumerate(self.mask_list.rows()):
                if row is not None and i < len(self._mask_sources):
                    row.set_active(self._same_mask(self._mask_sources[i], active))

    def set_selected_item(self):
        """
        Sets the selected statistical image and updates related UI components.
        
        This method retrieves the selected item from `stat_images_list`, updates the internal
        file index (`self.file_nr`), and displays relevant information and metrics for the selection.
        
        Functionality:
        - **Selection Retrieval:** Fetches the currently selected item in `stat_images_list` and sets `self.file_nr`
          to the corresponding row index.
        - **Item Display:** Prints the file name of the selected item for debugging or informational purposes.
        - **Metrics Display and Viewer Setup:** Calls `Metrics.show_metrics` to display metrics associated with
          the selected item and `OrthViewSetup.setup_viewer` to configure the viewer accordingly.
        - **Empty Selection Handling:** Prints a message if no item is selected.
        """
        prev_file_nr        = self.brain_nav.file_nr
        fileInfo            = self.brain_nav.fileInfo
        file_nr             = self.brain_nav.file_nr
        file_nr_template    = self.brain_nav.file_nr_template

        selected_items = self.stat_images_list.selectedItems()
        if selected_items:

            # store last selected thresholding method with conditional check, brain_nav.file_nr has not been updated yet
            if 'last_thresholding_method' in fileInfo[file_nr]:
                fileInfo[file_nr]['last_thresholding_method'] = self.brain_nav.initiate_tabs.thresholding_dropdown.currentText()
            else:
                fileInfo[file_nr]['last_thresholding_method'] = "TDP-based"

            selected_item = selected_items[0]
            
            # Get the index of the selected item in the list, file_nr is now updated
            file_nr = self.stat_images_list.row(selected_item)
            self.brain_nav.file_nr = file_nr
            
            self.switch_rawData_template()  # updates: template list with the selected statmap

            # It's possbile that the user has changed to a template for which the the overla data was not computed beyond the gradient map.
            gradmap = self.brain_nav.aligned_statMapInfo.get((file_nr, file_nr_template), {}).get('gradmap_flag', None)
            clusterlist_exists = 'clusterlist' in fileInfo[file_nr]

            if gradmap is True and clusterlist_exists:
                self.brain_nav.message_box.warn("No clustermap computed for selected template, do you want to do this now?")
                print("\033[38;5;214m"  # Orange terminal output
                      "Warning: No clustermap computed for selected template, do you want to compute it now?\033[0m")
                
                # Show dialog asking user whether to proceed
                dialog = QMessageBox(self.brain_nav)
                dialog.setWindowTitle("No clustermap found for selected template image")
                dialog.setText("No clustermap computed for selected template. Do you want to compute it now?")
                dialog.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
                dialog.setDefaultButton(QMessageBox.Ok)
                
                response = dialog.exec_()
                
                if response == QMessageBox.Ok:
                    self.set_selected_template()
                else:
                    self.brain_nav.file_nr = prev_file_nr
                    return

            if gradmap is True and not clusterlist_exists:
                # Show dialog with three options: Compute, Review, Cancel
                dialog = QMessageBox(self)
                dialog.setWindowTitle("No thresholding performed")
                dialog.setText("No thresholding has been done for this statistical map.\n"
                            "Would you like to compute it now, or review the gradient map first?")
                compute_button = dialog.addButton("Compute", QMessageBox.AcceptRole)
                review_button = dialog.addButton("Review Gradient Map", QMessageBox.ActionRole)
                cancel_button = dialog.addButton(QMessageBox.Cancel)

                dialog.setDefaultButton(compute_button)
                dialog.exec_()

                clicked_button = dialog.clickedButton()
                
                if clicked_button == compute_button:
                    self.brain_nav.WBTing.update_threshold_label(float(self.brain_nav.WBTing.tdp_textbox1.text()))
                elif clicked_button == review_button:
                    self.brain_nav.orth_view_setup.setup_viewer()
                    return
                elif clicked_button == cancel_button:
                    return

            item_widget = self.stat_images_list.itemWidget(selected_item)
            print(f"Selected item: {item_widget.file_name_label.text()}")

            # update the file_nr in the brain_nav object to the selected one
            # self.brain_nav.file_nr = file_nr

            # # Display metrics and set up the viewer
            self.brain_nav.tblARI.clear_table()          # clear the table
            self.brain_nav.UIHelp.refresh_ui()           # updated: ari table, 3dviewer, metrics, orthoview
            self.brain_nav.UIHelp.update_ui_xyz()        # updates: spinboxes    
            self.brain_nav.cluster_ws.update_work_station(selected_row=None)  # updates: workstation table and cluster tdp slider and box - requires selected row
            self.brain_nav.tblROI.sync_to_active_statmap()  # updates: ROI table, heatmap LUT, ROI selection
            

            # set the whole brain tresholdslider to the selected statmap (this is in sunch with the table etc.)
            method = self.brain_nav.fileInfo[self.brain_nav.file_nr].get('last_thresholding_method')
            if method is not None:
                self.brain_nav.WBTing.reset_threshold_slider(method)

            self.refresh_markers()
            self.brain_nav.message_box.info(f"Selected Map: {item_widget.file_name_label.text()}")
        else:
            print("No item selected")


    def switch_rawData_template(self):
        """
        Updates the statMap template name in the template list UI to match its filename.

        Assumes statMap entry is located at `self.data_bg_index` (an integer key).
        """
        # change the templates entry of the statmap to the currently selected one
        statmap_index = self.brain_nav.data_bg_index        
        self.brain_nav.templates[statmap_index] = self.brain_nav.statmap_templates[self.brain_nav.file_nr]

        # update the name in the UI list — item text AND row widget, or the
        # rail keeps showing the previous statmap's filename as the raw-data
        # background.
        statmap_name = self.brain_nav.templates[statmap_index]['filename']
        self.template_list.set_row_name(statmap_index, statmap_name)

    def set_selected_template(self):
        """
        Handles the selection of a new template from the template list.

        When a user selects a template, this function:
        - Retrieves the selected template's index.
        - Clears the current 3D scene.
        - Reinitializes the orthogonal viewer.
        - Recomputes and updates the table containing cluster metrics.
        - Restores the last selected cluster overlay (if any).
        - Updates the 3D cluster view and displays associated metrics.
        """

        # Get the selected item(s) from the template list
        selected_items = self.template_list.selectedItems()

        if selected_items:
            # Keep the xyz of the previous template ui space
            xprev, yprev, zprev = self.brain_nav.sagittal_slice, self.brain_nav.coronal_slice, self.brain_nav.axial_slice
            xyz_prev = (xprev, yprev, zprev)

            # Get cluster id based on currenty xyz position. If no clusterID return None.
            # this will retrieve a cluster even if not selected. Might not be ideal here
            # clusID = self.get_selected_cluster_id()

            if self.brain_nav.ui_params['selected_cluster_id']:
                clusID = self.brain_nav.ui_params['selected_cluster_id']
            else:
                clusID = None

            # Pick the first selected item
            selected_item = selected_items[0]

            # save previous template index
            file_nr_template_prev = self.brain_nav.file_nr_template
            
            # Save the index of the newly selected template
            self.brain_nav.file_nr_template = self.template_list.row(selected_item)

            # Clear the 3D view scene to prepare for new cluster display
            self.brain_nav.threeDviewer.cluster_3d_view.clear()

            # Reinitialize the orthogonal viewer with correct UI, slices, and 3D view
            self.brain_nav.orth_view_setup.setup_viewer()

            # Load the list of clusters for the selected template
            try:
                clusterlist = self.brain_nav.fileInfo[self.brain_nav.file_nr]['clusterlist']
            except KeyError:
                clusterlist = None

            # Skip cluster table/overlay rendering when no thresholding has run
            # yet for this statmap — prepare_tblARI returns an empty 4-tuple in
            # that case, and update_clust_img / update_table aren't meaningful
            # without real cluster data.
            if clusterlist:
                ord_clusterlist, _, tblARI_df, _ = self.brain_nav.metrics.prepare_tblARI(clusterlist)
                _, _, tblARI_df = self.brain_nav.metrics.update_clust_img(ord_clusterlist, tblARI_df)
                self.brain_nav.tblARI.update_table(tblARI_df)
            else:
                self.brain_nav.tblARI.clear_table()

            # Remap the xyz coordinates from old to new template ui space
            self.brain_nav.UIHelp.remap_ui_xyz(self.brain_nav.file_nr, xyz_prev, file_nr_template_prev, self.brain_nav.file_nr_template)

            # update_overlay_image re-aligns fileInfo['img_clus'] onto the new
            # template. Before any thresholding has run there is no cluster
            # image at all — the viewer is showing the gradient map — and this
            # raised KeyError: 'img_clus'. The branch above already recognises
            # that state for the table; the overlay and the gradmap flag below
            # need the same treatment.
            has_cluster_image = (
                self.brain_nav.fileInfo[self.brain_nav.file_nr].get('img_clus')
                is not None
            )
            if has_cluster_image:
                self.brain_nav.metrics.update_overlay_image(self.brain_nav.file_nr, clusID)

            # Centroids in the ROI table are display-grid voxel coordinates,
            # so they belong to the template we just left. Rewrite them for
            # the new one (TDP and Size are grid-independent and stay put).
            self.brain_nav.metrics.refresh_roi_centroids()

            self.brain_nav.orth_view_update.update_crosshairs()

            if clusID is not None:
                # Reset any previously highlighted cluster
                self.brain_nav.tblARI.reset_highlight()

            #     # Find the row in the table corresponding to the selected cluster
            #     selected_row = tblARI_df[tblARI_df['Unique ID'] == clusID].index[0]

            #     # Center the view and metrics on the selected cluster
            #     self.metrics.follow_cluster_xyz(selected_row) # also calls show_metrics

            # Show the cluster metrics in the UI
            self.brain_nav.metrics.show_metrics()

            # Render the selected cluster in the 3D view
            self.brain_nav.threeDviewer.update_cluster_3d_view(clusLabel=clusID)
            
            # gradmap_flag is no longer set here: Metrics.update_overlay_image
            # writes it alongside overlay_data, which is the only moment the
            # two can be guaranteed consistent. Clearing it here as well was
            # both redundant and, when no cluster image existed, wrong — it
            # told the renderer to stop drawing the gradient map without
            # giving it anything to draw instead.

            self.refresh_markers()
            self.brain_nav.message_box.info(
                f"Template switched to: {selected_item.text()}"
            )


    def add_template_to_list(self, file_path):
        """Add a new template to the template list widget."""
        item_name = os.path.basename(file_path)
        # str overload, so ResourceList's row_factory installs the row widget.
        self.template_list.addItem(item_name)
        self.template_list.setCurrentRow(self.template_list.count() - 1)

    def add_statmap_to_list(self, full_path):
        # Add items with custom widgets
        base_name = os.path.basename(full_path)
        base_dir = os.path.basename(os.path.dirname(full_path))

        # item_widget = StatImageItem(f"{base_dir}/{base_name}")
        item_widget = StatImageItem(f"{base_name}")
        item = QListWidgetItem(self.stat_images_list)
        item.setSizeHint(item_widget.sizeHint())
        self.stat_images_list.setItemWidget(item, item_widget)
        self.brain_nav.stat_image_items.append(item_widget)  # Store reference
        QTimer.singleShot(0, self.refresh_markers)

    def update_ari_status(self, completed=False):
        for item in self.brain_nav.stat_image_items:
            item.update_ari_status(completed)

    

class StatImageItem(ResourceRow):
    """
    A statistical-image row: activation dot, middle-elided filename, ARI badge.

    Kept as a named class with the same constructor and the same
    `file_name_label` / `update_ari_status` surface because main_window and
    save_and_export build these directly when restoring a session, and
    save_project reads names back off `file_name_label.text()`.

    The ARI badge used to be pushed off the right edge by the untruncated
    filename, so the one thing it existed to communicate was never visible.
    Middle elision on the name keeps it in view at any rail width.
    """

    def __init__(self, file_name):
        super().__init__(file_name, badge="ARI", badge_colour=_TEXT_DIM)
        self.ari_label = self.badge_label
        self.update_ari_status(False)

    def update_ari_status(self, completed=False):
        """Green once ARI has run for this map, dim until then."""
        self.set_badge("ARI \u2713" if completed else "ARI \u2013",
                       _ACCENT if completed else _TEXT_DIM)
