# Backlog

Known bugs and follow-ups that are not fixed yet. Each entry says what the user sees, what causes it, and how we plan to fix it. When you fix one, delete it here and mention the entry in the commit message.

Function names are given rather than line numbers, because line numbers drift.

## ROI / atlas analysis

Found in the review of PR #7 (atlas-based ROI TDP), November 2026.

### Templates and statmaps added after the atlas get no atlas

- **Symptom:** after uploading an atlas, a newly uploaded template has no atlas. The same goes for a newly uploaded statmap shown on its own raw-data background. On those backgrounds the atlas overlay is missing, and Run stops with "No user atlas loaded".
- **Cause:** only `NiftiLoader.load_user_atlas` creates `userAtlasInfo` entries, and it aligns the atlas only to the templates and statmaps that exist at that moment. For a statmap loaded afterwards, `check_file_type` builds its analysis grid (`align_atlas_to_analysis_grids`), but not its display entry.
- **Fix idea:** when a template or statmap is added while `userAtlasImage` is set, align the atlas to it with `_align_atlas_to_template` and store the entry under the same key scheme (`file_nr_template`, or `('data_as_template', file_nr)`).

### Whether an ROI gets a TDP depends on the displayed template

- **Symptom:** a small ROI can be reported as "no overlap" on one background and get a TDP on another.
- **Cause:** `Metrics.compute_roi_tdps` skips any ROI with no centroid in `_roi_centroids`. Those centroids come from the atlas on the *display* grid. A region that disappears when the atlas is resampled onto a coarse background is therefore skipped, even when it has voxels on the analysis grid. The TDP itself is computed on the analysis grid and does not depend on the template; only this skip decision does.
- **Fix idea:** decide whether to skip from `mask_positions` (analysis grid) alone. When the centroid is missing on the display grid, still report the TDP and show the centroid as N/A, as `refresh_roi_centroids` already does.

### Switching template in ROI mode shows the wrong region in 3D

- **Symptom:** select cluster 5, go to the ROI tab, click ROI 12, then switch template. The orth views outline ROI 12, but the 3D view shows atlas label 5. With no cluster selected beforehand, the ROI mesh disappears instead.
- **Cause:** `LeftSideBar.set_selected_template` refreshes the 3D view with `ui_params['selected_cluster_id']`. In `'roi'` overlay mode, `ThreeDViewer.update_cluster_3d_view` treats that number as an atlas label.
- **Fix idea:** in ROI mode, pass `ui_params['selected_roi_label']`.

### ROI centroids go stale for inactive statmaps after a template switch

- **Symptom:** run ROI analysis on maps A and B, switch template while A is active, then select B. B's "Centroid (vox)" and "Centroid (MNI)" columns still hold coordinates from the old template grid, both in the table and in the exported CSV. This is worst on the raw-data background, whose grid differs per statmap.
- **Cause:** `Metrics.refresh_roi_centroids` only rewrites the active statmap's table. `TblROI.sync_to_active_statmap` and `restore_from_session` never refresh centroids.
- **Fix idea:** refresh the centroids in `sync_to_active_statmap`, or recompute them for every statmap on a template switch.

### Atlas stays invisible after uploading with the opacity slider at 0

- **Symptom:** with the opacity slider at 0, upload an atlas or click Run. Raising the slider afterwards never shows the atlas.
- **Cause:** the categorical LUT (`NiftiLoader._build_atlas_lut`) and the heatmap LUT (`Metrics._build_atlas_tdp_lut`) store `int(alpha * 255)` as the alpha of each ROI row. `OrthViewUpdate.add_atlas_overlay` then re-applies the slider alpha only to rows whose alpha is already above 0 (`roi_rows = lut[:, 3] > 0`).
- **Fix idea:** build the LUTs with a fixed non-zero alpha (or a separate "is ROI" mask), and let the renderer apply the slider value.

### Run does not redraw the views

- **Symptom:** after clicking Run, the old ROI contour and 3D ROI stay on screen, and the crosshair readout shows "-" until the crosshair moves. On a re-run with the TDP heatmap selected, the overlay keeps the previous colours.
- **Cause:** `compute_roi_tdps` clears `selected_roi_label`, but `overlay_mode` stays `'roi'` and nothing re-renders (`TblROI` Run handler).
- **Fix idea:** after Run, set `overlay_mode` to `'atlas'`, then call `update_slices`, update the 3D view and refresh the crosshair readout.

