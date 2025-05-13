#ifndef ARICLUSTER_H
#define ARICLUSTER_H

#include <vector>
#include <stack>

std::vector<int> descendants(int v, std::vector<int>& SIZE, std::vector< std::vector<int> >& CHILD);

void heavyPathTDP(int v, int par, int m, int h, double alpha, double simesh, std::vector<double>& P, std::vector<int>& SIZE, std::vector< std::vector<int> >& CHILD, std::vector<double>& TDP);
std::vector<double> forestTDP(int m, int h, double alpha, double simesh, std::vector<double>& P, std::vector<int>& SIZE, std::vector<int>& ROOT, std::vector< std::vector<int> >& CHILD);
std::vector<std::vector<int> > findClusters(int m, std::vector< std::vector<int> >& ADJ, std::vector<int>& ORD, std::vector<int>& RANK);
std::vector<int> queryPreparation(int m, std::vector<int>& ROOT, std::vector<double>& TDP, std::vector< std::vector<int> >& CHILD);
int findLeft(double gamma, std::vector<int>& ADMSTC, std::vector<double>& TDP);

std::vector< std::vector<int> > answerQuery(double gamma, std::vector<int>& ADMSTC, std::vector<int>& SIZE, std::vector<int>& MARK, std::vector<double>& TDP, std::vector< std::vector<int> >& CHILD);

std::vector< std::vector< std::vector<int> > > answerQueryBatch(std::vector<double>& gamma_batch, std::vector<int>& ADMSTC, std::vector<int>& SIZE, std::vector<int>& MARK, std::vector<double>& TDP, std::vector< std::vector<int> >& CHILD);

// std::vector< std::vector< std::vector<int> > > answerQueryBatch_opt(
//     std::vector<double>& gamma_batch, std::vector<int>& ADMSTC, 
//     std::vector<int>& SIZE, std::vector<int>& MARK, 
//     std::vector<double>& TDP, std::vector< std::vector<int> >& CHILD);

// std::vector<std::vector<std::vector<int> > > answerQueryInChunks(
//     std::vector<double>& gamma_batch, std::vector<int>& ADMSTC, std::vector<int>& SIZE, 
//     std::vector<int>& MARK, std::vector<double>& TDP, std::vector<std::vector<int> >& CHILD, 
//     size_t chunk_size);

std::vector<int> counting_sort(int n, int maxid, std::vector<int>& CLSTRSIZE);

std::vector<int> index2xyz(int index, std::vector<int>& DIMS);
std::vector<std::vector<int> > ids2xyz(std::vector<int>& IDS, std::vector<int>& DIMS);
bool xyz_check(int x, int y, int z, int index, std::vector<int>& DIMS, std::vector<int>& MASK);
std::vector<int> findNeighbours(std::vector<int>& MASK, std::vector<int>& DIMS, int index, int conn);
std::vector<std::vector<int> > findAdjList(std::vector<int>& MASK, std::vector<int>& INDEXP, std::vector<int>& DIMS, int m, int conn);

std::vector<int> findDiscoveries_one_based(const std::vector<int>& idx, const std::vector<double>& allp, double simesfactor, int h, double alpha, int k, int m);
int findConcentration_one_based(const std::vector<double>& p, double simesfactor, int h, double alpha, int m);


// int findIndex(int irep, const std::vector<int>& ADMSTC, const std::vector<double>& TDP);
// std::vector<std::vector<int> > changeQuery(
//     int ix, double tdpchg, const std::vector<int>& ADMSTC, std::vector<int>& SIZE,
//     std::vector<int>& MARK, const std::vector<double>& TDP, 
//     std::vector<std::vector<int> >& CHILD, const std::vector<std::vector<int> >& ANS);

// Find the index of the cluster that contains voxel v in the cluster list ANS
int findRep(int v, const std::vector<int>& SIZE, const std::vector<std::vector<int> >& ANS);

// Find the index of a cluster in a cluster list (with no duplicate elements)
// Returns -1 if no such index exists
int findIndex(int irep, const std::vector<int>& ADMSTC, const std::vector<double>& TDP);

// Change the query, i.e., enlarge or shrink the chosen cluster
std::vector<std::vector<int> > changeQuery(
    int v,                             // 0-based node index
    double tdpchg,                     // Expected change in TDP
    const std::vector<int>& ADMSTC,    // Admissible vertices
    std::vector<int>& SIZE,            // Subtree sizes
    std::vector<int>& MARK,            // Mark nodes
    const std::vector<double>& TDP,    // TDP bounds
    std::vector<std::vector<int> >& CHILD, // Children list
    const std::vector<std::vector<int> >& ANS // Clusters
);

std::vector<int> findLMS(const std::vector<std::vector<int> >& CHILD);

#endif // ARICLUSTER_H