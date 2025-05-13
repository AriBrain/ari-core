
#include <vector>
#include <cmath>
#include <algorithm>
#include <stdbool.h> 
#include "hommel.h"

// Implementation of Fortune 1989
std::vector<int> findhull(int m, const std::vector<double>& p) {
    int r;
    std::vector<int> hull;
    hull.push_back(0); // Changed from 1 to 0 for zero-based indexing
    bool notconvex;

    for (int i = 1; i < m; i++) { // Changed from i = 2; i <= m to i = 1; i < m for zero-based indexing
        if (i == m-1 || (m-1) * (p[i] - p[0]) < i * (p[m-1] - p[0])) { // Changed indices for zero-based indexing
            do {
                r = hull.size() - 1;
                if (r > 0) { // Changed from r > 1 to r > 0 for zero-based indexing
                    notconvex = ((i-hull[r-1]) * (p[hull[r]] - p[hull[r-1]]) >=
                        (hull[r] - hull[r-1]) * (p[i] - p[hull[r-1]])); // Changed indices for zero-based indexing
                } else {
                    if (r == 0) { // Changed from r == 1 to r == 0 for zero-based indexing
                        notconvex = (i * p[hull[0]] >= hull[0] * p[i]); // Changed indices for zero-based indexing
                    } else {
                        notconvex = false;
                    }
                }
                if (notconvex) hull.resize(r);
            } while (notconvex);
            hull.push_back(i); // Changed index for zero-based indexing
        }
    }
    return hull;
}

// Definition of the findalpha function
// Purpose: This function calculates the alpha values that correspond to the jumps of the statistical function h(alpha).
// The function returns a std::vector<double> and takes the following arguments:
// - const std::vector<double>& p: A constant reference to a vector of sorted p-values.
// - int m: An integer representing the length of the vector p.
// - const std::vector<double>& simesfactor: A constant reference to a vector representing the denominator of the local test.
// - bool simes: A boolean indicating whether the Simes method is assumed or not.
std::vector<double> findalpha(const std::vector<double>& p, int m, const std::vector<double>& simesfactor, bool simes) {
    
    // Create a vector 'alpha' of size m, initialized with zeros.
    // This vector will store the alpha values that correspond to the jumps of h(alpha).
    std::vector<double> alpha(m); // The vector 'alpha' is initialized with size 'm'.

    // Call the 'findhull' function to compute the convex hull of the sorted p-values.
    // 'findhull' returns a vector of integers representing the indices of the hull points.
    std::vector<int> hull = findhull(m, p);
    
    // Initialize a variable 'Dk' to store the difference used in the hull verification process.
    double Dk = 0;

    // Initialize 'k' to the last index of the hull points (since hull is a 0-based index, this is hull.size() - 1).
    int k = hull.size() - 1;

    // Initialize 'i' to 0 (since we are using 0-based indexing).
    int i = 0;  // Changed from 1 to 0 for zero-based indexing

    // Start the main loop that will compute the alpha values.
    while (i < m) {  // Loop over all elements from 0 to m-1 (changed from i <= m to i < m for zero-based indexing)
        
        // If there are more than one hull points left (k > 0):
        if (k > 0)
            // Compute 'Dk', which checks whether the point should remain in the hull or if we need to step back.
            // It calculates the difference between the slopes of the lines formed by the p-values at the current hull points.
            Dk = p[hull[k-1]] * (hull[k] - m + i + 1) - p[hull[k]] * (hull[k-1] - m + i + 1);  // Changed indices for zero-based indexing
        
        // If the computed difference 'Dk' is negative, move to the previous hull point.
        if (k > 0 && Dk < 0) {
            k--;  // Decrease 'k' to step back to the previous hull point.
        } else {
            // If 'Dk' is not negative or there is only one hull point left, calculate the current alpha value.
            // The alpha value is calculated by scaling the p-value at the current hull point with the corresponding Simes factor.
            alpha[i] = simesfactor[i+1] * p[hull[k]] / (hull[k] - m + i + 1);  // Changed indices for zero-based indexing

            // Move to the next index for alpha.
            i++;
        }
    }

    // If the 'simes' flag is false, apply additional processing to ensure alpha values are bounded by 1 and cumulative maximum is calculated.
    if (!simes) {
        // Bound alpha values by 1.
        for (int i = m-1; i >= 0; i--) 
            if (alpha[i] > 1)
                alpha[i] = 1;

        // Ensure the cumulative maximum, so each alpha[i] is not less than any subsequent alpha value.
        for (int i = m-2; i >= 0; i--) {
            if (alpha[i] < alpha[i+1])
                alpha[i] = alpha[i+1];
        }
    }

    // Return the computed alpha values.
    return alpha;
}

