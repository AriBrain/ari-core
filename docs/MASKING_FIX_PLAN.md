# Fixing the analysis mask

Implementation plan for `fix/masking-logic`.

This document explains a problem in how ARIbrain decides which voxels enter
the analysis, why it makes every result more conservative than it needs to
be, and how to fix it. It is written to be readable by anyone on the
project; the technical detail is there where it is needed to be accurate.

---

## 1. The problem in one paragraph

ARIbrain decides which voxels are part of the analysis with a single line:

```python
fileInfo['mask'] = ~np.isnan(fileInfo['data'])      # nifti_loader.check_file_type
```

"Every voxel that is not NaN." Some software writes `NaN` outside the brain,
and for those files this is exactly right. But most software — FSL and SPM
included — writes **zero** outside the brain instead. For those files the
rule selects *the entire image volume*, so all the empty space around the
head is fed into the statistics as if it were brain tissue.

Both of the project's test maps are of the second kind.

---

## 2. What it looks like in practice

Two maps from `NewApp/Data/`, both written by FSL 5.0:

| | `z.nii` | `collection2606_…bart_Accept_orig.nii` |
|---|---|---|
| grid | 91 x 109 x 91 @ 2 mm | 65 x 77 x 49 @ 3x3x4 mm |
| NaNs in the file | **0** | **0** |
| voxels that are exactly 0 | 644,970 (71.5%) | 192,752 (78.6%) |
| voxels the analysis uses today | **902,629 (100%)** | **245,245 (100%)** |
| voxels that are actually brain | 257,673 (28.5%) | 52,493 (21.4%) |

So roughly **three quarters of every analysis is empty space.**

Those empty voxels have a statistic of exactly zero, which becomes a
p-value of exactly 1.0 — the least significant value possible. They can
never become a discovery. But they still count as hypotheses, and in
multiple-testing correction the number of hypotheses (`m`) sets the bar that
evidence has to clear. Padding the analysis with 645,000 guaranteed-null
hypotheses raises that bar for no benefit.

### The cost, measured

Same data, same alpha, the only change being which voxels are in the mask:

| | m | whole-brain TDP bound | total discoveries |
|---|---|---|---|
| `z.nii` today | 902,629 | 0.0439 | 39,644 |
| `z.nii` with a brain mask | 257,673 | **0.1978** | 50,968 |
| `bart_Accept` today | 245,245 | 0.1001 | 24,542 |
| `bart_Accept` with a brain mask | 52,493 | **0.5378** | 28,229 |

For `bart_Accept` the headline result moves from "at least 10% of the
detected signal is real" to "at least **54%** is". Same data. The only thing
that changed is that we stopped asking questions about empty space.

---

## 3. What this does *not* mean

**No result ARIbrain has produced is wrong.** This is important enough to be
unambiguous about.

True Discovery Proportion is reported as a *lower bound*: "at least this
proportion of the voxels in this region are true discoveries". Adding
hypotheses that are genuinely null cannot make that bound too high — it can
only make it too low. Every number the tool has produced is a valid bound;
it is simply a weaker one than the data supports.

The fix recovers statistical power. It does not correct an error.

There is one genuine (small) defect, covered in step 2 below: `~isnan` does
not exclude infinities, and `z.nii` contains two `-inf` voxels that enter
the analysis with a p-value of exactly 0.

---

## 4. Where it shows up

The three analysis paths are affected quite differently, and it is worth
knowing which is which before changing anything.

### Cluster analysis — moderate, invisible

Clusters themselves are **clean**. A voxel with p = 1.0 dragged into a
cluster would lower that cluster's TDP, so the cluster-forming routine never
includes background voxels at any threshold you can reach from the UI.
Measured on `z.nii` at TDP >= 0.05, the single cluster contains exactly the
257,659 non-zero voxels; the only two strays are the `-inf` voxels.

The cost is lost sensitivity, not contamination:

| TDP threshold | clusters today | clusters with mask | voxels today | voxels with mask |
|---|---|---|---|---|
| 0.50 | 15 | 11 | 59,353 | **68,042** (+15%) |
| 0.70 | 18 | 21 | 40,781 | **47,820** (+17%) |

About 16% more of the brain survives any given threshold. The cluster
decomposition also changes — at 0.50 you get fewer, larger clusters, because
regions that were separately sub-threshold merge once the bound tightens.

### ROI analysis — moderate, invisible

The atlas path is barely affected through its own voxel accounting: AAL2 is
brain-shaped, so 98.3% of the voxels it counts are genuinely in brain, and
correcting only the ROI denominators moves no region by more than 0.013 TDP.

