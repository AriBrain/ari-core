# Standard Library Imports
import copy
from itertools import chain

# Third-Party Library Imports
import numpy as np
import pandas as pd
import nibabel as nib
from scipy.stats import norm
import scipy.spatial.distance as distance
import scipy.cluster.hierarchy as hierarchy

# PyQt Imports
from PyQt5.QtWidgets import QProgressDialog
from PyQt5.QtCore import Qt

# Project-Specific Imports
import ari_application.cpp_extensions.cython_modules.ARICluster as ARI_C
from ari_application.analyses.getClusters import get_clusters
from ari_application.models.image_processing import ImageProcessing

# To do: some functions, toward the end of this class can and should be moved to util.py as they are helper functions. 

class Metrics:
    def __init__(self, BrainNaV):

        # Initialize the Metrics with a reference to the BrainNav instance.
        # :param brain_nav: Instance of the BrainNav class.
        self.brain_nav = BrainNaV

    def show_metrics(self):
        BrainNav = self.brain_nav
        file_nr = BrainNav.file_nr
        file_nr_template = BrainNav.file_nr_template

        # if the currently selected template is the raw data we want to move into the dict item (file_nr)
        # subID = file_nr if file_nr_template == self.brain_nav.data_bg_index else 0

        # templates = BrainNav.templates
        # template = templates[file_nr_template]
        # data = template['data']

        # if not hasattr(BrainNav, 'data') or BrainNav.data is None:
        #         # Placeholder metrics when no data is selected
        #         metrics = {
        #             'Dimensions': '',
        #             'Voxel Size': '',
        #             # 'Data Type': '',
        #             'Cross Hair (xyz)': '',
        #             'MNI (xyz)': '',
        #             'Cluster': '',
        #             'Region (AAL2)':''
        #         }
        # else:
        # Retrieve the crosshair position and data value
        x, y, z = BrainNav.sagittal_slice, BrainNav.coronal_slice, BrainNav.axial_slice
        
        # xyzs = np.array([x, y, z])
        # Flip Z (UI → anatomical correction) - this is needed because pyqtgraph has origin in upper left corner. 
        # I moved the flipping inside the xyz method.
        # z_flipped = BrainNav.data.shape[2] - 1 - z
        # xyzs = np.array([x, y, z_flipped])
        xyzs = np.array([x, y, z]) # this goes into xyzMNI() below
        
        # MNI_xyzs = Metrics.xyz2MNI(xyzs, BrainNav.image.header)

        # print('xyz:', x, y, z)
        if 'img_clus' in BrainNav.fileInfo[BrainNav.file_nr]:
            # We try because the ui xyz can return out of bound for the img_clus, the BBB is of a different size. 
            try:
                # xraw, yraw, zraw = BrainNav.fileInfo[file_nr]['mapped_coordinate_matrix_C'][x, y, z]
                xraw, yraw, zraw = BrainNav.aligned_templateInfo[(file_nr, file_nr_template)]['mapped_coordinate_matrix_C'][x, y, z]

                voxel_value = BrainNav.fileInfo[file_nr]['img_clus'][xraw, yraw, zraw]
                if np.isnan(voxel_value):
                    voxel_value = 'None'
                else:
                    voxel_value = int(round(voxel_value))
            except:
                voxel_value = 'None' 

        else:
            voxel_value = 'None'
        # voxel_value = round(BrainNav.data[x, y, z])  # Access the data value at the crosshair position
        
        # Retrieve atlas region if its in the brain nav object (not the case on first visit; initation)
        if hasattr(BrainNav, 'atlasInfo'):
            if file_nr_template == self.brain_nav.data_bg_index:
                atlasInfo = BrainNav.atlasInfo.get(('data_as_template', file_nr))
            else:
                atlasInfo = BrainNav.atlasInfo.get(file_nr_template)

            try:
                atlas_region_code = atlasInfo['data'][x, y, z]
                atlas_region_name = atlasInfo['codebook'].get(atlas_region_code, 'Undefined')
            except Exception as e:
                print(f"Failed to retrieve atlas region: {e}")
                atlas_region_name = 'None'

        # Metrics when data is available
        try:
            # dims = BrainNav.statmaps[file_nr]['overlay_header'].get_data_shape()
            # voxelsize = BrainNav.statmaps[file_nr]['overlay_header'].get_zooms()

            dims = BrainNav.aligned_statMapInfo[(file_nr, file_nr_template)]['overlay_header'].get_data_shape()
            voxelsize = BrainNav.aligned_statMapInfo[(file_nr, file_nr_template)]['overlay_header'].get_zooms()

            # MNI_xyzs = Metrics.xyz2MNI(xyzs, BrainNav.fileInfo[file_nr]['r_template_image_hdr'])
            # MNI_xyzs = self.xyz2MNI(xyzs, BrainNav.fileInfo[file_nr]['rtr_tamplate_affine'])
            MNI_xyzs = self.xyz2MNI(xyzs, BrainNav.aligned_templateInfo[(file_nr, file_nr_template)]['rtr_template_affine'] )

            # Update the xyz ui boxes in orth controls
            # BrainNav.mni_coord_boxes['x'].setValue(MNI_xyzs[0])
            # BrainNav.mni_coord_boxes['y'].setValue(MNI_xyzs[1])
            # BrainNav.mni_coord_boxes['z'].setValue(MNI_xyzs[2])

        except:
            dims = 'None'
            voxelsize = 'None'
            MNI_xyzs = 'None'

        metrics = {
            # 'Dimensions': BrainNav.image.header.get_data_shape(),
            # 'Voxel Size': BrainNav.image.header.get_zooms(),
            'Dimensions': dims,
            'Voxel Size': voxelsize,
            # 'Data Type': BrainNav.image.header.get_data_dtype(),
            'Cross Hair (xyz)': (x, y, z),
            'MNI (xyz)': MNI_xyzs,
            'Cluster': voxel_value,  # Add data value to the metrics
            'Region (AAL2)': atlas_region_name
        }

        
        region = metrics['Region (AAL2)']
        region_color = "#0f0" if region != "None" and region != "Undefined" else "#f44"

        metrics_text = f"""
                <table cellspacing="6" cellpadding="2">
                <tr><td><b>Dimensions:</b></td>       <td>{metrics['Dimensions']}</td></tr>
                <tr><td><b>Voxel Size:</b></td>       <td>{metrics['Voxel Size']}</td></tr>
                <tr><td colspan="2"><hr></td></tr>
                <tr><td><b>Cross Hair (xyz):</b></td> <td>{metrics['Cross Hair (xyz)']}</td></tr>
                <tr><td><b>MNI (xyz):</b></td>        <td>{metrics['MNI (xyz)']}</td></tr>
                <tr><td colspan="2"><hr></td></tr>
                <tr><td><b>Cluster ID:</b></td>       <td>{metrics['Cluster']}</td></tr>
                <tr><td><b>Region (AAL2):</b></td>    <td><span style="color:{region_color}">{region}</span></td></tr>
                </table>
            """
            # BrainNav.metrics_label.setText(metrics_text)

        # metrics_text = '\n'.join([f"{key}: {value}" for key, value in metrics.items()])
        BrainNav.initiate_tabs.metrics_label.setText(metrics_text)
    

    def control_transparency(self, value):
        # Transform reveived signal to alpha value between 0-1
        alpha = value / 100
        
        # Update the alpha value 
        self.brain_nav.alpha = alpha

        # Immediatly update the transparency in current image orientations
        self.brain_nav.orth_view_update.update_slices()

    def control_threshold(self, thresholding_method, threshold_value):
        """
        Apply thresholding and cluster analysis to functional/statistical brain data.

        This method supports two thresholding strategies: 'zscore' and 'tdp'.

        Parameters:
        ----------
        thresholding_method : str
            Either 'zscore' or 'tdp'.
            - 'zscore': Applies a voxel-wise threshold (converted from p or z values),
                        then performs cluster-wise TDP computation.
            - 'tdp': Selects supra-threshold clusters directly using precomputed TDP values.

        threshold_value : float
            The threshold value to use for filtering.
            - For 'zscore', this is converted to a Z-score if the data type is 'p'.
            - For 'tdp', it is used as a gamma threshold to query admissible clusters.

        Behavior:
        --------
        - Updates the orthogonal view overlay with a cluster map and TDP values.
        - Stores computed clusters, tblARI data, TDP map, and aligned overlay data.
        - Updates the cluster table in the UI and maintains or resets crosshair position.

        Notes:
        -----
        - Z-thresholding uses ARI-based cluster-level inference.
        - TDP thresholding uses a C++-accelerated function to extract hierarchical clusters.
        - Output cluster and TDP maps are aligned and rotated to match the background template.
        - Handles edge cases such as a single voxel passing the threshold.
        """

        # tdp_threshold = tdp_threshold / 100  # Convert TDP threshold to a fraction

        file_nr = self.brain_nav.file_nr
        file_nr_template = self.brain_nav.file_nr_template
        
        # Flag the gradmap to false to switch off the gradient map LUT scheme in:
        # add_overlay_with_transparency() method in OrthViewUpdate class
        # self.brain_nav.ui_params['gradmap'] = False # this might be obsolete now.. we store the flag in ARI
        self.brain_nav.aligned_statMapInfo[(file_nr, file_nr_template)]['gradmap_flag'] = False
        # self.brain_nav.fileInfo[file_nr]['gradmap_flag'] = False


        if thresholding_method == "zscore":
            pval = self.brain_nav.fileInfo[file_nr]['pval'] # pval is on transposed data. 
            
            # 'data' and 'mask' are not so they need to be tranposed here as well (these are not transposed)
            data = self.brain_nav.fileInfo[file_nr]['data'].T
            mask = self.brain_nav.fileInfo[file_nr]['mask'].T

            # Convert p-values to Z-scores if needed
            if self.brain_nav.fileInfo[file_nr]['type'] == "p":
                z_threshold = norm.ppf(1 - threshold_value)  # Convert threshold_value to correct Z-threshold
                mask = (pval < norm.cdf(-z_threshold)) & mask
            else:
                mask = (data > threshold_value) & mask

            # Apply clustering on thresholded regions
            cluster_map = Metrics.cluster_threshold(mask)

            # Identify unique clusters - ignore 0 (background)
            clus_labels = sorted(np.unique(cluster_map[cluster_map > 0]), reverse=True)

            # Run ARI analysis
            if self.brain_nav.fileInfo[file_nr]['type'] == "p":
                tblARI_raw, clusterlist = self.compute_ARI_analysis(
                    Pmap=pval,
                    clusters=cluster_map,
                    mask=self.brain_nav.fileInfo[file_nr]['mask'].T, # this could be changed to data as defined above.
                    Statmap=-norm.ppf(pval),  # Equivalent to `-qnorm(pval)`
                    silent=True
                )
            else:
                tblARI_raw, clusterlist = self.compute_ARI_analysis(
                    Pmap=pval,
                    clusters=cluster_map,
                    mask=self.brain_nav.fileInfo[file_nr]['mask'].T,
                    Statmap=data,
                    silent=True
                )

            # Remove last row (same as R: `tblARI <- tblARI[-dim(tblARI)[1],]`)
            # tblARI = tblARI[:-1]

            # Initialize TDP map
            # img_tdps = np.zeros(self.brain_nav.fileInfo[file_nr]['header']['dim'][1:4])
            img_tdps = np.zeros(cluster_map.shape)

            # For each cluster label (sorted by size, largest to smallest)
            for i, label in enumerate(clus_labels): # [:-1]
                
                # Create a mask selecting only the voxels that belong to this cluster
                cluster_voxel_mask = (cluster_map == label)

                # Find the TDP value for this cluster.
                # tblARI contains clusters sorted from smallest to largest,
                # so we reverse the order here using "len(clus_labels) - i - 1".
                # Column 4 in tblARI contains the TDP value.
                cluster_tdp = tblARI_raw.loc[len(clus_labels) - i - 1, 'Active Proportion']

                # Assign the TDP value to all voxels in this cluster
                img_tdps[cluster_voxel_mask] = cluster_tdp  

                # print(len(clus_labels) - i - 1, label)
                # print(tblARI_raw.loc[len(clus_labels) - i - 1, 'Cluster'])

            # Update image and table
            ord_clusterlist, tblARI, tblARI_df, Vox_xyzs = self.prepare_tblARI(clusterlist) # clus2node
            
            img_clus, _, tblARI_df = self.update_clust_img(ord_clusterlist, tblARI_df)

            # Create a mapping from Cluster to Active Proportion
            tdp_mapping = dict(zip(tblARI_raw['Cluster'], tblARI_raw['Active Proportion'].round(2)))
            
            # Update TDP column directly (inplace), using the mapping
            tblARI_df['TDP'] = tblARI_df['Cluster'].map(tdp_mapping)

            self.brain_nav.fileInfo[file_nr]['zscore_whole_brain_clusterlist'] = clusterlist
            self.brain_nav.fileInfo[file_nr]['tblARI_raw'] = tblARI_raw


            # img_clus = cluster_map
            

                
        elif thresholding_method == "tdp":
            # Find all maximal supra-threshold clusters with the given TDP threshold
            # The C++ function starts by finding the left boundary (left) based on the TDP threshold (gamma).
            # •	It then iterates over the admissible STCs starting from this left boundary.
            # •	For each admissible STC that hasn’t been marked (MARK[ADMSTC[i]] == 0), it:
            # •	Finds all descendants of the cluster using the descendants function.
            # •	Appends this list of descendants (DESC) to the output list (ANS).
            # •	Marks the corresponding voxels in the MARK array.
            # •	Finally, it clears the marks in MARK and converts the list ANS into a vector of vectors (result) to return.
            # clusterlist = ARI_C.py_answerQuery(
            #     threshold_value,                                      # TDP threshold value (gamma) to filter supra-threshold clusters (STCs)
            #     self.brain_nav.fileInfo[file_nr]['stcs'],                    # Indices of admissible supra-threshold clusters (STCs) that meet initial conditions
            #     self.brain_nav.fileInfo[file_nr]['reslist']['SIZE'],         # Sizes of the clusters; used to manage and sort clusters
            #     self.brain_nav.fileInfo[file_nr]['marks'],                   # Marker array to track processed clusters/voxels and prevent duplicate processing
            #     self.brain_nav.fileInfo[file_nr]['tdps'],                    # TDP values associated with each cluster, used to filter and process clusters
            #     self.brain_nav.fileInfo[file_nr]['reslist']['CHILD']         # Child relationships between clusters, representing hierarchical cluster structure
            # )
            clusterlist, _ = get_clusters.answer_query(
                threshold_value,                                               # TDP threshold value (gamma) to filter supra-threshold clusters (STCs)
                self.brain_nav.fileInfo[file_nr]['stcs'],                    # Indices of admissible supra-threshold clusters (STCs) that meet initial conditions
                self.brain_nav.fileInfo[file_nr]['reslist']['SIZE'],         # Sizes of the clusters; used to manage and sort clusters
                self.brain_nav.fileInfo[file_nr]['marks'],                   # Marker array to track processed clusters/voxels and prevent duplicate processing
                self.brain_nav.fileInfo[file_nr]['tdps'],                    # TDP values associated with each cluster, used to filter and process clusters
                self.brain_nav.fileInfo[file_nr]['reslist']['CHILD']         # Child relationships between clusters, representing hierarchical cluster structure
            )

            
            # •	Each element of clusterlist is a list of integers.
            # •	These integers represent indices of voxels in the 3D volume that belong to a specific supra-threshold cluster (STC).
            #       Voxel Indices:  The indices in clusterlist are indices of voxels within the entire 3D volume.
            #       Structure:      clusterlist is a list of lists  where each sublist represents 
            #                       the indices of voxels that make up one cluster.

            # Update image and table
            ord_clusterlist, tblARI, tblARI_df, Vox_xyzs = self.prepare_tblARI(clusterlist) # clus2node
            
            img_clus, img_tdps, tblARI_df = self.update_clust_img(ord_clusterlist, tblARI_df)

            self.brain_nav.fileInfo[file_nr]['tdp_whole_brain_clusterlist'] = clusterlist
        
        # print(tblARI_df)
        # Update the table in the UI
        self.brain_nav.tblARI.update_table(tblARI_df)

        img_clus[img_clus == 0] = np.nan  # Set background values in the cluster map to NaN
        img_tdps[img_clus == 0] = np.nan  # Set background values in the TDP map to NaN
        self.brain_nav.fileInfo[file_nr]['img_clus']        = img_clus  # Store the updated cluster map in the brain navigation object
        self.brain_nav.fileInfo[file_nr]['img_tdps']        = img_tdps  # Store the updated TDP map in the brain navigation object
        self.brain_nav.fileInfo[file_nr]['tblARI']          = tblARI
        self.brain_nav.fileInfo[file_nr]['tblARI_df']       = tblARI_df
        self.brain_nav.fileInfo[file_nr]['tblARI_df_comp']  = tblARI_df
        # self.brain_nav.fileInfo[file_nr]['Vox_xyzs']        = Vox_xyzs
        self.brain_nav.fileInfo[file_nr]['clusterlist']     = ord_clusterlist
        # self.brain_nav.fileInfo[file_nr]['clus2node']       = clus2node

        self.brain_nav.tblARI.reset_highlight()

        # Step 1: Construct cluster image using original affine - image is transposed back to original dimensions
        cluster_image = nib.Nifti1Image(
            img_clus.T, 
            affine=self.brain_nav.fileInfo[file_nr]['affine'],
            header=self.brain_nav.fileInfo[file_nr]['header']
        )

        template_image = self.brain_nav.templates[file_nr_template]['image']

        # Step 2: Align cluster image to the template (which is already in final space)
        a_cluster_image, _ = ImageProcessing.align_images(template_image, cluster_image, order=1)

        # Step 3: Transpose the aligned cluster image
        tra_cluster_image = ImageProcessing.transpose_image(a_cluster_image)

        # Step 4: Rotate the transposed cluster image (same way the template was rotated earlier)
        _, rtra_cluster_image, aligned_overlay_affine = ImageProcessing.rotate_volume(tra_cluster_image)

        # Step 5: Extract final data
        aligned_overlay_data = rtra_cluster_image.get_fdata()

        # Update self.brain_nav with the updated tdp_threshold overlay data
        # self.brain_nav.overlay_data = aligned_overlay_data 
        # self.brain_nav.statmaps[file_nr]['overlay_data']            = aligned_overlay_data
        # self.brain_nav.fileInfo[file_nr]['aligned_overlay_header']  = rtra_cluster_image.header
        # self.brain_nav.fileInfo[file_nr]['aligned_overlay_affine']  = aligned_overlay_affine

        self.brain_nav.aligned_statMapInfo[(file_nr, file_nr_template)]['overlay_data']            = aligned_overlay_data

        if len(tblARI_df) == 1 and tblARI_df['Size'].iloc[0] == 1:
            orange_text = "\033[38;5;214m"  # ANSI escape code for orange text
            reset_color = "\033[0m"          # Resets color back to default
            print(f"{orange_text}Warning! Only one voxel remains at the threshold — maintaining current crosshair.{reset_color}")
            
            message = (
                        f"<span style='color: orange; font-weight: bold;'>"
                        f"WARNING! Only one voxel remains at the threshold — maintaining current crosshair."
                        f"</span>"
                        )
            self.brain_nav.message_box.log_message(message)
            
            return

        # Update UI elements (like orthogonal view) to reflect the changes  
        if self.brain_nav.ui_params['selected_cluster_id']:

            if self.brain_nav.ui_params['selected_cluster_id'] in tblARI_df['Unique ID'].values:
                # If the selected cluster is still in the table
                selected_row = tblARI_df[tblARI_df['Unique ID'] == self.brain_nav.ui_params['selected_cluster_id']].index[0]
                self.follow_cluster_xyz(selected_row)
            else:
                # If the cluster is no longer in the table, find a fallback cluster
                # Retrieve the parent or merged cluster
                # fallback_cluster_id = self.find_fallback_cluster(self.brain_nav.ui_params['selected_cluster_id'])

                x,y,z = self.brain_nav.sagittal_slice , self.brain_nav.coronal_slice, self.brain_nav.axial_slice      

                # new_cluster_id = self.brain_nav.statmaps[file_nr]['overlay_data'][x, y, z]
                new_cluster_id = self.brain_nav.aligned_statMapInfo[(file_nr, file_nr_template)]['overlay_data'][x, y, z]

                new_row = tblARI_df[tblARI_df['Unique ID'] ==  new_cluster_id].index[0]

                self.brain_nav.tblARI.highlight_selected_row(selected_row=new_row)
                self.brain_nav.cluster_ws.update_work_station(selected_row=new_row)
                self.brain_nav.orth_view_update.update_slices()  
        else:
            self.brain_nav.orth_view_update.update_slices()  # Refresh the orthogonal view with the new cluster and TDP data

    @staticmethod
    def cluster_threshold(map, max_dist=np.sqrt(3)):
            """
            Apply single-linkage hierarchical clustering to suprathreshold voxels.

            Parameters:
                map (numpy.ndarray): A 3D binary array (True for suprathreshold voxels, False otherwise).
                max_dist (float): Maximum Euclidean distance between linked voxels (default: sqrt(3) for 3D adjacency).

            Returns:
                cluster_map (numpy.ndarray): A 3D array where each cluster is labeled with a unique integer.
            """
            # cpp computations are based on transposed arrays, so we transpose the arrays here UNLESS THE DATA ALREADY GOES IN TRANSPOSED!
            # map = map.T - we now have transposed the data before it goes in.

            # Convert NaNs to False (ensure valid binary mask)
            map = np.nan_to_num(map, nan=False)

            # Find suprathreshold voxel indices
            suprathreshold_voxels = np.argwhere(map)  # Extract 3D coordinates of nonzero voxels

            # === Safeguard for low voxel counts ===
            if len(suprathreshold_voxels) == 0:
                print("No voxels found; returning empty cluster map.")
                # No voxels exceed threshold — return empty map
                return np.zeros_like(map, dtype=int)

            elif len(suprathreshold_voxels) == 1:
                # Special case: only 1 voxel => assign cluster ID 1 directly
                print("Only 1 voxel found; assigning cluster ID 1.")
                cluster_map = np.zeros_like(map, dtype=int)
                cluster_map[tuple(suprathreshold_voxels[0])] = 1
                return cluster_map

            if len(suprathreshold_voxels) == 0:
                return np.zeros_like(map, dtype=int)  # Return empty cluster map if no clusters found

            # Compute pairwise distances between voxels
            pairwise_distances = distance.pdist(suprathreshold_voxels, metric="euclidean")

            # Perform hierarchical clustering (single linkage)
            linkage_matrix = hierarchy.linkage(pairwise_distances, method="single")

            # Cut the dendrogram at max_dist to assign cluster labels
            cluster_labels = hierarchy.fcluster(linkage_matrix, t=max_dist, criterion="distance")

            # Rank clusters by size (descending) and assign IDs
            unique_labels, counts = np.unique(cluster_labels, return_counts=True)
            sorted_labels = unique_labels[np.argsort(-counts)]  # Sort by cluster size (descending)
            # label_map = {old_label: new_label for new_label, old_label in enumerate(sorted_labels, start=1)}
            
            # make sure the largest cluster gets the highest label (for table purposes)
            n_clusters = len(sorted_labels)
            label_map = {old_label: n_clusters - rank for rank, old_label in enumerate(sorted_labels)}

            # Reassign cluster IDs based on size ranking
            cluster_labels = np.array([label_map[label] for label in cluster_labels])

            # Create output cluster map
            cluster_map = np.zeros_like(map, dtype=int)
            for i, voxel in enumerate(suprathreshold_voxels):
                cluster_map[tuple(voxel)] = cluster_labels[i]

            return cluster_map
    
    # @staticmethod
    def compute_ARI_analysis(self, Pmap, clusters, mask=None, alpha=0.05, Statmap=None, summary_stat="max", silent=False):
        """
        Performs ARI-based cluster analysis using Hommel correction.

        Parameters:
        - Pmap (numpy.ndarray): P-value map.
        - clusters (numpy.ndarray): Cluster map with labeled clusters.
        - mask (numpy.ndarray, optional): Binary mask to include/exclude voxels.
        - alpha (float): Significance level for discoveries.
        - Statmap (callable or numpy.ndarray, optional): Function or array specifying test statistics (e.g., Z-scores).
        - summary_stat (str): Summary statistic to use ('max' or 'center-of-mass').
        - silent (bool): If False, prints summary information.

        Returns:
        - pandas.DataFrame: Cluster statistics including size, TDP, max Z, and coordinates.
        """
        from ari_application.analyses.hommel import pyHommel

        # Ensure Pmap, clusters, and mask are properly formatted
        # Pmap        = Metrics.get_array(Pmap)
        # clusters    = Metrics.get_array(clusters, map_dims=Pmap.shape)
        # mask        = Metrics.get_array(mask, map_dims=Pmap.shape)

        # Handle Statmap: Function or Array
        if callable(Statmap):
            StatFun = Statmap
        else:
            Statmap = Metrics.get_array(Statmap, map_dims=Statmap.shape)
            StatFun = lambda ix: Statmap[ix]

        # Clip p-values to ensure they are within the range [0, 1]
        # Pmap = np.minimum(1, Pmap)
        # Pmap = np.maximum(0, Pmap)

        # The cpp computations are based on transposed arrays, so we transpose the arrays here.
        # we trasnpose before the call to compute_ARI_analysis - so comment out
        # Pmap = Pmap.T # Pmap (pval) is already transposed in the fileInfo
        # mask = mask.T # we fed the funciton the raw (untransposed) data
        
        
        # Extract valid voxel indices (mask)
        valid_voxels_hom = np.where(mask != 0)
        # valid_voxels_clus = np.where(mask !=0)
        # valid_voxels = mask

        # Metrics.xyz2index(valid_voxels, dims = Statmap.shape)

        # Compute Hommel-based TDP analysis
        hom = pyHommel.hommel_wbTDP(Pmap[valid_voxels_hom], simes=True)

        # Identify unique clusters in the valid mask, sorted in descending order
        cluster_ids = np.sort(np.unique(clusters[valid_voxels_hom]))[::-1]
        # Temporary quick fix: drop the last cluster ID (presumably non-cluster mask voxels)

        cluster_ids = cluster_ids[:-1] # This is how it is implemented like this in the shiny application
        # we do this because the last unqiqely cluster ID is always 0 (the background)

        progress = QProgressDialog("Computing tdp for z-based clusters...", "Cancel", 0, len(cluster_ids), self.brain_nav.main_window)
        progress.setWindowModality(Qt.WindowModal)
        progress.setValue(0)
        progress.show()

        # Process each cluster
        out = []
        clusterlist = []
        voxel_indices = np.zeros(mask.shape, dtype=int)
        voxel_indices[mask] = np.arange(np.count_nonzero(mask))
        for i, cluster_id in enumerate(cluster_ids):
            if progress.wasCanceled():
                break
            ix = clusters == cluster_id
            ix[~mask] = False  # Only allow voxels inside mask

            cluster_voxels_xyzs = np.where(ix)
            cluster_voxels_idxs = np.flatnonzero(ix)

            # Map global indices to mask-relative indices
            mask_relative_idxs = voxel_indices.flat[cluster_voxels_idxs]

            # Append to clusterlist (this is mask-relative for compatibility with Hommel)
            clusterlist.append(mask_relative_idxs.tolist())

            # Now compute Hommel summary using **mask-relative** indices
            cluster_summary = Metrics.summary_hommel_roi(hom, ix=mask_relative_idxs, alpha=alpha)

            # Get the statistics for each voxel
            voxel_stats = StatFun(cluster_voxels_xyzs)

            # Combine coordinates and statistics into one array
            cluster_voxels_with_stats = np.column_stack((cluster_voxels_xyzs[0], 
                                                        cluster_voxels_xyzs[1], 
                                                        cluster_voxels_xyzs[2], 
                                                        voxel_stats))
            # Compute additional cluster statistics
            cluster_stats = Metrics.summary_cluster(cluster_voxels_with_stats)
            # cluster_stats = cluster_stats['Max_Coords']
            
            # Combine all statistics into a single row
            # row = [cluster_id] + list(cluster_summary.values()) + list(cluster_stats.values())
            row = [cluster_id] + list(cluster_summary.values()) + list(cluster_stats)
            out.append(row)

            # Update progress
            progress.setValue(i + 1)

        # Convert output to DataFrame
        tblARI = pd.DataFrame(out, columns=[
            "Cluster", "Size", "False Null", "True Null", "Active Proportion", 
            "Voxel Count", "Max Stat"
        ])

        # Update row names for consistency with R (`paste("cl", clstr_id)`)
        # tblARI.index = [f"cl{int(i)}" for i in cluster_ids]

        if not silent:
            print(tblARI)

        return tblARI, clusterlist
    
    @staticmethod
    def summary_hommel_roi(hommel, ix, alpha=0.05):
        """
        Compute summary statistics for a given cluster using the Hommel correction.

        Parameters:
        - hommel (pyHommel): A Hommel correction object with adjusted p-values.
        - ix (array-like): Indices of the p-values corresponding to the cluster.
        - alpha (float): Significance level for discoveries.

        Returns:
        - dict: Dictionary with keys ["Size", "FalseNull", "TrueNull", "ActiveProp"].
        """
        # Total number of hypotheses in the cluster
        Total = len(hommel.p[ix])

        # Number of false nulls (discoveries) at given alpha
        False_Null = hommel.discoveries(ix=ix, alpha=alpha)

        # True Nulls: Remaining non-discovered hypotheses
        True_Null = Total - False_Null

        # Active Proportion: False Nulls / Total
        Active_Proportion = False_Null / Total if Total > 0 else 0

        # Return structured dictionary
        return {
            "Size": Total,
            "FalseNull": False_Null,
            "TrueNull": True_Null,
            "ActiveProp": Active_Proportion
        }
    
    @staticmethod
    def get_array(map, map_dims=None):
        """
        Ensures that the input `map` is properly formatted as a NumPy array.

        Parameters:
        - map (str or numpy.ndarray or None): The data array or a path to a NIfTI file.
        - map_dims (tuple, optional): Expected dimensions of the array.

        Returns:
        - numpy.ndarray: The processed map.

        Raises:
        - ValueError: If `map_dims` is provided but does not match the actual shape.
        """

        # Case 1: If map is None, create an array of True with map_dims
        if map is None:
            if map_dims is None:
                raise ValueError("The dimensions of the map are not defined.")
            return np.ones(map_dims, dtype=bool)

        # Case 2: If map is a string (assumed to be a filename), read it as a NIfTI image
        if isinstance(map, str):
            map = nib.load(map).get_fdata()

        # Case 3: Ensure map is a NumPy array
        map = np.asarray(map)

        # Case 4: If map_dims is provided, ensure map has expected dimensions
        if map_dims is not None and map.shape != tuple(map_dims):
            raise ValueError(f"The dimensions of the map {map.shape} do not match the expected {map_dims}.")

        return map
   
    @staticmethod
    def summary_cluster(coord_and_values, summary_stat="max"):
        """
        Compute the summary statistics for a given cluster.

        Parameters:
        - coord_and_values (numpy.ndarray or pandas.DataFrame):
            A table containing coordinates and a statistical value in the 4th column.
        - summary_stat (str): 
            The method for summarizing the cluster ('max' or 'center-of-mass').

        Returns:
        - dict: A dictionary containing the cluster size and key voxel coordinates/statistics.
        """
        # Validate summary_stat argument
        if summary_stat not in {"max", "center-of-mass"}:
            raise ValueError("summary_stat must be either 'max' or 'center-of-mass'")

        # Ensure input is a NumPy array
        if isinstance(coord_and_values, pd.DataFrame):
            coord_and_values = coord_and_values.to_numpy()

        # Ensure it has at least one row
        if coord_and_values.shape[0] == 0:
            return {"Size": 0}

        # Initialize output dictionary with cluster size
        out = {"Size": coord_and_values.shape[0]}

        if summary_stat == "max":
            # Identify row with the maximum statistic value (column index 3)
            id_max = np.argmax(coord_and_values[:, 3])  
            out.update({"Max_Coords": coord_and_values[id_max, :].tolist()})

        elif summary_stat == "center-of-mass":
            # Compute the center-of-mass
            id_mean = np.mean(coord_and_values[:, 1:], axis=0)  # Exclude cluster index column
            # Find the voxel closest to the barycenter
            distances = np.linalg.norm(coord_and_values[:, 1:] - id_mean, axis=1)
            id_closest_to_baricenter = np.argmin(distances)
            out.update({"Center_Coords": coord_and_values[id_closest_to_baricenter, :].tolist()})

        return out

    def prepare_tblARI(self, clusterlist): #  clus2node
        import time
        """
        Prepares the cluster statistics table (tblARI) by sorting clusters by size
        and calculating key cluster statistics, including TDP and maxima coordinates.

        Args:
            clusterlist (list of lists): The list of clusters to be processed.

        Returns:
            pd.DataFrame: The tblARI DataFrame with cluster statistics, including cluster size,
                        TDP values, and the voxel/MNI coordinates of the maxima.
        """
        # Get the number of clusters from the provided cluster list
        n = len(clusterlist)

        file_nr = self.brain_nav.file_nr
        file_nr_template = self.brain_nav.file_nr_template
        lm_ids_df = self.brain_nav.fileInfo[file_nr]['stable_LM_ids_df']

        # Handle the case where no clusters are found
        if n == 0:
            # Show a modal dialog to the user if no clusters were formed with the current threshold
            self.show_modal_dialog(
                "No clusters",
                "No clusters can be formed with the given TDP threshold. Please reduce the threshold."
            )
            return

        # If more than one cluster is found, proceed to sort the clusters by size
        elif n > 1:
            # Calculate the size of each cluster
            cluster_sizes = [len(cluster) for cluster in clusterlist]

            # Find the largest cluster size
            maxsize = max(cluster_sizes)

            # Calculate the size difference between the smallest and largest clusters
            # d = np.diff([min(cluster_sizes), maxsize])[0]

            # Use counting sort to efficiently order clusters by size (large to small)
            # This avoids performance issues with large clusters
            # print(" ")
            # start_time1 = time.time()
            cluster_ord = ARI_C.py_counting_sort(n, maxsize, cluster_sizes)
            # print(f"ARI_C.py_counting_sort: {time.time() - start_time1:.2f} seconds")
            # print(" ")

            # cluster_ord2 = get_clusters.counting_sort(n, maxsize, cluster_sizes)

            # Reorder cluster list and associated node list according to the sorting order
            clusterlist = [clusterlist[i] for i in cluster_ord]
            # clus2node = [clus2node[i] for i in cluster_ord]

        # Initialize an empty list to hold the cluster statistics
        tblARI = []

        # Retrieve the current file's data and indexp
        file_data = self.brain_nav.fileInfo[file_nr]['data'].T # transpose to match indexp (see getPVals)
        file_data = np.ascontiguousarray(file_data)

        indexp = self.brain_nav.fileInfo[file_nr]['indexp']

        # Iterate over each cluster to calculate statistics
        start_time1 = time.time()
        xyz_max_ui = []
        atlas_names = []  # Store the atlas region names for each cluster - at the voxel with the maximum statistic
        for i in range(n):

            # Determine cluster statistics based on the map type
            if self.brain_nav.fileInfo[file_nr]['type'] == "p":
                # Convert p-values to z-scores using the percent point function (ppf)
                clus_stat = -norm.ppf(file_data[indexp][clusterlist[i]])

            elif self.brain_nav.fileInfo[file_nr]['type'] == "z":
                # Use z-scores directly
                clus_stat = file_data[indexp][clusterlist[i]]
            
            else:
                # Assume raw values if no specific map type is specified
                clus_stat = file_data[indexp][clusterlist[i]]

            # Process the cluster minima
            cluster_indices     = clusterlist[i]
            cluster_indices_set = set(cluster_indices)  # Convert to a set for faster lookup
            cluster_minima_df   = lm_ids_df[lm_ids_df['lm_id'].isin(cluster_indices_set)]

            if not cluster_minima_df.empty:
                # Extract the IDs of the local minima
                cluster_minima_ids = cluster_minima_df['lm_id'].tolist()

                # Find the lowest minimum and its p-value
                lowest_minimum_id, lowest_minimum_p = Metrics.find_lowest_minimum(self, cluster_minima_ids)

                # Retrieve the voxel-to-local-minimum mapping and XYZ coordinates
                voxel_to_LM = self.brain_nav.fileInfo[file_nr]['voxel_to_LM']
                xyz_coords = list(voxel_to_LM[lowest_minimum_id])

                # map coords to ui space for mni conversion
                # x_ui, y_ui, z_ui  = self.brain_nav.fileInfo[file_nr]['inverse_mapped_matrix_F'][xyz_coords[0],xyz_coords[1], xyz_coords[2]]
                x_ui, y_ui, z_ui  = self.brain_nav.aligned_statMapInfo[(file_nr, file_nr_template)]['inverse_mapped_matrix_F'][xyz_coords[0],xyz_coords[1], xyz_coords[2]]

                xyz_max_ui.append([x_ui, y_ui, z_ui])

                # --- Get region name from atlas ---

                # Pick atlas key based on whether we're using the statmap as template or data as template
                if file_nr_template == self.brain_nav.data_bg_index:
                    atlas_key = ('data_as_template', file_nr)
                else:
                    atlas_key = file_nr_template

                atlasInfo = self.brain_nav.atlasInfo.get(atlas_key)

                try:
                    atlas_region_code = atlasInfo['data'][x_ui, y_ui, z_ui]
                    atlas_region_name = atlasInfo['codebook'].get(atlas_region_code, 'Undefined')
                except Exception as e:
                    print(f"Error retrieving atlas region: {e}")
                    atlas_region_name = 'None'

                atlas_names.append(atlas_region_name)

        
            # Identify the voxel with the maximum statistic within the cluster
            id_clus = np.argmax(clus_stat)

            # Get the index of the voxel with the maximum statistic
            # id_max = clusterlist[i][id_clus]

            # Use the previously retrieved coordinates as the maximum coordinates
            xyz_max = xyz_coords # These are in data space

            # Calculate the size of the current cluster
            clus_size = len(clusterlist[i])

            # Retrieve the TDP value for the cluster
            if clusterlist[i][clus_size - 1] < len(self.brain_nav.fileInfo[file_nr]['tdps']):
                clus_tdp = self.brain_nav.fileInfo[file_nr]['tdps'][clusterlist[i][clus_size - 1]]
            else:
                # If the index is out of bounds, print a warning
                print(f"Index {clusterlist[i][clus_size - 1]} is out of bounds for TDP list")

            # Append the calculated statistics for the current cluster to the tblARI list
            tblARI.append([
                clus_size,                # Cluster size
                None,                     # Placeholder for cluster ID, to be filled later
                round(clus_size * clus_tdp),  # Estimated number of false positives
                round(clus_size * (1 - clus_tdp)),  # Estimated number of true positives
                clus_tdp,                 # Active proportion (TDP) in the cluster
                xyz_max[0],               # X coordinate of the voxel with the maximum statistic
                xyz_max[1],               # Y coordinate of the voxel with the maximum statistic
                xyz_max[2],               # Z coordinate of the voxel with the maximum statistic
                clus_stat[id_clus]        # Maximum statistic value within the cluster
            ])
        
        print(f"Compute cluster statistics in prepare_tblARI: {time.time() - start_time1:.2f} seconds")
        print(" ")

        # Convert the list of cluster statistics to a NumPy array for easier handling
        tblARI = np.array(tblARI)

        # Update/overwrite result table and cluster/TDP maps
        if n == 1:
            clus = [1]
            Vox_xyzs = tblARI[0, 5:8].astype(int)  # Get voxel coordinates for the single cluster
            size = [int(tblARI[0, 0])]
            tdps = [float(tblARI[0, 4])]
            maxT = [float(tblARI[0, 8])]
            xyzV = [f"({int(Vox_xyzs[0])}, {int(Vox_xyzs[1])}, {int(Vox_xyzs[2])})"]
            
            # Convert voxel coordinates to MNI space
            # MNI_xyzs = self.xyz2MNI(Vox_xyzs, self.brain_nav.fileInfo[file_nr]['header'])
            try:
                # MNI_xyzs = self.xyz2MNI(Vox_xyzs, self.brain_nav.fileInfo[file_nr]['rtr_tamplate_affine'])
                # MNI_xyzs = self.xyz2MNI(np.array(xyz_max_ui[0]), self.brain_nav.fileInfo[file_nr]['rtr_template_affine'])
                MNI_xyzs = self.xyz2MNI(np.array(xyz_max_ui[0]), self.brain_nav.aligned_templateInfo[(file_nr, self.brain_nav.file_nr_template)]['rtr_template_affine'] )

            except:
                MNI_xyzs [0, 0, 0]

            xyzM = [f"({int(MNI_xyzs[0]):>4}, {int(MNI_xyzs[1]):>4}, {int(MNI_xyzs[2]):>4})"]

        else:
            clus = list(range(n, 0, -1))
            Vox_xyzs = tblARI[:, 5:8].astype(int)  # Get voxel coordinates for all clusters
            size = tblARI[:, 0].astype(int).tolist()
            tdps = np.round(np.array(tblARI[:, 4], dtype=float), 2).tolist()
            maxT = np.round(np.array(tblARI[:, 8], dtype=float), 2).tolist()
            xyzV = [f"({x[0]}, {x[1]}, {x[2]})" for x in Vox_xyzs]
            
            # Convert voxel coordinates to MNI space
            # MNI_xyzs = self.xyz2MNI(Vox_xyzs, self.brain_nav.fileInfo[file_nr]['header'])
            try:
                # MNI_xyzs = self.xyz2MNI(Vox_xyzs, self.brain_nav.fileInfo[file_nr]['rtr_tamplate_affine'])
                # MNI_xyzs = self.xyz2MNI(np.array(xyz_max_ui), self.brain_nav.fileInfo[file_nr]['rtr_tamplate_affine'])
                MNI_xyzs = self.xyz2MNI(np.array(xyz_max_ui), self.brain_nav.aligned_templateInfo[(file_nr, self.brain_nav.file_nr_template)]['rtr_template_affine'] )

            except:
                MNI_xyzs [0, 0, 0]
            # MNI_xyzs = self.xyz2MNI(Vox_xyzs, self.brain_nav.image.affine)
            xyzM = [f"{x[0]}, {x[1]}, {x[2]}" for x in MNI_xyzs]

        # Create the tblARI dictionary (common for both cases)
        tblARI = {
            'clus': clus,
            'cluster_ID': None,
            'size': size,
            'tdps': tdps,
            'maxT': maxT,
            'xyzV': xyzV,
            'xyzM': xyzM,
            'atlas_name': atlas_names
        }

        # Convert the list of lists into a pandas DataFrame for easier handling removed: 
        tblARI_df = pd.DataFrame(tblARI, columns=[
            'clus', "Unique ID", 'size', 'tdps', 'maxT', 'xyzV', 'xyzM', 'atlas_name'
        ])

        # Update the column names for final presentation
        tblARI_df.columns = [
            "Cluster",
            "Unique ID",
            "Size",
            "TDP",
            "max(Z)",
            "Vox (x, y, z)",
            "MNI (x, y, z)",
            "Region"
        ]
        
        # tblARI_df = pd.DataFrame({
        #     'clus': clus,
        #     'Unique ID': [None] * len(clus),
        #     'size': size,
        #     'tdps': tdps,
        #     'maxT': maxT,
        #     'xyzV': xyzV,
        #     'xyzM': xyzM
        # })

        # Return the prepared DataFrame (clusterlist is now ordered clusterlist)
        return clusterlist, tblARI, tblARI_df, Vox_xyzs

    def follow_cluster_xyz(self, selected_row):
        """
        Process the selected voxel coordinates, map them to UI space, 
        update slice indices, and trigger updates to the orthogonal view and metrics.

        Parameters:
            selected_row (int): The row index of the currently selected voxel in the table.
        """
        file_nr = self.brain_nav.file_nr
        file_nr_template = self.brain_nav.file_nr_template

        # Retrieve the voxel coordinates from the table
        voxel_coords_item = self.brain_nav.tblARI.table_widget.item(selected_row, 5)  # Assuming "Vox (x, y, z)" is the 5th column

        if voxel_coords_item:
            # Convert the string "(x, y, z)" into a tuple of integers
            voxel_coords_str = voxel_coords_item.text().strip("()")
            voxel_coords = tuple(map(int, voxel_coords_str.split(',')))
            
            # Map from native space to UI space coordinates
            # x_raw, y_raw, z_raw = self.brain_nav.fileInfo[self.brain_nav.file_nr]['mapped_coordinate_matrix_F'][
            #     voxel_coords[0], voxel_coords[1], voxel_coords[2]
            # ]
            # x_ui, y_ui, z_ui  = self.brain_nav.fileInfo[file_nr]['inverse_mapped_matrix_F'][voxel_coords[0], voxel_coords[1], voxel_coords[2]]
            x_ui, y_ui, z_ui = self.brain_nav.aligned_statMapInfo[(file_nr, file_nr_template)]['inverse_mapped_matrix_F'][voxel_coords[0], voxel_coords[1], voxel_coords[2]]


            # Update the slice indices
            self.brain_nav.sagittal_slice   = x_ui
            self.brain_nav.coronal_slice    = y_ui
            self.brain_nav.axial_slice      = z_ui

            # Retrieve and record the unique cluster ID
            cluster_id = int(self.brain_nav.tblARI.table_widget.item(selected_row, 1).text())  # Assuming "Unique ID" is the 2nd column
            self.brain_nav.ui_params['selected_cluster_id'] = cluster_id
            self.brain_nav.ui_params['selected_row'] = selected_row

            # Update the orthogonal view and display metrics
            self.brain_nav.orth_view_update.update_slices(selected_cluster_id=cluster_id)
            self.brain_nav.orth_view_update.update_crosshairs()
            # Metrics.show_metrics(self.brain_nav)
            self.show_metrics()
            self.brain_nav.UIHelp.update_ui_xyz()

    def change_cluster_size(self, value):
        import time
        """
        Adjust the size of a selected cluster based on user input (increase or decrease).
        """
        file_nr = self.brain_nav.file_nr
        file_nr_template = self.brain_nav.file_nr_template

        # Check if 'img_clus' exists in fileInfo for the current file number
        if 'img_clus' not in self.brain_nav.fileInfo[file_nr]:
            warning_message = (
                f"<span style='color: orange; font-weight: bold;'>"
                f"Warning: No clusters found, first run a thresholding analysis (TDP or ZSCORE based)."
                f"</span>"
            )
            self.brain_nav.message_box.log_message(warning_message)
            return

        xtr, ytr, ztr = self.brain_nav.sagittal_slice, self.brain_nav.coronal_slice, self.brain_nav.axial_slice
        
        # x_raw, y_raw, z_raw = self.brain_nav.fileInfo[file_nr]['mapped_coordinate_matrix_C'][xtr, ytr, ztr]
        x_raw, y_raw, z_raw = self.brain_nav.aligned_templateInfo[(file_nr, file_nr_template)]['mapped_coordinate_matrix_C'][xtr, ytr, ztr]


        cluster_label = self.brain_nav.fileInfo[file_nr]['img_clus'][x_raw, y_raw, z_raw]
        
        # We tranpose the img_clus because when img_clus is stored we transpose back to dimensions
        # before cpp computations (to prepare for alignment with template). Transposing it here will 
        # birng it in alignment with the cpp and indexing data (which takes the tranposed dimension as input).
        cluster_map = self.brain_nav.fileInfo[file_nr]['img_clus']
        cluster_label = cluster_map[x_raw, y_raw, z_raw]
        
        # self.brain_nav.statmaps[file_nr]['overlay_data'][x_raw, y_raw, z_raw]
        self.brain_nav.fileInfo[file_nr]['cluster_label'] = cluster_label

        print(" ")
        print("========== Timings within change_cluster_size START ==========")
        start_time0 = time.time()

        if not np.isnan(cluster_label):
            # Clear the old cluster label in the image (here we don't have to tranpose as dimensions do not
            # matter for this operation) image_clus is processed further in update_overlay_image called bellow
            tmp_clus_img = self.brain_nav.fileInfo[file_nr]['img_clus']
            self.brain_nav.fileInfo[file_nr]['img_clus'][tmp_clus_img == cluster_label] = np.nan
           
            # Get the current TDP for the cluster
            tblARI_df = self.brain_nav.fileInfo[file_nr]['tblARI_df']
            current_tdp = tblARI_df.loc[tblARI_df['Unique ID'] == cluster_label, 'TDP'].values[0]

            # Adjust the TDP
            # tdp_change = 0.01 if direction == "increase" else -0.01
            # new_tdp = current_tdp + tdp_change

            tdp_change = value - current_tdp 
            new_tdp = value

            # Call the cluster threshold modulation method
            start_time1 = time.time()
            updated_clusterlist = self.modulate_cluster_threshold(file_nr, cluster_label, new_tdp, tdp_change)
            # self.brain_nav.fileInfo[file_nr]['clusterlist'] = updated_clusterlist
            print(f"modulate_cluster_threshol: {time.time() - start_time1:.2f} seconds")
            
            # Update table data
            start_time2 = time.time()
            ord_clusterlist, _, tblARI_df, _ = self.prepare_tblARI(updated_clusterlist) #clus2node
            print(f"prepare_tblARI: {time.time() - start_time2:.2f} seconds")
            
            # Update cluster image (unique cluster ID is added to the table data here)
            start_time3 = time.time()
            _, _, tblARI_df = self.update_clust_img(ord_clusterlist, tblARI_df)
            print(f"update_clust_img: {time.time() - start_time3:.2f} seconds")
            
            # Update the table in the UI
            start_time4 = time.time()
            self.brain_nav.tblARI.update_table(tblARI_df)
            print(f"update table UI: {time.time() - start_time4:.2f} seconds")

            # Update the overlay image for visualization
            start_time5 = time.time()
            self.update_overlay_image(file_nr, cluster_label)
            print(f"update_overlay_image: {time.time() - start_time5:.2f} seconds")

            start_time6 = time.time()
            # Determine cluster ID of currently selected voxel (might have changed due to thresholding changes)
            x,y,z = self.brain_nav.sagittal_slice , self.brain_nav.coronal_slice, self.brain_nav.axial_slice 
            # xyz_clusID = self.brain_nav.statmaps[file_nr]['overlay_data'][x, y, z]
            xyz_clusID =  self.brain_nav.aligned_statMapInfo[(file_nr, file_nr_template)]['overlay_data'][x, y, z] 

            if xyz_clusID is not self.brain_nav.ui_params['selected_cluster_id']:
                # find corresponding row in table data
                row = tblARI_df[tblARI_df['Unique ID'] ==  xyz_clusID ].index[0]
                self.brain_nav.ui_params['selected_row'] = row
                new_tdp = tblARI_df.iloc[row].TDP
                
                # update UI
                self.brain_nav.ui_params['selected_cluster_id'] = xyz_clusID
                self.brain_nav.tblARI.highlight_selected_row(selected_row=row)
                self.brain_nav.cluster_ws.update_work_station(selected_row=row)
                self.brain_nav.orth_view_update.update_slices(selected_cluster_id=xyz_clusID)  
                self.brain_nav.UIHelp.update_tdp_ui(new_tdp)
                self.brain_nav.threeDviewer.update_cluster_3d_view(cluster_label)
            else:
                # Refresh the table and highlight the selected row
                self.brain_nav.tblARI.reset_highlight()
        
            print(f"update rest: {time.time() - start_time6:.2f} seconds")
            print(" ")
            print(f"total change time: {time.time() - start_time0:.2f} seconds")
            print("========== Timings within change_cluster_size END ==========")

            # else:
            #     # Refresh the table and highlight the selected row
            #     self.brain_nav.reset_highlight()
        else:
            print("\033[91m" + "No cluster found at the current location." + "\033[0m")
            message = (
                    f"<span style='color: orange; font-weight: bold;'>"
                    f"Warning! No cluster found at the current location. Make sure to select a cluster."
                    f"</span>"
                )
            self.brain_nav.message_box.log_message(message)

    def modulate_cluster_threshold(self, file_nr, cluster_label, new_tdp_threshold, tdp_change):
        """
        Modulate the threshold within a specific cluster and update the cluster voxel data.
        """
        file_nr_template = self.brain_nav.file_nr_template

        # check also if minimum has been reached or not, otherwise cpp will throuw error
        # increase should be fine, decrease an issue. 
        # Validate TDP threshold
        if not (0 <= new_tdp_threshold <= 1):
            print("\033[91mInvalid TDP threshold. Must be between 0 and 1. No changes were made.\033[0m")
            return self.brain_nav.fileInfo[file_nr]['clusterlist']  # Return without modification

        file_info = self.brain_nav.fileInfo[file_nr]

        # --- Update history for clusterlist ---
        # On the first threshold change, initialize the history with the current clusterlist
        if 'clusterlist_history' not in file_info:

            # Initialize the clusterlist history 
            file_info['clusterlist_history'] = []
            
            # Initalize the step counter
            if 'step' not in file_info:
                file_info['step'] = 0 
        
            # Append a deep copy of the current clusterlist.
            file_info['clusterlist_history'].append(copy.deepcopy(file_info['clusterlist']))

            # --- Update history for cluster label and crosshair position ---
            self.update_label_and_xyz_history()

            # step is always set as the last state in the history. 
            file_info['step'] = len(file_info['clusterlist_history']) - 1

            # Print the information 
            print('cluster_history n:', len(file_info['clusterlist_history']))
            print('step:', file_info['step'])
            print(" ")
            print('cluster_label_history:', file_info['cluster_label_history'])
            print('xyz_history:', file_info['xyz_history'])
            print(" ")

            message = (
            f"Cluster History: n = {len(file_info['clusterlist_history'])}<br>"
            f"Step: {file_info['step']}<br><br>"
            f"Cluster Label History: {file_info['cluster_label_history']}<br>"
            f"XYZ History: {file_info['xyz_history']}<br><br>"
            )
            self.brain_nav.message_box.log_message(message)
                                
        # Retrieve hierarchical data
        stcs = file_info['stcs']                 # Supra-threshold clusters
        marks = file_info['marks']               # Marking array
        tdp = file_info['tdps']                  # TDP values for clusters
        size = file_info['reslist']['SIZE']      # Cluster sizes
        child = file_info['reslist']['CHILD']    # Cluster hierarchy
        # clus2node = file_info['clus2node']

        # current voxel xyz (UI space) 
        xtr, ytr, ztr = self.brain_nav.sagittal_slice, self.brain_nav.coronal_slice, self.brain_nav.axial_slice

        # mapt current voxel (UI space) to unrototated raw space using mapping matrix
        # x_raw, y_raw, z_raw  = self.brain_nav.fileInfo[file_nr]['mapped_coordinate_matrix_C'][xtr, ytr, ztr]
        # xyz = self.brain_nav.fileInfo[file_nr]['mapped_coordinate_matrix_F'][xtr, ytr, ztr]
        xyz = self.brain_nav.aligned_templateInfo[(file_nr, file_nr_template)]['mapped_coordinate_matrix_F'][xtr, ytr, ztr]
        # xyz = self.brain_nav.fileInfo[file_nr]['mapped_coordinate_matrix_C'][xtr, ytr, ztr]
                

        # get volume dimensions
        # dims = self.brain_nav.fileInfo[file_nr]['header'].get_data_shape()
        
        # Because the cpp computations are done on transposed data, we take the transposed volume dimenions 
        # which we have defined in ARI.py
        dims =  self.brain_nav.fileInfo[file_nr]['tr_volDim']

        # retrieve voxel index based on xyz and dims
        # v = (z_raw - 1) * dims[0] * dims[1] + (y_raw - 1) * dims[0] + (x_raw - 1)
        v = Metrics.xyz2index(xyz, dims)

        # map to masked volume vector
        v = sum(file_info['indexp_linear']<=v)-1

        # check if v is part of any cluster. 
        # clustID = Metrics.findRep(v, size, file_info['clusterlist'])

        # --- New: Check the TDP change validity using the check_tdp_change function ---
        error_info = get_clusters.check_tdp_change(v, tdp_change, stcs, size, tdp, file_info['clusterlist'], marks)
        if error_info["error_code"] != 0:
            # If there is an error, do not call the changeQuery function.
            updated_clusters = file_info['clusterlist'] # old cluster list (misnomer)
            # print(f"Change Query Error {error_info['error_code']}: {error_info['error_message']}")
            print("\033[91m" + f"ERROR! Change Query Error {error_info['error_code']}: {error_info['error_message']}" + "\033[0m")
            # Construct the styled error message
            message = (
                f"<span style='color: red; font-weight: bold;'>"
                f"ERROR! Change Query Error {error_info['error_code']}: {error_info['error_message']}"
                f"</span>"
            )
            # Send the formatted message to the message log
            self.brain_nav.message_box.log_message(message)
            # return updated_clusters

        # Call the C++ changeQuery function generally faster!
        # updated_clusters = ARI_C.py_changeQuery(v, tdp_change, stcs, size, marks, tdp, child, file_info['clusterlist'])

        # Call the Pythonized  changeQuery routine
        updated_clusters = get_clusters.change_query(v, tdp_change, stcs, size, marks, tdp, child, file_info['clusterlist'])

        # update the clusterlist field
        file_info['clusterlist'] = updated_clusters 
        # check if xyz is still inside the cluster.. 



        # --- Update history for clusterlist, most recent version of clusterlist after threshold change ---

        # Append a deep copy of the current clusterlist.
        # if the current step is less than the max of history (user has gone back in history and then changed a state)
        # we update the current state with the new clusterlist. And remove the other future states.
        if file_info['step'] < len(file_info['clusterlist_history']) - 1:
            # file_info['step'] +=1
            file_info['clusterlist_history'][file_info['step']+1] = file_info['clusterlist']
            
            # Truncate history beyond the current step
            file_info['clusterlist_history'] = file_info['clusterlist_history'][:file_info['step'] + 2]
        
        # Otherwise we append to the end of the history.
        else:
            # First If already 5states are stored, remove the oldest one.
            if len(file_info['clusterlist_history']) >= 5:
                file_info['clusterlist_history'].pop(0)
            
            # add the latest
            file_info['clusterlist_history'].append(copy.deepcopy(file_info['clusterlist']))

        self.update_label_and_xyz_history()

        # step is always set as the last state in the history. When navigate the states in memory 
        # they can keep doing this and step will be updated in change_state(). As soon as they change
        # a state, that state becomes the most recent ones and the remaining future sates are deleted.
        # step will then again be reset to match the latest state in the history.
        file_info['step'] = len(file_info['clusterlist_history']) - 1

        print('cluster_history n:', len(file_info['clusterlist_history']))
        print('step:', file_info['step'])
        print(" ")
        print('cluster_label_history:', file_info['cluster_label_history'])
        print('xyz_history:', file_info['xyz_history'])
        print(" ")

        message = (
            f"Cluster History: n = {len(file_info['clusterlist_history'])}<br>"
            f"Step: {file_info['step']}<br><br>"
            f"Cluster Label History: {file_info['cluster_label_history']}<br>"
            f"XYZ History: {file_info['xyz_history']}<br><br>"
        )
        self.brain_nav.message_box.log_message(message)

        return updated_clusters

    def state_history(self):
        """
        Restore the previous cluster state, rolling back to the last valid step.
        """
        file_nr     = self.brain_nav.file_nr
        file_info   = self.brain_nav.fileInfo[file_nr]
        sender      = self.brain_nav.sender()  # Get the sender of the signal


        # Ensure history exists before using it
        if 'clusterlist_history' not in file_info or not file_info['clusterlist_history']:
            print("\033[91mNo history available.\033[0m")
            self.brain_nav.message_box.log_message("<span style='color: red;'>No history available.</span>")
            return

        step = file_info.get('step', 0)
        # clusterlist_history will never be longer then 5 so we can use the length of this list as max step
        max_step = len(file_info.get('clusterlist_history', [])) - 1
        if sender == self.brain_nav.cluster_ws.prev_state_button:
            if step - 1 < 0:
                print("\033[91m This is the earliest state in memory!\033[0m")
                self.brain_nav.message_box.log_message("<span style='color: red;'>This is the earliest state in memory!</span>")
                # return
            step = max(0, step - 1)  # Prevent step from going below 0
        elif sender == self.brain_nav.cluster_ws.next_state_button:
            if step >= max_step:
                print("\033[91m This is the most recent state!\033[0m")
                self.brain_nav.message_box.log_message("<span style='color: red;'>This is the most recent state!</span>")
                return
            else:
                step += 1

        # update step in file_info
        file_info['step'] = step

        # --- Restore previous clusterlist ---
        if 'clusterlist_history' in file_info and len(file_info['clusterlist_history']) > step:
            # Pop the last state and restore it
            clusterlist = file_info['clusterlist_history'][step]
            self.brain_nav.fileInfo[file_nr]['clusterlist'] = clusterlist
        else:
            print("\033[91mNo previous cluster state available to revert to\033[0m")
            return  # or do nothing
        
        # --- Restore previous cluster label ---
        if 'cluster_label_history' in file_info and len(file_info['cluster_label_history']) > step:
            label = file_info['cluster_label_history'][step]
        else:
            print("\033[91mNo previous cluster label available to revert to\033[0m")

        # --- Restore previous voxel coordinates (XYZ) ---
        if 'xyz_history' in file_info and len(file_info['xyz_history']) > step:
            x,y,z = file_info['xyz_history'][step]
        else:
            print("\033[91mNo previous coordinates available to revert to\033[0m")

        # --- Print State Information ---
        total_steps = len(file_info['clusterlist_history'])
        print("\033[96m--- State Restored ---\033[0m")
        print(f"Cluster State: {step + 1}/{total_steps}")  # Convert 0-based to 1-based for readability
        print(f"Cluster Label: {label if label is not None else 'N/A'}")
        print(f"Coordinates: (x={x}, y={y}, z={z})")
        
        message = (
            '<span style="color:#00ffff;">--- State Restored ---</span><br>'
            f"Cluster State: {step + 1}/{total_steps}<br>"
            f"Cluster Label: {label if label is not None else 'N/A'}<br>"
            f"Coordinates: (x={x}, y={y}, z={z})<br>"
        )
        self.brain_nav.message_box.log_message(message)

        # Recompute table data
        ord_clusterlist, _, tblARI_df, _ = self.prepare_tblARI(clusterlist)
        _, _, tblARI_df = self.update_clust_img(ord_clusterlist, tblARI_df)
        self.brain_nav.tblARI.update_table(tblARI_df)

        # Restore overlay
        self.update_overlay_image(file_nr, label)

        # Get updated cluster ID
        # xyz_clusID = self.brain_nav.statmaps[file_nr]['overlay_data'][x, y, z]
        xyz_clusID = self.brain_nav.aligned_statMapInfo[(file_nr, self.brain_nav.file_nr_template)]['overlay_data'][x, y, z]

        row = tblARI_df[tblARI_df['Unique ID'] == xyz_clusID].index[0]
        self.brain_nav.ui_params['selected_row'] = row
        new_tdp = tblARI_df.iloc[row].TDP

        # Map from native space to UI space coordinates
        # x_raw, y_raw, z_raw = self.brain_nav.fileInfo[self.brain_nav.file_nr]['mapped_coordinate_matrix_F'][x, y, z]
        # Update the slice indices
        self.brain_nav.sagittal_slice   = x
        self.brain_nav.coronal_slice    = y
        self.brain_nav.axial_slice      = z

        self.brain_nav.ui_params['selected_cluster_id'] = xyz_clusID
        self.brain_nav.tblARI.highlight_selected_row(selected_row=row)
        self.brain_nav.cluster_ws.update_work_station(selected_row=row)
        self.brain_nav.orth_view_update.update_slices(selected_cluster_id=xyz_clusID)
        self.brain_nav.orth_view_update.update_crosshairs()
        self.brain_nav.UIHelp.update_ui_xyz()
        self.brain_nav.UIHelp.update_tdp_ui(new_tdp)

    def update_label_and_xyz_history(self):
            """
            Updates the history for both the cluster label and the voxel coordinates (XYZ) based on the current UI state.
            This method ensures that if the user has navigated back in history and then made a change, the future (redo) history
            is truncated and the new state is inserted at the correct position. The history is capped at a maximum of 5 states.
            """
            # Get the file number and corresponding file_info dictionary
            file_nr     = self.brain_nav.file_nr
            file_info   = self.brain_nav.fileInfo[file_nr]  # Ensure consistency in accessing file_info

            # Retrieve the current cluster label from file_info (the one that was just updated in the UI)
            cluster_label = file_info['cluster_label']   
            
            # Retrieve the current voxel coordinates (from UI slices)
            x,y,z = self.brain_nav.sagittal_slice , self.brain_nav.coronal_slice, self.brain_nav.axial_slice 

            # --- Update history for cluster label ---
            # Initialize the history list if it doesn't exist
            if 'cluster_label_history' not in file_info:
                file_info['cluster_label_history'] = []
            # Ensure the step index exists; default to 0 if not
            if 'step' not in file_info:
                file_info['step'] = 0

            # If the current step is less than the last index in the history, we are in a "backed-up" state.
            # In that case, update the state immediately following the current step and truncate any future states.
            if file_info['step'] < len(file_info['cluster_label_history']) - 1:
                # Overwrite the history at the current step with the current cluster label
                file_info['cluster_label_history'][file_info['step']+1] = copy.deepcopy(cluster_label)
                
                # Remove any future history beyond the new current step
                file_info['cluster_label_history'] = file_info['cluster_label_history'][:file_info['step'] + 2]
            else:
                # If we are at the end of the history, first ensure we keep only a maximum of 5 states
                if len(file_info['cluster_label_history']) >= 5:
                    file_info['cluster_label_history'].pop(0)
                
                # Append the current cluster label as a deep copy to the end of the history list
                file_info['cluster_label_history'].append(copy.deepcopy(cluster_label))

            # --- Update history for voxel coordinates (XYZ) ---
            # Same logic as above, but for the voxel coordinates
            if 'xyz_history' not in file_info:
                file_info['xyz_history'] = []

            # If user navigated back in history and changed state, update and truncate future history
            if file_info['step'] < len(file_info['xyz_history']) - 1:
                file_info['xyz_history'][file_info['step']+1] = copy.deepcopy((x, y, z))
                file_info['xyz_history'] = file_info['xyz_history'][:file_info['step'] + 2]
            else:
                 # Keep only 5 states in history
                if len(file_info['xyz_history']) >= 5:
                    file_info['xyz_history'].pop(0)
                
                file_info['xyz_history'].append(copy.deepcopy((x, y, z)))  

    def update_overlay_image(self, file_nr, cluster_label=None):
        """
        Update and align the overlay image with the background for visualization.
        """
        # Important! The img_clus that goes in here needs to be set the the dimensions 
        # of the raw image data upon loading. The reason is that this is required to get 
        # proper alignment (or at leas the best possible). If you get misalignments this 
        # can either be realted to the origins not set to the same anatomical location (e.g. AC)
        # or a mismatch in data structure.

        file_nr_template = self.brain_nav.file_nr_template

        # If we make sure that img_clus is always in the state as it was defined (transposed raw data)
        # We transpose it back here to have it in original state before alignment.
        cluster_image =  self.brain_nav.fileInfo[file_nr]['img_clus'].T 

        # Step 1: Build cluster image using original affine and header
        cluster_image = nib.Nifti1Image(
            cluster_image, 
            affine=self.brain_nav.fileInfo[file_nr]['affine'],
            header=self.brain_nav.fileInfo[file_nr]['header']
        )

        template_image = self.brain_nav.templates[file_nr_template]['image']

        # Step 2: Align to background template (already fully preprocessed)
        a_cluster_image, _ = ImageProcessing.align_images(template_image, cluster_image, order=1)

        # Step 3: Transpose to match template orientation
        tra_cluster_image = ImageProcessing.transpose_image(a_cluster_image)

        # Step 4: Rotate to match template rotation
        _, rtra_cluster_image, _ = ImageProcessing.rotate_volume(tra_cluster_image)

        # Step 5: Extract data
        aligned_overlay_data = rtra_cluster_image.get_fdata()

        # Step 6: Update navigation tool with aligned overlay
        self.brain_nav.overlay_data = aligned_overlay_data
        # self.brain_nav.statmaps[file_nr]['overlay_data'] = aligned_overlay_data
        self.brain_nav.aligned_statMapInfo[(file_nr, file_nr_template)]['overlay_data']    = aligned_overlay_data

        # Step 7: Update visual slices with selected cluster highlighted
        self.brain_nav.orth_view_update.update_slices(selected_cluster_id=cluster_label)


    @staticmethod
    def findRep(v, size, ans):
        """
        Find the index of the cluster that contains voxel v in the cluster list ans.

        Parameters:
            v (int): The voxel index to find.
            size (list): List of subtree sizes for all nodes.
            ans (list of lists): List of clusters, where each cluster is a list of node indices.

        Returns:
            int: The index of the cluster containing v, or -1 if not found.
        """
        for i, clus in enumerate(ans):
            irep = clus[-1]  # Representative of the cluster (last element)

            # Check if the representative matches the voxel
            if irep == v:
                return i

            # Check subtree sizes
            if size[irep] > size[v]:
                left = 0
                right = len(clus) - 1

                # Perform a linear search
                while left <= right:
                    if clus[left] == v:
                        return i
                    left += 1

                    if clus[right] == v:
                        return i
                    right -= 1

        return -1

    def update_clust_img(self, clusterlist, tblARI_df):
        """
        Update the cluster image and ARI table by assigning cluster IDs based on the lowest local minima.

        This method processes a given list of clusters, retrieves corresponding voxel coordinates, and
        identifies the lowest local minima for each cluster using pre-stored file information. It then
        assigns cluster IDs to the appropriate voxel coordinates in the cluster image and updates the
        provided ARI table with these IDs.

        Parameters:
            clusterlist (list of lists): A list where each element is a list of voxel indices representing a cluster.
            tblARI_df (pandas.DataFrame): A DataFrame containing cluster statistics, which will be updated with cluster IDs.

        Returns:
            tuple:
                - img_clus (numpy.ndarray): A 3D array representing the updated cluster image with assigned cluster IDs.
                - tblARI_df (pandas.DataFrame): The updated ARI table with assigned cluster IDs in the 'Unique ID' column.
        """
        # Retrieve necessary data from self
        file_nr         = self.brain_nav.file_nr
        lm_ids_df       = self.brain_nav.fileInfo[file_nr]['stable_LM_ids_df']
        # img_clus        = np.zeros(self.brain_nav.fileInfo[file_nr]['header']['dim'][1:4])
        # img_tdps        = np.zeros(self.brain_nav.fileInfo[file_nr]['header']['dim'][1:4])  # Initialize an empty array for the TDP map
        img_clus        = np.zeros(self.brain_nav.fileInfo[file_nr]['tr_volDim'])
        img_tdps        = np.zeros(self.brain_nav.fileInfo[file_nr]['tr_volDim']) 
        # tblARI_df       = self.brain_nav.fileInfo[file_nr]['tblARI_df']
        # clusterlist = self.brain_nav.fileInfo[file_nr]['clusterlist']

        n = len(clusterlist)

        for i in range(n):  # Iterate over all clusters
            cluster_indices = clusterlist[i]  # Indices for the current cluster

            # Map indices to voxel coordinates
            x_coords = self.brain_nav.fileInfo[file_nr]['indexp'][0][cluster_indices]
            y_coords = self.brain_nav.fileInfo[file_nr]['indexp'][1][cluster_indices]
            z_coords = self.brain_nav.fileInfo[file_nr]['indexp'][2][cluster_indices]

            # Filter DataFrame
            cluster_indices_set = set(cluster_indices)  # Convert to a set for faster lookup
            cluster_minima_df = lm_ids_df[lm_ids_df['lm_id'].isin(cluster_indices_set)]

            # Extract the filtered IDs
            cluster_minima_ids = cluster_minima_df['lm_id'].tolist()

            if cluster_minima_ids:
                # Determine the lowest minimum using the tree structure
                lowest_minimum_id, _ = Metrics.find_lowest_minimum(self, cluster_minima_ids)

                # Index final cluster ID
                cluster_ID = self.brain_nav.fileInfo[file_nr]['stable_LM_ids_count'].get(lowest_minimum_id, None)

                # Assign the cluster ID based on the lowest minimum
                img_clus[x_coords, y_coords, z_coords] = cluster_ID

                # Update tblARI with the actual cluster_ID (second column)
                tblARI_df.loc[i, 'Unique ID'] = cluster_ID

                # img_tdps[x_coords, y_coords, z_coords] =  tblARI_df.loc[i, 'TPD']  # Assign the TDP value to the TDP map

            else:
                print(f"No local minima found for cluster {i}")
                # Append None or a placeholder value to maintain consistency
                tblARI_df.loc[i, 'Unique ID'] = None

        # Update the table in self to align other routines
        self.brain_nav.fileInfo[file_nr]['tblARI_df'] = tblARI_df

        # write img_clus to self
        # self.brain_nav.fileInfo[file_nr]['img_clus'] = img_clus
        self.brain_nav.fileInfo[file_nr]['img_clus'] = img_clus # transpose back to the original to align with background

        return img_clus, img_tdps, tblARI_df

    # @staticmethod
    # def xyz2MNI(xyz, hdr):
    #     """
    #     Convert voxel coordinates to MNI coordinates.
        
    #     Parameters:
    #     - xyz: A numpy array of shape (n, 3) containing voxel coordinates or a 1D array with 3 coordinates.
    #     - hdr: A dictionary containing the srow_x, srow_y, and srow_z vectors from the NIfTI header.
        
    #     Returns:
    #     - MNI_xyz: A numpy array containing the MNI coordinates.
    #     """

    #     # Transformation matrix
    #     transMatrix = np.vstack([hdr['srow_x'], hdr['srow_y'], hdr['srow_z']])

    #     if len(xyz.shape) == 1:  # Single coordinate
    #         MNI_xyz = np.dot(transMatrix, np.append(xyz, 1))
    #     else:  # Multiple coordinates
    #         MNI_xyz = np.dot(transMatrix, np.hstack([xyz, np.ones((xyz.shape[0], 1))]).T).T

    #     return MNI_xyz.astype(int)

    def xyz2MNI(self, xyz, affine):
        """
        Convert UI-space voxel coordinates (with Z-axis needing flipping) to MNI coordinates.

        Parameters:
        - xyz: A 1D array of 3 coordinates or a 2D array (n, 3)
        - affine: The affine matrix to convert voxel space to MNI space

        Returns:
        - MNI coordinates (int)
        """
        template_data = self.brain_nav.templates[self.brain_nav.file_nr_template]['data']

        # Flip the Z-axis to match voxel-to-world orientation
        if xyz.ndim == 1:
            xyz = xyz.copy()
            xyz[2] = template_data.shape[2] - 1 - xyz[2]
            return (affine @ np.append(xyz, 1))[:3].astype(int)
        else:
            xyz = xyz.copy()
            xyz[:, 2] = template_data.shape[2] - 1 - xyz[:, 2]
            return (affine @ np.hstack([xyz, np.ones((xyz.shape[0], 1))]).T).T[:, :3].astype(int)

    # @staticmethod
    # def xyz2MNI(xyz, hdr, ac_voxel=[98, 137, 121], ac_mni=[0, 0, -187]):
    #     """
    #     Convert voxel coordinates to MNI coordinates, with AC correction.

    #     Parameters:
    #     - xyz: A numpy array of shape (n, 3) containing voxel coordinates or a 1D array with 3 coordinates.
    #     - hdr: A dictionary containing the srow_x, srow_y, and srow_z vectors from the NIfTI header.
    #     - ac_voxel: The voxel coordinates of the Anterior Commissure (AC).
    #     - ac_mni: The desired MNI coordinates for the AC.

    #     Returns:
    #     - MNI_xyz: A numpy array containing the MNI coordinates.
    #     """

    #     # Transformation matrix
    #     transMatrix = np.vstack([hdr['srow_x'], hdr['srow_y'], hdr['srow_z'], [0, 0, 0, 1]])

    #     # Compute the AC correction
    #     ac_voxel_hom = np.append(ac_voxel, 1)  # Homogeneous coordinates
    #     ac_mni_current = np.dot(transMatrix, ac_voxel_hom)[:3]  # Current MNI of AC
    #     correction = np.array(ac_mni) - ac_mni_current  # Compute correction shift

    #     if len(xyz.shape) == 1:  # Single coordinate
    #         MNI_xyz = np.dot(transMatrix, np.append(xyz, 1))[:3] + correction
    #     else:  # Multiple coordinates
    #         MNI_xyz = np.dot(transMatrix, np.hstack([xyz, np.ones((xyz.shape[0], 1))]).T).T[:, :3] + correction

    #     return MNI_xyz.astype(int)

    # @staticmethod
    # def xyz2MNI(xyz, affine):
    #     """
    #     Convert voxel coordinates to MNI coordinates dynamically using the affine matrix.

    #     Parameters:
    #     - xyz: A numpy array of shape (n, 3) containing voxel coordinates or a 1D array with 3 coordinates.
    #     - affine: The affine transformation matrix from the NIfTI file.

    #     Returns:
    #     - MNI_xyz: A numpy array containing the MNI coordinates.
    #     """

    #     if len(xyz.shape) == 1:  # Single coordinate case
    #         MNI_xyz = np.dot(affine[:3, :3], xyz) + affine[:3, 3]
    #     else:  # Multiple coordinates case
    #         MNI_xyz = np.dot(affine[:3, :3], xyz.T).T + affine[:3, 3]

    #     return MNI_xyz.astype(int)  # Avoid unintended integer rounding
    
    @staticmethod
    def xyz2index(coords_array, dims):
        """
        Converts (x, y, z) coordinates into 1D indices given the volume dimensions.

        Parameters:
        coords_array (np.ndarray or list): Single (x, y, z) coordinate or an array of (x, y, z) coordinates.
                                        Shape should be (3,) for a single coordinate or (N, 3) for multiple.
        dims (tuple): The dimensions of the 3D volume (dim_x, dim_y, dim_z).

        Returns:
        int or np.ndarray: A single 1D index for a single (x, y, z) coordinate or an array of 1D indices for multiple.
        """
        # Ensure coords_array is a numpy array
        coords_array = np.asarray(coords_array)

        # Single coordinate case (shape: (3,))
        if coords_array.ndim == 1 and coords_array.shape[0] == 3:
            index = coords_array[0] + coords_array[1] * dims[0] + coords_array[2] * dims[0] * dims[1]
            return int(index)  # Return as a single integer

        # Multiple coordinates case (shape: (N, 3))
        elif coords_array.ndim == 2 and coords_array.shape[1] == 3:
            indices = coords_array[:, 0] + coords_array[:, 1] * dims[0] + coords_array[:, 2] * dims[0] * dims[1]
            return indices  # Return as an array of integers

        else:
            raise ValueError("Invalid input shape for coords_array. Expected shape (3,) or (N, 3).")

    @staticmethod
    def mapXYZs(coords, small_space_dims, large_space_dims):
        """
        Maps coordinates from a smaller space to a corresponding larger space.

        Args:
            coords (np.ndarray): Array of (x, y, z) coordinates in the smaller space, with shape (N, 3).
            small_space_dims (tuple or list): Dimensions of the smaller space (x, y, z).
            large_space_dims (tuple or list): Dimensions of the larger space (x, y, z).

        Returns:
            np.ndarray: Mapped (x, y, z) coordinates in the larger space, with shape (N, 3).
        """
        # Ensure coordinates are a NumPy array
        coords = np.asarray(coords)
        
        # Convert dimensions to NumPy arrays for element-wise operations
        small_space_dims = np.array(small_space_dims)
        large_space_dims = np.array(large_space_dims)
        
        # Calculate scaling factors for each dimension
        scaling_factors = large_space_dims / small_space_dims
        
        # Apply scaling factors to map coordinates to the larger space
        mapped_coords = np.round(coords * scaling_factors).astype(int)
        
        return mapped_coords    
    
    # def map_raw_to_aligned(self, raw_coords, file_nr):
    #     """
    #     Map coordinates from raw space to aligned space.
        
    #     :param raw_coords: numpy array of shape (N, 3) containing raw coordinates
    #     :param file_nr: file number to access the correct transformation information
    #     :return: numpy array of shape (N, 3) containing aligned coordinates
    #     """

    #     template_image = self.brain_nav.templates[file_nr]['image']

    #     # Get the necessary transformation matrices
    #     raw_affine = self.brain_nav.fileInfo[file_nr]['transposed_affine']
    #     # aligned_affine = self.brain_nav.fileInfo[file_nr]['aligned_overlay_affine']
    #     aligned_affine = template_image.affine;

    #     # Create the transformation matrix from raw to aligned space
    #     raw_to_aligned = np.linalg.inv(aligned_affine).dot(raw_affine)
        
    #     # Add a column of ones to the raw coordinates for homogeneous coordinates
    #     homogeneous_coords = np.hstack((raw_coords, np.ones((raw_coords.shape[0], 1))))
        
    #     # Apply the transformation
    #     aligned_coords = raw_to_aligned.dot(homogeneous_coords.T).T
        
    #     # Remove the homogeneous coordinate and round to nearest integer
    #     return np.round(aligned_coords[:, :3]).astype(int)
    
        
    # def find_lowest_minimum(self, cluster_indices):
    #     """
    #     Finds the 'lowest minimum' within a cluster by identifying the leaf node
    #     with the smallest p-value.

    #     Parameters:
    #         cluster_indices (list): Indices of leaf nodes belonging to the cluster.

    #     Returns:
    #         int: The index of the node that represents the 'lowest minimum'.
    #         float: The p-value of the lowest minimum.
    #     """

    #     file_nr = self.brain_nav.file_nr

    #     # Retrieve p-values and their sorted order
    #     p = self.brain_nav.fileInfo[file_nr]['p']           # Array of p-values for all nodes
    #     # ordp = self.brain_nav.fileInfo[file_nr]['ordp']     # Sorted indices of p-values (1-based)

    #     # Convert ordp to 0-based indexing for Python compatibility
    #     # ordp_0 = ordp - 1

    #     # Retrieve p-values for all nodes in cluster_indices
    #     # cluster_pvals = [p[ordp_0[node]] for node in cluster_indices]
    #     cluster_pvals = [p[node] for node in cluster_indices]

    #     # Find the index of the node with the smallest p-value
    #     min_index = cluster_indices[np.argmin(cluster_pvals)]

    #     # Retrieve the smallest p-value
    #     min_pval = min(cluster_pvals)

    #     return min_index, min_pval


    def find_lowest_minimum(self, cluster_indices):
        # This function identifies the "lowest minimum" in a given cluster by locating the leaf node with the smallest p-value. Here's how it works:

        # 1. **Retrieve Relevant Data**:
        # - `p`: The array of p-values for all nodes in the dataset, representing their statistical significance.
        # - `ordp`: The sorted indices of p-values, converted to 0-based indexing for Python compatibility (`ordp_0`).

        # 2. **Create a DataFrame**:
        # - A Pandas DataFrame (`p_df`) is created to pair each node's index with its corresponding p-value for easier indexing and filtering.
        # - An optional column (`sorted_node`) is added to store the 0-based sorted indices.

        # 3. **Filter to Relevant Nodes**:
        # - The DataFrame is filtered to include only the nodes that are part of the provided `cluster_indices`. This ensures the operation focuses exclusively on the current cluster.

        # 4. **Identify the Minimum**:
        # - Within the filtered DataFrame, the function identifies the row corresponding to the node with the smallest p-value using the `idxmin()` method.

        # 5. **Extract Results**:
        # - The node index (`min_index`) and its p-value (`min_pval`) are extracted from the identified row. These represent the cluster's "lowest minimum."

        # 6. **Return Values**:
        # - The function returns the node index of the lowest minimum and its associated p-value.

        # In summary, this function pinpoints the most statistically significant voxel (smallest p-value) within a given cluster, ensuring that subsequent cluster-based operations (like coloring or tracking) are grounded.
        
        """
        Finds the 'lowest minimum' within a cluster by identifying the leaf node
        with the smallest p-value using Pandas for efficient indexing.

        Parameters:
            cluster_indices (list): Indices of leaf nodes belonging to the cluster.

        Returns:
            int: The index of the node that represents the 'lowest minimum'.
            float: The p-value of the lowest minimum.
        """
        file_nr = self.brain_nav.file_nr

        # Retrieve p-values
        p = self.brain_nav.fileInfo[file_nr]['p']  # Array of p-values for all nodes

        # Optional: Retrieve ordp for mapping sorted indices (1-based to 0-based)
        ordp = self.brain_nav.fileInfo[file_nr]['ordp']  # Sorted indices of p-values (1-based)
        ordp_0 = ordp - 1  # Convert to 0-based indexing

        # Create a Pandas DataFrame for easy indexing and filtering
        p_df = pd.DataFrame({'node': range(len(p)), 'p_value': p})
        # Optional: Add ordp as an additional column for reference 
        p_df['sorted_node'] = ordp_0

        # Filter DataFrame to only include nodes in the cluster
        cluster_df = p_df.loc[p_df['node'].isin(cluster_indices)]

        # Find the row with the minimum p-value
        min_row = cluster_df.loc[cluster_df['p_value'].idxmin()]

        # Extract the node index and p-value of the lowest minimum
        min_index = min_row['node']
        min_pval = min_row['p_value']

        return int(min_index), float(min_pval)
    