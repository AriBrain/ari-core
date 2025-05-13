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
        int v = ORD[i];
        
        // Find neighbours for node with the ith smallest p-value
        std::vector<int>& IDS = ADJ[v];
        
        // Loop through all its neighbours
        for (size_t j = 0; j < IDS.size(); j++)
        {
            if (RANK[IDS[j]] < i + 1)  // Check if the neighbour has a smaller rank
            {
                int jrep = Find(IDS[j], PARENT);  // Representative of the tree
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
    // result.push_back(std::vector<int>()); // Placeholder for CHILD, will be merged later
    // result.insert(result.end(), CHILD.begin(), CHILD.end());
    // result.push_back(std::vector<int>(ROOT.begin(), ROOT.end()));
    // result.push_back(SIZE);
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
    std::vector<int> DESC(SIZE[v], 0);
    
    int len = 0;  // Track the number of found descendants
    int top = SIZE[v] - 1;  // Track the top of the stack
    DESC[top] = v;  // Push v on the stack (stack grows from right to left)
    
    while (top < static_cast<int>(DESC.size()))  // While stack is non-empty  // While stack is non-empty
    {
        v = DESC[top];  // Pop the top of the stack
        top++;
        if (v < 0)  // If ~v is a value, append ~v to the descendants
        {
            DESC[len] = ~v;  // Bitwise negation is used as minus doesn't work for zero
            len++;
        }
        else
        {
            top--;
            DESC[top] = ~v;  // Push v as a value
            
            // Push all children in reverse order
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

// // Compute the TDP bounds of the heavy path starting at v
// void heavyPathTDP(int v, int par, int m, int h, double alpha, double simesh, std::vector<double>& P, std::vector<int>& SIZE, std::vector< std::vector<int> >& CHILD, std::vector<double>& TDP)
// {
//     std::vector<int> HP = descendants(v, SIZE, CHILD);
//     for (size_t i = 0; i < HP.size(); i++)
//     {
//         HP[i]++;
//     }

    
//     std::vector<int> NUM = findDiscoveries(HP, P, simesh, h, alpha, HP.size(), m);
    
//     while (true)  // Walk down the heavy path
//     {
//         // Check if v represents an STC
//         if (par == -1 || P[v] != P[par])
//         {
//             TDP[v] = static_cast<double>(NUM[SIZE[v]]) / static_cast<double>(SIZE[v]);
//         }
//         else
//         {
//             TDP[v] = -1;  // Invalid STCs get TDP of -1
//         }

//         // Check if v is a leaf
//         if (SIZE[v] == 1) break;
        
//         // Update v & its parent
//         par = v;
//         std::vector<int>& CHD = CHILD[v];
//         v = CHD[0];
//     }
// }

// Find the start of every heavy path & compute the TDPs of that heavy path
// Start of heavy path: 1) root of F; 2) non-root node that is not the 1st heavy child
// std::vector<double> forestTDP(int m, int h, double alpha, double simesh, std::vector<double>& P, std::vector<int>& SIZE, std::vector<int>& ROOT, std::vector< std::vector<int> >& CHILD)
// {
//     std::vector<double> TDP(m);
    
//     // Loop through all roots
//     for (size_t i = 0; i < ROOT.size(); i++)
//     {
//         heavyPathTDP(ROOT[i], -1, m, h, alpha, simesh, P, SIZE, CHILD, TDP);
//     }
//     // Loop through all nodes
//     for (int i = 0; i < m; i++)
//     {
//         std::vector<int>& CHD = CHILD[i];
//         for (size_t j = 1; j < CHD.size(); j++)
//         {
//             heavyPathTDP(CHD[j], i, m, h, alpha, simesh, P, SIZE, CHILD, TDP);
//         }
//     }

//     return TDP;
// }

// // Compute the TDP bounds of the heavy path starting at v
// void heavyPathTDP(int v, int par, int m, int h, double alpha, double simesh, std::vector<double>& P, std::vector<int>& SIZE, std::vector< std::vector<int> >& CHILD, std::vector<double>& TDP)
// {
//     // std::cout << "Entering heavyPathTDP function for node " << v << " with parent " << par << std::endl;

//     std::vector<int> HP = descendants(v, SIZE, CHILD);
//     // std::cout << "Descendants of node " << v << " computed with size " << HP.size() << std::endl;

//     // The increment here was originally for converting from 1-based to 0-based.
//     // This may not be necessary depending on the specific context. Uncomment if needed.
//     // for (size_t i = 0; i < HP.size(); i++)
//     // {
//     //     HP[i]++;
//     // }

//     std::vector<int> NUM = findDiscoveries(HP, P, simesh, h, alpha, HP.size(), m);
//     // std::cout << "Discoveries for node " << v << " computed" << std::endl;

//     while (true)  // Walk down the heavy path
//     {
//         // std::cout << "Processing node " << v << " in heavy path" << std::endl;

//         // Check if v represents an STC
//         if (par == -1 || P[v] != P[par])
//         {
//             TDP[v] = static_cast<double>(NUM[SIZE[v]]) / static_cast<double>(SIZE[v]);
//             // std::cout << "TDP for node " << v << " set to " << TDP[v] << std::endl;
//         }
//         else
//         {
//             TDP[v] = -1;  // Invalid STCs get TDP of -1
//             // std::cout << "TDP for node " << v << " set to -1 (invalid STC)" << std::endl;
//         }

//         // Check if v is a leaf
//         if (SIZE[v] == 1) {
//             // std::cout << "Node " << v << " is a leaf, breaking the loop" << std::endl;
//             break;
//         }
        
//         // Update v & its parent
//         par = v;
//         std::vector<int>& CHD = CHILD[v];
//         if (CHD.empty()) {
//             std::cerr << "Error: Node " << v << " has no children, but SIZE[v] != 1" << std::endl;
//             break;
//         }
//         v = CHD[0];
//         // std::cout << "Moving to child node " << v << std::endl;
//     }

//     // std::cout << "Exiting heavyPathTDP function for node " << v << std::endl;
// }

void heavyPathTDP(int v, int par, int m, int h, double alpha, double simesh, std::vector<double>& P, std::vector<int>& SIZE, std::vector< std::vector<int> >& CHILD, std::vector<double>& TDP)
{
    static std::ofstream logFile("heavyPathTDP_log.txt", std::ios::app);
    static int callCount = 0;
    static const int LOG_FREQUENCY = 1000;  // Log every 1000th call

    callCount++;

    if (callCount % LOG_FREQUENCY == 0) {
        logFile << "Call #" << callCount << " - v: " << v << ", par: " << par << std::endl;
    }

    std::vector<int> HP = descendants(v, SIZE, CHILD);

    std::vector<int> NUM = findDiscoveries(HP, P, simesh, h, alpha, HP.size(), m);

    if (callCount % LOG_FREQUENCY == 0) {
        logFile << "  HP size: " << HP.size() << ", NUM size: " << NUM.size() << std::endl;
    }

    while (true)  // Walk down the heavy path
    {
        // Check if v represents an STC
        if (par == -1 || P[v] != P[par])
        {
            TDP[v] = static_cast<double>(NUM[SIZE[v]]) / static_cast<double>(SIZE[v]);
            
            if (callCount % LOG_FREQUENCY == 0) {
                logFile << "  v: " << v << ", SIZE[v]: " << SIZE[v] << ", NUM[SIZE[v]]: " << NUM[SIZE[v]] << ", TDP[v]: " << TDP[v] << std::endl;
            }

            // Log any extreme values
            if (TDP[v] > 1000 || TDP[v] < 0) {
                logFile << "WARNING: Extreme TDP value - v: " << v << ", TDP[v]: " << TDP[v] << ", SIZE[v]: " << SIZE[v] << ", NUM[SIZE[v]]: " << NUM[SIZE[v]] << std::endl;
            }
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
        std::vector<int>& CHD = CHILD[v];
        if (CHD.empty()) {
            logFile << "ERROR: Node " << v << " has no children, but SIZE[v] != 1" << std::endl;
            break;
        }
        v = CHD[0];
    }

    if (callCount % LOG_FREQUENCY == 0) {
        logFile << "  Finished processing heavy path" << std::endl;
    }
}

std::vector<double> forestTDP(int m, int h, double alpha, double simesh, std::vector<double>& P, std::vector<int>& SIZE, std::vector<int>& ROOT, std::vector< std::vector<int> >& CHILD)
{
    // std::cout << "Entering forestTDP function" << std::endl;  // Log entry to function
    std::vector<double> TDP(m);

    // Loop through all roots
    for (size_t i = 0; i < ROOT.size(); i++)
    {
        // if (i % 1000 == 0) {  // Log every 1000th root
        //     std::cout << "Processing root " << i << " with value " << ROOT[i] << std::endl;
        // }
        heavyPathTDP(ROOT[i], -1, m, h, alpha, simesh, P, SIZE, CHILD, TDP);
    }
    
    // Loop through all nodes
    for (int i = 0; i < m; i++)
    {
        std::vector<int>& CHD = CHILD[i];
        // if (i % 1000 == 0) {  // Log every 1000th node
        //     std::cout << "Processing node " << i << " with " << CHD.size() << " children" << std::endl;
        // }
        for (size_t j = 1; j < CHD.size(); j++)
        {
            // if (j % 1000 == 0) {  // Log every 1000th child
            //     std::cout << "Processing child " << j << " of node " << i << " with value " << CHD[j] << std::endl;
            // }
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

// Set up ADMSTC: a list of representative of admissible STCs
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
        // No need to guard against right<0 as right>=0 will always be true
        if (TDP[ADMSTC[right]] < gamma) return (right + 1);
    }
    
    return low;
}

// Answer the query, i.e., find maximal STCs under the TDP condition.
// gamma >= 0 is needed because inadmissible STCs have been assigned TDP -1.
std::vector< std::vector<int> > answerQuery(double gamma, std::vector<int>& ADMSTC, std::vector<int>& SIZE, std::vector<int>& MARK, std::vector<double>& TDP, std::vector< std::vector<int> >& CHILD)
{
    if (gamma < 0) gamma = 0;  // Constrain TDP threshold gamma to be non-negative
    
    // Initialise output: a list of sorting rank vectors for all clusters
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

    std::vector< std::vector< std::vector<int> > > answerQueryBatch_opt(
        std::vector<double>& gamma_batch, std::vector<int>& ADMSTC,
        std::vector<int>& SIZE, std::vector<int>& MARK, 
        std::vector<double>& TDP, std::vector< std::vector<int> >& CHILD) 
    {
        std::vector< std::vector< std::vector<int> > > batch_results;
        batch_results.reserve(gamma_batch.size());

        for (size_t i = 0; i < gamma_batch.size(); ++i) {
            double gamma = std::max(0.0, gamma_batch[i]); // Constrain TDP threshold gamma to be non-negative

            std::vector< std::vector<int> > result;
            result.reserve(ADMSTC.size());  // Pre-reserve space

            int left = findLeft(gamma, ADMSTC, TDP);

            for (size_t j = left; j < ADMSTC.size(); ++j) {
                if (MARK[ADMSTC[j]] == 0) {
                    // Collect descendants
                    std::vector<int> DESC = descendants(ADMSTC[j], SIZE, CHILD);
                    result.push_back(DESC);

                    // Mark the corresponding voxels
                    for (size_t k = 0; k < DESC.size(); ++k) {
                        MARK[DESC[k]] = 1;
                    }
                }
            }

            // Clear marks back to 0
            for (size_t j = 0; j < result.size(); ++j) {
                for (size_t k = 0; k < result[j].size(); ++k) {
                    MARK[result[j][k]] = 0;
                }
            }

            batch_results.push_back(result);
        }

        return batch_results;
    }

// This function is not used currently, it could be a solution to the choking. My hunch is that this operation is creating overhead
// when run on large data sets. So the potential solution could be to run it in chuncks instead. 
// Parallel Processing: Chunking naturally lends itself to parallel processing. Each chunk can be processed independently in parallel, 
// potentially leading to significant performance improvements on multi-core systems. This approach can also distribute the workload 
// more evenly across available resources.
std::vector<std::vector<std::vector<int> > > answerQueryInChunks(
    std::vector<double>& gamma_batch, std::vector<int>& ADMSTC, std::vector<int>& SIZE, 
    std::vector<int>& MARK, std::vector<double>& TDP, std::vector<std::vector<int> >& CHILD, 
    size_t chunk_size)
{
    std::vector<std::vector<std::vector<int> > > batch_results;
    size_t total_gammas = gamma_batch.size();

    for (size_t start = 0; start < total_gammas; start += chunk_size) {
        size_t end = std::min(start + chunk_size, total_gammas);
        std::vector<double> gamma_chunk(gamma_batch.begin() + start, gamma_batch.begin() + end);

        // Process this chunk
        std::vector<std::vector<std::vector<int> > > chunk_results = answerQueryBatch(
            gamma_chunk, ADMSTC, SIZE, MARK, TDP, CHILD);

        // Combine results
        batch_results.insert(batch_results.end(), chunk_results.begin(), chunk_results.end());
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