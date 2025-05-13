
import numpy as np
import pandas as pd

class HommelHelpers:
    def __init__(self, BrainNav):
        # , p, jump_alpha, sorter, adjusted, simes_factor, simes
        # self.p = p
        # self.jump_alpha = jump_alpha
        # self.sorter = sorter
        # self.adjusted = adjusted
        # self.simes_factor = simes_factor
        # self.simes = simes
        """
        Initialize the Hommel Helper class with a reference to the brain_nav instance.
        
        :param brain_nav: Instance of the BrainNav class containing the necessary data and parameters.
        """
        self.brain_nav = BrainNav
        
    def find_simes_factor(simes, m):
        """
        Calculates the denominator of the local test.

        Parameters:
        simes (bool): Assume simes yes or no.
        m (int): Number of p-values.

        Returns:
        np.ndarray: Denominator of simes test.
        """
        simes_factor = np.zeros(m + 1)  # denominator of simes test
        multiplier = 0  # extra multiplier term needed for non-simes
        simes_factor[0] = 0
        if simes:
            for i in range(1, m + 1):
                simes_factor[i] = i
        else:
            for i in range(1, m + 1):
                multiplier += 1.0 / i
                simes_factor[i] = i * multiplier

        return simes_factor