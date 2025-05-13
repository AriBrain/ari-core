
/**
 * @file ARICluster.cpp
 * @brief This file implements various functions for finding clusters, computing 
 *        TDP bounds, and processing voxel data. The main functions included are:
 * 
 * - **UnionBySize**: Merges sets using union by size for disjoint-set data structures.
 * - **findClusters**: Computes all supra-threshold clusters (STCs).
 * - **descendants**: Finds all descendants of a given node in a tree.
 * - **heavyPathTDP**: Computes the TDP bounds of the heavy path starting from a node.
 * - **forestTDP**: Iterates over the forest to compute TDP values for all nodes.
 * - **queryPreparation**: Prepares the admissible STCs based on TDP values.
 * - **findLeft**: Finds the leftmost index in the sorted list where TDP is above a threshold.
 * - **answerQuery**: Finds maximal STCs that meet the TDP condition for a given threshold.
 * - **answerQueryBatch**: Processes multiple gamma values to find clusters in batch mode.
 * - **counting_sort**: Performs counting sort on cluster sizes in descending order.
 * - **findAdjList**: Finds the adjacency list for in-mask voxels based on connectivity.
 * - **index2xyz**: Converts a linear voxel index to 3D (x, y, z) coordinates.
 * - **ids2xyz**: Converts a list of voxel indices to a list of 3D coordinates.
 * - **xyz_check**: Checks whether a voxel is within bounds and in the mask.
 * - **findNeighbours**: Finds the valid neighboring voxels for a given voxel.
 */


#include <iostream>
#include <vector>
#include <list>
#include <algorithm>
#include <iterator>
#include <cmath>
#include "hommel.h"
#include <fstream>
#include <iomanip>

// #include "../cpp_sources/ARICluster.h"

// Function prototypes for functions used but not defined within this file
int Find(int i, std::vector<int>& PARENT);

//------------------------- (1) FIND ALL STCS (USING SORTING RANKS) -------------------------//

// Union function of a disjoint-set data structure based on the "union by size" technique.
// The disjoint sets will represent the components of a forest, and the data structure is
// augmented to keep track of the forest root of each component. UnionBySize(i,j) merges
// the sets S_i and S_j (where S_k denotes the set containing k), and assigns the forestroot
// of S_i to be the forestroot of the resulting union.
void UnionBySize(int i, int j, std::vector<int>& PARENT, std::vector<int>& FORESTROOT, std::vector<int>& SIZE)
{
    int irep = Find(i, PARENT);
    int jrep = Find(j, PARENT);
    
    // if i and j are already in the same set
    if (irep == jrep) return;
    
    // i and j are not in same set, so we merge
    int iroot = FORESTROOT[irep];
    int jroot = FORESTROOT[jrep];
    if (SIZE[iroot] < SIZE[jroot])
    {
        PARENT[irep] = jrep;
        FORESTROOT[jrep] = iroot;
    }
    else
    {
        PARENT[jrep] = irep;
    }
    SIZE[iroot] += SIZE[jroot];
}

// Compute all supra-threshold clusters (STCs)
std::vector< std::vector<int> > findClusters(int m, std::vector< std::vector<int> >& ADJ, std::vector<int>& ORD, std::vector<int>& RANK)
{
    // Initialize output: a list of children for all nodes
    std::vector< std::vector<int> > CHILD(m);
    // Initialize output: a vector of sizes of subtrees
    std::vector<int> SIZE(m, 1);
    // Initialize output: a list of forest roots
    std::list<int> ROOT;
    
    // Initialize a child list for a single node
    std::list<int> CHD;
    
    // Prepare disjoint set data structure
    std::vector<int> PARENT, FORESTROOT;
    PARENT.reserve(m);
    FORESTROOT.reserve(m);
    for (int i = 0; i < m; i++)
    {
        PARENT.push_back(i);
        FORESTROOT.push_back(i);
    }
    
    // Loop through all nodes in the ascending order of p-values
    for (int i = 0; i < m; i++)
    {
        int v = ORD[i] - 1;  // Convert to 1-based indexing
        
        // Find neighbours for node with the ith smallest p-value
        std::vector<int>& IDS = ADJ[v];
        
        // Loop through all its neighbours
        for (size_t j = 0; j < IDS.size(); j++)
        {
            if (RANK[IDS[j] - 1] < i + 1)  // Convert to 1-based indexing
            {
                int jrep = Find(IDS[j] - 1, PARENT);  // Representative of the tree (1-based)
                int w = FORESTROOT[jrep];  // Forest root of the tree
                
                if (v != w)
                {
                    // Merge S_v and S_w = S_{jrep}
                    UnionBySize(v, jrep, PARENT, FORESTROOT, SIZE);
                    
                    // Put a heavy child in front (using std::list)
                    if (CHD.empty() || SIZE[CHD.front()] >= SIZE[w])
                    {
                        CHD.push_back(w);
                    }
                    else
                    {
                        CHD.push_front(w);
                    }
                }
            }
        }
        
        // Update child list
        CHILD[v] = std::vector<int>(CHD.begin(), CHD.end());
        CHD.clear();
    }
    
    // Find forest roots
    for (int i = 0; i < m; i++)
    {
        if (PARENT[i] == i)
        {
            ROOT.push_back(FORESTROOT[i]);
        }
    }

    // Construct the result vector
    std::vector< std::vector<int> > result;
    result.push_back(SIZE);
    result.push_back(std::vector<int>(ROOT.begin(), ROOT.end()));
    result.insert(result.end(), CHILD.begin(), CHILD.end());

    return result;
}


