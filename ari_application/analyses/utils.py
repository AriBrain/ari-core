import numpy as np
from scipy.stats import t, norm
from nilearn.masking import compute_epi_mask


class Utilities:
    def __init__(self, BrainNav):
        """
        Initialize the Utility class with a reference to the brain_nav instance.
        
        :param brain_nav: Instance of the BrainNav class containing the necessary data and parameters.
        """
        self.brain_nav = BrainNav
        # self.image = image
        # self.mask = mask

    def create_mask(self):
        """
        Create a binary mask based on a functional image using nilearn's compute_epi_mask function.

        Parameters:
        - func_img_path: str, path to the functional image (e.g., fMRI data).

        Returns:
        - mask_img: nibabel.Nifti1Image, the binary mask image.
        """
        # Load the functional image
        func_img = self.brain_nav.overlay_image_r

        # Compute the mask using nilearn's compute_epi_mask function
        mask_img = compute_epi_mask(func_img)

        # self.brain_nav.mask_r = mask_img

        return mask_img
    

    def getPVals(self):
        """
        Prepare data for ARI analysis by computing p-values from the given input parameters and data types.

        This method performs the following steps:
        1. Check and set input parameters related to the Simes method, connectivity, and significance level.
        2. Compute p-values based on the type of input data (p-values, t-values, or z-scores).
        3. Handle both two-sided and one-sided statistical tests.
        4. Clip p-values to ensure they lie within the range [0, 1].
        5. Extract indices of voxels within the mask.
        6. Extract p-values for voxels within the mask and compute the size of the multiple testing problem.

        :return: A tuple containing the extracted p-values and the size of the multiple testing problem.
        """
        file_nr = self.brain_nav.file_nr

        # Create a mask from the functional image (create mask is not reliable.. find another way)
        # mask_img = self.create_mask()
        # mask_data = mask_img.get_fdata().astype(bool)
        mask_data = self.brain_nav.fileInfo[file_nr]['mask'].T
        mask_data  = np.ascontiguousarray(mask_data)

        # Check input parameter types
        if self.brain_nav.input['simes'] == "Simes":
            simes = True
        else:
            simes = False
        
        # conn = int(self.brain_nav.input['conn'])  # Convert connectivity input to integer
        # alpha = float(self.brain_nav.input['alpha'])  # Convert alpha input to float

        # Initialize p-values from the data
        # pval = self.brain_nav.fileInfo['data']
        # pval = self.brain_nav.overlay_image_orig.get_fdata()
        pval  = self.brain_nav.fileInfo[file_nr]['data'].T
        pval = np.ascontiguousarray(pval)
        # Check if the test is two-sided
        if self.brain_nav.input['twosidedTest'] == True:  # Two-sided test
            
            # Handle case where the input data is already p-values
            if self.brain_nav.fileInfo[file_nr]['type'] == "p":
                pval[mask_data  == 0] = 1  # Set p-values to 1 for voxels outside the mask
                if self.brain_nav.input['twosidedTest'] == False:
                    pval = 2 * pval  # Convert to two-sided p-values if needed

            # Handle case where the input data is t-values
            elif self.brain_nav.fileInfo[file_nr]['type'] == "t":
                pval[mask_data == 0] = 0  # Set t-values to 0 for voxels outside the mask
                if self.brain_nav.input['tdf'] > 0:
                    pval = 2 * t.cdf(-np.abs(pval), df=self.brain_nav.input['tdf'])  # Convert t-values to two-sided p-values
                elif self.brain_nav.input['tdf'] == 0:
                    pval = 2 * norm.cdf(-np.abs(pval))  # Use normal distribution if degrees of freedom is 0

            # Handle case where the input data is z-scores
            elif self.brain_nav.fileInfo[file_nr]['type'] == "z":
                pval[mask_data == 0] = 0  # Set z-scores to 0 for voxels outside the mask
                pval = 2 * norm.cdf(-np.abs(pval))  # Convert z-scores to two-sided p-values
        
        else:  # One-sided test
            
            # Handle case where the input data is already p-values
            if self.brain_nav.fileInfo[file_nr]['type'] == "p":
                pval[mask_data == 0] = 1  # Set p-values to 1 for voxels outside the mask
                if self.brain_nav.input['twosided'] == True:
                    pval = pval / 2  # Convert to one-sided p-values if needed

            # Handle case where the input data is t-values
            elif self.brain_nav.fileInfo[file_nr]['type'] == "t":
                pval[mask_data == 0] = 0  # Set t-values to 0 for voxels outside the mask
                if self.brain_nav.input['tdf'] > 0:
                    pval = 1 - t.cdf(pval, df=self.brain_nav.input['tdf'])  # Convert t-values to one-sided p-values
                elif self.brain_nav.input['tdf'] == 0:
                    pval = 1 - norm.cdf(pval)  # Use normal distribution if degrees of freedom is 0

            # Handle case where the input data is z-scores
            elif self.brain_nav.fileInfo[file_nr]['type'] == "z":
                pval[mask_data == 0] = 0  # Set z-scores to 0 for voxels outside the mask
                pval = 1 - norm.cdf(pval)  # Convert z-scores to one-sided p-values
        
        # Clip p-values to ensure they are within the range [0, 1]
        pval = np.minimum(1, pval)
        pval = np.maximum(0, pval)
        
        # Get voxel indices of the mask in 3D space
        indexp = np.where(mask_data != 0)#[0]
        # indexp = mask_data != 0
        
        # Extract p-values of in-mask voxels
        p = pval[indexp]
        
        # Compute size of the multiple testing problem
        m = len(indexp[0])

        return p, pval, m, indexp
    