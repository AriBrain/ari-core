# ARIbrain User Guide

A comprehensive guide for researchers using ARIbrain to perform cluster-based statistical inference on neuroimaging data.

---

## Table of Contents

1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
   - [Launching the Application](#launching-the-application)
   - [The Landing Screen](#the-landing-screen)
3. [Setting Up Your Analysis](#setting-up-your-analysis)
   - [Loading a Statistical Map](#loading-a-statistical-map)
   - [Selecting Map Type](#selecting-map-type)
   - [Choosing a Background Template](#choosing-a-background-template)
4. [The Main Interface](#the-main-interface)
   - [Interface Overview](#interface-overview)
   - [Left Sidebar](#left-sidebar)
   - [Orthogonal Brain Views](#orthogonal-brain-views)
   - [3D Cluster Viewer](#3d-cluster-viewer)
   - [Metrics Panel](#metrics-panel)
5. [Brain Navigation](#brain-navigation)
   - [Navigating with Crosshairs](#navigating-with-crosshairs)
   - [Using Coordinate Controls](#using-coordinate-controls)
   - [Understanding Orientation Labels](#understanding-orientation-labels)
6. [Statistical Analysis](#statistical-analysis)
   - [Understanding the ARI Analysis](#understanding-the-ari-analysis)
   - [Whole-Brain Thresholding](#whole-brain-thresholding)
   - [TDP-Based Thresholding](#tdp-based-thresholding)
   - [Z-Score Based Thresholding](#z-score-based-thresholding)
7. [Working with the Cluster Table](#working-with-the-cluster-table)
   - [Reading the Table](#reading-the-table)
   - [Selecting Clusters](#selecting-clusters)
   - [Understanding Table Columns](#understanding-table-columns)
8. [Cluster Work Station](#cluster-work-station)
   - [Interactive TDP Adjustment](#interactive-tdp-adjustment)
   - [Changing Cluster Size](#changing-cluster-size)
   - [State History Navigation](#state-history-navigation)
9. [Managing Multiple Statistical Maps](#managing-multiple-statistical-maps)
10. [Saving and Loading Projects](#saving-and-loading-projects)
    - [Saving a Project](#saving-a-project)
    - [Loading a Project](#loading-a-project)
11. [Exporting Results](#exporting-results)
    - [Export Options](#export-options)
    - [Understanding Exported Files](#understanding-exported-files)
12. [Troubleshooting](#troubleshooting)
13. [Glossary](#glossary)

---

## Introduction

ARIbrain is a desktop application for performing cluster-based statistical inference on neuroimaging data using the All-Resolutions Inference (ARI) framework. It enables researchers to:

- Visualize statistical brain maps in 2D orthogonal views and 3D renderings
- Apply statistically principled thresholding using True Discovery Proportion (TDP)
- Interactively explore and adjust cluster boundaries
- Export publication-ready results and reports

ARI provides a powerful alternative to traditional cluster-based inference by offering:
- **Simultaneous inference** at all possible thresholds
- **TDP guarantees** for each identified cluster
- **Flexible exploration** without inflating false positive rates

---

## Getting Started

### Launching the Application

**From Terminal (recommended for troubleshooting):**
```bash
aribrain
```

**From macOS Application:**
Double-click `ARIbrain.app` in your Applications folder or wherever you installed it.

### The Landing Screen

When ARIbrain launches, you'll see the landing screen with two options:

| Button | Description |
|--------|-------------|
| **New Project** | Start a fresh analysis with new data |
| **Load Project** | Resume a previously saved analysis session |

---

## Setting Up Your Analysis

After clicking **New Project**, you'll be guided through the setup process.

### Loading a Statistical Map

1. Click the **Browse** button next to the file input field
2. Navigate to your NIfTI file (`.nii` or `.nii.gz`)
3. Select your statistical map file
4. A preview of your data will appear in the orthogonal view panels on the right

**Supported file formats:**
- Uncompressed NIfTI (`.nii`)
- Compressed NIfTI (`.nii.gz`)

### Selecting Map Type

ARIbrain will attempt to automatically detect your map type from the NIfTI header. If detection fails, or you need to override it, select from:

| Map Type | Description | Additional Input |
|----------|-------------|------------------|
| **z-map** | Z-score statistical map | None |
| **t-map** | T-statistic map | Degrees of freedom (required) |
| **p-map** | P-value map | None |

**Note for t-maps:** You will be prompted to enter the degrees of freedom. This is essential for accurate p-value conversion.

### Choosing a Background Template

Select the anatomical reference for visualization:

| Option | Description |
|--------|-------------|
| **Raw Data** | Use your statistical map as background (no template) |
| **MNI Template T1** | Standard MNI152 T1-weighted template |
| **MNI Template GM** | MNI152 grey matter probability template |
| **Upload Template** | Use your own anatomical template |

After configuring these options, click **Next** to proceed. ARIbrain will automatically run the ARI analysis, which may take a few moments depending on your data size.

---

## The Main Interface

### Interface Overview

The main interface is divided into several functional areas:

```
+------------------+----------------------------------------+------------------+
|                  |                                        |                  |
|  Left Sidebar    |     Orthogonal Brain Views            |   Right Panel    |
|  - Stat Images   |     +------------+------------+        |   - Metrics      |
|  - Templates     |     | Sagittal   | Coronal    |        |   - 3D Viewer    |
|  - Atlases       |     +------------+------------+        |                  |
|                  |     | Axial      |            |        |                  |
|                  |     +------------+------------+        |                  |
|                  |                                        |                  |
+------------------+----------------------------------------+------------------+
|                        Tab Panel                                            |
|  [Whole Brain Thresholding] [Cluster Analysis] [Save & Export]              |
|                                                                             |
+-----------------------------------------------------------------------------+
```

### Left Sidebar

The left sidebar manages your analysis resources:

**Statistical Images**
- Lists all loaded statistical maps
- The "ARI" label turns green when analysis is complete
- Click **Add** to load additional maps
- Click **Set** to switch between maps

**Template**
- Lists available background templates
- Click **Add** to upload custom templates
- Click **Set** to change the current template

**Atlas**
- Shows available anatomical atlases (AAL2 by default)
- Used for region labeling in the metrics panel

### Orthogonal Brain Views

Three synchronized 2D slice views showing:

| View | Orientation | Plane |
|------|-------------|-------|
| **Sagittal** | Left-Right | YZ plane |
| **Coronal** | Front-Back | XZ plane |
| **Axial** | Top-Bottom | XY plane |

Each view displays:
- The anatomical template (grayscale)
- Cluster overlay (colored)
- Crosshairs indicating current position
- Orientation labels (L/R, A/P, S/I)

### 3D Cluster Viewer

An interactive 3D rendering showing:
- Semi-transparent brain surface for spatial context
- The currently selected cluster in its assigned color
- XYZ axis lines for orientation reference

**3D Viewer Controls:**
- **Rotate:** Click and drag
- **Zoom:** Scroll wheel
- **Pan:** Shift + click and drag
- **Pause updates:** Click ⏸ button (improves performance during exploration)
- **Undock:** Click ⧉ button to open in a separate, larger window

### Metrics Panel

Displays real-time information about the current crosshair position:

| Metric | Description |
|--------|-------------|
| **Dimensions** | Size of the current image (voxels) |
| **Voxel Size** | Physical dimensions of each voxel (mm) |
| **Cross Hair (xyz)** | Current position in voxel coordinates |
| **MNI (xyz)** | Current position in MNI coordinates (mm) |
| **Cluster ID** | The cluster at the current position (if any) |
| **Region (AAL2)** | Anatomical region from the AAL2 atlas |

---

## Brain Navigation

### Navigating with Crosshairs

**Click Navigation:**
- Click anywhere in any orthogonal view to move the crosshairs to that location
- All three views update simultaneously

**Drag Navigation:**
- Click and drag in any view to continuously update the position
- Useful for exploring along a specific axis

### Using Coordinate Controls

Located near the orthogonal views, coordinate controls allow precise navigation:

**XYZ Spinboxes:**
- Enter exact voxel coordinates
- Use arrow buttons for fine adjustments
- Press Enter to confirm and navigate

### Understanding Orientation Labels

Each view displays anatomical orientation labels at its edges:

| Label | Full Name | Meaning |
|-------|-----------|---------|
| **L** | Left | Patient's left side |
| **R** | Right | Patient's right side |
| **A** | Anterior | Front of the brain |
| **P** | Posterior | Back of the brain |
| **S** | Superior | Top of the brain |
| **I** | Inferior | Bottom of the brain |

Labels are determined from the NIfTI sform matrix and accurately reflect your data's orientation.

---

## Statistical Analysis

### Understanding the ARI Analysis

When you load data, ARIbrain automatically performs All-Resolutions Inference:

1. **Hommel correction** computes the whole-brain TDP
2. **Adjacency mapping** identifies voxel neighborhoods
3. **Cluster tree** builds a hierarchical cluster structure
4. **TDP computation** calculates TDP for all possible clusters
5. **Gradient map** visualizes the maximum TDP at each voxel

The gradient map you see initially shows, for each voxel, the highest TDP threshold at which that voxel would be included in a cluster.

### Whole-Brain Thresholding

Access via the **Whole Brain Thresholding** tab.

#### Controls

| Control | Function |
|---------|----------|
| **Slider** | Adjust threshold value |
| **- / +** | Fine adjustment (±0.01) |
| **Text box** | Enter exact threshold value |
| **Run** | Apply the entered threshold |
| **Dropdown** | Switch between TDP-based and Z-score based methods |

### TDP-Based Thresholding

**What it does:** Identifies clusters where at least X% of voxels are truly active.

**How to use:**
1. Select "TDP-based" from the dropdown
2. Set your desired TDP threshold (e.g., 0.75 for 75%)
3. The slider adjusts from the minimum achievable TDP to 1.0
4. Higher values = more stringent = smaller/fewer clusters

**Interpretation:** A TDP of 0.75 means that at least 75% of voxels in each displayed cluster are truly active (with statistical guarantee at alpha = 0.05).

### Z-Score Based Thresholding

**What it does:** Traditional voxel-wise thresholding followed by cluster-level TDP computation.

**How to use:**
1. Select "Z-score based" from the dropdown
2. Set your Z-score threshold (e.g., 3.0)
3. Clusters are formed from contiguous voxels exceeding this threshold
4. TDP is computed for each resulting cluster

**Interpretation:** Each cluster's TDP tells you the proportion of truly active voxels within that cluster.

---

## Working with the Cluster Table

### Reading the Table

Access via the **Cluster Analysis** tab. The table shows all clusters meeting your current threshold.

### Understanding Table Columns

| Column | Description |
|--------|-------------|
| **Cluster** | Cluster number (corresponds to exported NIfTI labels) |
| **Unique ID** | Internal identifier for tracking across threshold changes |
| **Size** | Number of voxels in the cluster |
| **TDP** | True Discovery Proportion (0-1) |
| **max(Z)** | Maximum Z-score within the cluster |
| **Vox (x, y, z)** | Voxel coordinates of the local maximum |
| **MNI (x, y, z)** | MNI coordinates of the local maximum |

### Selecting Clusters

**To select a cluster:**
1. Click on any row in the table
2. The selected cluster is highlighted in the orthogonal views
3. The 3D viewer shows only that cluster
4. The crosshairs move to the cluster's peak voxel

**Visual feedback:**
- Selected cluster: Full opacity in views
- Non-selected clusters: Reduced opacity
- Table row: Green highlight

---

## Cluster Work Station

The **Selected Cluster Work Station** appears below the table when a cluster is selected.

### Interactive TDP Adjustment

Adjust the TDP threshold for the selected cluster only:

| Control | Function |
|---------|----------|
| **Slider** | Adjust cluster-specific TDP |
| **- / +** | Fine adjustment (±0.01) |
| **Text box** | Enter exact TDP value |

**What happens when you adjust:**
- Lowering TDP: Cluster grows (includes more voxels)
- Raising TDP: Cluster shrinks (only highest-confidence voxels remain)

### Changing Cluster Size

As you adjust the TDP slider:
1. The cluster boundary updates in real-time
2. The table values update to reflect the new size
3. Other clusters remain unchanged

**Note:** Clusters with TDP = 0 cannot be adjusted (no truly active voxels detected).

### State History Navigation

Use the ↺ and ↻ buttons to navigate through cluster modification history:
- **↺** Previous state
- **↻** Next state

---

## Managing Multiple Statistical Maps

ARIbrain supports analyzing multiple statistical maps simultaneously.

**To add another map:**
1. Click **Add** in the Statistical Images section
2. Browse and select your NIfTI file
3. Configure map type if needed
4. The new map appears in the list

**To switch between maps:**
1. Click on the desired map in the list
2. Click **Set**
3. If ARI hasn't been run, you'll be prompted

**Indicator:**
- Grey "ARI" label = Analysis not yet performed
- Green "ARI" label = Analysis complete

---

## Saving and Loading Projects

### Saving a Project

Access via the **Save & Export** tab.

1. Click **Save Project**
2. Choose a location and filename
3. The project saves as an `.ari` file

**What's saved:**
- All loaded statistical maps and their ARI results
- Current thresholds and settings
- Cluster modifications
- Template configurations
- UI state (selected clusters, crosshair positions)

### Loading a Project

**From the landing screen:**
1. Click **Load Project**
2. Navigate to your `.ari` file
3. The entire session restores automatically

**From within the application:**
1. Go to **Save & Export** tab
2. Click **Load Project**
3. Select your `.ari` file

---

## Exporting Results

### Export Options

Click **Export Results** in the **Save & Export** tab to export all results to a selected directory.

### Understanding Exported Files

| File | Format | Description |
|------|--------|-------------|
| `cluster_table_N.csv` | CSV | Cluster statistics table for each statistical map |
| `cluster_map_filename_N.nii.gz` | NIfTI | 3D cluster label image (values = cluster numbers) |
| `3d_cluster_view.png` | PNG | Screenshot of the current 3D view |
| `full_report.html` | HTML | Interactive report with tables and images |
| `ARI_report_table.pdf` | PDF | Formatted cluster table for publication |

**Using the cluster map NIfTI:**
- Load in any NIfTI viewer (FSLeyes, MRIcron, etc.)
- Voxel values correspond to cluster numbers in the CSV
- Value 0 = background (no cluster)
- Values 1-N = cluster labels

**The HTML report includes:**
- Analysis settings and parameters
- Interactive tabs for each statistical map
- Cluster tables with all statistics
- Embedded orthogonal view screenshots
- Explanation of table columns

---

## Troubleshooting

### Common Issues

**"No significant brain activations can be detected"**
- Your data may not contain statistically significant effects
- Try using a different statistical threshold
- Verify your input data is a valid statistical map

**Clusters disappear when changing threshold**
- This is expected behavior - higher thresholds are more stringent
- Lower the TDP threshold to reveal more clusters

**Application runs slowly**
- Pause 3D updates using the ⏸ button
- Close other applications to free memory
- Consider using a subset of your data for initial exploration

**Crosshairs don't align with expected coordinates**
- Verify your NIfTI file has correct header information
- Check that the sform/qform matrices are properly set

### Getting Help

If you encounter issues:
1. Run from terminal to see error messages: `aribrain`
2. Check the message log at the bottom of the application
3. Report issues at: https://github.com/your-repo/issues

---

## Glossary

| Term | Definition |
|------|------------|
| **ARI** | All-Resolutions Inference - a statistical framework for simultaneous inference at all thresholds |
| **Cluster** | A contiguous group of voxels meeting the statistical threshold |
| **Crosshair** | The intersecting lines indicating the current position in 3D space |
| **Degrees of Freedom** | Statistical parameter required for t-distributions |
| **Gradient Map** | Visualization showing maximum achievable TDP at each voxel |
| **Hommel Correction** | A statistical method for controlling family-wise error rate |
| **Local Minimum** | The voxel with the most extreme statistic within a cluster |
| **MNI Coordinates** | Standardized brain coordinates in millimeters (Montreal Neurological Institute space) |
| **NIfTI** | Neuroimaging Informatics Technology Initiative - standard brain image format |
| **Orthogonal Views** | The three perpendicular 2D slice views (sagittal, coronal, axial) |
| **P-value** | Probability of observing the data under the null hypothesis |
| **Sform** | Affine transformation matrix in NIfTI headers defining spatial orientation |
| **TDP** | True Discovery Proportion - the proportion of truly active voxels in a cluster |
| **Template** | Anatomical reference image for visualization |
| **Thresholding** | Filtering data based on a statistical cutoff |
| **Voxel** | A 3D pixel - the smallest unit in a brain image |
| **Z-score** | Standardized statistic measuring deviation from the null hypothesis |

---

## Quick Reference Card

### Keyboard & Mouse

| Action | Control |
|--------|---------|
| Navigate slices | Click in any orthogonal view |
| Continuous navigation | Click and drag in views |
| Rotate 3D view | Click and drag in 3D viewer |
| Zoom 3D view | Scroll wheel |
| Select cluster | Click table row |
| Apply threshold | Press Enter in threshold textbox |

### Key Thresholds

| TDP Value | Interpretation |
|-----------|----------------|
| 1.00 | All voxels in cluster are truly active |
| 0.75 | At least 75% of voxels are truly active |
| 0.50 | At least 50% of voxels are truly active |
| 0.00 | No evidence of truly active voxels |

### File Extensions

| Extension | Type |
|-----------|------|
| `.nii` | Uncompressed NIfTI image |
| `.nii.gz` | Compressed NIfTI image |
| `.ari` | ARIbrain project file |

---

*Last updated: February 2025*
*ARIbrain Version 0.1.0*
