# ARICluster.pyx
# distutils: language = c++
# cython: language_level=3

from libcpp.vector cimport vector
from libcpp cimport bool
from cython.operator cimport dereference as deref

cdef extern from "../cpp_sources/ARICluster.h":
    vector[int] descendants(int v, vector[int]& SIZE, vector[vector[int]]& CHILD)
    void heavyPathTDP(int v, int par, int m, int h, double alpha, double simesh, vector[double]& P, vector[int]& SIZE, vector[vector[int]]& CHILD, vector[double]& TDP)
    vector[double] forestTDP(int m, int h, double alpha, double simesh, vector[double]& P, vector[int]& SIZE, vector[int]& ROOT, vector[vector[int]]& CHILD)
    
    vector[vector[int]] findClusters(int m, vector[vector[int]]& ADJ, vector[int]& ORD, vector[int]& RANK)

    vector[int] queryPreparation(int m, vector[int]& ROOT, vector[double]& TDP, vector[vector[int]]& CHILD)
    int findLeft(double gamma, vector[int]& ADMSTC, vector[double]& TDP)
    
    vector[vector[int]] answerQuery(double gamma, vector[int]& ADMSTC, vector[int]& SIZE, vector[int]& MARK, vector[double]& TDP, vector[vector[int]]& CHILD)
    vector[vector[vector[int]]] answerQueryBatch(vector[double]& gamma_batch, vector[int]& ADMSTC, vector[int]& SIZE, vector[int]& MARK, vector[double]& TDP, vector[vector[int]]& CHILD)
    vector[vector[vector[int]]] answerQueryBatch_opt(vector[double]& gamma_batch, vector[int]& ADMSTC, vector[int]& SIZE, vector[int]& MARK, vector[double]& TDP, vector[vector[int]]& CHILD)

    vector[vector[vector[int]]] answerQueryInChunks(vector[double]& gamma_batch, vector[int]& ADMSTC, vector[int]& SIZE, vector[int]& MARK, vector[double]& TDP, vector[vector[int]]& CHILD, size_t chunk_size)
    
    vector[int] counting_sort(int n, int maxid, vector[int]& CLSTRSIZE)

    vector[int] index2xyz(int index, vector[int]& DIMS)
    vector[vector[int]] ids2xyz(vector[int]& IDS, vector[int]& DIMS)
    bool xyz_check(int x, int y, int z, int index, vector[int]& DIMS, vector[int]& MASK)
    vector[int] findNeighbours(vector[int]& MASK, vector[int]& DIMS, int index, int conn)
    vector[vector[int]] findAdjList(vector[int]& MASK, vector[int]& INDEXP, vector[int]& DIMS, int m, int conn)
   
    vector[int] findDiscoveries_one_based(const vector[int]& idx, const vector[double]& allp, double simesfactor, int h, double alpha, int k, int m)
    int findConcentration_one_based(const vector[double]& p, double simesfactor, int h, double alpha, int m)

    int findIndex(int irep, const vector[int]& ADMSTC, const vector[double]& TDP)
    cdef vector[vector[int]] changeQuery(int ix, double tdpchg, const vector[int]& ADMSTC,
                                     vector[int]& SIZE, vector[int]& MARK,
                                     const vector[double]& TDP, vector[vector[int]]& CHILD,
                                     const vector[vector[int]]& ANS)
    vector[int] findLMS(const vector[vector[int]]& CHILD)

def py_descendants(int v, list SIZE, list CHILD):
    cdef vector[int] SIZE_vector = SIZE
    cdef vector[vector[int]] CHILD_vector = [vector[int]() for _ in CHILD]
    for i, child in enumerate(CHILD):
        CHILD_vector[i] = child
    cdef vector[int] result = descendants(v, SIZE_vector, CHILD_vector)
    return list(result)

def py_heavyPathTDP(int v, int par, int m, int h, double alpha, double simesh, list P, list SIZE, list CHILD, list TDP):
    cdef vector[double] P_vector = P
    cdef vector[int] SIZE_vector = SIZE
    cdef vector[vector[int]] CHILD_vector = [vector[int]() for _ in CHILD]
    for i, child in enumerate(CHILD):
        CHILD_vector[i] = child
    cdef vector[double] TDP_vector = TDP
    heavyPathTDP(v, par, m, h, alpha, simesh, P_vector, SIZE_vector, CHILD_vector, TDP_vector)

def py_forestTDP(int m, int h, double alpha, double simesh, list P, list SIZE, list ROOT, list CHILD):
    cdef vector[double] P_vector = P
    cdef vector[int] SIZE_vector = SIZE
    cdef vector[int] ROOT_vector = ROOT
    cdef vector[vector[int]] CHILD_vector = [vector[int]() for _ in CHILD]
    for i, child in enumerate(CHILD):
        CHILD_vector[i] = child

    cdef vector[double] result = forestTDP(m, h, alpha, simesh, P_vector, SIZE_vector, ROOT_vector, CHILD_vector)
    
    return list(result)

