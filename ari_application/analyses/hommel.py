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
        # ix_sorted_p[self.sorter] = np.arange(1, m + 1)
        ix_sorted_p[self.sorter] = np.arange(m)
        ix_sorted_p = ix_sorted_p[ix]

        # Convert to list for compatibility with the C++ function
        ix_sorted_p = ix_sorted_p.tolist()
        all_sorted_p = all_sorted_p.tolist()

        # Find the number of discoveries using the C++ function
        discoveries = hommel.py_findDiscoveries(ix_sorted_p, all_sorted_p, simes_factor, h, alpha, k, m)

        if not incremental:
            # If not incremental, return the number of discoveries for the last index
            # return discoveries[k]
            return discoveries[k-1]
        else:
            # If incremental, return the number of discoveries for each step
            return discoveries[1:]


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
        z = hommel.py_findConcentration(sorted_p.tolist(), simes_factor, h, alpha, m)

        # Return the p-value at the determined concentration index
        return sorted_p[z]

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
