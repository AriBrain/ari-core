import numpy as np
import pandas as pd
# import BrainNav.cpp_extensions.cython_modules.hommel as hommel
import ari_application.cpp_extensions.cython_modules.hommel as hommel

class pyHommel:
    def __init__(self, p, jump_alpha, sorter, adjusted, simes_factor, simes):
        self.p = p
        self.jump_alpha = jump_alpha
        self.sorter = sorter
        self.adjusted = adjusted
        self.simes_factor = simes_factor
        self.simes = simes

    @classmethod
    def hommel_wbTDP(cls, p, simes=True):
        """
        Compute the whole-brain TDP, i.e. min(TDP).
        
        :param p: Array-like, p-values.
        :param simes: Boolean, whether to use the Simes method.
        :return: Instance of PyHommel.
        """
        # Check for missing values in p
        if np.any(np.isnan(p)):
            raise ValueError("Missing values in input p-values")
        
        # Check if the p-values vector is empty
        if len(p) == 0:
            raise ValueError("The p-values vector is empty")

        # Get the names if p is a pandas Series
        names = p.index if isinstance(p, pd.Series) else None

        # Sort the p-values and get the permutation indices
        # flattened_p = p.flatten(order='C')
        # ordp_flat   = np.argsort(flattened_p)
        # ordp        = ordp_flat.astype(int)

        perm = list(np.argsort(p, kind='stable'))
        sorted_p = p[perm]

        # List sorted_p for input below
        sorted_p = sorted_p.tolist()

        # Length of p-values
        m = len(p)

        # Compute Simes factor
        simes_factor        = hommel.py_findsimesfactor(simes, m)

        # Find the jumps of h(alpha)
        jump_alpha          = hommel.py_findalpha(sorted_p, m, simes_factor, simes)

        # Calculate adjusted p-values for all elementary hypotheses
        adjusted            = hommel.py_adjustedElementary(sorted_p, jump_alpha, m, simes_factor)

        # Reorder adjusted p-values to match original order
        adjusted = np.array(adjusted)
        adjusted[perm] = adjusted

        # If names are present, convert adjusted to a pandas Series
        if names is not None:
            adjusted = pd.Series(adjusted, index=names)

        # Create and return a new instance of PyHommel
        return cls(p=p, jump_alpha=jump_alpha, sorter=perm, adjusted=adjusted, simes_factor=simes_factor, simes=simes)
    

    def tdp(self, alpha=0.05, ix=None, incremental=False):
        """
        Calculate the True Discovery Proportion (TDP) for a given alpha.

        Parameters:
        alpha (float): Significance level for determining discoveries.
        ix (array-like, optional): Indices of the p-values to consider.
        incremental (bool): Whether to calculate discoveries incrementally.

        Returns:
        float: True Discovery Proportion (TDP).
        """
        m = len(self.p)  # Total number of p-values

        if ix is None:
            # If no specific indices are provided, use all p-values
            k = m
            d = self.discoveries(alpha=alpha, incremental=incremental)
        else:
            # If specific indices are provided, use them - currently not correct!!
            k = len(self.p[ix])
            d = self.discoveries(ix=ix, alpha=alpha, incremental=incremental)

        # Calculate TDP by dividing the number of discoveries by the number of hypotheses
        return d / k


    def discoveries(self, ix=None, incremental=False, alpha=0.05):
        """
        Calculate the number of discoveries for given indices and alpha.

        Parameters:
        ix (array-like, optional): Indices of the p-values to consider.
        incremental (bool): Whether to calculate discoveries incrementally.
        alpha (float): Significance level for determining discoveries.

        Returns:
        int or list: Number of discoveries or a list of discoveries if incremental is True.
        """
        m = len(self.p)  # Total number of p-values

        if ix is None and not incremental:
            # If no specific indices are provided and incremental is False, use all p-values
            k = m
            ix = self.sorter
        elif ix is None and incremental:
            # Raise an error if incremental is True but no indices are provided
            raise ValueError("Found incremental=TRUE but missing ix.")
        elif ix is not None:
            # If specific indices are provided, use them
            k = len(self.p[ix])

        # Check for any missing values in the selected p-values
        if np.any(np.isnan(self.p[ix])):
            raise ValueError("NAs produced by selecting with ix.")

        # If no hypotheses are selected, return 0 with a warning
        if k == 0:
            print("Warning: empty selection")
            return 0

        # Find the index h for the given alpha
        h = hommel.py_findHalpha(self.jump_alpha, alpha, m)
        # Get the Simes factor for the determined h
        simes_factor = self.simes_factor[h]
        # Sort the p-values using the stored sorter
        all_sorted_p = self.p[self.sorter]

        # Create an array of indices sorted by p-values
        ix_sorted_p = np.zeros(m, dtype=int)
        ix_sorted_p[self.sorter] = np.arange(1, m + 1)
        ix_sorted_p = ix_sorted_p[ix]

        # Convert to list for compatibility with the C++ function
        ix_sorted_p = ix_sorted_p.tolist()
        all_sorted_p = all_sorted_p.tolist()

        # Size of the concentration set, then the number of discoveries
        z = self.concentration_size(alpha, h=h, simes_factor=simes_factor)
        discoveries = hommel.py_findDiscoveries(ix_sorted_p, all_sorted_p, simes_factor, h, alpha, k, z, m)

        if not incremental:
            # The C++ routine returns k+1 cumulative counts, discoveries[0] = 0,
            # so the total for the whole selection is discoveries[k].
            # discoveries[k-1] dropped the last hypothesis in ix.
            return discoveries[k]
        else:
            # If incremental, return the number of discoveries for each step
            return discoveries[1:]


    def discovery_context(self, alpha=0.05):
        """
        Build a reusable evaluator for many discovery queries at one alpha.

        `discoveries()` recomputes h, the Simes factor, the sorted p-value
        list and the 1-based rank array on every call — all O(m) and all
        invariant across queries. When a caller asks the same question for
        hundreds of voxel sets (ROI-level TDP over an atlas), that setup
        dominates: measured at m=902,629, 120 ROIs took ~21s through
        `discoveries()` versus ~4s through this context, for identical values.

        Returns a DiscoveryContext; use `.count(ix)` or `.tdp(ix)` per set.
        """
        return DiscoveryContext(self, alpha)

    def concentration_size(self, alpha, h=None, simes_factor=None):
        """
        Size z of the concentration set at `alpha`, as findDiscoveries needs it.

        The C++ findConcentration walks the p-values in ascending order via
        their 1-based sort order (ORD), so the p-values can be passed in their
        original order: ORD is self.sorter + 1. h and simes_factor can be
        passed in when the caller already has them.
        """
        m = len(self.p)
        if h is None:
            h = hommel.py_findHalpha(self.jump_alpha, alpha, m)
        if simes_factor is None:
            simes_factor = self.simes_factor[h]
        ord_1based = (np.asarray(self.sorter) + 1).tolist()
        return hommel.py_findConcentration(
            np.asarray(self.p, dtype=float).tolist(), ord_1based, simes_factor, h, alpha, m
        )

    def concentration(self, alpha):
        """
        Calculate the concentration of p-values for a given alpha.

        Parameters:
        alpha (float): Significance level for determining concentration.

        Returns:
        float: Concentration value for the given alpha.
        """
        m = len(self.p)  # Total number of p-values
        # Find the index h for the given alpha
        h = hommel.py_findHalpha(self.jump_alpha, alpha, m)

        # Get the Simes factor for the determined h
        # simes_factor = self.simes_factor[h + 1]
        simes_factor = self.simes_factor[h]

        # Sort the p-values using the stored sorter
        sorted_p = self.p[self.sorter]
        # Find the concentration using the C++ function
        z = self.concentration_size(alpha, h=h, simes_factor=simes_factor)

        # z counts p-values (1-based), so the z-th smallest is sorted_p[z - 1],
        # as R's hommel::concentration returns sortedp[z]. sorted_p[z] was the
        # next one up. z = 0 (h = m) means an empty concentration set: R
        # returns numeric(0); 0.0 here means no p-value qualifies.
        if z == 0:
            return 0.0
        return sorted_p[z - 1]

    def set_brain_nav(self, brain_nav):
        """
        Set the BrainNav instance after the object is created.
        """
        self.brain_nav = brain_nav

        # Set BrainNav later if needed
        # hom.set_brain_nav("some_brain_nav_instance")

    def another_method_using_brain_nav(self):
        """
        Example method that requires brain_nav to be set.
        """
        if self.brain_nav is None:
            raise ValueError("BrainNav instance is not set.")
        # Perform operations using self.brain_nav
        print(f"Using BrainNav: {self.brain_nav}")