def py_findClusters(int m, list ADJ, list ORD, list RANK):

    cdef vector[vector[int]] ADJ_vector = [vector[int]() for _ in ADJ]
    for i in range(len(ADJ)):
        ADJ_vector[i] = ADJ[i]
    cdef vector[int] ORD_vector = ORD
    cdef vector[int] RANK_vector = RANK

    cdef vector[vector[int]] result = findClusters(m, ADJ_vector, ORD_vector, RANK_vector)

    # Extract SIZE, ROOT, and CHILD from the result
    SIZE = list(result[0])
    ROOT = list(result[1])
    CHILD = [list(result[i]) for i in range(2, len(result))]

    return {
        'CHILD': CHILD,
        'SIZE': SIZE,
        'ROOT': ROOT
    }

def py_queryPreparation(int m, list ROOT, list TDP, list CHILD):
    cdef vector[int] ROOT_vector = ROOT
    cdef vector[double] TDP_vector = TDP
    cdef vector[vector[int]] CHILD_vector = [vector[int]() for _ in CHILD]
    for i, child in enumerate(CHILD):
        CHILD_vector[i] = child
    cdef vector[int] result = queryPreparation(m, ROOT_vector, TDP_vector, CHILD_vector)
    return list(result)

def py_findLeft(double gamma, list ADMSTC, list TDP):
    cdef vector[int] ADMSTC_vector = ADMSTC
    cdef vector[double] TDP_vector = TDP
    cdef int result = findLeft(gamma, ADMSTC_vector, TDP_vector)
    return result

def py_answerQuery(double gamma, list ADMSTC, list SIZE, list MARK, list TDP, list CHILD):
    cdef vector[int] ADMSTC_vector = ADMSTC
    cdef vector[int] SIZE_vector = SIZE
    cdef vector[int] MARK_vector = MARK
    cdef vector[double] TDP_vector = TDP
    cdef vector[vector[int]] CHILD_vector = [vector[int]() for _ in CHILD]
    for i, child in enumerate(CHILD):
        CHILD_vector[i] = child
    cdef vector[vector[int]] result = answerQuery(gamma, ADMSTC_vector, SIZE_vector, MARK_vector, TDP_vector, CHILD_vector)
    return [list(x) for x in result]


def py_answerQueryBatch(list gamma_batch, list ADMSTC, list SIZE, list MARK, list TDP, list CHILD):
    cdef vector[double] gamma_batch_vector = gamma_batch
    cdef vector[int] ADMSTC_vector = ADMSTC
    cdef vector[int] SIZE_vector = SIZE
    cdef vector[int] MARK_vector = MARK
    cdef vector[double] TDP_vector = TDP
    cdef vector[vector[int]] CHILD_vector = [vector[int]() for _ in CHILD]
    for i, child in enumerate(CHILD):
        CHILD_vector[i] = child
    
    cdef vector[vector[vector[int]]] batch_results = answerQueryBatch(gamma_batch_vector, ADMSTC_vector, SIZE_vector, MARK_vector, TDP_vector, CHILD_vector)
    
    # Convert the results back to Python lists
    result = []
    for batch_result in batch_results:
        result.append([list(x) for x in batch_result])
    
    return result

# def py_answerQueryBatch_opt(list gamma_batch, list ADMSTC, list SIZE, list MARK, list TDP, list CHILD):
#     cdef vector[double] gamma_batch_vector = gamma_batch
#     cdef vector[int] ADMSTC_vector = ADMSTC
#     cdef vector[int] SIZE_vector = SIZE
#     cdef vector[int] MARK_vector = MARK
#     cdef vector[double] TDP_vector = TDP
#     cdef vector[vector[int]] CHILD_vector = [vector[int]() for _ in CHILD]
    
#     for i, child in enumerate(CHILD):
#         CHILD_vector[i] = child
    
#     cdef vector[vector[vector[int]]] batch_results = answerQueryBatch_opt(
#         gamma_batch_vector, ADMSTC_vector, SIZE_vector, MARK_vector, TDP_vector, CHILD_vector
#     )
    
#     return [[list(cluster) for cluster in gamma_result] for gamma_result in batch_results]

# def py_answerQueryInChunks(list gamma_batch, list ADMSTC, list SIZE, list MARK, list TDP, list CHILD, int chunk_size):
#     cdef vector[double] gamma_batch_vector = gamma_batch
#     cdef vector[int] ADMSTC_vector = ADMSTC
#     cdef vector[int] SIZE_vector = SIZE
#     cdef vector[int] MARK_vector = MARK
#     cdef vector[double] TDP_vector = TDP
#     cdef vector[vector[int]] CHILD_vector = [vector[int]() for _ in CHILD]
#     for i, child in enumerate(CHILD):
#         CHILD_vector[i] = child
    