//------------------------- (2) COMPUTE TDPS FOR ALL STCS -------------------------//

// Iterative post-order traversal to find descendants of v (including v).
// Note: When we pop a vertex from the stack, we push that vertex again as a value and
// then all its children in reverse order on the stack. If we pop a value, it means that
// all its children have been fully explored and added to the descendants, so we append
// the current value to the descendants too.
std::vector<int> descendants(int v, std::vector<int>& SIZE, std::vector< std::vector<int> >& CHILD)
{
    // Initialize the descendant list based on the size of the subtree at node v
    std::vector<int> DESC(SIZE[v], 0);
    
    int len = 0;  // Track the number of found descendants
    int top = SIZE[v] - 1;  // Track the top of the stack
    DESC[top] = v;  // Push v on the stack (stack grows from right to left)
    
    // Process the stack while it's not empty
    while (top < static_cast<int>(DESC.size()))  // Ensure we process all the descendants
    {
        v = DESC[top];  // Pop the top of the stack
        top++;
        
        if (v < 0)  // If ~v is a value, append ~v to the descendants
        {
            DESC[len] = ~v;  // Bitwise negation to mark the node as processed
            len++;
        }
        else
        {
            top--;
            DESC[top] = ~v;  // Mark the current node as a value
            
            // Process all children in reverse order
            std::vector<int>& CHD = CHILD[v];
            for (int j = CHD.size() - 1; j >= 0; j--)
            {
                top--;
                DESC[top] = CHD[j]; 
            }
        }
    }
    
    return DESC;
}



// Calculates the size of the concentration set at a fixed alpha
int findConcentration_one_based(const std::vector<double>& p, double simesfactor, int h, double alpha, int m) {
    int z = m - h;
    if (z > 0) {
        while ((z < m) & (simesfactor * p[z-1] > (z - m + h + 1) * alpha)) {
            z++;
        }
    }
    return z;
}

// Implementation of findDiscoveries
std::vector<int> findDiscoveries_one_based(const std::vector<int>& idx, const std::vector<double>& allp, double simesfactor, int h, double alpha, int k, int m) {
    // Calculate categories for the p-values
    std::vector<int> cats;
    for (int i = 0; i < k; i++) {
        cats.push_back(getCategory(allp[idx[i] - 1], simesfactor, alpha, m));
    }

    // Find the maximum category needed
    int z = findConcentration_one_based(allp, simesfactor, h, alpha, m);
    int maxcat = std::min(z - m + h + 1, k);
    int maxcatI = 0;
    for (int i = k - 1; i >= 0; i--) {
        if (cats[i] > maxcatI) {
            maxcatI = cats[i];
            if (maxcatI >= maxcat) break;
        }
    }
    maxcat = std::min(maxcat, maxcatI);

    // Prepare disjoint set data structure
    std::vector<int> parent(maxcat + 1);
    std::vector<int> lowest(maxcat + 1);
    std::vector<int> rank(maxcat + 1, 0);
    for (int i = 0; i <= maxcat; i++) {
        parent[i] = i;
        lowest[i] = i;
    }

    // The algorithm proper
    std::vector<int> discoveries(k + 1, 0);
    int lowestInPi;
    for (int i = 0; i < k; i++) {
        if (cats[i] <= maxcat) {
            lowestInPi = lowest[Find(cats[i], parent)];
            if (lowestInPi == 1) {
                discoveries[i + 1] = discoveries[i] + 1;
            } else {
                discoveries[i + 1] = discoveries[i];
                Union(lowestInPi - 1, Find(cats[i], parent), parent, lowest, rank);
            }
        } else {
            discoveries[i + 1] = discoveries[i];
        }
    }

    return discoveries;
}



