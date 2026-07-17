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
from ari_application.models.image_processing import ImageProcessing



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
            if hasattr(self, 'metrics'):
                self.metrics.show_metrics()
            OrthViewSetup(self.brain_nav).setup_viewer()
        
        except Exception as e:
            print(f'Error in load_bg: {e}')
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

    @staticmethod
    def parse_atlas_codebook(codebook_path):
        """
        Parse an AAL2-style codebook text file. Each line has the shape
        `<row_id> <name_token(s)> <int_label>` (at least three whitespace-
        separated columns). Returns {int_label: title_cased_name}.

        Logic is byte-for-byte the same as the previous inline parser inside
        load_atlases — preserved verbatim so the AAL2 codebook still parses
        identically after this refactor. Callers that need a fallback on
        malformed files should wrap in try/except.
        """
        codebook = {}
        with open(codebook_path, 'r') as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) >= 3:
                    code = int(parts[2])  # e.g., 2001
                    name = ' '.join(parts[1:-1]) if len(parts) > 3 else parts[1]
                    name = name.replace('_', ' ').title()
                    codebook[code] = name
        return codebook

    def load_user_atlas(self, file_path):
        """
        Load a user-supplied atlas NIfTI (integer-labelled ROI map) and align
        it to every loaded template — and to every statmap-as-template entry
        — so it survives template switches without re-aligning.

        Mirrors load_atlases (which is hardcoded to AAL2) but:
          - Takes the path from the UI instead of from disk-bundled assets.
          - Auto-generates a codebook from the unique non-zero labels when no
            AAL2-style sidecar .txt is found next to the file.
          - Builds a stable RGBA LUT sized to max(label)+1 so np.take(lut,
            atlas_slice, axis=0) renders directly through the existing overlay
            pipeline.
          - Stores under self.brain_nav.userAtlasInfo (keyed the same way as
            atlasInfo) so it lives alongside AAL2 without colliding.

        On failure, logs to the in-app message box and returns False so the
        caller can decide whether to flip UI state. Returns True on success.
        """
        try:
            atlas_img = nib.load(file_path)
        except Exception as e:
            self.brain_nav.message_box.log_message(
                f"<span style='color: red;'>Failed to load atlas: {e}</span>"
            )
            return False

        atlas_img = nib.as_closest_canonical(atlas_img)
        atlas_data = atlas_img.get_fdata()

        if atlas_data.ndim != 3:
            self.brain_nav.message_box.log_message(
                f"<span style='color: red;'>Atlas must be 3D, got shape "
                f"{atlas_data.shape}.</span>"
            )
            return False

        unique_labels = np.unique(atlas_data[atlas_data > 0])
        if unique_labels.size == 0:
            self.brain_nav.message_box.log_message(
                "<span style='color: red;'>Atlas has no non-zero voxels — "
                "nothing to label.</span>"
            )
            return False

        # Round to nearest int before casting, in case the NIfTI is float32
        # (AAL2 is — labels arrive as 2001.0, etc.).
        unique_labels = np.round(unique_labels).astype(int)
        labels_set = set(unique_labels.tolist())

        # Codebook: sidecar .txt in AAL2 format if present, else auto-generate.
        codebook = self._load_atlas_codebook(file_path, labels_set)

        # Stable LUT sized to max(label)+1. Most rows stay transparent; only
        # ROI rows get an HSV-cycled colour. Alpha is set to brain_nav.alpha
        # so it matches the cluster overlay's transparency.
        lut = self._build_atlas_lut(unique_labels)

        # Align against every template + every statmap-as-template entry.
        # alignment uses order=0 (nearest-neighbour) to preserve integer
        # labels — the same call load_atlases makes for AAL2.
        n_template_alignments = 0
        for template_key, template_entry in self.brain_nav.templates.items():
            template_image = template_entry.get('image')
            if template_image is None:
                continue
            aligned = self._align_atlas_to_template(atlas_img, template_image)
            self.brain_nav.userAtlasInfo[template_key] = {
                'filename': os.path.basename(file_path),
                'full_path': file_path,
                'data': aligned,
                'codebook': codebook,
                'lut': lut,
                'original_affine': atlas_img.affine,
                'tdps_per_roi': None,
            }
            n_template_alignments += 1

        for file_nr, stm in self.brain_nav.statmap_templates.items():
            template_image = stm.get('image')
            if template_image is None:
                continue
            aligned = self._align_atlas_to_template(atlas_img, template_image)
            self.brain_nav.userAtlasInfo[('data_as_template', file_nr)] = {
                'filename': os.path.basename(file_path),
                'full_path': file_path,
                'data': aligned,
                'codebook': codebook,
                'lut': lut,
                'original_affine': atlas_img.affine,
                'tdps_per_roi': None,
            }
            n_template_alignments += 1

        self.brain_nav.message_box.log_message(
            f"<span style='color: lightgreen;'>Atlas loaded: "
            f"{os.path.basename(file_path)} — {len(unique_labels)} ROIs, "
            f"aligned to {n_template_alignments} template(s).</span>"
        )
        return True

    def _load_atlas_codebook(self, atlas_path, labels_set):
        """
        Look for a sidecar `<basename>.txt` in the AAL2 codebook format next
        to the atlas NIfTI; parse it via the shared parse_atlas_codebook
        helper if it exists, and fill in `ROI <n>` defaults for any labels
        missing from the codebook (or for all labels if there's no sidecar).

        Logs whether a sidecar was found and how many labels it named vs.
        how many fell through to auto-generated defaults, so the user isn't
        guessing whether their codebook file was picked up.
        """
        codebook = {}
        sidecar = self._sidecar_path_for(atlas_path)

        if os.path.exists(sidecar):
            try:
                codebook = NiftiLoader.parse_atlas_codebook(sidecar)
                matched = sum(1 for lbl in labels_set if int(lbl) in codebook)
                self.brain_nav.message_box.log_message(
                    f"Codebook sidecar found: {os.path.basename(sidecar)} "
                    f"— {matched} of {len(labels_set)} atlas labels named."
                )
            except Exception as e:
                self.brain_nav.message_box.log_message(
                    f"<span style='color: orange;'>Codebook sidecar exists "
                    f"but failed to parse ({e}); using auto-generated names."
                    f"</span>"
                )
                codebook = {}
        else:
            self.brain_nav.message_box.log_message(
                f"<span style='color: #888;'>No codebook sidecar found at "
                f"{os.path.basename(sidecar)} — using auto-generated "
                f"'ROI &lt;label&gt;' names. Use Upload Codebook to attach "
                f"anatomical names.</span>"
            )

        # Fill any missing labels with a default ROI <n> name.
        for lbl in labels_set:
            codebook.setdefault(int(lbl), f"ROI {int(lbl)}")
        return codebook

    def load_user_codebook(self, codebook_path):
        """
        Replace the codebook on every userAtlasInfo entry with names parsed
        from `codebook_path` (AAL2-format `.txt`). Preserves the auto-
        generated `ROI <label>` fallback for any labels missing from the
        file so no ROI ever renders as blank.

        Returns True on a successful parse (regardless of how many labels
        matched), False if the file couldn't be read or the atlas isn't
        loaded yet. Callers typically re-render TblROI in-place after True.
        """
        if not self.brain_nav.userAtlasInfo:
            self.brain_nav.message_box.log_message(
                "<span style='color: orange;'>No user atlas loaded — "
                "upload an atlas before its codebook.</span>"
            )
            return False

        try:
            parsed = NiftiLoader.parse_atlas_codebook(codebook_path)
        except Exception as e:
            self.brain_nav.message_box.log_message(
                f"<span style='color: red;'>Failed to parse codebook "
                f"{os.path.basename(codebook_path)}: {e}</span>"
            )
            return False

        # Every userAtlasInfo entry (one per template + one per data-as-
        # template) shares the same label set — grab labels from any entry
        # to fill defaults for unmatched labels.
        sample_entry = next(iter(self.brain_nav.userAtlasInfo.values()))
        sample_atlas = sample_entry['data']
        labels_present = np.unique(sample_atlas[sample_atlas > 0]).astype(int)

        new_codebook = dict(parsed)
        for lbl in labels_present:
            new_codebook.setdefault(int(lbl), f"ROI {int(lbl)}")

        # Every entry keyed under the current atlas gets the new dict.
        # Reference-shared is fine — the codebook is immutable in practice.
        for entry in self.brain_nav.userAtlasInfo.values():
            entry['codebook'] = new_codebook

        matched = sum(1 for lbl in labels_present if int(lbl) in parsed)
        self.brain_nav.message_box.log_message(
            f"Codebook replaced from {os.path.basename(codebook_path)} — "
            f"{matched} of {len(labels_present)} labels named."
        )
        return True

    @staticmethod
    def _sidecar_path_for(atlas_path):
        """
        Resolve `foo.nii` -> `foo.txt` and `foo.nii.gz` -> `foo.txt`.
        os.path.splitext only strips the last extension, so .nii.gz needs
        an explicit second peel.
        """
        base = atlas_path
        if base.endswith('.nii.gz'):
            base = base[:-len('.nii.gz')]
        elif base.endswith('.nii'):
            base = base[:-len('.nii')]
        return base + '.txt'

    def _build_atlas_lut(self, unique_labels):
        """
        Build a (max_label + 1, 4) uint8 RGBA LUT with a deterministic
        HSV-cycled palette. Row 0 and any label not present in the atlas
        stay transparent. Sized so np.take(lut, atlas_volume, axis=0)
        works directly — same shape contract as fileInfo['custom_lut']
        after the background-row insertion that add_overlay_with_transparency
        performs.
        """
        import colorsys

        max_label = int(unique_labels.max())
        lut = np.zeros((max_label + 1, 4), dtype=np.uint8)
        alpha_byte = int(self.brain_nav.alpha * 255)

        # Deterministic colour-cycling. Use a golden-ratio hue step so adjacent
        # ROIs get visually distinct colours without us having to randomise.
        golden = 0.61803398875
        for i, lbl in enumerate(unique_labels.tolist()):
            h = (i * golden) % 1.0
            r, g, b = colorsys.hsv_to_rgb(h, 0.75, 0.95)
            lut[int(lbl)] = [int(r * 255), int(g * 255), int(b * 255), alpha_byte]
        return lut

    def _align_atlas_to_template(self, atlas_img, template_image):
        """
        Resample atlas_img onto template_image's grid via the shared
        align_label_volume helper, then round-trip the resampled volume
        through int32 to drop any float drift from nearest-neighbour
        resampling. The int cast is the only thing user atlases need that
        the AAL2 path doesn't — AAL2 stores its data as float.
        """
        rtr_img = ImageProcessing.align_label_volume(template_image, atlas_img)
        return np.ascontiguousarray(
            np.round(rtr_img.get_fdata()).astype(np.int32)
        )

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

        # align + transpose + rotate (shared with the user-atlas path)
        rtr_atlas_img = ImageProcessing.align_label_volume(image, atlas_img)

        # codebook (shared parser; identical logic to the previous inline loop)
        codebook = NiftiLoader.parse_atlas_codebook(codebook_path)

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




 
