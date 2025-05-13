
import numpy as np
import nibabel as nib
from scipy.ndimage import affine_transform, label
from nilearn import image, datasets
from nilearn.image import new_img_like

# import SimpleITK as sitk
# import fsl.data.image as fslimage
# import fsl.wrappers as fslwrap

from error_handling.ErrorHandler import ErrorHandler  # Import ErrorHandler
# import logging
# logging.basicConfig(filename='alignment_debug.log', level=logging.DEBUG, format='%(asctime)s %(message)s')



class ImageProcessing:
    def __init__(self, BrainNav):
        
        self.brain_nav = BrainNav

    @staticmethod
    def rotate_volume(image, image_type=None):
        """
        Rotates a NIfTI image by 90 degrees in the sagittal plane (X ↔ Z swap),
        then applies a 180-degree flip along the axial slice (Y-axis flip)
        to align UI with brain orientation, and finally corrects the left–right inversion.
        
        Parameters:
        - image: A NIfTI image (nib.Nifti1Image)
        
        Returns:
        - data: Rotated and left–right corrected voxel data (numpy array)
        - rotated_image: A new NIfTI image with the updated affine
        - final_affine: The final updated affine transformation matrix
        """
        # -------------------------
        # Step A: Define transforms
        # -------------------------
        # 1) 90-degree rotation around y (x↔z swap).
        rotation_matrix_90 = np.array([
            [0, 0, 1],  # new x = old z
            [0, 1, 0],  # new y = old y
            [1, 0, 0],  # new z = old x
        ])
        
        # 2) Flip along y-axis (to get correct axial orientation)
        flip_y_matrix_4x4 = np.eye(4)
        flip_y_matrix_4x4[1, 1] = -1

        # data = image.get_fdata()
        # affine = image.affine.copy()

        # print("Affine before rotation:\n", affine)
        # print("Orientation before rotation:", nib.aff2axcodes(affine))

        # 3) Define a left–right flip (for later correction).
        # flip_lr_matrix_4x4 = np.eye(4)
        # flip_lr_matrix_4x4[0, 0] = -1

        # ---------------------------
        # Step B: Apply to the data
        # ---------------------------
        data = image.get_fdata()
        affine = image.affine.copy()
        
        # 1) Rotate data array 90° in (x,z) plane.
        #    (This swaps axis 0 and 2.)
        data = np.rot90(data, k=1, axes=(2, 0))
        rotated_shape = data.shape

        # 2) Flip data along y-axis.
        data = np.flip(data, axis=1)
        # (rotated_shape remains the same after a flip)

        # -----------------------------------------
        # Step C: Build the combined affine for rotation + y-flip
        # -----------------------------------------
        # Apply the 90° rotation to the original affine.
        rotated_affine = affine.copy()
        rotated_affine[:3, :3] = rotation_matrix_90 @ affine[:3, :3]
        
        # Then apply the y-axis flip.
        combined_affine = flip_y_matrix_4x4 @ rotated_affine

        # ------------------------------------------
        # Step D: Compute correct translation shift for rotation+y-flip
        # ------------------------------------------
        # Compute the center of the original image in voxel space.
        orig_shape = image.shape
        orig_center_voxel = (np.array(orig_shape) - 1) / 2
        orig_center_world = affine[:3, :3] @ orig_center_voxel + affine[:3, 3]
        
        # Compute the new center after rotation.
        center_after_rotation = rotation_matrix_90 @ orig_center_voxel
        # Then after y-flip: flip the y coordinate
        center_after_flip = center_after_rotation.copy()
        center_after_flip[1] = (rotated_shape[1] - 1) - center_after_flip[1]
        
        # Map that voxel center to world coordinates using the combined_affine.
        new_center_world = combined_affine[:3, :3] @ center_after_flip + combined_affine[:3, 3]
        
        # Determine the translation shift needed.
        translation_shift = orig_center_world - new_center_world
        # print("Translation shift (rotate+flip):", translation_shift)

        combined_affine[:3, 3] += translation_shift
        # print("Final affine after rotation+flip:\n", combined_affine)
        # print("Orientation after rotation+flip:", nib.aff2axcodes(combined_affine))

        # --------------------------
        # Step E: Build intermediate NIfTI image
        # --------------------------
        data = np.ascontiguousarray(data)
        intermediate_image = nib.Nifti1Image(data, combined_affine, header=image.header)
        intermediate_image.set_sform(combined_affine)
        intermediate_image.set_qform(combined_affine)

        # # --------------------------
        # # Step F: Correct left–right inversion
        # # --------------------------
        # # Flip the data along the left–right axis.
        # # (Assume that in the current data, axis 0 corresponds to left–right.)
        # data = np.flip(data, axis=0)
        
        # # Update the affine by applying the left–right flip.
        # # Note: Multiplying the current affine by flip_lr_matrix_4x4 updates the rotation part.
        # corrected_affine = flip_lr_matrix_4x4 @ combined_affine

        # # Adjust the translation so that the center remains unchanged.
        # # Compute the center of the current (flipped) data in voxel space.
        # new_data_shape = data.shape
        # center_voxel_final = (np.array(new_data_shape)-1) / 2
        # # Current center in world coordinates (after left–right flip).
        # center_world_final = corrected_affine[:3, :3] @ center_voxel_final + corrected_affine[:3, 3]
        # # We want to preserve the original center (from before this left–right flip).
        # # Here, we use the orig_center_world computed in Step D.
        # lr_translation_correction = orig_center_world - center_world_final
        # corrected_affine[:3, 3] += lr_translation_correction

        # --------------------------
        # Step G: Build final NIfTI image
        # --------------------------
        # data = np.ascontiguousarray(data)
        # rotated_image = nib.Nifti1Image(data, corrected_affine, header=image.header)
        # rotated_image.set_sform(corrected_affine)
        # rotated_image.set_qform(corrected_affine)

        # Debug info (optional)
        # print("Before rotation (affine):\n", image.affine)
        # print("After rotation+y-flip (affine):\n", combined_affine)
        # print("Final corrected affine:\n", corrected_affine)
        # print("Orientation before rotation:", nib.aff2axcodes(image.affine))
        # print("Orientation after correction:", nib.aff2axcodes(rotated_image.affine))

        # return data, rotated_image, corrected_affine
        return data, intermediate_image, combined_affine

    @staticmethod
    def align_images(bg_image, overlay_image, overlay_affine=None, order = 1):
        """
        Aligns the overlay image to the background image using affine transformations based on header information.

        This method extracts the affine matrices from the headers of the background and overlay images, computes the 
        transformation matrix needed to align the overlay image to the background image, and applies this transformation
        to the overlay image data. The result is a new image that is aligned with the background image in terms of 
        spatial orientation and voxel correspondence.

        Important! The img_clus that goes in here needs to be set the the dimensions 
        of the raw image data upon loading. The reason is that this is required to get 
        proper alignment (or at leas the best possible). If you get misalignments this 
        can either be realted to the origins not set to the same anatomical location (e.g. AC)
        or a mismatch in data structure.

        Justification:
        - Direct use of affine matrices from image headers ensures that the spatial relationship between the images 
          is preserved without relying on image intensity-based registration, which can fail if the overlay image has 
          been smoothed or has low contrast.
        - This method leverages the inherent spatial metadata in the NIfTI headers, providing a robust initial alignment 
          step that can be refined if needed.

        Parameters:
        bg_image (nib.Nifti1Image): The background image (reference image) to which the overlay image will be aligned.
        overlay_image (nib.Nifti1Image): The overlay image (moving image) that will be aligned to the background image.

        Returns:
        nib.Nifti1Image: A new NIfTI image with the overlay data aligned to the background image space.
        """

        if overlay_affine is None:
            if isinstance(overlay_image, nib.Nifti1Image):
                # If overlay_image is a nibabel image object
                func_data = overlay_image.get_fdata()
                func_affine = overlay_image.affine
            else:
                raise ValueError("When overlay_affine is None, overlay_image must be a nibabel image object.")
        else:
            if isinstance(overlay_image, np.ndarray) and overlay_image.ndim == 3:
                # If overlay_image is a 3D image array (numpy array with 3 dimensions)
                func_data = overlay_image
                func_affine = overlay_affine
            else:
                raise ValueError("When overlay_affine is provided, overlay_image must be a 3D numpy array.")        

        template_affine = bg_image.affine

        # Compute the transformation matrix to align the functional image to the template
        # 1. Affine Matrices in NIfTI Images:
        #    NIfTI images have affine matrices that define the spatial relationship between voxel coordinates 
        #    (i.e., the grid of points that make up the image) and real-world coordinates 
        #    (e.g., in millimeters relative to some origin).
        # 2. Purpose of the Transformation:
        #    The goal is to align the overlay image (functional image) with the background image (template). 
        #    This involves finding a transformation that maps the voxel coordinates of the overlay image 
        #    into the voxel coordinates of the background image.
        # 3. Inverse Affine Matrix (func_affine_inv):
        #    The inverse of the affine matrix from the overlay image (func_affine_inv = np.linalg.inv(func_affine)) 
        #    transforms coordinates from the overlay image space back to a standard coordinate system 
        #    (usually the scanner’s coordinate system or a reference space).
        # 4. Affine Matrix of the Background Image (template_affine):
        #    The affine matrix from the background image (template_affine) transforms coordinates from the standard 
        #    coordinate system to the background image space.
        # 5. Combining Transformations:
        #    The line transform_affine = func_affine_inv @ template_affine combines these two transformations:
        #    - func_affine_inv transforms coordinates from the overlay image space to the standard coordinate system.
        #    - template_affine then transforms these coordinates from the standard coordinate system to the background image space.
        #    - The @ operator represents matrix multiplication, so the combined transformation matrix (transform_affine) 
        #      directly maps coordinates from the overlay image space to the background image space.
         # Calculate the origin (real-world coordinates) for both images
        origin_bg = template_affine[:3, 3]
        origin_overlay = func_affine[:3, 3]

        origin_diff = origin_bg - origin_overlay

        # Extract the rotation/scaling matrix
        rotation_scaling_matrix = func_affine[:3, :3]

        # Compute the voxel space offset
        voxel_offset = np.linalg.inv(rotation_scaling_matrix) @ origin_diff #
        # voxel_offset =  [-4, -4, -4]

        # Compute the inverse of the overlay affine
        func_affine_inv = np.linalg.inv(func_affine)

        # Compute the transformation matrix to align the overlay image to the template
        transform_affine = func_affine_inv @ template_affine

        # matrix = transform_affine[:3, :3]
        # offset = transform_affine[:3, 3]

        # Ensure the output shape matches the template image
        output_shape = bg_image.shape

        # Apply affine transform with the correct output shape and interpolation order
        # transformed_data = affine_transform(func_data, transform_affine[:3, :3], offset=transform_affine[:3, 3], output_shape=output_shape, order=1)
        # transformed_data = affine_transform(func_data, transform_affine[:3, :3], offset=voxel_offset, output_shape=output_shape, order=order)

        transformed_data = affine_transform(func_data, transform_affine[:3, :3], offset=voxel_offset, output_shape=output_shape, order=0)
       
        # transformed_data = affine_transform(
        #                         func_data,
        #                         matrix=matrix,
        #                         offset=offset,
        #                         output_shape=bg_image.shape,
        #                         order=0  # or 0
        #                     )
        # Ensure the data is C-contiguous
        transformed_data = np.ascontiguousarray(transformed_data)

        # Create a new NIfTI image with the transformed data and the template affine
        aligned_img = nib.Nifti1Image(transformed_data, template_affine, header=bg_image.header)

        return aligned_img, transform_affine
        

    @staticmethod
    def transpose_image(image, affine = None):
        """
        Transposes the image data and updates the affine matrix correctly.
        Ensures alignment in real-world space.
        """
        if affine is None:
            original_affine = image.affine.copy()
        else:
            original_affine = affine

        # print("Original affine:\n", original_affine)
        # print("Original orientation:", nib.aff2axcodes(original_affine)) 
        
        # Extract original affine and data
        original_affine = image.affine.copy()
        data = image.get_fdata().T  # Transpose that we need for cpp ordering

        data = np.ascontiguousarray(data) # Ensure data is C-contiguous

        # Correct the affine rotation
        transposed_affine = original_affine.copy()
        transposed_affine[:3, :] = original_affine[[2, 1, 0], :]  # Swap X ↔ Z
        # print("Transposed affine (before shift):\n", transposed_affine)
        # print("Orientation after transpose:", nib.aff2axcodes(transposed_affine))

        # Compute voxel center before transpose
        shape = image.shape
        center_voxel = (np.array(shape)-1) / 2  

        # Convert center voxel to world coordinates (before transpose)
        orig_center_world = original_affine[:3, :3] @ center_voxel + original_affine[:3, 3]

        # Apply voxel swap to get new center
        transposed_center_voxel = center_voxel[[2, 1, 0]]  # Swap X ↔ Z

        # Convert new center voxel back to world coordinates
        new_center_world = transposed_affine[:3, :3] @ transposed_center_voxel + transposed_affine[:3, 3]

        # Compute translation shift
        translation_shift = orig_center_world - new_center_world
        # print("Translation shift (transpose):", translation_shift)

        # Apply translation shift
        transposed_affine[:3, 3] += translation_shift
        # print("Transposed affine (after shift):\n", transposed_affine)

        data = np.ascontiguousarray(data) # Ensure data is C-contiguous

        # Create the new transposed NIfTI image
        transposed_image = nib.Nifti1Image(data, affine=transposed_affine, header=image.header)

        # Update the sform and qform in the header to match the new affine
        transposed_image.set_sform(transposed_affine)
        transposed_image.set_qform(transposed_affine)

        return transposed_image

    # @staticmethod
    # def reorient_to_ras(BrainNav):
    #     # error_handler = ErrorHandler(log_file='image_processing_errors.log')  # Create an instance of ErrorHandler

    #     # try:
    #     #     ornt = nib.io_orientation(BrainNav.image.affine)
    #     #     ras_ornt = nib.orientations.axcodes2ornt(('R', 'A', 'S'))
    #     #     transform = nib.orientations.ornt_transform(ornt, ras_ornt)
    #     #     BrainNav.data = nib.orientations.apply_orientation(BrainNav.data, transform)
    #     # except Exception as e:
    #     #     error_handler.handle_exception(e)  # Handle exceptions during reorientation
    #     canonical_image = nib.as_closest_canonical(BrainNav.image)

    #     return canonical_image
    


        # @staticmethod
        # def coregister_images(bg_image, overlay_image, overlay_affine=None, order=1):
        #     """
        #     Aligns the overlay image to the background image using an intensity-based affine
        #     registration via DIPY.

        #     This method reads the background (reference) image and the overlay (moving) image,
        #     then performs a stepwise affine registration (translation, rigid, then affine) using
        #     mutual information as the cost function. The final transform is applied to the overlay
        #     data to produce an aligned image in the background's space.

        #     Parameters
        #     ----------
        #     bg_image : nib.Nifti1Image
        #         The background (reference) image.
        #     overlay_image : nib.Nifti1Image or np.ndarray
        #         The overlay (moving) image. If passing a NumPy array, you must provide
        #         `overlay_affine`.
        #     overlay_affine : np.ndarray, optional
        #         Affine for the overlay if `overlay_image` is a NumPy array. Ignored if
        #         `overlay_image` is a NIfTI image.
        #     order : int, optional
        #         Interpolation order. 0 for nearest neighbor, >=1 for linear in this example.

        #     Returns
        #     -------
        #     aligned_img : nib.Nifti1Image
        #         A new NIfTI image with the overlay data registered and resampled into the
        #         background's space.
        #     final_affine : np.ndarray
        #         The 4x4 affine matrix that maps the overlay image into the background space.
        #     """
        #     import nibabel as nib
        #     import numpy as np
        #     # Import DIPY registration components.
        #     from dipy.align.imaffine import AffineRegistration, MutualInformationMetric
        #     from dipy.align.transforms import TranslationTransform3D, RigidTransform3D, AffineTransform3D
        #     # Optionally import reslice if voxel sizes need matching.
        #     from dipy.align.reslice import reslice

        #     # -----------------------------
        #     # 1) Extract overlay data/affine
        #     # -----------------------------
        #     if overlay_affine is None:
        #         if isinstance(overlay_image, nib.Nifti1Image):
        #             func_data = overlay_image.get_fdata()
        #             func_affine = overlay_image.affine
        #         else:
        #             raise ValueError("When overlay_affine is None, overlay_image must be a NIfTI image object.")
        #     else:
        #         if isinstance(overlay_image, np.ndarray) and overlay_image.ndim == 3:
        #             func_data = overlay_image
        #             func_affine = overlay_affine
        #         else:
        #             raise ValueError("When overlay_affine is provided, overlay_image must be a 3D numpy array.")

        #     # -------------------------------------------
        #     # 2) Load background data and extract its affine
        #     # -------------------------------------------
        #     bg_data = bg_image.get_fdata()
        #     bg_affine = bg_image.affine

        #     # (Optional) If the voxel sizes differ, reslice the overlay to match the background.
        #     overlay_zooms = overlay_image.header.get_zooms()[:3] if isinstance(overlay_image, nib.Nifti1Image) else (1, 1, 1)
        #     bg_zooms = bg_image.header.get_zooms()[:3]
        #     if overlay_zooms != bg_zooms:
        #         func_data, func_affine = reslice(func_data, func_affine, overlay_zooms, bg_zooms)

        #     # --------------------------------------
        #     # 3) Set up the DIPY registration pipeline.
        #     # --------------------------------------
        #     metric = MutualInformationMetric(nbins=32)
        #     level_iters = [10000, 1000, 100]  # Multi-resolution iterations.
        #     affreg = AffineRegistration(metric=metric, level_iters=level_iters)

        #     # --------------------------------------
        #     # 4) Perform stepwise registration:
        #     #     (a) Translation, (b) Rigid, (c) Full Affine.
        #     # We update the moving image's grid-to-world affine at each step.
        #     # --------------------------------------

        #     # (a) Translation registration
        #     translation = affreg.optimize(
        #         static=bg_data,
        #         moving=func_data,
        #         transform=TranslationTransform3D(),
        #         params0=None,
        #         static_grid2world=bg_affine,
        #         moving_grid2world=func_affine
        #     )
        #     # Update the moving affine by chaining: new_moving_affine = translation.affine @ func_affine
        #     new_moving_affine = translation.affine @ func_affine

        #     # (b) Rigid registration
        #     rigid = affreg.optimize(
        #         static=bg_data,
        #         moving=func_data,
        #         transform=RigidTransform3D(),
        #         params0=None,
        #         static_grid2world=bg_affine,
        #         moving_grid2world=new_moving_affine
        #     )
        #     # Update the moving affine further:
        #     new_moving_affine = rigid.affine @ new_moving_affine

        #     # (c) Full affine registration
        #     affine_map = affreg.optimize(
        #         static=bg_data,
        #         moving=func_data,
        #         transform=AffineTransform3D(),
        #         params0=None,
        #         static_grid2world=bg_affine,
        #         moving_grid2world=new_moving_affine
        #     )
        #     # The final mapping is given by affine_map.affine.
            
        #     # --------------------------------------
        #     # 5) Resample the overlay into the background space.
        #     # --------------------------------------
        #     interp = 'nearest' if order == 0 else 'linear'
        #     aligned_data = affine_map.transform(func_data, interpolation=interp)

        #     # --------------------------------------
        #     # 6) Create the aligned NIfTI image.
        #     # --------------------------------------
        #     aligned_img = nib.Nifti1Image(aligned_data, bg_affine, header=bg_image.header)
        #     final_affine = affine_map.affine  # 4x4 mapping from overlay to background

        #     return aligned_img, final_affine