// Compute the TDP bounds of the heavy path starting at v (1-based indexing)
void heavyPathTDP(int v, int par, int m, int h, double alpha, double simesh, std::vector<double>& P, std::vector<int>& SIZE, std::vector< std::vector<int> >& CHILD, std::vector<double>& TDP)
{
    // Use descendants with one-based indexing
    std::vector<int> HP = descendants(v, SIZE, CHILD);  
    for (size_t i = 0; i < HP.size(); i++)
    {
        HP[i]++;  // Adjust descendants to 1-based indexing
    }

    std::vector<int> NUM = findDiscoveries(HP, P, simesh, h, alpha, HP.size(), m);
    // std::vector<int> NUM = findDiscoveries_one_based(HP, P, simesh, h, alpha, HP.size(), m);


    while (true)  // Walk down the heavy path
    {
        // Check if v represents an STC
        if (par == -1 || P[v] != P[par])  // Adjust for 1-based indexing in P
        {
            TDP[v] = static_cast<double>(NUM[SIZE[v]]) / static_cast<double>(SIZE[v]);  
        }
        else
        {
            TDP[v] = -1;  // Invalid STCs get TDP of -1
        }

        // Check if v is a leaf
        if (SIZE[v] == 1) {
            break;
        }
        
        // Update v & its parent
        par = v;
        std::vector<int>& CHD = CHILD[v];  // Adjust CHILD for 1-based indexing
        v = CHD[0];  // Move to the first child and adjust for 1-based indexing
    }
}


std::vector<double> forestTDP(int m, int h, double alpha, double simesh, std::vector<double>& P, std::vector<int>& SIZE, std::vector<int>& ROOT, std::vector< std::vector<int> >& CHILD)
{
    // std::cout << "Entering forestTDP function" << std::endl;  // Log entry to function
    std::vector<double> TDP(m);

    // Loop through all roots
    for (size_t i = 0; i < ROOT.size(); i++)
    {
        // No subtraction for ROOT[i] as it matches the original
        heavyPathTDP(ROOT[i], -1, m, h, alpha, simesh, P, SIZE, CHILD, TDP);  
    }
    
    // Loop through all nodes
    for (int i = 0; i < m; i++)
    {
        std::vector<int>& CHD = CHILD[i];
        
        // Loop through all children starting from the second child (1-based index logic)
        for (size_t j = 1; j < CHD.size(); j++)
        {
            heavyPathTDP(CHD[j], i, m, h, alpha, simesh, P, SIZE, CHILD, TDP);
        }
    }

    // std::cout << "Exiting forestTDP function" << std::endl;  // Log exit from function
    return TDP;
}

//------------------------- (3) PREPARE ADMISSIBLE STCS -------------------------//

// Construct a comparator for the below sorting step
struct compareBy
{
    std::vector<double>& value;
    compareBy(std::vector<double>& val) : value(val) {}
    bool operator() (int i, int j) { return value[i] < value[j]; }
};

// Set up ADMSTC: a list of representatives of admissible STCs
std::vector<int> queryPreparation(int m, std::vector<int>& ROOT, std::vector<double>& TDP, std::vector< std::vector<int> >& CHILD)
{
    std::vector<int> ADMSTC;  // A vector of representatives of admissible STCs
    ADMSTC.reserve(m);
    std::vector<double> STACK;
    STACK.reserve(m * 2);
    
    // Loop through all roots
    for (size_t i = 0; i < ROOT.size(); i++)
    {
        STACK.push_back(ROOT[i]);  // Walk down the forest from ROOT[i]
        STACK.push_back(-1);       // Maximum seen TDP on the path to ROOT[i]: non-existent
        while (STACK.size() > 0)
        {
            double q = STACK.back();  // Maximum seen TDP on the path to v
            STACK.pop_back();
            int v = static_cast<int>(STACK.back());
            STACK.pop_back();
            
            // Check if v has higher TDP than its ancestors
            if (TDP[v] > q) ADMSTC.push_back(v);  // Note: q>=-1 & invalid STCs have TDP=-1
            
            std::vector<int>& CHD = CHILD[v];
            for (size_t j = 0; j < CHD.size(); j++)
            {
                STACK.push_back(CHD[j]);
                STACK.push_back(std::max(TDP[v], q));
            }
        }
    }
    
    // Sort ADMSTC in ascending order of TDP using the comparator
    std::sort(ADMSTC.begin(), ADMSTC.end(), compareBy(TDP));

    return ADMSTC;
}

//-------------------------- (4) FORM CLUSTERS USING gamma --------------------------//

