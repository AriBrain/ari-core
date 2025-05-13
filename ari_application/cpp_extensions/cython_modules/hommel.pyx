# hommel.pyx
# distutils: language = c++
# cython: language_level=3

from libcpp.vector cimport vector
from libcpp cimport bool

cdef extern from "../cpp_sources/hommel.h":
    vector[int] findhull(int m, const vector[double]& p)
    vector[double] findalpha(const vector[double]& p, int m, const vector[double]& simesfactor, bool simes)
    vector[double] findsimesfactor(bool simes, int m)
    vector[double] adjustedElementary(const vector[double]& p, const vector[double]& alpha, int m, const vector[double]& simesfactor)
    double adjustedIntersection(double pI, const vector[double]& alpha, int m, const vector[double]& simesfactor)
    int findHalpha(const vector[double]& jumpalpha, double alpha, int m)
    int findConcentration(const vector[double]& p, double simesfactor, int h, double alpha, int m)
    vector[int] findDiscoveries(const vector[int]& idx, const vector[double]& allp, double simesfactor, int h, double alpha, int k, int m)

def py_findhull(int m, list p):
    cdef vector[double] p_vector = p
    cdef vector[int] result = findhull(m, p_vector)
    return list(result)

def py_findalpha(list p, int m, list simesfactor, bool simes):
    cdef vector[double] p_vector = p
    cdef vector[double] simesfactor_vector = simesfactor
    cdef vector[double] result = findalpha(p_vector, m, simesfactor_vector, simes)
    return list(result)

def py_findsimesfactor(bool simes, int m):
    cdef vector[double] result = findsimesfactor(simes, m)
    return list(result)

def py_adjustedElementary(list p, list alpha, int m, list simesfactor):
    cdef vector[double] p_vector = p
    cdef vector[double] alpha_vector = alpha
    cdef vector[double] simesfactor_vector = simesfactor
    cdef vector[double] result = adjustedElementary(p_vector, alpha_vector, m, simesfactor_vector)
    return list(result)

def py_adjustedIntersection(double pI, list alpha, int m, list simesfactor):
    cdef vector[double] alpha_vector = alpha
    cdef double result = adjustedIntersection(pI, alpha_vector, m, simesfactor)
    return result

def py_findHalpha(list jumpalpha, double alpha, int m):
    cdef vector[double] jumpalpha_vector = jumpalpha
    cdef int result = findHalpha(jumpalpha_vector, alpha, m)
    return result

def py_findConcentration(list p, double simesfactor, int h, double alpha, int m):
    cdef vector[double] p_vector = p
    cdef int result = findConcentration(p_vector, simesfactor, h, alpha, m)
    return result

def py_findDiscoveries(list idx, list allp, double simesfactor, int h, double alpha, int k, int m):
    cdef vector[int] idx_vector = idx
    cdef vector[double] allp_vector = allp
    cdef vector[int] result = findDiscoveries(idx_vector, allp_vector, simesfactor, h, alpha, k, m)
    return list(result)

