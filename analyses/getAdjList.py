
class get_adjList:

    # @staticmethod
    # def xyz2index(x, y, z, DIMS):
    #     """
    #     Convert 3D coordinates (x, y, z) to a linear index, using C-order (row-major)
    #     as defined by:
    #        index = z * DIMS[1] * DIMS[0] + y * DIMS[0] + x
    #     """
    #     return z * DIMS[1] * DIMS[0] + y * DIMS[0] + x

    
    # @staticmethod
    # def index2xyz(index, DIMS):
    #     """
    #     Convert a linear index to [x, y, z] coordinates.
        
    #     Given:
    #        x = index % DIMS[0]
    #        y = (index // DIMS[0]) % DIMS[1]
    #        z = index // (DIMS[0] * DIMS[1])
        
    #     Returns a list: [x, y, z]
    #     """
    #     x = index % DIMS[0]
    #     y = (index // DIMS[0]) % DIMS[1]
    #     z = index // (DIMS[0] * DIMS[1])
    #     return [x, y, z]
    
    @staticmethod
    def xyz2index(x, y, z, DIMS):
        """
        Convert 3D coordinates (x, y, z) to a linear index, using C-order (row-major)
        **Updated to match the new transposed dimensions.**
        """
        return x * DIMS[1] * DIMS[2] + y * DIMS[2] + z

    @staticmethod
    def index2xyz(index, DIMS):
        """
        Convert a linear index to [x, y, z] coordinates.
        **Updated to correctly retrieve coordinates using the transposed dimensions.**
        """
        x = index // (DIMS[1] * DIMS[2])
        y = (index // DIMS[2]) % DIMS[1]
        z = index % DIMS[2]
        return [x, y, z]
    
    @staticmethod
    def xyz_check(x, y, z, index, DIMS, MASK):
        """
        Check if the voxel at coordinates (x, y, z) is within the valid bounds of 
        the image (using DIMS) and if MASK at the corresponding linear index is nonzero.
        
        This mirrors the C++ function:
          return (x >= 0 && x < DIMS[0] &&
                  y >= 0 && y < DIMS[1] &&
                  z >= 0 && z < DIMS[2] &&
                  MASK[index] != 0);
        """
        return (x >= 0 and x < DIMS[0] and
                y >= 0 and y < DIMS[1] and
                z >= 0 and z < DIMS[2] and
                MASK[index] != 0)
    
    @staticmethod
    def ids2xyz(IDS, DIMS):
        """
        Convert multiple voxel indices to a list of xyz-coordinate lists.

        Parameters:
            IDS (list of int): List of voxel indices.
            DIMS (list or tuple of int): Dimensions of the 3D volume.

        Returns:
            list of lists: A list where each sublist contains the [x, y, z] coordinates 
                        corresponding to an index in IDS.
        """
        return [get_adjList.index2xyz(index, DIMS) for index in IDS]




    @staticmethod
    def findNeighbours(MASK, DIMS, index, conn):
        """
        For a given voxel (identified by its linear index) in a 3D image,
        find all valid neighbors (up to conn neighbors) based on predefined
        offsets (using 26-connectivity).
        
        This function:
        - Converts the linear index into (x,y,z) coordinates.
        - Iterates over the 26 predefined directional offsets.
        - For each neighbor, computes its linear index and uses xyz_check to
            determine if the neighbor is valid (i.e. within bounds and MASK != 0).
        - Returns a list of neighbor values from MASK.
        
        Parameters:
        MASK: list or array of integers representing the mask (assumed to be 1-indexed as in C++)
        DIMS: list or tuple of three integers representing image dimensions [DIMS[0], DIMS[1], DIMS[2]]
        index: the linear index of the current voxel
        conn: connectivity (e.g., 26)
        
        Returns:
        A list of neighbor mask values.
        """
        # Get voxel coordinates for the given index
        XYZ = get_adjList.index2xyz(index, DIMS)
        
        # Directional offset arrays (26-connectivity)
        DX = [1, -1, 0, 0, 0, 0, 1, -1, 1, -1, 1, -1, 1, -1, 0, 0, 0, 0, 1, -1, 1, -1, 1, -1, 1, -1]
        DY = [0, 0, 1, -1, 0, 0, 1, 1, -1, -1, 0, 0, 0, 0, 1, -1, 1, -1, 1, 1, -1, -1, 1, 1, -1, -1]
        DZ = [0, 0, 0, 0, 1, -1, 0, 0, 0, 0, 1, 1, -1, -1, 1, 1, -1, -1, 1, 1, 1, 1, -1, -1, -1, -1]
        
        IDS = []  # List to store valid neighbor values
        for i in range(conn):
            nx = XYZ[0] + DX[i]
            ny = XYZ[1] + DY[i]
            nz = XYZ[2] + DZ[i]
            neighbor_index = get_adjList.xyz2index(nx, ny, nz, DIMS)
            if get_adjList.xyz_check(nx, ny, nz, neighbor_index, DIMS, MASK):
                IDS.append(MASK[neighbor_index])
        return IDS

    @staticmethod
    def findAdjList(MASK, INDEXP, DIMS, m, conn):
        """
        Compute the adjacency list for all in-mask voxels.
        
        Parameters:
        MASK: A list or array representing the 3D mask (ordered as in the original data, 1-indexed)
        INDEXP: A list of linear voxel indices for unsorted p-values (or in-mask voxels)
        DIMS: A list or tuple of image dimensions [width, height, depth]
        m: Number of in-mask voxels
        conn: Connectivity criterion (e.g., 6, 18, or 26)
        
        Returns:
        A list of lists, where each sublist contains the neighbor values for the corresponding voxel.
        """
        ADJ = []
        for i in range(m):
            IDS = get_adjList.findNeighbours(MASK, DIMS, INDEXP[i], conn)
            ADJ.append(IDS)
        return ADJ