// Find leftmost index i in ADMSTC such that TDP[ADMSTC[i]] >= g
// Return size(ADMSTC) if no such index exists;
// Run linear search & binary search in parallel;
// gamma >= 0 is needed because inadmissible STCs have been assigned TDP -1.
int findLeft(double gamma, std::vector<int>& ADMSTC, std::vector<double>& TDP)
{
    int right = ADMSTC.size();
    int low = 0;
    int high = right;
    while (low < high)
    {
        int mid = (low + high) / 2;  // (1) Binary search part (using integer division)
        if (TDP[ADMSTC[mid]] >= gamma)
        {
            high = mid;
        }
        else
        {
            low = mid + 1;
        }
        
        right--;  // (2) Linear search part
        // The linear search will decrement `right`, but no need to guard against right < 0
        if (TDP[ADMSTC[right]] < gamma)
        {
            return right + 1;  // Return the adjusted position
        }
    }
    
    return low;  // If no linear search match, return low index
}

// Answer the query, i.e., find maximal STCs under the TDP condition.
// gamma >= 0 is needed because inadmissible STCs have been assigned TDP -1.
std::vector< std::vector<int> > answerQuery(double gamma, std::vector<int>& ADMSTC, std::vector<int>& SIZE, std::vector<int>& MARK, std::vector<double>& TDP, std::vector<std::vector<int> >& CHILD)
{
    if (gamma < 0) gamma = 0;  // Constrain TDP threshold gamma to be non-negative

    // Initialize output: a list of sorting rank vectors for all clusters
    std::list<std::vector<int> > ANS;

    int left = findLeft(gamma, ADMSTC, TDP);

    for (int i = left; i < static_cast<int>(ADMSTC.size()); i++)  // Loop through ADMSTC
    {
        if (MARK[ADMSTC[i]] == 0)
        {
            // Append a cluster to ANS
            std::vector<int> DESC = descendants(ADMSTC[i], SIZE, CHILD);
            ANS.push_back(DESC);

            // Mark the corresponding voxels
            for (int j = 0; j < static_cast<int>(DESC.size()); j++)
            {
                MARK[DESC[j]] = 1;
            }
        }
    }

    // Clear marks back to 0
    for (std::list<std::vector<int> >::iterator it = ANS.begin(); it != ANS.end(); ++it)
    {
        for (size_t j = 0; j < it->size(); j++)
        {
            MARK[it->at(j)] = 0;
        }
    }

    // Convert list to a vector of vectors for the result
    std::vector< std::vector<int> > result(ANS.begin(), ANS.end());
    return result;
}

    // Processes a batch of gamma values to identify maximal STCs under the TDP condition.
    // The gamma_batch vector contains all gamma values to be processed in one function call, 
    // as opposed to calling answerQuery in a loop for each gamma individually (as done in R).
    // This approach significantly improves performance, reducing processing times compared to
    // the single-call method. However, this batch processing might introduce 
    // overhead that could lead to crashes, particularly with large datasets.
    std::vector< std::vector< std::vector<int> > > answerQueryBatch(std::vector<double>& gamma_batch, std::vector<int>& ADMSTC, std::vector<int>& SIZE, std::vector<int>& MARK, std::vector<double>& TDP, std::vector< std::vector<int> >& CHILD)
    {
        std::vector< std::vector< std::vector<int> > > batch_results;

        for (size_t i = 0; i < gamma_batch.size(); ++i) {
            double gamma = gamma_batch[i];
            if (gamma < 0) gamma = 0; // Constrain TDP threshold gamma to be non-negative

            // Initialize output for this gamma: a list of sorting rank vectors for all clusters
            std::list< std::vector<int> > ANS;

            int left = findLeft(gamma, ADMSTC, TDP);

            for (size_t i = left; i < ADMSTC.size(); i++)
            {
                if (MARK[ADMSTC[i]] == 0)
                {
                    // Append a cluster to ANS
                    std::vector<int> DESC = descendants(ADMSTC[i], SIZE, CHILD);
                    ANS.push_back(DESC);
                    // Mark the corresponding voxels
                    for (size_t j = 0; j < DESC.size(); j++)
                    {
                        MARK[DESC[j]] = 1;
                    }
                }
            }

            // Clear marks back to 0
            for (std::list<std::vector<int> >::iterator it = ANS.begin(); it != ANS.end(); ++it)
            {
                for (size_t j = 0; j < it->size(); j++)
                {
                    MARK[it->at(j)] = 0;
                }
            }

            // Convert the list of vectors to a vector of vectors for this gamma
            std::vector< std::vector<int> > result(ANS.begin(), ANS.end());

            // Store the result for this gamma
            batch_results.push_back(result);
        }

        return batch_results;
    }


// Counting sort in descending order of cluster sizes.
std::vector<int> counting_sort(int n, int maxid, std::vector<int>& CLSTRSIZE)
{
    // Initialise output sorted indices for descending cluster sizes
    std::vector<int> SORTED(n, 0);
    std::vector<int> COUNT(maxid + 1, 0);
    
    // Store count of each cluster size
    for (int i = 0; i < n; i++)
    {
        COUNT[CLSTRSIZE[i]]++;
    }
    
    // Find cumulative frequency
    for (int i = maxid; i > 0; i--)
    {
        COUNT[i - 1] += COUNT[i];
    }
    
    for (int i = 0; i < n; i++)
    {
        SORTED[COUNT[CLSTRSIZE[i]] - 1] = i;
        COUNT[CLSTRSIZE[i]]--;
    }
    
    return SORTED;
}