#     # Call the C++ answerQueryInChunks function directly
#     cdef vector[vector[vector[int]]] batch_results = answerQueryInChunks(
#         gamma_batch_vector, ADMSTC_vector, SIZE_vector, MARK_vector, TDP_vector, CHILD_vector, chunk_size)
    
#     # Convert the results back to Python lists
#     result = []
#     for batch_result in batch_results:
#         result.append([list(x) for x in batch_result])
    
#     return result

def py_counting_sort(int n, int maxid, list CLSTRSIZE):
    cdef vector[int] CLSTRSIZE_vector = CLSTRSIZE
    cdef vector[int] result = counting_sort(n, maxid, CLSTRSIZE_vector)
    return list(result)


def py_index2xyz(int index, list DIMS):
    cdef vector[int] DIMS_vector = DIMS
    cdef vector[int] result = index2xyz(index, DIMS_vector)
    return list(result)

def py_ids2xyz(list IDS, list DIMS):
    cdef vector[int] IDS_vector = IDS
    cdef vector[int] DIMS_vector = DIMS
    cdef vector[vector[int]] result = ids2xyz(IDS_vector, DIMS_vector)
    return [list(x) for x in result]

def py_xyz_check(int x, int y, int z, int index, list DIMS, list MASK):
    cdef vector[int] DIMS_vector = DIMS
    cdef vector[int] MASK_vector = MASK
    return xyz_check(x, y, z, index, DIMS_vector, MASK_vector)

def py_findNeighbours(list MASK, list DIMS, int index, int conn):
    cdef vector[int] MASK_vector = MASK
    cdef vector[int] DIMS_vector = DIMS
    cdef vector[int] result = findNeighbours(MASK_vector, DIMS_vector, index, conn)
    return list(result)

def py_findAdjList(list MASK, list INDEXP, list DIMS, int m, int conn):
    cdef vector[int] MASK_vector = MASK
    cdef vector[int] INDEXP_vector = INDEXP
    cdef vector[int] DIMS_vector = DIMS
    cdef vector[vector[int]] result = findAdjList(MASK_vector, INDEXP_vector, DIMS_vector, m, conn)
    return [list(x) for x in result]


def py_findDiscoveries_one_based(list idx, list allp, double simesfactor, int h, double alpha, int k, int m):
    cdef vector[int] idx_vector = idx
    cdef vector[double] allp_vector = allp
    
    cdef vector[int] discoveries = findDiscoveries_one_based(idx_vector, allp_vector, simesfactor, h, alpha, k, m)
    
    return list(discoveries)


def py_findConcentration_one_based(list p, double simesfactor, int h, double alpha, int m):
    cdef vector[double] p_vector = p
    
    cdef int concentration = findConcentration_one_based(p_vector, simesfactor, h, alpha, m)
    return concentration


def py_findIndex(int irep, list ADMSTC, list TDP):
    """
    Python wrapper for the C++ findIndex function.
    :param irep: Cluster index to find.
    :param ADMSTC: List of cluster indices.
    :param TDP: List of TDP values.
    :return: Index of the cluster in ADMSTC or -1 if not found.
    """
    cdef vector[int] ADMSTC_vector = ADMSTC
    cdef vector[double] TDP_vector = TDP

    return findIndex(irep, ADMSTC_vector, TDP_vector)

def py_changeQuery(
    int ix, double tdpchg, list ADMSTC, list SIZE, list MARK, list TDP, list CHILD, list ANS
):
    """
    Python wrapper for the C++ changeQuery function.
    """
    cdef vector[int] ADMSTC_vector = ADMSTC
    cdef vector[int] SIZE_vector = SIZE
    cdef vector[int] MARK_vector = MARK
    cdef vector[double] TDP_vector = TDP

    # Convert nested lists to vector[vector[int]]
    cdef vector[vector[int]] CHILD_vector
    cdef vector[int] child_vector  # Declare this outside the loop
    for x in CHILD:
        child_vector = x  # Assign within the loop
        CHILD_vector.push_back(child_vector)

    cdef vector[vector[int]] ANS_vector
    cdef vector[int] ans_vector  # Declare this outside the loop
    for x in ANS:
        ans_vector = x
        ANS_vector.push_back(ans_vector)

    cdef vector[vector[int]] result = changeQuery(
        ix, tdpchg, ADMSTC_vector, SIZE_vector, MARK_vector, TDP_vector, CHILD_vector, ANS_vector
    )
    return [list(x) for x in result]

def py_findLMS(list CHILD):
    """
    Python wrapper for the C++ findLMS function.
    """
    cdef vector[vector[int]] CHILD_vector
    cdef vector[int] child_vector  # Declare this outside the loop
    for x in CHILD:
        child_vector = x
        CHILD_vector.push_back(child_vector)

    cdef vector[int] result = findLMS(CHILD_vector)
    return list(result)