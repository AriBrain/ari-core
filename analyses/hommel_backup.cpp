#include <vector>
#include <cmath>
#include <algorithm>
#include <stdbool.h> 

// Implementation of Fortune 1989
std::vector<int> findhull(int m, const std::vector<double>& p) {
    int r;
    std::vector<int> hull(1);
    hull.push_back(1);
    bool notconvex;

    for (int i = 2; i <= m; i++) {
        if (i == m || (m-1) * (p[i-1] - p[0]) < (i-1) * (p[m-1] - p[0])) {
            do {
                r = hull.size() - 1;
                if (r > 1) {
                    notconvex = ((i-hull[r-1]) * (p[hull[r]-1] - p[hull[r-1]-1]) >=
                        (hull[r] - hull[r-1]) * (p[i-1] - p[hull[r-1]-1]));
                } else {
                    if (r == 1) {
                        notconvex = (i * p[hull[1]-1] >= hull[1] * p[i-1]);
                    } else {
                        notconvex = false;
                    }
                }
                if (notconvex) hull.resize(r);
            } while (notconvex);
            hull.push_back(i);
        }
    }
    return hull;
}

// Finds the jumps of h(alpha)
std::vector<double> findalpha(const std::vector<double>& p, int m, const std::vector<double>& simesfactor, bool simes) {
    std::vector<double> alpha(m+1);
    std::vector<int> hull = findhull(m, p);
    double Dk = 0;
    int k = hull.size() - 1;
    int i = 1;

    while (i <= m) {
        if (k > 1)
            Dk = p[hull[k-1]-1] * (hull[k] - m + i) - p[hull[k]-1] * (hull[k-1] - m +i);
        if (k > 1 && Dk < 0) {
            k--;
        } else {
            alpha[i-1] = simesfactor[i] * p[hull[k]-1] / (hull[k] - m + i);
            i++;
        }
    }

    if (!simes) {
        for (int i = m-1; i >= 0; i--) 
            if (alpha[i] > 1)
                alpha[i] = 1;
        for (int i = m-2; i >= 0; i--) {
            if (alpha[i] < alpha[i+1])
                alpha[i] = alpha[i+1];
        }
    }

    return alpha;
}

// Calculates the denominator of the local test
std::vector<double> findsimesfactor(bool simes, int m) {
    std::vector<double> simesfactor(m+1);
    double multiplier = 0;
    simesfactor[0] = 0;
    if (simes) 
        for (int i = 1; i <= m; i++)
            simesfactor[i] = i;
    else 
        for (int i = 1; i <= m; i++) {
            multiplier += 1.0/i;
            simesfactor[i] = i * multiplier;
        }

    return simesfactor;
}

// Calculate adjusted p-values for all elementary hypotheses
std::vector<double> adjustedElementary(const std::vector<double>& p, const std::vector<double>& alpha, int m, const std::vector<double>& simesfactor) {
    std::vector<double> adjusted(m);
    int i = 1;
    int j = m + 1;
    while (i <= m) {
        if (simesfactor[j-1] * p[i-1] <= alpha[j-1]) {
            adjusted[i-1] = std::min(simesfactor[j] * p[i-1], alpha[j-1]);
            i++;
        } else {
            j--;
        }
    }
    return adjusted;
}

// Calculate the adjusted p-value of an intersection hypotheses
double adjustedIntersection(double pI, const std::vector<double>& alpha, int m, const std::vector<double>& simesfactor) {
    int lower = 1;
    int upper = m + 2;
    int mid = 0;

    while (lower < upper - 1) {
        mid = (lower + upper) / 2;
        if (simesfactor[mid-1] * pI <= alpha[mid-1]) {
            lower = mid;
        } else {
            upper = mid;
        }
    }

    pI = std::min(simesfactor[lower] * pI, alpha[lower-1]);
    return pI;
}