// Macros:
// 1) Convert xyz coordinates to index
// #define xyz2index(x, y, z, DIMS) ( (z)*DIMS[0]*DIMS[1] + (y)*DIMS[0] + (x) )
// // 2) Compute size of 3D image
// #define ndims(DIMS) ( DIMS[0]*DIMS[1]*DIMS[2] )

// // Convert voxel index to [x y z] coordinates
// std::vector<int> index2xyz(int index, std::vector<int>& DIMS)
// {
//     std::vector<int> XYZ;
//     XYZ.reserve(3);
//     XYZ.push_back( index % DIMS[0] );
//     XYZ.push_back( (index/DIMS[0]) % DIMS[1] );
//     XYZ.push_back( index/(DIMS[0]*DIMS[1]) );
    
//     return XYZ;
// }
// Macros:
// 1) Convert xyz coordinates to index
#define xyz2index(x, y, z, DIMS) ( (z) * DIMS[1] * DIMS[0] + (y) * DIMS[0] + (x) )

// 2) Compute size of 3D image
#define ndims(DIMS) ( DIMS[0] * DIMS[1] * DIMS[2] )

// Convert linear index to [x y z] coordinates
std::vector<int> index2xyz(int index, std::vector<int>& DIMS)
{
    std::vector<int> XYZ;
    XYZ.reserve(3);
    XYZ.push_back(index % DIMS[0]);  // x
    XYZ.push_back((index / DIMS[0]) % DIMS[1]);  // y
    XYZ.push_back(index / (DIMS[0] * DIMS[1]));  // z

    return XYZ;
}


// Convert several voxel indices to an xyz-coordinate matrix
std::vector<std::vector<int> > ids2xyz(std::vector<int>& IDS, std::vector<int>& DIMS)
{
    std::vector<std::vector<int> > XYZS(IDS.size(), std::vector<int>(3));
    for (size_t i = 0; i < IDS.size(); i++)
    {
        std::vector<int> XYZ = index2xyz(IDS[i], DIMS);
        XYZS[i][0] = XYZ[0];
        XYZS[i][1] = XYZ[1];
        XYZS[i][2] = XYZ[2];
    }

    return XYZS;
}

// Check if a voxel is in the mask
bool xyz_check(int x, int y, int z, int index, std::vector<int>& DIMS, std::vector<int>& MASK)
{
    return (x >= 0 && x < DIMS[0] &&  // C order: x corresponds to the first dimension
            y >= 0 && y < DIMS[1] &&  // y corresponds to the second dimension
            z >= 0 && z < DIMS[2] &&  // z corresponds to the third dimension
            MASK[index] != 0);
}

