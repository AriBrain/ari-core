
import matplotlib.pyplot as plt
import numpy as np

class OrthViewSetup:
    def __init__(self, BrainNaV):
        """
        Initialize the OrthViewSetup with a reference to the BrainNav instance.

        :param brain_nav: Instance of the BrainNav class.
        """
        self.brain_nav = BrainNaV
      
    def setup_viewer(self, gradmap = False):
        template_data_shape = self.brain_nav.templates[self.brain_nav.file_nr_template]['data'].shape 
        # template_data_shape = self.brain_nav.aligned_templateInfo[(self.brain_nav.file_nr, self.brain_nav.file_nr_template)]['r_template_image'].get_fdata()  

        # Set the initial slice positions to the middle of the data volume
        self.brain_nav.axial_slice = template_data_shape[ self.brain_nav.axial_dim ] // 2 
        self.brain_nav.sagittal_slice =  template_data_shape[ self.brain_nav.sagittal_dim ] // 2 
        self.brain_nav.coronal_slice =  template_data_shape[ self.brain_nav.coronal_dim ] // 2 

        # Set the positions of the crosshairs in the axial view
        self.brain_nav.axial_crosshair_h.setPos(self.brain_nav.coronal_slice + 0.5)  # Horizontal crosshair
        self.brain_nav.axial_crosshair_v.setPos(self.brain_nav.sagittal_slice + 0.5)   # Vertical crosshair

        # Set the positions of the crosshairs in the sagittal view
        self.brain_nav.sagittal_crosshair_h.setPos(self.brain_nav.axial_slice + 0.5)  # Horizontal crosshair
        self.brain_nav.sagittal_crosshair_v.setPos(self.brain_nav.coronal_slice + 0.5) # Vertical crosshair

        # Set the positions of the crosshairs in the coronal view
        self.brain_nav.coronal_crosshair_h.setPos(self.brain_nav.axial_slice + 0.5)   # Horizontal crosshair
        self.brain_nav.coronal_crosshair_v.setPos(self.brain_nav.sagittal_slice + 0.5) # Vertical crosshair

        # Initialize the ranges for the views
        self.set_initial_ranges()

        # Update the slices to reflect the new positions and ranges
        self.brain_nav.orth_view_update.update_slices()

        # Render the 3d template brain (no clusters are present yet)
        self.brain_nav.threeDviewer.update_cluster_3d_view()

        # Update xyz boxes 
        self.brain_nav.UIHelp.update_ui_xyz()

    def set_initial_ranges(self):
        # Get the dimensions of the brain volume from the header
        file_nr_template = self.brain_nav.file_nr_template
        template_image = self.brain_nav.templates[file_nr_template]['image']
        template_data = self.brain_nav.templates[file_nr_template]['data']
        shape = template_image.header.get_data_shape()

        # Determine the order of dimensions based on memory layout
        if template_data.flags['F_CONTIGUOUS']:
            # C-order: (Z, Y, X) in memory layout
            dims = (shape[2], shape[1], shape[0])
            views = {
                'axial': (1, 2),   # X, Y
                'sagittal': (0, 2), # Z, X
                'coronal': (0, 1)  # Z, Y
            }
        elif template_data.flags['C_CONTIGUOUS']:
            # F-order: (X, Y, Z) in memory layout
            dims = (shape[0], shape[1], shape[2])
            views = {
                'axial': (0, 1),   # X, Y
                'sagittal': (1, 2), # X, Z
                'coronal': (0, 2)  # Y, Z
            }
        else:
            dims = (shape[0], shape[1], shape[2])
            views = {
                'axial': (0, 1),   # X, Y
                'sagittal': (1, 2), # X, Z
                'coronal': (0, 2)  # Y, Z
            }


        # # C-order: (Z, Y, X) in memory layout
        # dims = (shape[2], shape[1], shape[0])
        # views = {
        #     'axial': (1, 2),   # X, Y
        #     'sagittal': (0, 2), # Z, X
        #     'coronal': (0, 1)  # Z, Y
        # }

        # Calculate the center and margin for each dimension
        center_xyz = [dim / 2 for dim in dims]
        margin_xyz = [dim // 2 for dim in dims]

        # Set the initial display ranges for the brain navigation views (Axial, Sagittal, Coronal).
        # Each range is defined by subtracting and adding the margin (half the dimension) from the center
        # for the two relevant axes in each view. The views are determined based on the memory layout 
        # (C-contiguous or F-contiguous) as specified in the 'views' dictionary:
        self.brain_nav.ranges = np.array([

             # Axial view initial range
            [center_xyz[views['axial'][0]] - margin_xyz[views['axial'][0]], center_xyz[views['axial'][0]] + margin_xyz[views['axial'][0]],
            center_xyz[views['axial'][1]] - margin_xyz[views['axial'][1]], center_xyz[views['axial'][1]] + margin_xyz[views['axial'][1]]], 

            # Sagittal view initial range
            [center_xyz[views['sagittal'][0]] - margin_xyz[views['sagittal'][0]], center_xyz[views['sagittal'][0]] + margin_xyz[views['sagittal'][0]],
            center_xyz[views['sagittal'][1]] - margin_xyz[views['sagittal'][1]], center_xyz[views['sagittal'][1]] + margin_xyz[views['sagittal'][1]]],  

            # Coronal view initial range
            [center_xyz[views['coronal'][0]] - margin_xyz[views['coronal'][0]], center_xyz[views['coronal'][0]] + margin_xyz[views['coronal'][0]],
            center_xyz[views['coronal'][1]] - margin_xyz[views['coronal'][1]], center_xyz[views['coronal'][1]] + margin_xyz[views['coronal'][1]]],   

        ])
        
            # Apply these ranges to the views
        self.brain_nav.orth_view_update.set_ranges()


    def create_stable_lut(self, alpha=0.5):
        """
        Create a LUT (Lookup Table) for stable cluster IDs based on `stable_LM_ids_count`,
        ensuring maximized color distance for better visualization.
        
        :param alpha: Transparency level for cluster voxels (default is 0.5).
        :return: A custom LUT for stable clusters with maximized color distance.
        """
        file_nr = self.brain_nav.file_nr

        # Retrieve stable LM_ids_count and sort to maintain consistency
        stable_ids_count = self.brain_nav.fileInfo[file_nr]['stable_LM_ids_count']
        stable_ids = np.array(list(stable_ids_count.values()))

        # Total number of unique stable IDs
        num_ids = len(stable_ids)

        # Normalize IDs to a range of 0 to 1 for colormap mapping
        if num_ids > 1:
            normalized_ids = (stable_ids - stable_ids.min()) / (stable_ids.max() - stable_ids.min())
        else:
            normalized_ids = [0.5]  # Center the single cluster in the colormap

        # Create a rainbow colormap
        cmap = plt.get_cmap('rainbow', 256)

        # Map normalized IDs to colors
        colors = cmap(normalized_ids)

        # Shuffle colors for better separation, while ensuring reproducibility
        if num_ids > 1:
            np.random.seed(42)  # Ensure consistent randomization
            np.random.shuffle(colors)
        colors = (colors[:, :3] * 255).astype(np.uint8)  # Convert to 8-bit RGB

        # Initialize the LUT with an alpha channel
        custom_lut = np.zeros((num_ids, 4), dtype=np.uint8)  # +1 for background
        custom_lut[:, :3] = colors  # Assign RGB colors, skipping background
        custom_lut[:, 3] = int(alpha * 255)  # Set transparency for all entries

        return custom_lut