// Calculate the value of h(alpha) for a given alpha
int findHalpha(const std::vector<double>& jumpalpha, double alpha, int m) {
    int lower = 0;
    int upper = m + 1;
    int mid = 0;
    while (lower + 1 < upper) {
        mid = (lower + upper + 1) / 2;
        if (jumpalpha[mid-1] > alpha) {
            lower = mid;
        } else {
            upper = mid;
        }
    }
    return lower;
}

// Calculates the size of the concentration set at a fixed alpha
int findConcentration(const std::vector<double>& p, double simesfactor, int h, double alpha, int m) {
    int z = m - h;
    if (z > 0) {
        while ((z < m) & (simesfactor * p[z-1] > (z - m + h + 1) * alpha)) {
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
    int xRoot = Find(x, parent);
    int yRoot = Find(y, parent);

    if (xRoot == yRoot) return;

    if (rank[xRoot] < rank[yRoot]) {
        parent[xRoot] = yRoot;
        lowest[yRoot] = std::min(lowest[xRoot], lowest[yRoot]);
    } else if (rank[xRoot] > rank[yRoot]) {
        parent[yRoot] = xRoot;
        lowest[xRoot] = std::min(lowest[xRoot], lowest[yRoot]);
    } else {
        parent[yRoot] = xRoot;
        rank[xRoot]++;
        lowest[xRoot] = std::min(lowest[xRoot], lowest[yRoot]);
    }
}

// Calculate the category for each p-value
int getCategory(double p, double simesfactor, double alpha, int m) {
    if (p == 0 || simesfactor == 0)
        return 1;
    else if (alpha == 0)
        return m + 1;
    else {
        double cat = (simesfactor / alpha) * p;
        return static_cast<int>(std::ceil(cat));
    }
}

// Forward declarations for functions used by findDiscoveries
int Find(int x, std::vector<int>& parent);
void Union(int x, int y, std::vector<int>& parent, std::vector<int>& lowest, std::vector<int>& rank);
int getCategory(double p, double simesfactor, double alpha, int m);
int findConcentration(const std::vector<double>& p, double simesfactor, int h, double alpha, int m);

// Implementation of findDiscoveries
std::vector<int> findDiscoveries(const std::vector<int>& idx, const std::vector<double>& allp, double simesfactor, int h, double alpha, int k, int m) {
    // Calculate categories for the p-values
    std::vector<int> cats;
    for (int i = 0; i < k; i++) {
        cats.push_back(getCategory(allp[idx[i] - 1], simesfactor, alpha, m));
    }

    // Find the maximum category needed
    int z = findConcentration(allp, simesfactor, h, alpha, m);
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

// Helper functions
int Find(int x, std::vector<int>& parent) {
    while (parent[x] != x) {
        parent[x] = parent[parent[x]];
        x = parent[x];
    }
    return x;
}

void Union(int x, int y, std::vector<int>& parent, std::vector<int>& lowest, std::vector<int>& rank) {
    int xRoot = Find(x, parent);
    int yRoot = Find(y, parent);

    if (xRoot == yRoot) return;

    if (rank[xRoot] < rank[yRoot]) {
        parent[xRoot] = yRoot;
        lowest[yRoot] = std::min(lowest[xRoot], lowest[yRoot]);
    } else if (rank[xRoot] > rank[yRoot]) {
        parent[yRoot] = xRoot;
        lowest[xRoot] = std::min(lowest[xRoot], lowest[yRoot]);
    } else {
        parent[yRoot] = xRoot;
        rank[xRoot]++;
        lowest[xRoot] = std::min(lowest[xRoot], lowest[yRoot]);
    }
}

int getCategory(double p, double simesfactor, double alpha, int m) {
    if (p == 0 || simesfactor == 0)
        return 1;
    else if (alpha == 0)
        return m + 1;
    else {
        double cat = (simesfactor / alpha) * p;
        return static_cast<int>(std::ceil(cat));
    }
}

int findConcentration(const std::vector<double>& p, double simesfactor, int h, double alpha, int m) {
    int z = m - h;
    if (z > 0) {
        while ((z < m) & (simesfactor * p[z - 1] > (z - m + h + 1) * alpha)) {
            z++;
        }
    }
    return z;
}