// Find valid neighbours of a voxel
std::vector<int> findNeighbours(std::vector<int>& MASK, std::vector<int>& DIMS, int index, int conn)
{
    // compute [x y z] coordinates based on voxel index
    std::vector<int> XYZ = index2xyz(index, DIMS);
    
    // xyz coordinate adjustment vectors
    // Coordinate adjustment vectors for finding neighbors in a 3D grid.
        // These vectors represent the relative offsets to move from a given voxel 
        // to its neighboring voxels. Each triplet (DX[i], DY[i], DZ[i]) specifies 
        // a direction to a neighboring voxel.
        //
        // The 26 possible directions correspond to the neighbors in 26-connectivity:
        // - 6-connectivity: includes only the voxels that share a face with the central voxel (6 neighbors).
        // - 18-connectivity: includes the voxels that share an edge or a face with the central voxel (18 neighbors).
        // - 26-connectivity: includes the voxels that share a vertex, an edge, or a face with the central voxel (26 neighbors).
        //
        // Example offsets:
        // - (1, 0, 0)   : move one step in the x-direction (right neighbor)
        // - (-1, 0, 0)  : move one step in the negative x-direction (left neighbor)
        // - (0, 1, 0)   : move one step in the y-direction (front neighbor)
        // - (0, -1, 0)  : move one step in the negative y-direction (back neighbor)
        // - (0, 0, 1)   : move one step in the z-direction (top neighbor)
        // - (0, 0, -1)  : move one step in the negative z-direction (bottom neighbor)
        // - (1, 1, 0)   : move one step in both the x and y directions (diagonal neighbor in the xy-plane)
        // - (-1, 1, 0)  : move one step in the negative x direction and one step in the y direction (another diagonal neighbor in the xy-plane)
        // - (1, 0, 1)   : move one step in the x direction and one step in the z direction (diagonal neighbor in the xz-plane)
        // - (0, 1, 1)   : move one step in the y direction and one step in the z direction (diagonal neighbor in the yz-plane)
        // - (1, 1, 1)   : move one step in all three directions (diagonal neighbor in the 3D space)
        //
        // These vectors are used in the findNeighbours function to iterate through
        // all potential neighbors of a voxel by simply adding these offsets to the voxel's coordinates.
    int DX[26] = {1,-1,0, 0,0, 0,  1,-1, 1,-1,1,-1, 1,-1,0, 0, 0, 0,  1,-1, 1,-1, 1,-1, 1,-1};
    int DY[26] = {0, 0,1,-1,0, 0,  1, 1,-1,-1,0, 0, 0, 0,1,-1, 1,-1,  1, 1,-1,-1, 1, 1,-1,-1};
    int DZ[26] = {0, 0,0, 0,1,-1,  0, 0, 0, 0,1, 1,-1,-1,1, 1,-1,-1,  1, 1, 1, 1,-1,-1,-1,-1};
    
    // find all valid neighbours of a voxel
    std::vector<int> IDS(conn);
    int len = 0;
    for (int i = 0; i < conn; i++)
    {
        int id = xyz2index(XYZ[0]+DX[i], XYZ[1]+DY[i], XYZ[2]+DZ[i], DIMS);
        bool inmask = xyz_check(XYZ[0]+DX[i], XYZ[1]+DY[i], XYZ[2]+DZ[i], id, DIMS, MASK);
        if (inmask)
        {
            IDS[len] = MASK[id];
            len++;
        }
    }
    
    if (len < conn)
    {
        IDS.resize(len);
    }
    
    return IDS;
}

// Find the adjacency list for all in-mask voxels
// This function computes the adjacency list for all in-mask voxels based on the given 3D mask,
// voxel indices, image dimensions, and connectivity criterion. The adjacency list represents
// the neighboring voxels for each voxel in the mask.

std::vector<std::vector<int> > findAdjList(std::vector<int>& MASK,    // 3D mask of original orders (1:m)
                                           std::vector<int>& INDEXP,  // Voxel indices of unsorted p-values
                                           std::vector<int>& DIMS,    // Image dimensions (width, height, depth)
                                           int m,                     // Number of in-mask voxels
                                           int conn)                  // Connectivity criterion (e.g., 6, 18, or 26)
{
    // Initialize the adjacency list with 'm' empty vectors
    // Each entry in ADJ will be a list of neighbors for a corresponding voxel
    std::vector<std::vector<int> > ADJ(m);

    // Loop through all in-mask voxels
    for (int i = 0; i < m; i++)
    {
        // Find the neighboring voxels for the current voxel (INDEXP[i])
        // The function findNeighbours returns a list of indices of neighboring voxels
        std::vector<int> IDS = findNeighbours(MASK, DIMS, INDEXP[i], conn);
        
        // Store the list of neighbors in the adjacency list at position 'i'
        ADJ[i] = IDS;
    }

    // Return the computed adjacency list
    return ADJ;
}


//-------------------------- NEWLY ADDED: (5) CHANGE CLUSTER SIZE --------------------------//

// Find the index of the cluster that contains voxel v in cluster list ANS
// Return -1 if no such cluster exists
int findRep(int v, const std::vector<int>& SIZE, const std::vector<std::vector<int> >& ANS) {
    for (size_t i = 0; i < ANS.size(); ++i) {
        const std::vector<int>& CLUS = ANS[i];
        int irep = CLUS[CLUS.size() - 1];  // Representative of the cluster

        // Check if the representative matches the voxel
        if (irep == v) {
            return i;
        }

        // Check subtree sizes
        if (SIZE[irep] > SIZE[v]) {
            int left = 0;
            int right = CLUS.size() - 1;

            // Perform a linear search
            while (left <= right) {
                if (CLUS[left] == v) {
                    return i;
                }
                left++;
                if (CLUS[right] == v) {
                    return i;
                }
                right--;
            }
        }
    }
    return -1;
}


// Find the index of a cluster in a cluster list (with no duplicate elements)
// Return -1 if no such index exists
int findIndex(int irep, const std::vector<int>& ADMSTC, const std::vector<double>& TDP) {
    int left = 0;
    int right = static_cast<int>(ADMSTC.size()) - 1;  // Explicit cast for size()
    int low = left;
    int high = right;

    while (low <= high) {
        int mid = (low + high) / 2;  // Binary search part
        if (TDP[ADMSTC[mid]] > TDP[irep]) {
            high = mid - 1;
        } else if (TDP[ADMSTC[mid]] < TDP[irep]) {
            low = mid + 1;
        } else {
            return mid;
        }

        // Linear search part
        if (ADMSTC[right] == irep) {
            return right;
        }
        right--;
        if (ADMSTC[left] == irep) {
            return left;
        }
        left++;
    }

    return -1;
}



