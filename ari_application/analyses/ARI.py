# Standard library imports
import time

# Third-party imports
import numpy as np
import pandas as pd
import nibabel as nib
from scipy.stats import norm

# PyQt5 imports
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QProgressDialog

# Project-specific imports (organized by module type)
from ari_application.models.image_processing import ImageProcessing
from ari_application.models.metrics import Metrics

from ari_application.analyses.utils import Utilities
from ari_application.analyses.hommel import pyHommel
from ari_application.orth_views.orth_view_setup import OrthViewSetup

# Cython extensions
import ari_application.cpp_extensions.cython_modules.hommel as hommel
import ari_application.cpp_extensions.cython_modules.ARICluster as ARI_C

class pyARI:
    def __init__(self, BrainNav):
        """
        Initialize the ARI class with a reference to the brain_nav instance.
        
        :param brain_nav: Instance of the BrainNav class containing the necessary data and parameters.
        """
        self.brain_nav = BrainNav

    @property
    def fileInfo(self):
        return self.brain_nav.fileInfo

    def runARI(self):
        gammas = np.arange(0, 1.01, 0.01)

        # Use a fixed total of 100 steps for better control
        TOTAL_STEPS = 100
        
        # Allocate steps for each major phase
        HOMMEL_STEPS = 5        # 5% for hommel
        HALPHA_STEPS = 5        # 5% for alpha thresholds
        ADJLIST_STEPS = 10      # 10% for adjacency list
        CLUSTERS_STEPS = 10     # 10% for clusters
        TDP_STEPS = 10          # 10% for TDP calculations
        QUERY_PREP_STEPS = 10   # 10% for query preparation
        GAMMA_STEPS = 30        # 30% for gamma iteration
        LM_STEPS = 5            # 5% for local minima
        TEMPLATE_STEPS = 10     # 10% for template alignment
        FINAL_STEPS = 5         # 5% for final updates
    
        progress = QProgressDialog("Initializing ARI analysis...", "Cancel", 0, TOTAL_STEPS, self.brain_nav.main_window)
        progress.setWindowModality(Qt.WindowModal)
        progress.setValue(0)
        progress.show()

        file_nr = self.brain_nav.file_nr
        file_nr_template = self.brain_nav.file_nr_template

        # Get the p values required by hommel & co below
        p, pval, m, indexp = Utilities(self.brain_nav).getPVals()

        # retrieve conn
        conn = self.brain_nav.input['conn']

        # Compute the whole-brain TDP, i.e. min(TDP)
        #    1.	Instance Creation with hommel_wbTDP Method:
        #        •	When you call hom = pyHommel.hommel_wbTDP(p, simes=True), you create an instance of the pyHommel class.
        #        •	This instance, hom, has attributes like p, jump_alpha, sorter, adjusted, simes_factor, and simes.
        #    2.	Calling the tdp Method:
        #        •	By calling mintdp = hom.tdp(alpha=0.05), you invoke the tdp method on the hom instance.
        #        •	Inside this method, self refers to the hom instance, allowing access to its attributes (self.p is equivalent to hom.p).
        #    3.	Accessing and Passing Instance Attribut es:
        #        •	The tdp method can access self.p, self.jump_alpha, etc., because these are attributes of the hom instance.
        #        •	When calling self.discoveries(alpha=alpha, incremental=incremental), the discoveries method is 
        #           invoked with the self instance, allowing it to access the same attributes.
        #    4.	Using Attributes in Methods:
        #        •	Within the discoveries method, self.p, self.sorter, and other attributes are accessible, 
        #           allowing the method to perform computations based on these values.
        #        •	These values are then passed to the C++ function hommel.py_findDiscoveries, which 
        #           returns the discoveries back to the discoveries method.
        #    5. Returning Values:
        #       •	The discoveries method returns a value, which is then used in the tdp method.
        #       •	The tdp method calculates the True Discovery Proportion (TDP) and returns this value to 
        #           the initial call mintdp = hom.tdp(alpha=0.05). 
        #        
        
        # Use alpha from settings 
        alpha = self.brain_nav.input['alpha']

        print('entering hommel')
        # Hommel step
        progress.setLabelText("Computing whole-brain TDP...")
        hom = pyHommel.hommel_wbTDP(p, simes=True)
        mintdp = hom.tdp(alpha = alpha)
        progress.setValue(HOMMEL_STEPS)

        # Update progress
        progress.setValue(5)

        if mintdp == 0:
            print("No significant brain activations can be detected.")
            return None
        
        print('entering findHalpha')
        # Alpha threshold step
        progress.setLabelText("Calculating alpha thresholds...")
        halpha          = hommel.py_findHalpha(hom.jump_alpha, alpha = alpha, m=m)
        # simeshalpha = hom.simes_factor[halpha + 1]
        simeshalpha     = hom.simes_factor[halpha]
        conc_thres      = hom.concentration(alpha)
        progress.setValue(HOMMEL_STEPS + HALPHA_STEPS)

        # Remove hom (not needed in Python unused variables are
        # automatically removed by the garbage collector)
        # del hom

        # Sort p-values in ascending order and get the sorted indices  
        # ordp = np.argsort(p)
        # ordp = ordp.astype(int)  # Ensure ordp is of integer type
        flattened_p = p.flatten(order='C')
        ordp_flat   = np.argsort(p, kind='stable')
        ordp        = ordp_flat.astype(int)

        # Find the sorting ranks for unsorted p-values
        rankp       = np.zeros(m, dtype=int)
        # rankp[ordp] = np.arange(1, m + 1)
        rankp[ordp] = np.arange(m)
        
        rankp       = rankp.astype(int)  # Ensure rankp is of integer type

        # Correct for one based ordering
        ordp += 1
        rankp +=1

        # Create a 3D whole-brain mask of unsorted orders (starts from 1)
        # volDim = self.fileInfo[file_nr]['header'].get_data_shape()
        # volDim =  self.fileInfo[file_nr]['original_data_dimensions']
        # volDim = self.fileInfo[file_nr]['data'].shape

        # In pval utility function we have transposed the data, this is needed for cpp, here we take the data shape
        # which is still untransposed and transpose its dimensions the same way so that the mask is in alignment
        volDim = self.fileInfo[file_nr]['data'].shape
        volDim = [volDim[i] for i in [2, 1, 0]]
   

        # Initialize 3D mask with zeros
        maskI = np.zeros(volDim, dtype=int)  # Assuming volDim is equivalent to fileInfo$header$dim[2:4]

        # Create a 1-based index for assigning values to mask
        maskI[tuple(indexp)] = np.arange(1, len(indexp[0]) + 1)  # Assigns 1 to m (like 1:m in R)

        # Flatten maskI into a list in C-order
        maskI_flat = maskI.flatten('C').tolist()
        
        indexp_linear   = np.ravel_multi_index(indexp, maskI.shape, order='C')

        # Convert volDim to list
        # volDim_list = list(volDim)
        # volDim_list = list(self.fileInfo[file_nr]['original_data_dimensions'])
        
        # While the mask is constructed using the 'new' dimensions, findAdjList still requires the original data dimensions
        # for it to work properly --> WHY?
        volDim_list = list(self.fileInfo[file_nr]['data'].shape)
        # volDim_list = [volDim_list[i] for i in [2, 1, 0]]  

        # Call the Cython functions

        # Adjacency list step
        print('entering py_findAdjList')
        progress.setLabelText("Building voxel adjacency list...")
        adj     = ARI_C.py_findAdjList(maskI_flat, indexp_linear.tolist(), volDim_list, m, conn)        
        # adj     = get_adjList.findAdjList(maskI_flat, indexp_linear.tolist(), volDim_list, m, conn)
        # adj     = ARI_C.py_findAdjList(maskI_flat, indexp_linear.tolist(), [59, 77, 65], m, conn)
        progress.setValue(HOMMEL_STEPS + HALPHA_STEPS + ADJLIST_STEPS)

        # Cluster identification step
        print('entering py_findClusters')
        progress.setLabelText("Identifying brain clusters...")
        reslist = ARI_C.py_findClusters(m, adj, ordp.tolist(), rankp.tolist())
        progress.setValue(HOMMEL_STEPS + HALPHA_STEPS + ADJLIST_STEPS + CLUSTERS_STEPS)

        # TDP calculation step
        print('entering py_forestTDP')
        progress.setLabelText("Computing cluster TDP values...")
        tdps    = ARI_C.py_forestTDP(m, halpha, alpha, simeshalpha, p.tolist(), reslist["SIZE"], reslist["ROOT"], reslist["CHILD"])
        progress.setValue(HOMMEL_STEPS + HALPHA_STEPS + ADJLIST_STEPS + CLUSTERS_STEPS + TDP_STEPS)

        # Query preparation step
        print('entering py_queryPreparation')
        progress.setLabelText("Preparing for TDP queries...")
        stcs    = ARI_C.py_queryPreparation(m, reslist["ROOT"], tdps, reslist["CHILD"])
        progress.setValue(HOMMEL_STEPS + HALPHA_STEPS + ADJLIST_STEPS + CLUSTERS_STEPS + TDP_STEPS + QUERY_PREP_STEPS)


        # initialize a vector for marking found clusters
        marks = np.zeros(m, dtype=int)
        marks = marks.tolist()

        # initialize cluster image: >0 for voxels within clusters & gradient map
        # Get the dimensions of the transposed functional data 
        # dim = self.fileInfo[file_nr]['header'].get_data_shape()
        dim = volDim
        # dim = [65, 77, 49]

        # Initialize the cluster image and gradient map with zeros
        clusimg = np.zeros(dim)
        gradmap = np.zeros(dim)

        # Define TDP thresholds ranging from 0 to 1 with 0.01 increments
        # gammas = np.arange(0, 1.01, 0.01)

        # Start timer for the batch query
        query_time = 0
        tic = time.time()

        # Call the batch function with all gamma values at once. Results are the same but C implementation outperforms
        # Python version. Making connection with C routine takes long but the itterations are much faster in C. 
        print('entering py_answerQueryBatch')
        progress.setLabelText("Running TDP queries for gradient map...")
        batch_clusterlists = ARI_C.py_answerQueryBatch(gammas.tolist(), stcs, reslist['SIZE'], marks, tdps, reslist['CHILD'])
        # batch_clusterlists = get_clusters.answer_query_batch(gammas.tolist(), stcs, reslist['SIZE'], marks, tdps, reslist['CHILD'])

        # Update for starting gamma loop
        current_progress = HOMMEL_STEPS + HALPHA_STEPS + ADJLIST_STEPS + CLUSTERS_STEPS + TDP_STEPS + QUERY_PREP_STEPS
        progress.setValue(current_progress)
        
        # For gamma iterations, use a subset of update points to avoid excessive redraws
        num_gammas = len(gammas)
        update_points = 10  # Number of visual updates during gamma iteration
        update_interval = max(1, num_gammas // update_points)

        # End timer for the batch query
        toc = time.time()
        query_time += toc - tic
        print(f"Query time: {query_time:.4f} seconds")

        # Loop through each result in the batch
        for i, clusterlist in enumerate(batch_clusterlists):
            if progress.wasCanceled():
                break
            
            g = gammas[i]  # Corresponding gamma value
            
            # Only update the progress dialog occasionally to avoid UI slowdowns
            if i % update_interval == 0 or i == num_gammas - 1:
                # Calculate progress within the GAMMA_STEPS allocation
                gamma_progress = int((i / num_gammas) * GAMMA_STEPS)
                progress.setValue(current_progress + gamma_progress)
                progress.setLabelText(f"Building gradient map: {int(g*100)}% TDP")

            
            if len(clusterlist) != 0:
                # Adjust the zero-based index correction
                # Flatten the cluster list and use it to index into 'indexp'
                out_ids = indexp_linear[np.concatenate(clusterlist)]
                
                # Set the corresponding indices in 'clusimg' to 1 for the current clusters
                clusimg.flat[out_ids] = 1
                
                # Update the gradient map with the maximum value between the current map and the new clusters
                gradmap = np.maximum(gradmap, (clusimg > 0) * g)
                
                # Reset the cluster image to zeros for the next iteration
                clusimg.flat[out_ids] = 0


          # After gamma loop
        current_progress = HOMMEL_STEPS + HALPHA_STEPS + ADJLIST_STEPS + CLUSTERS_STEPS + TDP_STEPS + QUERY_PREP_STEPS + GAMMA_STEPS
        
        # Local minima step
        progress.setLabelText("Computing local minima...")
        progress.setValue(current_progress)


        # Create a Nifti1Image object. We use the transpose affine because that is where the image processing left off
        # gradmap_img = nib.Nifti1Image(gradmap, affine=self.fileInfo[file_nr]['transposed_affine'] )
        gradmap = gradmap.T
        # gradmap_image will define the first overlay image. Because this will be aligned with the template
        # we transpose it back to the original. 
        gradmap_img = nib.Nifti1Image(gradmap, affine=self.fileInfo[file_nr]['affine'] )

        # Using the property funciton defined below we can drop the brain_nav chaining
        self.fileInfo[file_nr].update({
            'pval': pval,
            'p': p,
            'ordp': ordp,
            'm': m,
            'marks': marks,
            'mintdp': mintdp,
            'indexp': indexp,
            'indexp_linear': indexp_linear,
            'reslist': reslist,
            'tdps': tdps,
            'stcs': stcs,
            'conc_thres': conc_thres,
            'tr_volDim': volDim,
            'grad_map': gradmap
        })

        # self.fileInfo[file_nr]['grad_map_image']  = gradmap_img

        # Get min and max z-score depending on data type. Min and max
        # are used to define the range of the whole brain threshold slider in the UI
        # Step 1: Compute z-scores
        z_001 = round(-norm.ppf(0.001), 2)
        z_conc = round(-norm.ppf(conc_thres), 2)

        # Step 2: Minimum Z-score
        zmin = min(z_001, z_conc)

        # Step 3: Maximum Z-score, depending on data type
        mask_data = self.fileInfo[file_nr]['mask']
        if self.fileInfo[file_nr]['type'] == "p":
            # For p-values: find minimum p-value within mask and convert to Z
            masked_pvals = self.fileInfo[file_nr]['data'][mask_data  != 0]
            z_max = round(-norm.ppf(np.min(masked_pvals)), 2)

        elif self.fileInfo[file_nr]['type'] == "z":
            # For z-scores: find max z-score within mask
            masked_zscores = self.fileInfo[file_nr]['data'][mask_data  != 0]
            z_max = round(np.max(masked_zscores), 2)

        # Optionally, if we want to store or log this, 
        self.fileInfo[file_nr]['zmin'] = zmin
        self.fileInfo[file_nr]['zmax'] = z_max

        # ==== Local Minima ====
        progress.setLabelText("Computing local minima...")
        progress.setValue(current_progress + 5)


        # Precompute the IDs of local minima (leaves of the tree) based on the CHILD structure.
        LM_ids = ARI_C.py_findLMS(self.fileInfo[file_nr]['reslist']['CHILD'])

        # Map local minima IDs (LM_ids) to their corresponding voxel indices using the linear indexing system.
        LM_voxel_indices = [self.fileInfo[file_nr]['indexp_linear'][lm] for lm in LM_ids]

        # Convert voxel indices to their corresponding XYZ coordinates in the brain image.
        LM_xyz = ARI_C.py_ids2xyz(LM_voxel_indices, list(dim))
        # LM_xyz = get_adjList.py_ids2xyz(LM_voxel_indices, list(dim))
        # LM_xyz = ARI_C.py_ids2xyz(LM_voxel_indices, list(self.fileInfo[file_nr]['original_data_dimensions']))

        # Store the calculated local minima IDs, their coordinates, and a DataFrame for easy indexing.
        self.fileInfo[file_nr]['stable_LM_ids'] = LM_ids
        self.fileInfo[file_nr]['stable_LM_xyz'] = LM_xyz
        self.fileInfo[file_nr]['stable_LM_ids_df'] = pd.DataFrame({'lm_id': self.fileInfo[file_nr]['stable_LM_ids']})

        # Create a mapping from local minima IDs (LM_ids) to their XYZ coordinates.
        self.fileInfo[file_nr]['voxel_to_LM'] = {
            lm_id: tuple(coord) for lm_id, coord in zip(LM_ids, LM_xyz)
        }

        # Create a count mapping for each LM_id, used to generate unique cluster IDs.
        LM_ids_count = {lm_id: idx + 1 for idx, lm_id in enumerate(sorted(LM_ids))}

        # Store the mapping in the brain navigation file information.
        self.fileInfo[file_nr]['stable_LM_ids_count'] = LM_ids_count

        # Create a stable lookup table (LUT) for all clusters with preassigned colors. This is used
        # for visualizing clusters in the brain map. The LUT is created once and dynamically updated
        # during visualization with transparency (alpha) adjustments.
        custom_lut = OrthViewSetup.create_stable_lut(self, alpha=0.5)

        # Store the custom LUT in the file information for later use.
        self.fileInfo[file_nr]['custom_lut'] = custom_lut

        current_progress += LM_STEPS

        # ====================
        progress.setLabelText("Aligning maps to templates...")
        progress.setValue(current_progress)

        
        # Handle ARI output
        # overlay_image = self.fileInfo[file_nr]['grad_map_image']
        overlay_image = gradmap_img

        file_nr_template = self.brain_nav.file_nr_template
        
        template_count = len(self.brain_nav.templates)
        for idx, template in enumerate(self.brain_nav.templates):
            if idx > 0:  # Skip first update which we already did
                template_progress = int((idx / template_count) * TEMPLATE_STEPS)
                progress.setValue(current_progress + template_progress)
                progress.setLabelText(f"Processing template {idx+1}/{template_count}")
            
            # make sure there is space to the template and stamap info
            if (file_nr, template) not in self.brain_nav.aligned_templateInfo:
                self.brain_nav.aligned_templateInfo[(file_nr, template)] = {}
            if (file_nr, template) not in self.brain_nav.aligned_statMapInfo:
                self.brain_nav.aligned_statMapInfo[(file_nr, template)] = {}
            # if (file_nr) not in self.brain_nav.statmaps:
            #     self.brain_nav.statmaps[file_nr] = {}

            # subID = file_nr if file_nr_template == self.brain_nav.data_bg_index else 0
            template_image = self.brain_nav.templates[template]['image']

            # Align the overlay image with the background image
            a_overlay_image, transform_affine = ImageProcessing.align_images(template_image, overlay_image, order = 0)

            tr_template_image = ImageProcessing.transpose_image(template_image)
            tra_overlay_image = ImageProcessing.transpose_image(a_overlay_image)

            # rotate the same as the bg image
            _, rtra_overlay_image, _                    = ImageProcessing.rotate_volume(tra_overlay_image)
            _, rtr_template_image, rtr_template_affine  = ImageProcessing.rotate_volume(tr_template_image)

            r_aligned_overlay_data =  rtra_overlay_image.get_fdata()

            """
            The following operation constructs a mapping between the transformed voxel space and 
            the original voxel indices of the brain image, ensuring proper alignment 
            after applying transformations such as rotation and spatial normalization.

            ### **Overview**
            1. **Create an Index Matrix:** 
            - Generates a 3D array where each voxel is assigned a unique index.
            - This serves as a reference grid to track voxel correspondences through transformations.

            2. **Apply Image Transformations:**
            - Converts the index matrix into a NIfTI image with the same affine transformation as the overlay image.
            - Rotates and aligns the index image to match the transformed brain image.

            3. **Extract Valid Voxel Mappings:**
            - Identifies non-zero (or non-NaN) voxel indices in the transformed space.
            - Retrieves corresponding original voxel indices.

            4. **Compute Original Coordinates:**
            - Uses `np.unravel_index` to derive the original voxel (X, Y, Z) coordinates from the 1D index.
            - Computes coordinates in both C-order (`order='C'`) and Fortran-order (`order='F'`).
            - This ensures compatibility across different data ordering conventions.

            5. **Store Mappings for Later Use:**
            - Saves the aligned index data and coordinate mappings in `brain_nav.fileInfo[file_nr]`.
            - Enables efficient retrieval of original voxel locations after transformations.

            ### **Purpose**
            This process ensures that voxel-based analyses (e.g., statistical overlays, region extractions) 
            are correctly mapped to their original positions, preventing misalignment issues 
            after spatial transformations.
            """
            # Set the matrix dimensions based on the aligned index data
            # oldDim = dim
            oldDim = volDim # We use the transposed dimensions because that's what the cluster image is based on
            
            # Step 1: Create the index image
            index_matrix = np.arange(1, np.prod(oldDim) + 1).reshape(oldDim)
            # Transpose to original dimensions before alignment with background, for conistency we do this explicitly. This is 
            # now the same as the data orientation that goes into the cpp routines. 
            index_matrix = index_matrix.T
            index_image = nib.Nifti1Image(index_matrix, affine=overlay_image.affine, header=overlay_image.header)

            # Step 2: Align the index image to the template
            a_index_image, _ = ImageProcessing.align_images(template_image, index_image, order=0)

            # Step 3: Transpose the aligned index image
            tra_index_image = ImageProcessing.transpose_image(a_index_image)

            # Step 4: Rotate the transposed aligned image
            _, rtra_index_image, _ = ImageProcessing.rotate_volume(tra_index_image)

            # Step 5: Extract the final data
            aligned_index_data = rtra_index_image.get_fdata()

            # Mapping Matrices
            # The mapped coordinate matrices store the *original voxel coordinates* (before transformation)
            # for each position in the final transformed space. They allow reverse mapping:
            # given a coordinate in the transformed space (after alignment, transpose, and rotation),
            # you can retrieve the corresponding coordinate in the original image.
            # 
            # Two versions are computed:
            # - mapped_coordinate_matrix_C uses 'C' order (row-major, x-fastest)
            # - mapped_coordinate_matrix_F uses 'F' order (column-major, z-fastest, common in NIfTI)

            # •	Use 'C' if you’re mapping between UI/display space and transformed voxel data (after transpose/rotate).
	        # •	Use 'F' if you’re mapping between unaltered original images or need to compare to reference brain atlases/NIfTI headers.

            # These matrices are useful for tracking how each voxel was displaced
            # and for mapping results (e.g. cluster labels) back into original data space. They are used extensivley 
            # to take ui space coordinates (transformed space) and retrieve the cluster ID, statistics etc in the
            # maps computed by our cpp routine.

            # matdim = self.fileInfo[file_nr]['original_data_dimensions'] # Use the original data dimensions
            newDim = aligned_index_data.shape

            # Identify all non-zero indices in the transformed space
            # non_zero_mask = aligned_index_data != 0
            non_zero_mask       = ~np.isnan(aligned_index_data) & (aligned_index_data != 0)
            non_zero_indices    = np.where(non_zero_mask != 0)

            # Extract valid original indices from the transformed data
            valid_orig_indices = aligned_index_data[non_zero_indices]
            # Convert valid_orig_indices to integer type
            valid_orig_indices = valid_orig_indices.astype(np.int64)

            # Compute zero-based original coordinates using unravel_index (all at once for each order)
            orig_coords_C = np.array(np.unravel_index(valid_orig_indices - 1, oldDim, order='C')).T
            orig_coords_F = np.array(np.unravel_index(valid_orig_indices - 1, oldDim, order='F')).T

            mapped_coordinate_matrix_C = np.zeros((*newDim, 3), dtype=np.int32)
            mapped_coordinate_matrix_F = np.zeros((*newDim, 3), dtype=np.int32)

            # Map the computed original coordinates back to the transformed matrix positions
            mapped_coordinate_matrix_C[non_zero_indices] = orig_coords_C
            mapped_coordinate_matrix_F[non_zero_indices] = orig_coords_F

            # self.fileInfo[file_nr]['aligned_index_data'] = aligned_index_data
            # self.fileInfo[file_nr]['mapped_coordinate_matrix_C'] = mapped_coordinate_matrix_C
            # self.fileInfo[file_nr]['mapped_coordinate_matrix_F'] = mapped_coordinate_matrix_F

            # UI Space -> Data Space
            self.brain_nav.aligned_templateInfo[(file_nr, template)]['aligned_index_data'] = aligned_index_data
            self.brain_nav.aligned_templateInfo[(file_nr, template)]['mapped_coordinate_matrix_C'] = mapped_coordinate_matrix_C
            self.brain_nav.aligned_templateInfo[(file_nr, template)]['mapped_coordinate_matrix_F'] = mapped_coordinate_matrix_F

            # ---------------------- NEW: Create Reverse Mapping (Data Space -> UI Space) ---------------------- #

            # Initialize an inverse mapping matrix for the functional space
            inverse_mapped_matrix_C = np.full((*oldDim, 3), -1, dtype=np.int32)
            inverse_mapped_matrix_F = np.full((*oldDim, 3), -1, dtype=np.int32)

            # Fill inverse mapping where original coordinates exist
            inverse_mapped_matrix_C[orig_coords_C[:, 0], orig_coords_C[:, 1], orig_coords_C[:, 2]] = np.array(non_zero_indices).T
            inverse_mapped_matrix_F[orig_coords_F[:, 0], orig_coords_F[:, 1], orig_coords_F[:, 2]] = np.array(non_zero_indices).T
            
            # self.fileInfo[file_nr]['inverse_mapped_matrix_C'] = inverse_mapped_matrix_C
            # self.fileInfo[file_nr]['inverse_mapped_matrix_F'] = inverse_mapped_matrix_F
            
            self.brain_nav.aligned_statMapInfo[(file_nr, template)]['inverse_mapped_matrix_C'] = inverse_mapped_matrix_C
            self.brain_nav.aligned_statMapInfo[(file_nr, template)]['inverse_mapped_matrix_F'] = inverse_mapped_matrix_F
            # Add inverse mapping matrices to aligned_templateInfo



            data = rtr_template_image.get_fdata()
            self.brain_nav.axial_slice      = data.shape[ self.brain_nav.axial_dim ] // 2
            self.brain_nav.sagittal_slice   = data.shape[ self.brain_nav.sagittal_dim ] // 2
            self.brain_nav.coronal_slice    = data.shape[ self.brain_nav.coronal_dim ] // 2

            # if template == self.brain_nav.file_nr_template:
            #     data = rtr_template_image.get_fdata()
            #     self.brain_nav.axial_slice      = data.shape[ self.brain_nav.axial_dim ] // 2
            #     self.brain_nav.sagittal_slice   = data.shape[ self.brain_nav.sagittal_dim ] // 2
            #     self.brain_nav.coronal_slice    = data.shape[ self.brain_nav.coronal_dim ] // 2

            #     self.brain_nav.statmaps[file_nr]['overlay_data']            = r_aligned_overlay_data
            #     self.brain_nav.statmaps[file_nr]['gradmap_flag']            = True


            # Store relevant data for later use
            # self.fileInfo[file_nr]['transform_affine']        = transform_affine
            # self.fileInfo[file_nr]['r_template_image']        = rtr_template_image
            # self.fileInfo[file_nr]['r_template_image_hdr']    = rtr_template_image.header
            # self.fileInfo[file_nr]['rtr_tamplate_affine']     = rtr_tamplate_affine

            # self.brain_nav.statmaps[file_nr]['overlay_image_FP']        = self.fileInfo[file_nr]['full_path']
            # self.brain_nav.statmaps[file_nr]['overlay_data']            = r_aligned_overlay_data
            # self.brain_nav.statmaps[file_nr]['overlay_header']          = rtra_overlay_image.header
            # self.brain_nav.statmaps[file_nr]['gradmap_flag']            = True


            # We probably don't need the template entry, all images are brought into alignment with the templates so they do not change beyong transp
            # and rotation. But it's useful to precompute them once so we dont need to do it each time we update the orthview.
            self.brain_nav.aligned_templateInfo[(file_nr, template)]['transform_affine']        = transform_affine
            self.brain_nav.aligned_templateInfo[(file_nr, template)]['r_template_image']        = rtr_template_image
            self.brain_nav.aligned_templateInfo[(file_nr, template)]['r_template_image_hdr']    = rtr_template_image.header
            self.brain_nav.aligned_templateInfo[(file_nr, template)]['rtr_template_affine']     = rtr_template_affine

            # for each statmap we align to the different templates on start up. 
            self.brain_nav.aligned_statMapInfo[(file_nr, template)]['overlay_image_FP']        = self.fileInfo[file_nr]['full_path']
            self.brain_nav.aligned_statMapInfo[(file_nr, template)]['overlay_data']            = r_aligned_overlay_data
            self.brain_nav.aligned_statMapInfo[(file_nr, template)]['overlay_header']          = rtra_overlay_image.header
            self.brain_nav.aligned_statMapInfo[(file_nr, template)]['gradmap_flag']            = True

            # self.fileInfo[file_nr]['gradmap_flag']                                    = True

        current_progress += TEMPLATE_STEPS

        # Final update
        progress.setLabelText("Finalizing and updating views...")
        progress.setValue(current_progress)


        # # Display metrics and set up the viewer
        # Metrics.show_metrics(self.brain_nav)
        self.brain_nav.metrics.show_metrics()
        self.brain_nav.UIHelp.update_ui_xyz()

        # OrthViewSetup(self.brain_nav).setup_viewer(gradmap =self.brain_nav.statmaps[file_nr]['gradmap_flag'])
        OrthViewSetup(self.brain_nav).setup_viewer()
        
        # Update other UI related elements
        self.brain_nav.message_box.initiate_first_message()
        self.brain_nav.left_side_bar.update_ari_status(True)
        self.brain_nav.WBTing.update_tdp_bounds()  

        # Complete the progress
        progress.setValue(TOTAL_STEPS)

        # Filter out invalid TDP values (remove -1)
        # filtered_tdps = [tdp for tdp in tdps if tdp > 0]
        # min_tdp = mintdp

        # # These values are used to update the TDP labels in the UI
        # if filtered_tdps:  # Only update if data exists
        #     # min_tdp = min(filtered_tdps)
        #     max_tdp = max(filtered_tdps)
        #     mean_tdp = sum(filtered_tdps) / len(filtered_tdps)
        #     median_tdp = sorted(filtered_tdps)[len(filtered_tdps) // 2]

        #     # Update labels
        #     self.brain_nav.tdp_min_label.setText(f"Min: {min_tdp:.3f}")
        #     self.brain_nav.tdp_max_label.setText(f"Max: {max_tdp:.3f}")
        #     self.brain_nav.tdp_mean_label.setText(f"Mean: {mean_tdp:.3f}")
        #     self.brain_nav.tdp_median_label.setText(f"Median: {median_tdp:.3f}")

        # Update the histogram
        # self.brain_nav.histogram_canvas.update_histogram(filtered_tdps)

