# User-uploaded atlas → ROI-level TDP

Implementation plan for letting users upload an integer-labelled atlas NIfTI,
visually verify the alignment on the orthoviews, and run an ROI-level
true discovery proportion (TDP) analysis driven by the existing ARI
machinery.

This document is the design contract. Open questions are listed at the
bottom; resolve them before starting Phase 2.

---

## 1. Background: how the existing pipeline already handles this shape of data

Upload → load → align is the same three-step dance for statmaps,
templates, and the built-in AAL2 atlas. Each path differs only in where
the result lands on `BrainNav`.

| Surface          | Entry                                                  | Loader                                                                                    | Key transform                                                          | Lands on                                                       |
|------------------|--------------------------------------------------------|-------------------------------------------------------------------------------------------|------------------------------------------------------------------------|----------------------------------------------------------------|
| Statmap          | [upload_files.py:72](../ari_application/ui/components/upload_files.py#L72) | [nifti_loader.py:264](../ari_application/models/nifti_loader.py#L264) `load_overlay`      | `as_closest_canonical` + `align_images(template, overlay, order=0)`    | `fileInfo[file_nr]` + `aligned_statMapInfo[(file_nr, template)]` |
| Template         | [upload_files.py:110](../ari_application/ui/components/upload_files.py#L110) | [nifti_loader.py:25](../ari_application/models/nifti_loader.py#L25) `load_bg`             | `as_closest_canonical`; align statmaps **to** it                       | `templates[file_nr_template]`                                  |
| Atlas (built-in) | implicit, during `load_bg`                             | [nifti_loader.py:222](../ari_application/models/nifti_loader.py#L222) `load_atlases`      | `as_closest_canonical` + `align_images(template, atlas, order=0)`      | `atlasInfo[file_nr_template]` or `atlasInfo[('data_as_template', file_nr)]` |

The single most important detail:
[`ImageProcessing.align_images(..., order=0)`](../ari_application/models/image_processing.py#L259)
uses nearest-neighbour resampling, which preserves integer labels.
That's already the right primitive for atlases — `load_atlases` uses it.

Dimension/orientation handling is currently implicit:
`as_closest_canonical` forces RAS+, and `align_images` resamples
whatever shape comes in onto the template's grid. There is no explicit
shape check; the atlas pipeline will add one (warn-only, mirroring the
orientation-info line the team has been migrating toward).

ARI itself stashes on `fileInfo[file_nr]`: sorted p-values, `sorter`,
`indexp`, `halpha`, `alpha`, `simeshalpha`, `m`, and per-voxel `tdps`.
That is everything an ROI-TDP routine needs — no second ARI run, just
one more Cython call per ROI.

---

## 2. Scope

### In scope (Phase 1)
- Atlas is a 3D integer-labelled NIfTI. Non-zero voxels carry an ROI
  label; voxels with the same integer are one ROI; `0` is background.
- "All ROIs included" mode: every voxel of interest is in *some*
  labelled ROI. Sparse atlases (where chunks of the brain mask have
  label `0` and should be excluded) work for free because we iterate
  non-zero labels — but UX assumes full coverage.
- One user atlas active at a time per `(file_nr, file_nr_template)`
  pair. The user atlas coexists with the built-in AAL2 — they live in
  separate dicts.
- Entry point in the UI: the **Anatomical Atlas** option in the
  thresholding dropdown on the Whole Brain TDP tab
  ([initiate_tabs.py:79](../ari_application/ui/components/tabs/initiate_tabs.py#L79)).
- Visual verification before computing anything: render the aligned
  atlas as a coloured overlay on the orthoviews so the user can confirm
  it lines up with the template before TDPs are computed.

### Out of scope (this PR)
- Probabilistic / continuous atlases.
- Multi-atlas analyses (one user atlas at a time).
- Editing the codebook from the UI.
- The "User-specified cluster map" dropdown option — separate feature.

### Branch note
This branch (`feature/atlas-based-tdp-computation`) is cut from `main`
and does **not** contain the leveled `MessageLogger` from
`feature/enhanced-error-logging`. All user-facing log lines here use
the existing `self.brain_nav.message_box.log_message(...)` API.

---

## 3. End-to-end user flow

1. User selects **Anatomical Atlas** from the Whole Brain TDP dropdown.
   Advisory text updates; an **Upload Atlas** button appears beneath it.
2. User clicks Upload Atlas, picks a `.nii` / `.nii.gz`. The loader
   runs `as_closest_canonical`, validates shape, aligns it to every
   loaded template with `align_images(..., order=0)`, and builds a
   codebook (either from an optional sidecar `.txt` or auto-generated
   `ROI N` names).
3. The orthoviews immediately switch to an **atlas-overlay mode** — the
   aligned atlas is rendered on the template with one stable colour per
   ROI label. The cluster overlay is hidden in this mode.
4. User visually confirms alignment. If something's wrong, they upload
   a different atlas — the previous one is replaced.
5. User clicks **Run ROI Analysis** (button in the Whole Brain TDP tab
   under the atlas section). This calls `compute_roi_tdps`, which loops
   the codebook and calls `py_findDiscoveries` per ROI.
6. A new ROI results table (`TblROI`) is populated. Selecting a row
   focuses the orthoviews on that ROI's centroid and prints the TDP
   plus ROI metadata to the workstation panel.

---

## 4. Data structures

### 4.1 New top-level dict on `BrainNav`
```python
self.userAtlasInfo[(file_nr, file_nr_template)] = {
    'filename':      str,          # basename
    'full_path':     str,
    'data':          np.ndarray,   # aligned int label volume, same grid as the template
    'codebook':      dict,         # {int label -> "Region name"}
    'original_affine': np.ndarray, # before resample, for diagnostics
    'lut':           np.ndarray,   # 256x4 uint8 RGBA LUT, one stable colour per label
    'tdps_per_roi':  dict | None,  # {int label -> float tdp}; None until computed
}
```
Stored as a separate dict (not folded into `atlasInfo`) so the existing
AAL2 readout at [metrics.py:87-98](../ari_application/models/metrics.py#L87)
is untouched. If we later want unified atlas storage that's a Phase 3
refactor.

### 4.2 New entry on `fileInfo[file_nr]`
```python
fileInfo[file_nr]['tblROI_df']  # pandas DataFrame, populated by compute_roi_tdps
```
Columns: `["ROI", "Label", "Size (vox)", "TDP", "max(Z)", "Region", "Centroid (vox)", "Centroid (MNI)"]`.

### 4.3 New entry on `ui_params`
```python
ui_params['overlay_mode']         # 'cluster' | 'atlas' | 'roi'
ui_params['selected_roi_label']   # int | None
```
- `'cluster'` — existing behaviour, cluster overlay drawn from `img_clus`.
- `'atlas'` — verification view; aligned atlas drawn from `userAtlasInfo[...]['data']` with the ROI LUT.
- `'roi'` — post-analysis view; same atlas overlay, but with the
  selected ROI at full alpha and the others dimmed (matches the
  cluster-selection styling at [orth_view_update.py:298-313](../ari_application/orth_views/orth_view_update.py#L298)).

---

## 5. Implementation steps

Each step compiles and can be tested independently. Commit after each.

### Step 1 — Scaffold and wire entry points

**Files**: `main_window.py`, `initiate_tabs.py`, `whole_brain_thresholding.py`, `upload_files.py`.

- Add `self.userAtlasInfo = {}` to `BrainNav.__init__`.
- Add `ui_params['overlay_mode'] = 'cluster'` default.
- In `initiate_tabs.py`, immediately under the thresholding dropdown,
  build a vertical container `atlas_section` with two widgets:
  - `QPushButton("Upload Atlas")`
  - `QPushButton("Run ROI Analysis")` (disabled until an atlas is loaded)
  Both hidden by default; `setVisible(True)` only when the dropdown is
  "Anatomical Atlas".
- Wire the upload button to a new
  `UploadFiles.upload_atlas_dialog` (currently a `pass` stub at
  [upload_files.py:128](../ari_application/ui/components/upload_files.py#L128)).
- Wire `thresholding_dropdown.currentIndexChanged` (in
  `WBTing.update_threshold_option` or a new handler) to toggle the
  atlas section's visibility based on the current selection.

Verification: launch the app, switch the dropdown to "Anatomical Atlas",
confirm the new buttons appear; switch back, confirm they disappear.

### Step 2 — Atlas loader

**Files**: `nifti_loader.py`, `upload_files.py`.

- Implement `NiftiLoader.load_user_atlas(file_path)`. Mirror
  `load_atlases` ([nifti_loader.py:222](../ari_application/models/nifti_loader.py#L222))
  but parameterise by user-supplied path.
  1. `nib.load(file_path)` inside try/except → on failure, `log_message`
     with a clear error string and return early.
  2. `nib.as_closest_canonical(image)`.
  3. Validate:
     - Must be 3D.
     - Must be castable to int (warn if floats are passed; `np.round` and
       cast).
     - Log shape + axcodes the same way `load_overlay` logs statmap
       orientation; warn if the affine doesn't match the active
       template's affine within tolerance (the alignment will still
       proceed via nearest-neighbour resample — this is just a heads-up).
  4. For each loaded template *and* the data-as-template entry, run
     `aligned_atlas, _ = ImageProcessing.align_images(template_image, atlas_image, order=0)`,
     then apply the same transpose / rotation that `load_atlases`
     applies to keep axes consistent.
  5. Codebook:
     - If a sidecar `<basename>.txt` exists in AAL2 format, parse it.
     - Else `codebook = {int(lbl): f"ROI {int(lbl)}" for lbl in np.unique(aligned_atlas[aligned_atlas > 0])}`.
  6. Build a stable LUT: cycle through `pg.colormap` or a
     deterministic HSV palette (`colorsys.hsv_to_rgb` over the number
     of ROIs). Index 0 maps to transparent. Store as a `256×4 uint8`
     RGBA array (same shape as `fileInfo['custom_lut']` so it slots into
     the existing renderer).
  7. Write `userAtlasInfo[(file_nr, file_nr_template)] = {...}` for the
     active pair *and* for every other `(file_nr, t)` pair, so template
     switching keeps showing the atlas.
- Implement `UploadFiles.upload_atlas_dialog`:
  - File dialog → `nifti_loader.load_user_atlas(path)`.
  - On success: log "Atlas loaded: <name>, N ROIs", set
    `ui_params['overlay_mode'] = 'atlas'`, enable the "Run ROI
    Analysis" button, call `orth_view_update.update_slices()`.

Verification: load an atlas, confirm the message log line and that no
exception fires. Don't yet expect anything to render — that's Step 3.

### Step 3 — Visual verification on the orthoviews

**Files**: `orth_view_update.py`, possibly `orth_view_setup.py`.

The cluster overlay path at
[orth_view_update.py:249-380](../ari_application/orth_views/orth_view_update.py#L249)
consumes an integer label map + a LUT and draws coloured regions on
each slice. An ROI label map is already shaped exactly like `img_clus`,
so the same path renders both — we just need to choose which array and
which LUT to feed it based on `ui_params['overlay_mode']`.

- Refactor `add_overlay_with_transparency` (or whichever function reads
  `img_clus` + `custom_lut`) so it accepts a `(label_volume, lut,
  highlight_label)` argument bundle instead of hard-coding the cluster
  variants. Keep a thin wrapper for the cluster path so existing call
  sites don't change.
- Add a branch in `update_slices`:
  - `mode == 'cluster'` → existing behaviour.
  - `mode == 'atlas'` → render `userAtlasInfo[(file_nr, file_nr_template)]['data']`
    with `userAtlasInfo[...]['lut']` and `highlight_label = None`
    (all labels at uniform alpha).
  - `mode == 'roi'`  → same data and LUT, but
    `highlight_label = ui_params['selected_roi_label']` so selection
    transparency works.
- The template renders unchanged underneath; we're only swapping the
  overlay layer.

Verification: load an atlas with a known orientation (e.g. AAL2 itself
as a user atlas), confirm each ROI appears in its own colour, confirm
the colours stay stable when scrubbing slices, confirm switching
templates re-renders the atlas at the new template's grid.

### Step 4 — ROI-level TDP computation

**Files**: `metrics.py` (or a new `analyses/roi_tdp.py`).

- Add `Metrics.compute_roi_tdps(file_nr, file_nr_template)`. Inputs are
  read from `fileInfo` and `userAtlasInfo`; output is written to
  `userAtlasInfo[...]['tdps_per_roi']` and
  `fileInfo[file_nr]['tblROI_df']`.

The math, given `S` = voxel set for one ROI:

```
TDP(S) = py_findDiscoveries(idx_sorted_for_S, sorted_p,
                            simeshalpha, halpha, alpha,
                            len(S), m)[-1] / len(S)
```

Pre-loop setup (runs once for the whole atlas):
- `sorter = fileInfo[file_nr]['sorter']`              (from pyHommel)
- `sorted_p = fileInfo[file_nr]['sorted_p']`
- `halpha = fileInfo[file_nr]['halpha']`
- `simeshalpha = fileInfo[file_nr]['simeshalpha']`
- `alpha = fileInfo[file_nr]['alpha']`
- `m = fileInfo[file_nr]['m']`
- `mask = fileInfo[file_nr]['mask']`
- `ix_sorted = np.zeros(m, dtype=int); ix_sorted[sorter] = np.arange(1, m+1)`
  — **1-based** (see [docs/BUG_REPORT_hommel_indexing.md](BUG_REPORT_hommel_indexing.md);
  the Cython side subtracts 1 internally).

Per-label loop:
- `S = np.flatnonzero((atlas == label) & mask)`
  (flat indices into the m-voxel mask).
- Skip if `|S| == 0`.
- `idx = ix_sorted[S].tolist()`
- `disc = py_findDiscoveries(idx, sorted_p, simeshalpha, halpha, alpha, len(S), m)`
- `tdp = disc[-1] / len(S)`

Build `tblROI_df`:
- `"ROI"`         — display name from codebook
- `"Label"`       — int label
- `"Size (vox)"`  — `|S|`
- `"TDP"`         — `tdp` (0–1, two decimals)
- `"max(Z)"`      — peak statistic value within S, from
                    `aligned_statMapInfo[(file_nr, t)]['overlay_data']`
- `"Region"`      — same as ROI name (kept for parity with `tblARI_df`)
- `"Centroid (vox)"` — mean of S coords in template grid space
- `"Centroid (MNI)"` — centroid mapped through
                       `aligned_templateInfo[(file_nr, t)]['rtr_template_affine']`

Wire the **Run ROI Analysis** button to call `compute_roi_tdps`, then
populate the ROI table.

Verification: log the resulting `tblROI_df` to the message box so you
can sanity-check values before the table widget exists. Compare against
hand-computed TDPs for a small synthetic atlas (two ROIs, known voxel
sets) before trusting it on real data.

### Step 5 — ROI results table widget

**Files**: new `ui/components/tabs/tblROI.py`, registration in `main_window.py`.

- Clone `TblARI` ([ui/components/tabs/tblARI.py](../ari_application/ui/components/tabs/tblARI.py))
  into `TblROI` with the column set from Step 4.
- Selection behaviour: on row select, set
  `ui_params['selected_roi_label']`, set
  `ui_params['overlay_mode'] = 'roi'`, and call a new
  `Metrics.follow_roi_xyz(label)` that picks the ROI centroid (or
  peak-Z voxel) and moves the crosshair there before
  `update_slices()`.
- Tab placement: a second tab next to TblARI inside the existing
  cluster-table area, labelled "ROIs". Empty until `compute_roi_tdps`
  runs.

Verification: load atlas → run analysis → confirm the ROI table
populates, confirm row selection moves the crosshair and dims the other
ROIs in the overlay.

### Step 6 — Persistence and re-runs

**Files**: `save_and_export.py`, `start_window.py`, possibly `ARI.py`.

- Add `userAtlasInfo` to the dict pickled by `save_project` and
  unpickled by `load_project` / `StartWindow.load_project_from_start`.
  Tag it with a version so future codebooks (e.g. sparse atlas
  support) can migrate.
- Re-run `compute_roi_tdps` automatically at the end of:
  - `pyARI.runARI` (so TDPs refresh when the statmap changes), guarded
    on the existence of a user atlas for the active pair.
  - `LeftSideBar.set_selected_template` after the template-switch
    settles.
  - `upload_atlas_dialog` (after loader returns).
- Update the workstation metric panel
  ([metrics.py:87-98](../ari_application/models/metrics.py#L87)) to
  read the user-atlas region under the crosshair in addition to AAL2,
  with the TDP in parens — e.g.
  `"User atlas: frontal_pole_R (TDP=0.83)"`.

Verification: save a project after running ROI analysis, close the
app, load it, confirm the ROI table and atlas overlay are restored.

---

## 6. Edge cases and pre-known footguns

- **Indexing**: `py_findDiscoveries` is 1-based; build `ix_sorted`
  with `np.arange(1, m + 1)`. The cluster-tree path already burned
  this incident — write a small inline assertion in
  `compute_roi_tdps` (`assert ix_sorted.min() == 1`) to catch
  regressions.
- **Atlas voxels outside the brain mask**: ignore. The
  `(atlas == label) & mask` AND-filter handles it; warn in the log if
  more than (say) 10% of an ROI's voxels fall outside the mask, since
  that usually signals a misaligned atlas.
- **Empty ROI**: skip with a debug log; do not insert into
  `tblROI_df`.
- **Label collisions across templates**: not possible — alignment is
  per-template and the codebook is shared, so the same label means the
  same region across all template grids.
- **Re-uploading an atlas**: replace `userAtlasInfo[...]` entirely;
  drop `tblROI_df`; reset `selected_roi_label`.

---

## 7. Commit order (suggested)

1. `feat(scaffold): add userAtlasInfo + atlas section to Whole Brain TDP tab`
2. `feat(atlas-loader): load and align user atlases via align_images(order=0)`
3. `feat(orthviews): render user atlas as coloured overlay (verification mode)`
4. `feat(roi-tdp): compute per-ROI TDP via py_findDiscoveries`
5. `feat(tblROI): ROI results table + selection wiring`
6. `feat(atlas-persistence): version userAtlasInfo in .ari project files`

Each commit is independently runnable and reviewable, and the visual
verification step (commit 3) lands before TDPs are computed so the
user gets to confirm the alignment is right before they trust any
numbers.

---

## 8. Open questions

Resolve before starting Phase 2:

1. **Codebook source for atlases without a sidecar `.txt`** — `ROI 1`,
   `ROI 2`, … is the assumed default. Want anything fancier (e.g. try
   to parse NIfTI extension headers, or fall back to the atlas
   filename)?
2. **Overlay mode after analysis runs** — assumed: switch from
   `'atlas'` (verification) to `'roi'` (interactive selection)
   automatically once `compute_roi_tdps` returns. Alternative: stay in
   `'atlas'` until the user clicks a row in `TblROI`.
3. **Cluster overlay alongside ROI overlay?** — current plan: mutually
   exclusive (driven by `overlay_mode`). Alternative: a "both" mode
   with the cluster overlay drawn over the ROI overlay at reduced
   alpha. Useful for sanity-checking ROI ↔ cluster correspondence but
   adds rendering complexity. Phase 1 keeps them exclusive.
4. **Where the Run ROI Analysis button lives** — current plan: under
   the dropdown on the Whole Brain TDP tab, only visible when the
   "Anatomical Atlas" option is selected. Alternative: always-visible
   button in the workstation panel.