### Returning to the ROI tab can show the cluster overlay

- **Symptom:** if the saved ROI has no voxels on the current template, switching back to the ROI tab shows the cluster overlay, and the right-click menu offers cluster actions.
- **Cause:** `Metrics.restore_view_context('roi')` calls `follow_roi_xyz`, which returns early ("has no voxels in the current template") without setting `overlay_mode`.
- **Fix idea:** fall back to `'atlas'` mode when `follow_roi_xyz` cannot select the label.

## Cluster analysis

### 3D viewer crashes when a cluster merges into another

Reported November 2026.

- **Symptom:** select a cluster and lower its TDP with the cluster work station slider until it merges into a neighbouring cluster. The message box shows `ValueError: Empty meshes cannot be plotted. Input mesh has zero points.`, raised from `ThreeDViewer.update_cluster_3d_view` (`add_mesh(grid.threshold(0.5), ...)`).
- **Call chain:** `ClusterWorkStation.update_tdp_from_slider` -> `set_tdp` -> `Metrics.change_cluster_size` -> `ThreeDViewer.update_cluster_3d_view(cluster_label)`.
- **Cause (from reading the code, not yet reproduced in the debugger):** after re-clustering, `change_cluster_size` works out the new cluster under the crosshair (`xyz_clusID`) and updates the table, work station and orth views with it. It still passes the old `cluster_label` to the 3D view. Once that cluster has been absorbed, no voxel carries the old label, so the mesh is empty.
- **Two more problems in the same block:**
  - `xyz_clusID is not ui_params['selected_cluster_id']` compares identity, not value, so it is effectively always true.
  - If the crosshair is in no cluster after the change, `tblARI_df[...].index[0]` raises IndexError.
- **Fix idea:**
  - Pass `xyz_clusID` to the 3D view.
  - In `update_cluster_3d_view`, skip `add_mesh` when the cluster has no voxels. Don't just set `pv.global_theme.allow_empty_mesh`.
  - Compare the cluster IDs with `!=`.
  - Guard the empty-row lookup.

## Other known issues

### One-sided analysis of a p-map raises KeyError

- **Symptom:** a one-sided test on a p-map stops with `KeyError: 'twosided'`.
- **Cause:** `Utilities.getPVals` reads `input['twosided']`, but the key used everywhere else is `twosidedTest`.
- **Fix idea:** read `twosidedTest`, and check the p-map conversion logic in both branches while there. The two-sided branch contains a `twosidedTest == False` check that can never be true.

### Masking follow-ups (PR #8)

- **p-maps with a background of 0.5 or 1** (for example `pvalue.nii`): the auto-mask (non-NaN and non-zero) keeps the background voxels in the analysis. This is conservative, not wrong: it inflates m and lowers TDPs. Uploading a mask handles it.
- **p-maps whose strongest voxels underflowed to exactly 0:** the auto-mask removes those voxels without warning. Uploading a mask avoids it. Document this in the user guide.
- **The masking work was not tested in the real 3D viewer.** Offscreen test runs replace it with a stand-in, because it needs an OpenGL context.
- **`docs/MASKING_FIX_PLAN.md` is out of date.** It describes an earlier, broader plan.

### Cluster decompositions on z.nii differ slightly from R

- **Symptom:** whole-brain numbers match R, but cluster decompositions on z.nii do not.
- **Two competing explanations; check both before fixing:**
  - **Tie order:** the app reorients LAS to RAS before analysis, which changes the order of tied p-values. Run in the file's native orientation, the app matches R exactly.
  - **`forestTDP` sorting:** `forestTDP`/`heavyPathTDP` pass p-values to `findDiscoveries` in voxel order, but it expects them sorted. An earlier investigation found that this, not ties, causes the orientation dependence, and that with sorted input the clusters are identical across orientations.
- **Status:** a fix for the `forestTDP` issue is being brought in from a collaborator's repository; re-test this item after it lands.