// // Change the query, i.e., enlarge or shrink the chosen cluster
// std::vector<std::vector<int> > changeQuery(
//     int ix,                                     // 1-based index of cluster in ANS
//     double tdpchg,                              // Expected change in TDP
//     const std::vector<int>& ADMSTC,             // Admissible vertices
//     std::vector<int>& SIZE,                     // Subtree sizes
//     std::vector<int>& MARK,                     // Mark nodes
//     const std::vector<double>& TDP,             // All TDP bounds
//     std::vector< std::vector<int> >& CHILD,     // Children list
//     const std::vector<std::vector<int> >& ANS   // Clusters
// ) {
//     std::vector<std::vector<int> > CHG;  // Initialize the output list of clusters

//     // Get the cluster to process
//     const std::vector<int>& CLUS = ANS[ix - 1];

//     // Mark all nodes in the cluster
//     for (size_t i = 0; i < CLUS.size(); ++i) {
//         int node = CLUS[i];
//         MARK[node] = 1;
//     }

//     // Find the index of the cluster representative in ADMSTC
//     int idxv = findIndex(CLUS[CLUS.size() - 1], ADMSTC, TDP);

//     if (tdpchg < 0) {  // Increase cluster size (decrease TDP)
//         for (int i = idxv - 1; i >= 0; --i) {
//             if (TDP[ADMSTC[i]] >= 0 && TDP[ADMSTC[i]] - TDP[ADMSTC[idxv]] <= tdpchg &&
//                 SIZE[ADMSTC[i]] > SIZE[ADMSTC[idxv]]) {
//                 std::vector<int> DESC = descendants(ADMSTC[i], SIZE, CHILD);
//                 for (size_t j = 0; j < DESC.size(); ++j) {
//                     if (MARK[DESC[j]] > 0) {
//                         CHG.push_back(DESC);
//                         for (size_t k = 0; k < CLUS.size(); ++k) {
//                             MARK[CLUS[k]] = 0;
//                         }
//                         return CHG;
//                     }
//                 }
//             }
//         }
//     } else {  // Decrease cluster size (increase TDP)
//         for (int i = idxv + 1; i < (int)ADMSTC.size(); ++i) {
//             if (TDP[ADMSTC[i]] >= 0 && TDP[ADMSTC[i]] - TDP[ADMSTC[idxv]] >= tdpchg && MARK[ADMSTC[i]] == 1) {
//                 std::vector<int> DESC = descendants(ADMSTC[i], SIZE, CHILD);
//                 CHG.push_back(DESC);
//                 for (size_t j = 0; j < DESC.size(); ++j) {
//                     MARK[DESC[j]] = 2;
//                 }
//             }
//         }
//     }

//     // Clear marks
//     for (size_t i = 0; i < CLUS.size(); ++i) {
//         MARK[CLUS[i]] = 0;
//     }

