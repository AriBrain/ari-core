// hommel.h
#ifndef HOMMEL_H
#define HOMMEL_H

#include <vector>
#include <cmath>
#include <algorithm>
#include <stdbool.h>

// Function declarations
// Declaration of functions used in the project.
// These declarations inform the compiler about the functions' existence,
// their return types, and the types of their parameters, but do not provide
// the actual implementation. This allows other files to use these functions.

// /**
//  * findhull - Finds the convex hull of a given set of points.
//  * @param m: The number of points.
//  * @param p: A vector of p-values (sorted).
//  * @return: A vector of integers representing the convex hull.
//  */

std::vector<int> findhull(int m, const std::vector<double>& p);

// /**
//  * findalpha - Computes the jumps of h(alpha) for given p-values.
//  * @param p: A vector of p-values (sorted).
//  * @param m: The number of p-values.
//  * @param simesfactor: A vector representing the denominator of the local test.
//  * @param simes: A boolean indicating if Simes' correction is used.
//  * @return: A vector of alpha values representing the jumps.
//  */
std::vector<double> findalpha(const std::vector<double>& p, int m, const std::vector<double>& simesfactor, bool simes);


std::vector<double> findsimesfactor(bool simes, int m);
std::vector<double> adjustedElementary(const std::vector<double>& p, const std::vector<double>& alpha, int m, const std::vector<double>& simesfactor);
double adjustedIntersection(double pI, const std::vector<double>& alpha, int m, const std::vector<double>& simesfactor);
int findHalpha(const std::vector<double>& jumpalpha, double alpha, int m);
int findConcentration(const std::vector<double>& p, double simesfactor, int h, double alpha, int m);
int Find(int x, std::vector<int>& parent);
void Union(int x, int y, std::vector<int>& parent, std::vector<int>& lowest, std::vector<int>& rank);
int getCategory(double p, double simesfactor, double alpha, int m);
std::vector<int> findDiscoveries(const std::vector<int>& idx, const std::vector<double>& allp, double simesfactor, int h, double alpha, int k, int m);

#endif // HOMMEL_H