// // Calculates the denominator of the local test
// std::vector<double> findsimesfactor(bool simes, int m) {
//     std::vector<double> simesfactor(m);
//     double multiplier = 0.0;

//     if (simes) {
//         for (int i = 0; i < m; i++) {
//             simesfactor[i] = i + 1;
//         }
//     } else {
//         for (int i = 0; i < m; i++) {
//             multiplier += 1.0 / (i + 1);
//             simesfactor[i] = (i + 1) * multiplier;
//         }
//     }

//     return simesfactor;
// }

// Calculates the denominator of the local test
std::vector<double> findsimesfactor(bool simes, int m) {
    std::vector<double> simesfactor(m + 1);  // Allocate space for m + 1 elements
    double multiplier = 0.0;

    simesfactor[0] = 0.0;  // Set the first element to 0

    if (simes) {
        for (int i = 1; i <= m; i++) {
            simesfactor[i] = i;
        }
    } else {
        for (int i = 1; i <= m; i++) {
            multiplier += 1.0 / i;
            simesfactor[i] = i * multiplier;
        }
    }

    return simesfactor;
}

// Calculate adjusted p-values for all elementary hypotheses
std::vector<double> adjustedElementary(const std::vector<double>& p, const std::vector<double>& alpha, int m, const std::vector<double>& simesfactor) {
    std::vector<double> adjusted(m);
    int i = 0;  // Changed from 1 to 0 for zero-based indexing
    int j = m;  // Changed from m + 1 to m for zero-based indexing
    while (i < m) {  // Changed from i <= m to i < m for zero-based indexing
        if (simesfactor[j-1] * p[i] <= alpha[j-1]) {  // Changed indices for zero-based indexing
            adjusted[i] = std::min(simesfactor[j] * p[i], alpha[j-1]);  // Changed indices for zero-based indexing
            i++;
        } else {
            j--;
        }
    }
    return adjusted;
}

// Calculate the adjusted p-value of an intersection hypotheses
double adjustedIntersection(double pI, const std::vector<double>& alpha, int m, const std::vector<double>& simesfactor) {
    int lower = 0;  // Changed from 1 to 0 for zero-based indexing
    int upper = m + 1;  // Changed from m + 2 to m + 1 for zero-based indexing
    int mid = 0;

    while (lower < upper - 1) {
        mid = (lower + upper) / 2;
        if (simesfactor[mid] * pI <= alpha[mid]) {  // Changed indices for zero-based indexing
            lower = mid;
        } else {
            upper = mid;
        }
    }

    pI = std::min(simesfactor[lower] * pI, alpha[lower]);
    return pI;
}

// Calculate the value of h(alpha) for a given alpha
int findHalpha(const std::vector<double>& jumpalpha, double alpha, int m) {
    int lower = 0;  // Starting from the zero-based index
    int upper = m;  // Changed from m + 1 to m for zero-based indexing
    int mid = 0;

    while (lower + 1 < upper) {
        mid = (lower + upper) / 2;  // Correct calculation for mid
        if (jumpalpha[mid] > alpha) {  // Changed indices for zero-based indexing
            lower = mid;
        } else {
            upper = mid;
        }
    }

    return lower;
}
// int findHalpha(const std::vector<double>& jumpalpha, double alpha, int m) {
//     int lower = 0;  // Starting from the zero-based index
//     int upper = m+1;  // Changed from m + 1 to m for zero-based indexing
//     int mid = 0;