//     if (CHG.empty()) {
//         CHG.push_back(CLUS);
//     }
//     return CHG;
// }
std::vector<std::vector<int> > changeQuery(
    int v,                              // 0-based node index
    double tdpchg,                      // Used to specify an expected change in TDP. A positive value indicates increasing the TDP bound or reducing the current cluster size.
    const std::vector<int>& ADMSTC,     // Admissible vertices (sorted by TDP)
    std::vector<int>& SIZE,             // Subtree sizes for all nodes
    std::vector<int>& MARK,             // Node markers, used to mark the nodes
    const std::vector<double>& TDP,     // All TDP bounds
    std::vector<std::vector<int> >& CHILD, // Children list for all vertices
    const std::vector<std::vector<int> >& ANS) // Cluster list, normally, the output of calling the function answerQuery()
{
    // Initialise output: a list of clusters
    std::list<std::vector<int> > CHG;

    // Check for v
    if (v < 0) throw std::invalid_argument("'v' should be non-negative");

    // Find the cluster that contains v
    int iclus = findRep(v, SIZE, ANS);
    if (iclus < 0) throw std::invalid_argument("No cluster can be specified with 'v'");
    const std::vector<int>& CLUS = ANS[iclus];

    // Find the index of the cluster representative in ADMSTC
    int idxv = findIndex(CLUS[CLUS.size() - 1], ADMSTC, TDP);
    if (idxv < 0) throw std::invalid_argument("The chosen cluster cannot be found in 'ADMSTC'");

    // Check the TDP change value
    if (tdpchg <= -1 || tdpchg == 0 || tdpchg >= 1) throw std::invalid_argument("'tdpchg' must be non-zero & within (-1,1)");

    // Check for max(TDP), min(TDP) & curr(TDP)
    double maxtdp = TDP[ADMSTC[ADMSTC.size() - 1]];
    double mintdp = TDP[ADMSTC[0]];
    double curtdp = TDP[CLUS[CLUS.size() - 1]];

    if ((tdpchg < 0 && mintdp == curtdp) || (tdpchg > 0 && maxtdp == curtdp)) {
        throw std::invalid_argument("No further changes can be attained");
    }

    if (tdpchg < 0 && mintdp - curtdp > tdpchg) {
        throw std::invalid_argument("A further TDP reduction cannot be achieved");
    }

    if (tdpchg > 0 && maxtdp - curtdp < tdpchg) {
        throw std::invalid_argument("A further TDP augmentation cannot be achieved");
    }

    // Mark all nodes within the cluster
    for (int j = 0; j < CLUS.size(); j++) {
        MARK[CLUS[j]] = 1;
    }

    if (tdpchg < 0) {  // Increase size (OR decrease TDP) of the cluster
        for (int i = idxv - 1; i >= 0; i--) {
            if (TDP[ADMSTC[i]] >= 0 && TDP[ADMSTC[i]] - TDP[ADMSTC[idxv]] <= tdpchg && SIZE[ADMSTC[i]] > SIZE[ADMSTC[idxv]]) {
                std::vector<int> DESC = descendants(ADMSTC[i], SIZE, CHILD);

                int left = 0;
                int right = DESC.size() - 1;
                while (left <= right) {
                    if (MARK[DESC[left]] > 0 || MARK[DESC[right]] > 0) {
                        CHG.push_back(DESC);

                        // Append remaining clusters to CHG
                        int dfsz = DESC.size() - CLUS.size();
                        for (int j = 0; j < ANS.size(); j++) {  // <<<<< UNTOUCHED LOOP
                            if (j != iclus) {
                                const std::vector<int>& CL = ANS[j];

                                if (dfsz >= CL.size()) {
                                    for (int k = 0; k < CL.size(); k++) {
                                        MARK[CL[k]] = 2;
                                    }

                                    // Check if DESC contains CL
                                    int l = 0;
                                    int r = DESC.size() - 1;
                                    while (r - l >= CL.size() - 1) {
                                        if (MARK[DESC[l]] == 2 || MARK[DESC[r]] == 2) {
                                            dfsz = dfsz - CL.size();
                                            break;
                                        }
                                        l++;
                                        r--;
                                    }

                                    // Append CL to CHG if DESC does not contain CL
                                    if (l > DESC.size() - 1 || r < 0 || (MARK[DESC[l]] != 2 && MARK[DESC[r]] != 2)) {
                                        CHG.push_back(CL);
                                    }

                                    for (int k = 0; k < CL.size(); k++) {
                                        MARK[CL[k]] = 0;
                                    }
                                } else {
                                    CHG.push_back(CL);
                                }
                            }
                        }

                        // Clear marks back to 0
                        for (int j = 0; j < CLUS.size(); j++) {
                            MARK[CLUS[j]] = 0;
                        }

                        return std::vector<std::vector<int> >(CHG.begin(), CHG.end());
                    }
                    left++;
                    right--;
                }
            }
        }
    } else {  // Decrease size (OR increase TDP) of the cluster
        for (int i = idxv + 1; i < ADMSTC.size(); i++) {
            if (TDP[ADMSTC[i]] >= 0 && TDP[ADMSTC[i]] - TDP[ADMSTC[idxv]] >= tdpchg && MARK[ADMSTC[i]] == 1) {
                std::vector<int> DESC = descendants(ADMSTC[i], SIZE, CHILD);
                CHG.push_back(DESC);

                for (int j = 0; j < DESC.size(); j++) {
                    MARK[DESC[j]] = 2;
                }
            }
        }

        // Append remaining clusters to CHG
        for (int j = 0; j < ANS.size(); j++) {  // <<<<< UNTOUCHED LOOP
            if (j != iclus) {
                CHG.push_back(ANS[j]);
            }
        }
    }

    // Clear marks back to 0
    for (int j = 0; j < CLUS.size(); j++) {
        MARK[CLUS[j]] = 0;
    }

    return std::vector<std::vector<int> >(CHG.begin(), CHG.end());
}

// Find all local minima (leaves of the constructed forest)
std::vector<int> findLMS(const std::vector<std::vector<int> >& CHILD) {
    std::vector<int> LMS;
    for (int i = 0; i < static_cast<int>(CHILD.size()); i++) {  // Use explicit type cast for size()
        if (CHILD[i].size() == 0) {  // Replace empty() with size() check
            LMS.push_back(i);
        }
    }
    return LMS;
}