It is affected through `m`, like everything else. Recomputing per-ROI TDPs
with a brain mask on `z.nii` + AAL2:

| region | TDP today | TDP with mask | change |
|---|---|---|---|
| Heschl L | 0.396 | 0.502 | +0.107 |
| Rolandic Oper L | 0.289 | 0.380 | +0.092 |
| Frontal Mid 2 R | 0.293 | 0.378 | +0.085 |

Across 120 AAL2 regions: mean change **+0.0215**, 83 regions increase, 20
move by at least 0.05, none decrease.

### Gradient map — severe, and the only visible symptom

This is where it actually surfaces on screen. Because the mask spans the
whole volume, the cluster tree spans the whole volume too, and *every* voxel
in the image ends up with a gradient-map value at or above the whole-brain
TDP bound. On `z.nii`:

- 0 voxels have a gradient value of exactly 0
- 644,970 voxels (71.5% of the volume) sit on the floor value 0.04
- **every one of those is outside the brain**

That plateau is the purple wash that appears over the whole field of view.
The orthoview renderer currently hides it by anchoring the colour scale at
the whole-brain TDP bound (`OrthViewUpdate._gradient_levels`), which is a
display-level workaround for this data-level problem. Once the mask is
fixed, the background will be genuinely absent from the gradient map and
that anchoring becomes belt-and-braces rather than load-bearing.

---

## 5. Why the obvious fix is wrong

The tempting one-line change is `mask = data != 0`. **Do not do this.**

Zero is a legitimate value for a brain voxel. `z.nii` contains 16 voxels
that are exactly zero and genuinely inside the brain. Dropping them removes
real hypotheses from the analysis.

Worse, the failure is in the dangerous direction. Excluding voxels shrinks
the *denominator* of the TDP calculation. Dropping likely-null voxels from a
region therefore makes its TDP look **higher** than it should be. Silently
including background is conservative; silently excluding brain is not.

### The topology idea, and where it breaks

A better heuristic: background zeros form one huge region connected to the
edge of the image, while in-brain zeros are isolated voxels surrounded by
data. Label the zero voxels and discard only the components touching the
volume border.

On `z.nii` this works perfectly — the zeros form 19 components: one of
644,954 (the background) and 18 single voxels inside the brain. It keeps all
16 of the in-brain zeros that `data != 0` would have dropped.

But it collapses on a **pre-thresholded map**, where sub-threshold in-brain
voxels have been set to zero by upstream software. Those zeros connect to
the background through the edge of the brain, so no connectivity rule can
separate them. Simulated by thresholding `z.nii` at |z| > 3:

| mask rule | keeps |
|---|---|
| border-connected zeros | 24.1% of the true brain |
| `data != 0` | 24.1% of the true brain |

Both throw away three quarters of the brain, and both inflate TDP as a
result. **This is the case that needs a real mask, not a heuristic.**

---

## 6. The fix: a disclosed ladder

No single rule is safe for every file, so the tool should try rules in order
of trustworthiness, and always say which one it used.

1. **NaNs present in the file** -> `np.isfinite(data)`.
   The software that wrote the file declared its own background. Trust it.
   Using `isfinite` rather than `~isnan` also excludes infinities.

2. **User-supplied mask file** -> use it.
   Every neuroimaging package produces one (`mask.nii`, SPM's `mask.nii`,
   FSL's `*_mask`). This is the authoritative answer and should be offered
   in the UI.

3. **Bundled MNI brain mask, resampled to the data grid.**
   The app already ships `public/template_masks/mni_template_icbm152_inmask.nii`
   and uses it for the 3D viewer. Valid whenever the statistical map is in
   MNI space, which `_spatial_space()` can check from the NIfTI header.

4. **Border-connected-zero heuristic**, as a last resort, and only if the
   result still looks like a brain (see the sanity check below).

If nothing above applies, keep today's behaviour and say so. Conservative
and stated is an acceptable outcome; silently wrong is not.

### Always disclose

Whatever is chosen, log one line: the rule used, the resulting `m`, the
fraction of the volume retained, and the whole-brain TDP bound. A bad mask
currently hides inside a conservative-looking result; it should be visible
in the message box the moment the analysis runs.

### Sanity check before accepting a heuristic mask

Reject a heuristic mask and fall back if it retains more than ~90% of the
volume (it did not find a background) or less than ~5% (it probably ate the
brain, i.e. the pre-thresholded case). Warn loudly rather than proceeding
quietly.

---

## 7. Implementation steps

Each step is independently runnable and reviewable. Commit after each.

**Step 1 — `BrainMask` resolver, no behaviour change yet.**
New `models/brain_mask.py` with `resolve(data, affine, header, user_mask=None)`
returning `(mask, rule_name, diagnostics)`. Implement all four tiers plus the
sanity check. Pure function over arrays, no `brain_nav` — so it can be
exercised directly against both test maps. Not wired in.

**Step 2 — switch `~isnan` to `isfinite`.**
The only part of this work that fixes a defect rather than recovering power.
`z.nii` has two `-inf` voxels that currently enter as p = 0 hypotheses.
Expected effect: `m` 902,629 -> 902,627, whole-brain TDP unchanged at 0.0439.
Small, isolated, easy to verify.

**Step 3 — wire the resolver in behind a setting, default OFF.**
`check_file_type` calls the resolver; a preference selects legacy
(`~isnan`) or resolved masking. Default legacy so existing projects
reproduce exactly. Log the disclosure line either way — even in legacy mode
the user learns that 71.5% of their analysis is empty space.

**Step 4 — mask upload in the UI.**
A slot in the sidebar's rail (the `Section`/`ResourceList` widgets already
support a fourth section) plus `UploadFiles.upload_mask_dialog`. Feeds
tier 2. Persist the path in the `.ari` project like the user atlas does.

