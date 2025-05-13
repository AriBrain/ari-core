import nibabel as nib
import numpy as np
# from scipy.ndimage import zoom
# from nilearn import image, plotting
# from nilearn.image import resample_to_img
from nilearn.masking import compute_epi_mask
from PyQt5.QtWidgets import QInputDialog, QMessageBox
from PyQt5.QtWidgets import QInputDialog, QMessageBox
import pyqtgraph as pg
import os
from ari_application.orth_views.orth_view_setup import OrthViewSetup
from ari_application.models.image_processing import ImageProcessing


from models.image_processing import ImageProcessing



class NiftiLoader:
    def __init__(self, BrainNaV):

        # Initialize the Metrics with a reference to the BrainNav instance.
        # :param brain_nav: Instance of the BrainNav class.
        self.brain_nav = BrainNaV

    def load_bg(self, file_path):
        # error_handler = ErrorHandler(log_file='nifti_loader_errors.log')  # Create an instance of ErrorHandler
        file_nr = self.brain_nav.file_nr
        # file_nr_template = self.brain_nav.file_nr_template
        
        # Retrieve the template directory 
        templates = self.brain_nav.templates

        # Set the dimensions for the data
        self.brain_nav.sagittal_dim = 0
        self.brain_nav.coronal_dim  = 1
        self.brain_nav.axial_dim    = 2

        try:
            # We always take all the .nii template files in the template_dir plus the uploaded data for backgrounds
            for file_nr_template, filename in enumerate(f for f in os.listdir(self.brain_nav.start_input['template_dir']) if f.endswith('.nii')):
                
                # Create the template dictionary if it doesnt exist. 
                if file_nr_template not in templates:
                    templates[file_nr_template] = {'image': None, 'data': None, 'original_bg_affine': None, 'filename': None, 'full_path': None,
                                                   'statMap': False}

                # Load the template image
                image_path  = os.path.join(self.brain_nav.start_input['template_dir'], filename)
                image       = nib.load(image_path)
                image       = nib.as_closest_canonical(image)
                data_out    = np.ascontiguousarray(image.get_fdata())

                # Set the loaded image and metadata in the BrainNav `templates` dictionary for later use
                templates[file_nr_template].update({
                    'filename': filename,  # Store just the filename (e.g. 'T1_template.nii.gz')
                    'full_path': os.path.join(self.brain_nav.start_input['template_dir'], filename),  # Full path for future access
                    'image': image,  # Store the NIfTI image object
                    'data': data_out,  # Store the image data as a NumPy array
                    'original_bg_affine': image.affine  # Keep the original affine matrix for correct spatial referencing
                })

                # Initate the data for the orth and 3d viewer based on inital seletion on start window.
                if filename == self.brain_nav.start_input['show_template']:
                    # Set the current template image and data
                    tmpdata = data_out
                    which_template = file_nr_template

                # load and align the atlas to the current template image
                self.load_atlases(image, file_nr_template)
                # self.brain_nav.atlasInfo[(file_nr, file_nr_template)] = self.load_atlases(image)
            
            # add one to the the file_nr_template to accommodate the uploaded data 
            file_nr_template += 1

            # Add the uploaded data to the list of templates
            fp =  self.brain_nav.start_input['data_dir']
            image = nib.load(fp)  # Load the NIfTI file
            image = nib.as_closest_canonical(image)
            data_out =  np.ascontiguousarray(image.get_fdata())

            # Initialize and set the statMap image and metadata in the BrainNav `templates` dictionary
            templates[file_nr_template] = {
                'filename': os.path.basename(fp),       # Just the file name (e.g., 'activation_map.nii.gz')
                'image': image,                         # The loaded NIfTI image object
                'data': data_out,                       # Image data as a NumPy array
                'original_bg_affine': image.affine,     # Original affine matrix for spatial reference
                'statMap': True                         # Flag this entry as a statMap overlay
            }

            # Initate the data for the orth and 3d viewer based on inital seletion on start window.
            # If user selected raw data as initial background we set it here.
            if self.brain_nav.start_input['show_template'] == 'raw_data':
                # Set the current template image and data
                tmpdata = data_out
                which_template = file_nr_template

            self.brain_nav.data_bg_index = file_nr_template
            self.brain_nav.statmap_templates[file_nr] = templates[file_nr_template]

            # load and align the atlas to the current template image
            # self.load_atlases(image, file_nr_template)
            self.load_atlases(image, ('data_as_template', file_nr))


            # Update the file_nr_template to match the selected intial template
            file_nr_template = which_template
            self.brain_nav.file_nr_template = file_nr_template

            # Here we load the template mask that goes with the MNI template T1 in the template dir. 
            # We use this later on to mask out the skull and other non-brain areas for the 3d viewer
            # Here we make sure that the template mask is in the same orientation as the template image.
            image_3d_viewer = nib.load(self.brain_nav.start_input['template_mask_fp'])
            image_3d_viewer             = nib.as_closest_canonical(image_3d_viewer)
            data_3d_viewer              = image_3d_viewer.get_fdata().T
            data_3d_viewer              = np.ascontiguousarray(data_3d_viewer)
            transposed_image_3d_viewer  = nib.Nifti1Image(data_3d_viewer, affine=image_3d_viewer.affine, header=image_3d_viewer.header)
            data_out_3d_viewer, _, _    = ImageProcessing.rotate_volume(transposed_image_3d_viewer, image_type = 'background')
            self.brain_nav.ui_params['3d_brain_data'] = data_out_3d_viewer


            if self.brain_nav.start_input['show_template'] == 'user_template':
                # here we will load the user defined template (selected on startup) and add it to the list as constructed above
                # this will need some work as we need to do quality and alignment test etc. 
                pass


            # define center slices for orthoview
            
            self.brain_nav.sagittal_slice   = tmpdata.shape[ self.brain_nav.sagittal_dim ] // 2
            self.brain_nav.coronal_slice    = tmpdata.shape[ self.brain_nav.coronal_dim ] // 2 
            self.brain_nav.axial_slice      = tmpdata.shape[ self.brain_nav.axial_dim ] // 2 

        
            # Display metrics and set up the viewer
            # Metrics.show_metrics(self.brain_nav)
            self.metrics.show_metrics()
            OrthViewSetup(self.brain_nav).setup_viewer()
        
        except Exception as e:
            # error_handler.handle_exception(e)  # Use ErrorHandler to handle the exception
            return None, None
        
    def load_data_as_bg(self, file_path):
        """
        Loads data as a background template with a composite key (file_nr, template_index).
        This allows associating templates with specific files for easy reference.
        
        Args:
            file_path (str): Path to the NIfTI file to load as background.
        
        Returns:
            tuple: The composite key (file_nr, template_index) for the loaded template
        """
        tmp_templates = {}

        # Get current file_nr 
        file_nr = self.brain_nav.file_nr
        statmap_index = self.brain_nav.data_bg_index
        
        # # Create a template index for this file
        # # Check if any templates exist for this file already
        # template_indices = [key[1] for key in self.brain_nav.templates.keys() 
        #                 if isinstance(key, tuple) and key[0] == file_snr]
        
        # template_index = max(template_indices) if template_indices else 0
        
        # Create composite key
        # composite_key = (statmap_index, file_nr)
        key = statmap_index
        
        try:
            # Load the image
            image = nib.load(file_path)
            image = nib.as_closest_canonical(image)
            data_out = np.ascontiguousarray(image.get_fdata())

            # swap the data template to the new one (we made a back up on load_bg to reinstate later)
            # templates[key] = {'image': None, 'data': None, 'original_bg_affine': None}      
            # Swap in the new data template (we made a backup earlier in load_bg to reinstate later)
            tmp_templates = {
                'filename': os.path.basename(file_path),
                'full_path': file_path,
                'image': image,
                'data': data_out,
                'original_bg_affine': image.affine
            }


            # Save template for swapping when user selects other statmap
            self.brain_nav.statmap_templates[file_nr] = tmp_templates

            # Load and align the atlas to the current template image this will swap the statmap template in atlasInfo
            # self.load_atlases(image, key)
            
            # Store atlas aligned to data-as-template with a special key
            self.load_atlases(image, ('data_as_template', file_nr))
            
        except Exception as e:
            print(f"Error loading data as background: {e}")
            return None
        
    # Under construction!
    def add_template(self, file_path):
        file_nr_template = self.brain_nav.file_nr_template


        image = nib.load(file_path)  # Load the NIfTI file
        image = nib.as_closest_canonical(image)
        data_out =  np.ascontiguousarray(image.get_fdata())

        # match the atlast
        self.load_atlases(image, file_nr_template)


        # Set the (new) image and data in the BrainNav instance for later use
        self.brain_nav.templates[file_nr_template]['image'] = image
        self.brain_nav.templates[file_nr_template]['data'] = data_out
        self.brain_nav.templates[file_nr_template]['original_bg_affine'] = image.affine    

    def load_atlases(self, image, file_nr_template):
        """
        Load and align atlas data with the given template image.
        'key' can be:
            - an integer: for template-only alignment (file_nr_template)
            - a tuple: ('data_as_template', file_nr) for special case
        """
        atlasInfo = {
            'image': None,
            'data': None,
            'codebook': None
        }

        # load atlas and codebook - hardcoded for now
        atlas_path                  = os.path.join(os.path.dirname(__file__), '..', 'public/atlases/AAL2/AAL2.nii')
        codebook_path               = os.path.join(os.path.dirname(__file__), '..', 'public/atlases/AAL2/AAL2_CodeBook.txt')
        atlas_img                   = nib.load(atlas_path)
        atlas_img                   = nib.as_closest_canonical(atlas_img)
        a_atlas_image, _            = ImageProcessing.align_images(image, atlas_img, order=0)
        tr_atlas_img                = ImageProcessing.transpose_image(a_atlas_image)
        _, rtr_atlas_img, _         = ImageProcessing.rotate_volume(tr_atlas_img)

        # codebook
        codebook = {}
        with open(codebook_path, 'r') as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) >= 3:
                    code = int(parts[2])  # e.g., 2001
                    name = ' '.join(parts[1:-1]) if len(parts) > 3 else parts[1]
                    name = name.replace('_', ' ').title() 
                    codebook[code] = name

        # atlasInfo['image'] = rtr_atlas_img
        atlasInfo['data'] = np.ascontiguousarray(rtr_atlas_img.get_fdata())
        atlasInfo['codebook'] = codebook

        self.brain_nav.atlasInfo[file_nr_template] = atlasInfo

        # return atlasInfo


    def load_overlay(self, file_path):

        # error_handler = ErrorHandler(log_file='nifti_loader_errors.log')  # Create an instance of ErrorHandler

        try:
            # Check the file type and add the fileInfo to the instance
            # in check_file_type the data is transposed. So ARI routine is run
            # only on transposed data. This was done to align it with the R routine so 
            # i could compare numbers. 
            self.check_file_type(file_path) 

        except Exception as e:
            return None
            # error_handler.handle_exception(e)  # Use ErrorHandler to handle the exception


    def check_file_type(self, file_path):
        """
        Creates and starts to fill fileInfo

        This function determines the type of the NIfTI file provided. It initializes file-type properties and reads the file's header
        to extract information about the data it contains. This includes the statistical type (e.g., t-map, z-map, p-map), degrees 
        of freedom if applicable, and the validity of the file. 

        The function performs the following steps:
        1. Initialize the file-type properties with default values.
        2. Load the NIfTI data from the given file path.
        3. Check if the data was loaded successfully and update the validity status.
        4. Extract and store the header information.
        5. Determine the type of statistical map based on the `intent_code` or `descrip` field in the header.
        6. If available, extract the degrees of freedom from the header description.
        7. Set the appropriate type for selection in a dropdown menu.
        8. Store the processed file-type information in the brain_nav instance.

        This function helps in identifying the nature of the data in the NIfTI file, which is crucial for subsequent analysis and 
        visualization steps in the application.
        """
        # Initialize file-type properties
        fileInfo = {
            'type': 'u',
            'df': 0,
            # 'twosided': None,
            'valid': False,
            'selected': 'unknown',
            'filename': os.path.basename(file_path),
            'full_path': file_path,
            'header': None,
            'data': None,
            'mask': None,
            'grad_map': None,
            'newAffine': None,
            'original_orientation': None
        }

        try:
            # Load the overlay image
            data = nib.load(file_path)
            fileInfo['valid'] = True
        except Exception as e:
            print(f"Error loading file: {e}")
            return
        
        file_nr = self.brain_nav.file_nr

        orient = nib.orientations.aff2axcodes(data.affine)
        fileInfo['original_orientation'] = orient
        
        print(f"Original data orientation: {orient}")

        # Reorient to RAS
        # Code    Label      Meaning
        #  0      unknown    sform not defined
        #  1      scanner    RAS+ in scanner coordinates
        #  2      aligned    RAS+ aligned to some other scan
        #  3      talairach  RAS+ in Talairach atlas space
        #  4      mni        RAS+ in MNI atlas space
        # rasCode = data.header['sform_code']

        data = nib.as_closest_canonical(data)

        # Read in header to determine statistic type
        header = data.header
        affine = data.affine

        orient = nib.orientations.aff2axcodes(affine)
        print(f"Switched data orientation to: {orient}")

        # Ensure the data is in C-contiguous format
        fileInfo['data'] = np.ascontiguousarray(data.get_fdata())
        # fileInfo['data'] = data.get_fdata()

        # Store original dimensions before transposing
        fileInfo['original_data_dimensions'] = fileInfo['data'].shape

        # We need this transpose for the cpp computations to work. 
        # tr_image = ImageProcessing.transpose_image(data)
        # fileInfo['data'] = tr_image.get_fdata()

        # Set mask based on valid data values
        fileInfo['mask'] = ~np.isnan(fileInfo['data']) #& (fileInfo['data'] != 0)
        # fileInfo['mask'] = (fileInfo['data'] != 0)

        # transposed_affine = tr_image.affine
        # print("Updated affine after reordering axes:\n", transposed_affine)

        # Update the header to reflect the new affine
        # new_img = nib.Nifti1Image(fileInfo['data'], affine=transposed_affine, header=header)
        # new_img = tr_image

        # fileInfo['raw_overlay_Tr'] = new_img
        # fileInfo['header'] = new_img.header
        # fileInfo['transposed_affine'] = transposed_affine

        fileInfo['header'] = header
        fileInfo['affine'] = affine
        fileInfo['sform'] = data.get_sform()


        if file_nr == 0:
            # If this is the first file (the one specified on start_window) we already have
            # this data so we retrieve it here. 
            fileInfo['type'] = self.brain_nav.start_input['file_type']
        else:
            # If it's a file that was uploaded later >1 we rerun the routine
            # Set type based on intent_code
            intent_code = header.get_intent()[0]
            if intent_code:
                if intent_code == 't test':
                    fileInfo['type'] = 't'
                elif intent_code == 'f test':
                    fileInfo['type'] = 'f'
                elif intent_code == 'z score':
                    fileInfo['type'] = 'z'
                elif intent_code == 'p-value':
                    fileInfo['type'] = 'p'
                else:
                    ftype, tdf = self.ask_for_map_type(fileInfo)
                    fileInfo['type'] = ftype
                    self.brain_nav.input['tdf'] = tdf
                
                print(f"Determined intent_code: {fileInfo['type']}")
            else:
                # Determine type based on description
                descrip = header['descrip'].tostring().decode('utf-8')
                try:
                    if "SPM{T" in descrip:
                        fileInfo['type'] = 't'
                    else:
                        # If description-based determination fails, ask for map type
                        ftype, tdf = self.ask_for_map_type(fileInfo)
                        fileInfo['type'] = ftype
                        self.brain_nav.input['tdf'] = tdf
                        
                    print(f"Determined descrip: {fileInfo['type']}")

                    # Extract degrees of freedom from the description
                    try:
                        df = float(descrip.split("[")[1].split("]")[0])
                        self.brain_nav.input['tdf'] = df
                        print(f"Determined df: {self.brain_nav.input['tdf']}")
                    except (IndexError, ValueError):
                        print("Could not determine degrees of freedom from the description.")
                        pass
                except Exception as e:
                    print(f"Error determining map type from description: {str(e)}")
                    ftype, tdf = self.ask_for_map_type(fileInfo)
                    fileInfo['type'] = ftype
                    self.brain_nav.input['tdf'] = tdf


        # # hard code zmap for testing, test file returns u
        # fileInfo['type'] = 'z' 

        self.brain_nav.fileInfo[file_nr] = fileInfo

    def ask_for_map_type(self, fileInfo):
        # Open a dialog to ask the user to select the map type
        items = ['t-map', 'z-map', 'p-map']
        ftype = None
        tdf = None
        item, ok = QInputDialog.getItem(self.brain_nav, "Select Map Type", 
                                        "Map type not recognized. Please select the map type:", 
                                        items, 0, False)
        if ok and item:
            if item == 't-map':
                ftype = 't'
            elif item == 'z-map':
                ftype = 'z'
            elif item == 'p-map':
                ftype = 'p'
        else:
            QMessageBox.warning(self.brain_nav, "Selection Required", "Map type selection is required.")
        
        if ftype == 't':
            df, ok = QInputDialog.getInt(self.brain_nav, "Degrees of Freedom", "Enter the degrees of freedom:", 1, 1, 100)
            if ok:
                tdf = df
                print(f"Degrees of Freedom: {df}")
            else:
                print("User cancelled the input")
        
        return ftype, tdf
    

    # def get_preferred_affine(img):
    #     header = img.header
    #     qform_code = header.get('qform_code', 0)
    #     sform_code = header.get('sform_code', 0)
        
    #     print("qform_code:", qform_code)
    #     print("sform_code:", sform_code)
        
    #     # Prefer the sform if it's set (nonzero)
    #     if sform_code > 0:
    #         affine = img.get_sform()
    #         print("Using sform.")
    #     elif qform_code > 0:
    #         affine = img.get_qform()
    #         print("Using qform.")
    #     else:
    #         affine = img.affine
    #         print("Using the default affine.")
    #     return affine

    # def load_and_reorient(file_path, desired_order=('R', 'A', 'S')):
    #     # Load the image
    #     img = nib.load(file_path)
        
    #     # Determine the best affine using the header codes
    #     preferred_affine = NiftiLoader.get_preferred_affine(img)
        
    #     # Force the image to use the preferred affine for both qform and sform
    #     img.set_sform(preferred_affine)
    #     img.set_qform(preferred_affine)
        
    #     # Reorient the image to canonical (usually RAS)
    #     canonical_img = nib.as_closest_canonical(img)
        
    #     # Get the orientation codes (e.g., ('R','A','S') for canonical)
    #     orientation = io_orientation(canonical_img.affine)
    #     axcodes = ornt2axcodes(orientation)
    #     print("Canonical orientation:", axcodes)
        
    #     return canonical_img

    # def load_and_prepare(file_path, desired_order=('R', 'A', 'S')):
    #     # Load the image and reorient to canonical (RAS)
    #     image = nib.load(file_path)
    #     image = nib.as_closest_canonical(image)
        
    #     # Check current orientation using the affine
    #     current_axcodes = ornt2axcodes(io_orientation(image.affine))
    #     print("Image is in orientation:", current_axcodes)
        
    #     # If current orientation doesn't match desired_order, compute the necessary reorientation
    #     if current_axcodes != desired_order:
    #         # Determine the transformation to get to desired_order
    #         # nib.orientations.ornt_transform can compute the needed reorientation.
    #         from nibabel.orientations import axcodes2ornt, ornt_transform, apply_orientation
    #         current_ornt = axcodes2ornt(current_axcodes)
    #         desired_ornt = axcodes2ornt(desired_order)
    #         transform = ornt_transform(current_ornt, desired_ornt)
    #         data = image.get_fdata()
    #         reoriented_data = apply_orientation(data, transform)
    #     else:
    #         reoriented_data = image.get_fdata()
        
    #     # Now, if your UI expects a particular order (e.g., (sagittal, coronal, axial) = (0,1,2))
    #     # you might still need to transpose the data:
    #     data_out = reoriented_data.T  # adjust if needed
        
    #     return data_out, image.affine




 