class DiscoveryContext:
    """
    Alpha-fixed view over a pyHommel object that hoists every per-query
    invariant out of the loop, so repeated discovery queries only pay for
    the C++ call and the per-set rank lookup.

    Built by pyHommel.discovery_context(). Valid only for the p-values and
    alpha it was built from — rebuild it if either changes.
    """

    def __init__(self, hom, alpha):
        p = np.asarray(hom.p)
        m = len(p)

        self.m = m
        self.alpha = alpha

        # Invariant across queries: the jump index for this alpha and its
        # Simes factor.
        self.h = hommel.py_findHalpha(hom.jump_alpha, alpha, m)
        self.simes_factor = hom.simes_factor[self.h]

        sorter = np.asarray(hom.sorter)

        # The full ascending p-value list the C++ routine scans. Built once as
        # a Python list because py_findDiscoveries takes a vector<double>.
        self.all_sorted_p = p[sorter].tolist()

        # Rank of each hypothesis among the sorted p-values, ONE-BASED: the
        # C++ side does allp[idx[i] - 1] internally. See
        # docs/BUG_REPORT_hommel_indexing.md — a 0-based array segfaults when
        # the smallest p-value is in the selection.
        rank_1based = np.zeros(m, dtype=int)
        rank_1based[sorter] = np.arange(1, m + 1)
        self.rank_1based = rank_1based

        # Size of the concentration set: depends only on p and alpha, so it
        # is computed once here instead of inside every findDiscoveries call.
        self.z = hom.concentration_size(alpha, h=self.h, simes_factor=self.simes_factor)

        # p is NaN-free by construction (hommel_wbTDP raises on missing
        # values), so the per-call NaN check discoveries() performs is
        # redundant here.

    def count(self, ix):
        """
        Number of true discoveries in the selection `ix` (0-based indices
        into the original p-value vector). Returns 0 for an empty selection.
        """
        ix = np.asarray(ix)
        k = int(ix.size)
        if k == 0:
            return 0

        discoveries = hommel.py_findDiscoveries(
            self.rank_1based[ix].tolist(),
            self.all_sorted_p,
            self.simes_factor,
            self.h,
            self.alpha,
            k,
            self.z,
            self.m,
        )
        # k+1 cumulative counts with discoveries[0] = 0; the total is [k].
        return discoveries[k]

    def tdp(self, ix):
        """
        True discovery proportion for the selection `ix`: count / |ix|.
        Returns 0.0 for an empty selection.
        """
        ix = np.asarray(ix)
        k = int(ix.size)
        if k == 0:
            return 0.0
        return float(self.count(ix)) / k