**Step 5 — flip the default to resolved masking.**
Separate commit so it can be reverted alone. Bump
`PROJECT_FILE_FORMAT_VERSION` and record the mask rule in the project file,
so a reloaded project reproduces the numbers it was saved with rather than
silently recomputing them under a new rule.

**Step 6 — follow-ups unblocked by the fix.**
- `compute_roi_tdps`: the "no overlap with brain mask" message becomes
  meaningful; implement the planned "more than 10% of this ROI falls outside
  the analysis mask" warning from `ATLAS_TDP_PLAN.md` section 6.
- `export_all_roi_maps` already restricts output to analysed voxels; that
  restriction is currently a no-op (the mask is everything) and starts doing
  real work here.
- Re-check `OrthViewUpdate._gradient_levels`: with a real mask the
  background is absent rather than sitting on the floor, so the mintdp
  anchoring should become redundant.

---

## 8. How to verify

Both test maps live in `NewApp/Data/` and bracket the problem nicely:
`z.nii` has in-brain zeros (16) and needs them kept; `bart_Accept` has none
and every rule agrees on it.

| check | expected |
|---|---|
| `z.nii`, tier 4 | m = 257,673; keeps all 16 in-brain zeros |
| `bart_Accept`, tier 4 | m = 52,493; 1 zero component, 0 interior |
| `z.nii` thresholded at \|z\|>3 | sanity check **rejects** the heuristic mask |
| a NaN-coded map | tier 1 fires, tier 4 never runs |
| legacy mode | m and TDP identical to `main` on both maps |
| whole-brain TDP, `z.nii` | 0.0439 -> 0.1978 |
| whole-brain TDP, `bart_Accept` | 0.1001 -> 0.5378 |
| saved project reloaded | same numbers as when it was saved |

Every TDP change must be non-negative. A region whose TDP *drops* means
brain was excluded — stop and investigate.

---

## 9. Open questions

1. **Default for existing users.** Step 5 changes every number in every
   existing project. Flip the default, or keep legacy and let people opt in?
2. **Is tier 3 safe enough to be automatic?** It assumes the map is in MNI
   space on the strength of a header field that is often wrong. Prompt
   instead of assuming?
3. **Detecting pre-thresholded maps.** The sanity check catches the
   symptom. Worth detecting the cause directly — a large gap between zero
   and the smallest non-zero absolute value is a strong signal.

---

## Appendix: an unrelated finding, so it is not re-litigated

`Metrics.control_threshold` calls the **Python** `get_clusters.answer_query`,
with the C++ `ARI_C.py_answerQuery` commented out directly above it. This
looks like an oversight. It is not — it is correct, and it should stay.

Benchmarked on `z.nii` (m = 902,629, 186,203 admissible clusters), results
**identical at every threshold tested**:

| | C++ | Python |
|---|---|---|
| single query (interactive thresholding) | 1111.7 ms | **34.6 ms** |
| batch of 101 gammas (gradient map) | **2.48 s** | 11.57 s |

Single queries are dominated by marshalling: `stcs`, `SIZE`, `tdps` and
`CHILD` are m-length Python lists that must be converted to C++ vectors on
every call, costing a flat ~1.1 s regardless of the threshold. The batch
version converts once and amortises that over 101 queries, which is why the
gradient map correctly uses the C++ batch while interactive thresholding
correctly uses Python.