//     while (lower + 1 < upper) {
//         mid = (lower + upper + 1) / 2;  // Correct calculation for mid
//         if (jumpalpha[mid-1] > alpha) {  // Changed indices for zero-based indexing
//             lower = mid;
//         } else {
//             upper = mid;
//         }
//     }

//     return lower;
// }


// Calculates the size of the concentration set at a fixed alpha
int findConcentration(const std::vector<double>& p, double simesfactor, int h, double alpha, int m) {
    int z = m - h - 1;  // Adjusted for zero-based indexing
    if (z >= 0) {  // Changed condition to be consistent with zero-based indexing
        while (z < m - 1 && (simesfactor * p[z] > (z - m + h + 2) * alpha)) {  // Changed indices for zero-based indexing
            z++;
        }
    }
    return z;
}

// Find function for disjoint set data structure
int Find(int x, std::vector<int>& parent) {
    while (parent[x] != x) {
        parent[x] = parent[parent[x]];
        x = parent[x];
    }
    return x;
}

// Union function for disjoint set data structure
void Union(int x, int y, std::vector<int>& parent, std::vector<int>& lowest, std::vector<int>& rank) {
    int xRoot = Find(x, parent);  // Find the root of x
    int yRoot = Find(y, parent);  // Find the root of y

    // If they have the same root, they are already in the same set
    if (xRoot == yRoot) return;

    // Union by rank
    if (rank[xRoot] < rank[yRoot]) {
        parent[xRoot] = yRoot;  // Make yRoot the parent of xRoot
        lowest[yRoot] = std::min(lowest[xRoot], lowest[yRoot]);  // Update the lowest value
    } else if (rank[xRoot] > rank[yRoot]) {
        parent[yRoot] = xRoot;  // Make xRoot the parent of yRoot
        lowest[xRoot] = std::min(lowest[xRoot], lowest[yRoot]);  // Update the lowest value
    } else {
        parent[yRoot] = xRoot;  // Make xRoot the parent of yRoot
        rank[xRoot]++;  // Increase the rank of xRoot
        lowest[xRoot] = std::min(lowest[xRoot], lowest[yRoot]);  // Update the lowest value
    }
}

// Calculate the category for each p-value
int getCategory(double p, double simesfactor, double alpha, int m) {
    if (p == 0 || simesfactor == 0)
        return 0;  // Changed from 1 to 0 for zero-based indexing
    else if (alpha == 0)
        return m;  // Changed from m + 1 to m for zero-based indexing
    else {
        double cat = (simesfactor / alpha) * p;
        return static_cast<int>(std::ceil(cat)) - 1;  // Adjusted to zero-based indexing
    }
}

// Implementation of findDiscoveries
std::vector<int> findDiscoveries(const std::vector<int>& idx, const std::vector<double>& allp, double simesfactor, int h, double alpha, int k, int m) {
    // Calculate categories for the p-values
    std::vector<int> cats;
    for (int i = 0; i < k; i++) {
        cats.push_back(getCategory(allp[idx[i]], simesfactor, alpha, m));  // Adjusted index for zero-based indexing
    }

    // Find the maximum category needed
    int z = findConcentration(allp, simesfactor, h, alpha, m);
    int maxcat = std::min(z - m + h, k);  // Adjusted maxcat calculation for zero-based indexing
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
    std::vector<int> discoveries(k, 0);  // Adjusted size for zero-based indexing
    int lowestInPi;
    for (int i = 0; i < k; i++) {
        if (cats[i] <= maxcat) {
            lowestInPi = lowest[Find(cats[i], parent)];
            if (lowestInPi == 0) {  // Adjusted from 1 to 0 for zero-based indexing
                discoveries[i] = (i == 0) ? 1 : discoveries[i - 1] + 1;  // Handle first element separately for zero-based indexing
            } else {
                discoveries[i] = (i == 0) ? 0 : discoveries[i - 1];  // Handle first element separately for zero-based indexing
                Union(lowestInPi - 1, Find(cats[i], parent), parent, lowest, rank);  // Adjusted lowestInPi - 1 for zero-based indexing
            }
        } else {
            discoveries[i] = (i == 0) ? 0 : discoveries[i - 1];  // Handle first element separately for zero-based indexing
        }
    }

    return discoveries;
}
