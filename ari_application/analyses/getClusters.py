import numpy as np
import cpp_extensions.cython_modules.ARICluster as ARI_C

class get_clusters:
    """
    get_clusters class for hierarchical clustering analysis.
    
    This class provides methods for answering queries related to cluster hierarchies,
    finding descendants, and performing batch operations on clustering data.
    """

    @staticmethod
    def answer_query_batch(gamma_batch, admstc, size, mark, tdp, child):
        """
        Process a batch of queries for cluster analysis.

        Args:
            gamma_batch (list): List of gamma values for each query.
            admstc (list): Admissible set of nodes.
            size (list): Size of subtree rooted at each node.
            mark (list): Marking array for visited nodes.
            tdp (list): True discovery proportion
            child (list): Child nodes for each node.

        Returns:
            list: Results for each query in the batch.
        """
        batch_results = []
        for gamma in gamma_batch:
            # Process each query individually
            ans = get_clusters.answer_query(gamma, admstc, size, mark, tdp, child)
            batch_results.append(ans)
        return batch_results

    # @staticmethod
    # def answer_query(gamma, admstc, size, mark, tdp, child):
    #     """
    #     Answer a single query for cluster analysis.

    #     Args:
    #         gamma (float): TDP threshold.
    #         admstc (list): Admissible set of nodes.
    #         size (list): Size of subtree rooted at each node.
    #         mark (list): Marking array for visited nodes.
    #         tdp (list): Top-down parameter values.
    #         child (list): Child nodes for each node.

    #     Returns:q
    #         list: List of lists, where each sublist contains the descendants of a cluster.
    #     """
    #     gamma = max(0, gamma)  # Ensure non-negative gamma
    #     ans = []  # List of lists to store cluster descendants
    #     # Find the starting point for cluster analysis
    #     left = get_clusters.find_left(gamma, admstc, tdp)
        
    #     # Find and mark descendants
    #     for i in range(left, len(admstc)):
    #         if mark[admstc[i]] == 0:  # Check if node is not already marked
    #             desc = get_clusters.descendants(admstc[i], size, child)
    #             if isinstance(desc, list):
    #                 ans.append(desc)  # Append the descendants as a list
    #             else:
    #                 ans.append(list(desc))  # Convert to list if necessary
    #             for j in desc:
    #                 mark[j] = 1  # Mark all descendants
        
    #     # Reset marks for future use
    #     for cluster in ans:
    #         for j in cluster:
    #             mark[j] = 0
        
    #     return ans  # Returns a list of lists ORTECH, GOOGLE; deep mind, RIVM op skills ministiries, rijkswaterstaat,

    @staticmethod
    def answer_query(gamma, admstc, size, mark, tdp, child):
        """
        Answer a single query for cluster analysis and record the node ID for each cluster.

        Args:
            gamma (float): TDP threshold.
            admstc (list): Admissible set of nodes.
            size (list): Size of subtree rooted at each node.
            mark (list): Marking array for visited nodes.
            tdp (list): Top-down parameter values.
            child (list): Child nodes for each node.

        Returns:
            tuple:
                list: List of lists, where each sublist contains the descendants of a cluster.
                dict: Mapping from cluster index (table ID) to hierarchical node ID.
        """
        gamma = max(0, gamma)  # Ensure non-negative gamma
        ans = []  # List of lists to store cluster descendants
        cluster_to_node = [] # Map cluster index to node ID in the hierarchy

        # Find the starting point for cluster analysis
        left = get_clusters.find_left(gamma, admstc, tdp)

        # Find and mark descendants
        for cluster_index, i in enumerate(range(left, len(admstc))):  # Assign cluster indices
            if mark[admstc[i]] == 0:  # Check if node is not already marked
                desc = get_clusters.descendants(admstc[i], size, child)
                if isinstance(desc, list):
                    ans.append(desc)  # Append the descendants as a list
                else:
                    ans.append(list(desc))  # Convert to list if necessary
                
                # Record the mapping from cluster index to hierarchical node ID
                cluster_to_node.append(admstc[i])

                # Mark all descendants
                for j in desc:
                    mark[j] = 1


        # Reset marks for future use
        for cluster in ans:
            for j in cluster:
                mark[j] = 0

        return ans, cluster_to_node  # Return the cluster-to-node mapping

    @staticmethod
    def find_left(gamma, admstc, tdp):
        """
        Find the leftmost index in admstc where TDP value >= gamma.

        Args:
            gamma (float): TDP threshold.
            admstc (list): Admissible set of nodes.
            tdp (list): Top-down parameter values.

        Returns:
            int: Leftmost index satisfying the condition.
        """
        right = len(admstc)
        low, high = 0, right

        while low < high:
            mid = (low + high) // 2  # Binary search
            if tdp[admstc[mid]] >= gamma:
                high = mid
            else:
                low = mid + 1
            right -= 1
            # Optimization: check from right to left
            if tdp[admstc[right]] < gamma:
                return right + 1
        return low

    @staticmethod
    def descendants(v, size, child):
        """
        Find all descendants of a given node in the hierarchy.

        Args:
            v (int): Node to find descendants for.
            size (list): Size of subtree rooted at each node.
            child (list): Child nodes for each node.

        Returns:
            numpy.ndarray: Array of descendant nodes.
        """
        desc = np.zeros(size[v], dtype=int)
        length, top = 0, size[v] - 1
        desc[top] = v  # Start with the root node

        while top < len(desc):
            v = desc[top]
            top += 1
            if v < 0:  # Negative values indicate processed nodes
                desc[length] = ~v  # Bitwise NOT to get original value
                length += 1
            else:
                top -= 1
                desc[top] = ~v  # Mark as processed
                chd = child[v]
                # Add children to the stack in reverse order
                for j in range(len(chd) - 1, -1, -1):
                    top -= 1
                    desc[top] = chd[j]

        return desc[:length]  # Return only the actual descendants
    

    def query_preparation(m, roots, tdp, child):
        """
        Prepare the list of representatives of admissible STCs.

        Args:
            m (int): Total number of nodes.
            roots (list): List of root node IDs.
            tdp (list): TDP values for all nodes.
            child (list): List of child nodes for each node.

        Returns:
            list: Sorted list of admissible STC representatives (ADMSTC).
        """
        admstc = []  # List to store representatives of admissible STCs
        stack = []   # Stack for DFS traversal

        # Traverse each root in the forest
        for root in roots:
            stack.append((root, -1))  # Add root with initial max TDP (-1)
            
            while stack:
                v, q = stack.pop()
                
                # Check if v has higher TDP than its ancestors
                if tdp[v] > q:
                    admstc.append(v)
                
                # Add children to the stack
                for chd in child[v]:
                    stack.append((chd, max(tdp[v], q)))

        # Sort ADMSTC in ascending order of TDP
        admstc.sort(key=lambda v: tdp[v])
        return admstc
    

    @staticmethod
    def adjust_cluster_by_threshold(current_cluster_id, gamma, size, child, tdp):
        """
        Adjust the cluster by finding the updated node for the new threshold and fetching descendants.

        Args:
            current_cluster_id (int): The hierarchical node ID of the selected cluster.
            gamma (float): The updated threshold (TDP value).
            size (list): Sizes of the subtrees rooted at each node.
            child (list): Child relationships of the hierarchical tree.
            tdp (list): TDP values for all nodes.

        Returns:
            list: Updated list of voxel indices for the cluster after threshold adjustment.
        """
        print(f"Adjusting Cluster for Node {current_cluster_id} with Gamma {gamma}")

        # Step 1: Traverse the tree to find the updated node
        current_node = current_cluster_id

        while True:
            # Move down the tree if the threshold is raised and children exist
            children_below_threshold = [
                chd for chd in child[current_node] if tdp[chd] >= gamma
            ]

            if tdp[current_node] >= gamma:
                if children_below_threshold:
                    # Traverse down to the child that meets the threshold
                    current_node = children_below_threshold[0]
                else:
                    # No children meet the threshold, stop here
                    break
            else:
                # Move up the tree to the parent if threshold is lowered
                parent_candidates = [node for node, children in enumerate(child) if current_node in children]
                if parent_candidates:
                    current_node = parent_candidates[0]
                else:
                    # No parent exists to move up, stop here
                    break

        print(f"Updated Node after Threshold Adjustment: {current_node}")

        # Step 2: Fetch descendants from the updated node
        updated_voxel_indices = get_clusters.descendants(current_node, size, child)
        print(f"Updated Voxel Indices: {len(updated_voxel_indices)} voxels found.")

        return updated_voxel_indices
    

    def find_index(irep, admstc, tdp):
        """
        Find the index of a cluster in a cluster list (ADMSTC) using binary and linear search.

        Args:
            irep (int): The cluster representative ID to find.
            admstc (list): List of admissible cluster representatives.
            tdp (list): List of TDP values corresponding to the clusters.

        Returns:
            int: Index of the cluster representative in ADMSTC, or -1 if not found.
        """
        left = 0
        right = len(admstc) - 1
        low, high = left, right

        while low <= high:
            mid = (low + high) // 2  # Binary search

            if tdp[admstc[mid]] > tdp[irep]:
                high = mid - 1
            elif tdp[admstc[mid]] < tdp[irep]:
                low = mid + 1
            else:
                return mid

            # Linear search
            if admstc[right] == irep:
                return right
            right -= 1

            if admstc[left] == irep:
                return left
            left += 1

        return -1
    
    
    def adjust_cluster_by_tdp_change(current_cluster_id, tdp_change, admstc, size, child, tdp, mark):
        """
        Adjust the cluster membership by modifying the TDP threshold.

        Args:
            current_cluster_id (int): The hierarchical node ID of the selected cluster.
            tdp_change (float): The change in TDP threshold (positive or negative).
            admstc (list): List of admissible nodes (ADMSTC).
            size (list): Sizes of the subtrees rooted at each node.
            child (list): Child relationships of the hierarchical tree.
            tdp (list): TDP values for all nodes.
            mark (list): Marking array to avoid duplicate processing.

        Returns:
            list: Updated list of voxel indices for the cluster after adjustment.
        """
        print(f"Adjusting Cluster for Node {current_cluster_id} with TDP Change {tdp_change}")

        # Fetch descendants of the current cluster to mark them
        initial_descendants = get_clusters.descendants(current_cluster_id, size, child)
        for node in initial_descendants:
            mark[node] = 1  # Mark current cluster nodes

        # Find the index of the cluster representative in ADMSTC using find_index
        cluster_rep_index = get_clusters.find_index(current_cluster_id, admstc, tdp)
        if cluster_rep_index == -1:
            raise ValueError(f"Cluster representative {current_cluster_id} not found in ADMSTC.")

        updated_cluster = []

        if tdp_change < 0:  # Decreasing TDP (enlarge cluster)
            for i in range(cluster_rep_index - 1, -1, -1):  # Iterate backward
                node = admstc[i]
                if (
                    tdp[node] >= 0 and 
                    tdp[current_cluster_id] - tdp[node] <= -tdp_change and 
                    size[node] > size[current_cluster_id]
                ):
                    descendants = get_clusters.descendants(node, size, child)
                    updated_cluster.extend(descendants)
                    for d in descendants:
                        mark[d] = 2  # Mark as added

        else:  # Increasing TDP (shrink cluster)
            for i in range(cluster_rep_index + 1, len(admstc)):  # Iterate forward
                node = admstc[i]
                if (
                    tdp[node] >= 0 and 
                    tdp[node] - tdp[current_cluster_id] >= tdp_change and 
                    mark[node] == 1
                ):
                    descendants = get_clusters.descendants(node, size, child)
                    updated_cluster.extend(descendants)
                    for d in descendants:
                        mark[d] = 2  # Mark as removed

        # Reset marks
        for node in initial_descendants:
            mark[node] = 0

        # If no changes, return the initial cluster
        if not updated_cluster:
            updated_cluster = initial_descendants

        print(f"Updated Cluster: {len(updated_cluster)} nodes")
        return updated_cluster
    

    def adjust_cluster_by_tdp_change_focused(current_cluster_id, tdp_change, admstc, size, child, tdp, mark):
        """
        Adjust cluster membership by modifying the TDP threshold, isolating changes to the selected cluster.

        Args:
            current_cluster_id (int): The hierarchical node ID of the selected cluster.
            tdp_change (float): The change in TDP threshold (positive or negative).
            admstc (list): List of admissible nodes (ADMSTC).
            size (list): Sizes of the subtrees rooted at each node.
            child (list): Child relationships of the hierarchical tree.
            tdp (list): TDP values for all nodes.
            mark (list): Marking array to avoid duplicate processing.

        Returns:
            dict: A dictionary with `added` and `removed` nodes related to the current cluster.
        """
        print(f"Adjusting Cluster for Node {current_cluster_id} with TDP Change {tdp_change}")

        # Initialize trackers for added and removed nodes
        added_nodes = []
        removed_nodes = []

        # Fetch initial descendants of the current cluster to mark them
        initial_descendants = get_clusters.descendants(current_cluster_id, size, child)
        for node in initial_descendants:
            mark[node] = 1  # Mark current cluster nodes

        # Find the index of the cluster representative in ADMSTC
        cluster_rep_index = get_clusters.find_index(current_cluster_id, admstc, tdp)
        if cluster_rep_index == -1:
            raise ValueError(f"Cluster representative {current_cluster_id} not found in ADMSTC.")

        if tdp_change < 0:  # Decreasing TDP (enlarge cluster)
            for i in range(cluster_rep_index - 1, -1, -1):  # Traverse backward in ADMSTC
                node = admstc[i]
                if (
                    tdp[node] >= 0 and 
                    tdp[current_cluster_id] - tdp[node] <= -tdp_change and 
                    size[node] > size[current_cluster_id]
                ):
                    descendants = get_clusters.descendants(node, size, child)
                    # Add only descendants not in the initial cluster
                    for d in descendants:
                        if mark[d] == 0:  # Newly added
                            added_nodes.append(d)
                            mark[d] = 2  # Mark as added

        else:  # Increasing TDP (shrink cluster)
            for i in range(cluster_rep_index + 1, len(admstc)):  # Traverse forward in ADMSTC
                node = admstc[i]
                if (
                    tdp[node] >= 0 and 
                    tdp[node] - tdp[current_cluster_id] >= tdp_change and 
                    mark[node] == 1
                ):
                    descendants = get_clusters.descendants(node, size, child)
                    # Add only descendants that are in the initial cluster
                    for d in descendants:
                        if mark[d] == 1:  # Previously part of the cluster
                            removed_nodes.append(d)
                            mark[d] = 2  # Mark as removed

        # Reset marks
        for node in initial_descendants:
            mark[node] = 0

        # Reset marks for added/removed nodes
        for node in added_nodes + removed_nodes:
            mark[node] = 0

        print(f"Added Nodes: {len(added_nodes)}")
        print(f"Removed Nodes: {len(removed_nodes)}")

        return {"added": added_nodes, "removed": removed_nodes}
    
    @staticmethod
    def findRep(v, size, ans):
        """
        Find the index of the cluster that contains voxel v in the cluster list ans.

        Parameters:
            v (int): The voxel index to find.
            size (list): List of subtree sizes for all nodes.
            ans (list of lists): List of clusters, where each cluster is a list of node indices.

        Returns:
            int: The index of the cluster containing v, or -1 if not found.
        """
        for i, clus in enumerate(ans):
            irep = clus[-1]  # Representative of the cluster (last element)

            # Check if the representative matches the voxel
            if irep == v:
                return i

            # Check subtree sizes
            if size[irep] > size[v]:
                left = 0
                right = len(clus) - 1

                # Perform a linear search
                while left <= right:
                    if clus[left] == v:
                        return i
                    left += 1

                    if clus[right] == v:
                        return i
                    right -= 1

        return -1
    

    # @staticmethod
    # def change_query(v, tdpchg, admstc, size, mark, tdp, child, ans):
    #     """
    #     Modify the cluster membership by changing the TDP threshold for a given cluster.

    #     Args:
    #         v (int): 0-based node index.
    #         tdpchg (float): Expected change in TDP. Positive values increase the TDP bound or reduce cluster size.
    #         admstc (list): Admissible vertices, sorted by TDP.
    #         size (list): Subtree sizes for all nodes.
    #         mark (list): Node markers, used to track visited nodes.
    #         tdp (list): TDP values for all nodes.
    #         child (list): Children list for all vertices.
    #         ans (list of lists): Cluster list, normally the output of `answerQuery`.

    #     Returns:
    #         list of lists: Updated clusters after adjusting the TDP.
    #     """
    #     # Initialize output cluster list
    #     chg = []

    #     # Ensure 'v' is valid
    #     if v < 0:
    #         raise ValueError("'v' should be non-negative")

    #     # Find the cluster containing 'v'
    #     iclus = get_clusters.findRep(v, size, ans)
    #     if iclus < 0:
    #         raise ValueError("No cluster can be specified with 'v'")
    #     clus = ans[iclus]

    #     # Find the index of the cluster representative in ADMSTC
    #     idxv = get_clusters.find_index(clus[-1], admstc, tdp)
    #     if idxv < 0:
    #         raise ValueError("The chosen cluster cannot be found in 'ADMSTC'")

    #     # Validate tdpchg
    #     if tdpchg <= -1 or tdpchg == 0 or tdpchg >= 1:
    #         raise ValueError("'tdpchg' must be non-zero & within (-1,1)")

    #     # Check TDP boundaries
    #     maxtdp = tdp[admstc[-1]]
    #     mintdp = tdp[admstc[0]]
    #     curtdp = tdp[clus[-1]]

    #     if (tdpchg < 0 and mintdp == curtdp) or (tdpchg > 0 and maxtdp == curtdp):
    #         raise ValueError("No further changes can be attained")

    #     if tdpchg < 0 and mintdp - curtdp > tdpchg:
    #         raise ValueError("A further TDP reduction cannot be achieved")

    #     if tdpchg > 0 and maxtdp - curtdp < tdpchg:
    #         raise ValueError("A further TDP augmentation cannot be achieved")

    #     # Mark all nodes in the cluster
    #     for node in clus:
    #         mark[node] = 1

    #     if tdpchg < 0:  # Increase cluster size or decrease TDP
    #         for i in range(idxv - 1, -1, -1):
    #             if (
    #                 tdp[admstc[i]] >= 0
    #                 and tdp[admstc[i]] - tdp[admstc[idxv]] <= tdpchg
    #                 and size[admstc[i]] > size[admstc[idxv]]
    #             ):
    #                 desc = get_clusters.descendants(admstc[i], size, child)

    #                 left, right = 0, len(desc) - 1
    #                 while left <= right:
    #                     if mark[desc[left]] > 0 or mark[desc[right]] > 0:
    #                         chg.append(desc)

    #                         # Append remaining clusters to CHG
    #                         dfsz = len(desc) - len(clus)
    #                         for j, cluster in enumerate(ans):
    #                             if j != iclus:
    #                                 if dfsz >= len(cluster):
    #                                     for node in cluster:
    #                                         mark[node] = 2

    #                                     # Check if desc contains the cluster
    #                                     l, r = 0, len(desc) - 1
    #                                     while r - l >= len(cluster) - 1:
    #                                         if mark[desc[l]] == 2 or mark[desc[r]] == 2:
    #                                             dfsz -= len(cluster)
    #                                             break
    #                                         l += 1
    #                                         r -= 1

    #                                     if l > len(desc) - 1 or r < 0 or (
    #                                         mark[desc[l]] != 2 and mark[desc[r]] != 2
    #                                     ):
    #                                         chg.append(cluster)

    #                                     for node in cluster:
    #                                         mark[node] = 0
    #                                 else:
    #                                     chg.append(cluster)

    #                         # Reset marks
    #                         for node in clus:
    #                             mark[node] = 0

    #                         return chg

    #                     left += 1
    #                     right -= 1
    #     else:  # Decrease cluster size or increase TDP
    #         for i in range(idxv + 1, len(admstc)):
    #             if (
    #                 tdp[admstc[i]] >= 0
    #                 and tdp[admstc[i]] - tdp[admstc[idxv]] >= tdpchg
    #                 and mark[admstc[i]] == 1
    #             ):
    #                 desc = get_clusters.descendants(admstc[i], size, child)
    #                 chg.append(desc)
    #                 for node in desc:
    #                     mark[node] = 2                    

    #         # Append remaining clusters to CHG
    #         for j, cluster in enumerate(ans):
    #             if j != iclus:
    #                 chg.append(cluster)

    #     # Reset marks
    #     for node in clus:
    #         mark[node] = 0

    #     return chg
    

    @staticmethod
    def change_query(v, tdpchg, admstc, size, mark, tdp, child, ans):
        """
        Modify the cluster membership by changing the TDP threshold for a given cluster.
        This optimized version minimizes repeated loops and leverages NumPy vectorized
        operations where possible.

        Args:
            v (int): 0-based node index.
            tdpchg (float): Expected change in TDP. Positive values increase the TDP bound or reduce cluster size.
            admstc (list): Admissible vertices, sorted by TDP.
            size (list): Subtree sizes for all nodes.
            mark (list): Node markers (assumed mutable), used to track visited nodes.
            tdp (list): TDP values for all nodes.
            child (list): Children list for all vertices.
            ans (list of lists): Cluster list, normally the output of `answerQuery`.

        Returns:
            list of lists: Updated clusters after adjusting the TDP.
        """
        # Validate input v.
        if v < 0:
            print("\033[91m" + "ERROR! Change Query Error 1: 'v' should be non-negative" + "\033[0m")
            return ans
        
        iclus = get_clusters.findRep(v, size, ans)
        if iclus < 0:
            print("\033[91m" + "ERROR! Change Query Error 2: No cluster can be specified with 'v'" + "\033[0m")
            return ans
        clus = ans[iclus]
        
        idxv = get_clusters.find_index(clus[-1], admstc, tdp)
        if idxv < 0:
            print("\033[91m" + "ERROR! Change Query Error 3: The chosen cluster cannot be found in 'ADMSTC'" + "\033[0m")
            return ans
        
        if tdpchg <= -1 or tdpchg == 0 or tdpchg >= 1:
            print("\033[91m" + "ERROR! Change Query Error 4: 'tdpchg' must be non-zero & within (-1,1)" + "\033[0m")
            return ans
        
        maxtdp = tdp[admstc[-1]]
        mintdp = tdp[admstc[0]]
        curtdp = tdp[clus[-1]]
        
        if (tdpchg < 0 and mintdp == curtdp) or (tdpchg > 0 and maxtdp == curtdp):
            print("\033[91m" + f"ERROR! Change Query Error 5: No further changes can be attained" + "\033[0m")
            return ans

        if tdpchg < 0 and mintdp - curtdp > tdpchg:
            print("\033[91m" + f"ERROR! Change Query Error 6: A further TDP reduction cannot be achieved" + "\033[0m")
            return ans

        # if tdpchg > 0 and maxtdp - curtdp < tdpchg:
        # We add a small tolerance to account for floating-point rounding errors.
        # Without this epsilon, slight numerical discrepancies might falsely trigger the error condition
        # (i.e. when maxtdp - curtdp is only marginally less than tdpchg due to rounding).
        # epsilon = 1e-6
        # if tdpchg > 0 and (maxtdp - curtdp < tdpchg - epsilon):
        if tdpchg > 0 and maxtdp - curtdp < tdpchg:
            print("\033[91m" + f"ERROR! Change Query Error 7: A further TDP augmentation cannot be achieved" + "\033[0m")
            return ans
        
        # Mark nodes in the current cluster (use a simple loop; if mark were a NumPy array, vectorized assignment could be used)
        for node in clus:
            mark[node] = 1

        chg = []
        # Cache the current cluster's TDP for reuse
        cur_cluster_tdp = curtdp


        if tdpchg < 0:
            # TDP reduction: Increase cluster size (or decrease TDP) by iterating backward over admstc.
            for i in range(idxv - 1, -1, -1):
                node_i = admstc[i]
                # Check candidate conditions:
                #    TDP[node_i] >= 0,
                #    (TDP[node_i] - TDP[admstc[idxv]]) <= tdpchg,
                #    and SIZE[node_i] > SIZE[admstc[idxv]]
                if tdp[node_i] >= 0 and (tdp[node_i] - tdp[admstc[idxv]] <= tdpchg) and (size[node_i] > size[admstc[idxv]]):
                    desc = get_clusters.descendants(node_i, size, child)
                    left = 0
                    right = len(desc) - 1
                    while left <= right:
                        if mark[desc[left]] > 0 or mark[desc[right]] > 0:
                            chg.append(desc)
                            dfsz = len(desc) - len(clus)
                            # For every other cluster in ans (except the selected one)
                            for j, cluster in enumerate(ans):
                                if j == iclus:
                                    continue
                                if dfsz >= len(cluster):
                                    for k in range(len(cluster)):
                                        mark[cluster[k]] = 2
                                    l = 0
                                    r = len(desc) - 1
                                    while (r - l) >= (len(cluster) - 1):
                                        if mark[desc[l]] == 2 or mark[desc[r]] == 2:
                                            dfsz = dfsz - len(cluster)
                                            break
                                        l += 1
                                        r -= 1
                                    if l > len(desc) - 1 or r < 0 or (mark[desc[l]] != 2 and mark[desc[r]] != 2):
                                        chg.append(cluster)
                                    for k in range(len(cluster)):
                                        mark[cluster[k]] = 0
                                else:
                                    chg.append(cluster)
                            # Reset marks for nodes in the selected cluster before returning.
                            for node in clus:
                                mark[node] = 0
                            return chg
                        left += 1
                        right -= 1
        else:
            # TDP augmentation: Decrease cluster size (or increase TDP) by iterating forward over admstc.
            for i in range(idxv + 1, len(admstc)):
                node_i = admstc[i]
                if tdp[node_i] >= 0 and (tdp[node_i] - cur_cluster_tdp >= tdpchg) and (mark[node_i] == 1):
                    desc = get_clusters.descendants(node_i, size, child)
                    chg.append(desc)
                    for d in desc:
                        mark[d] = 2
            # Append all clusters (except the selected one) from ans.
            for j, cluster in enumerate(ans):
                if j != iclus:
                    chg.append(cluster)
        
        # Clear the marks in the selected cluster.
        for node in clus:
            mark[node] = 0

        return chg
    
    @staticmethod
    def check_tdp_change(v, tdpchg, admstc, size, tdp, ans, mark):
        """
        Modify the cluster membership by changing the TDP threshold for a given cluster.
        Instead of raising errors, this method returns a dictionary with an error code and message.
        
        Args:
            v (int): 0-based node index.
            tdpchg (float): Expected change in TDP. Positive values increase the TDP bound or reduce cluster size.
            admstc (list): Admissible vertices, sorted by TDP.
            size (list): Subtree sizes for all nodes.
            tdp (list): TDP values for all nodes.
            ans (list of lists): Cluster list, normally the output of `answerQuery`.
            mark (list): Node marker array, used to determine if a node is part of the updated clusters.

        Returns:
            dict: A dictionary with keys:
                "error_code" (int): 0 if no error; otherwise a positive integer identifying the error.
                "error_message" (str): Description of the error or "No error" if none.
        """
        # Initialize the error dictionary
        error_info = {}
    
        # Error 1: v must be non-negative.
        if v < 0:
            error_info["error_code"] = 1
            error_info["error_message"] = "'v' should be non-negative"
            return error_info

        # Error 2: Ensure a cluster is specified with 'v'.
        iclus = get_clusters.findRep(v, size, ans)
        if iclus < 0:
            error_info["error_code"] = 2
            error_info["error_message"] = "No cluster can be specified with 'v'"
            return error_info
        clus = ans[iclus]

        # Error 3: The chosen cluster must be found in ADMSTC.
        idxv = get_clusters.find_index(clus[-1], admstc, tdp)
        if idxv < 0:
            error_info["error_code"] = 3
            error_info["error_message"] = "The chosen cluster cannot be found in 'ADMSTC'"
            return error_info

        # Error 4: Validate tdpchg is non-zero and within (-1, 1).
        if tdpchg <= -1 or tdpchg == 0 or tdpchg >= 1:
            error_info["error_code"] = 4
            error_info["error_message"] = "'tdpchg' must be non-zero & within (-1,1)"
            return error_info

        # Get boundary TDP values and the current cluster's TDP.
        maxtdp = tdp[admstc[-1]]
        mintdp = tdp[admstc[0]]
        curtdp = tdp[clus[-1]]

        # Error 5: If cluster's TDP is at an extreme, no further changes can be attained.
        if (tdpchg < 0 and mintdp == curtdp) or (tdpchg > 0 and maxtdp == curtdp):
            error_info["error_code"] = 5
            error_info["error_message"] = f"ERROR! Change Query Error 5: No further changes can be attained as the current TDP = {curtdp:.10f}"
            return error_info

        # Error 6: For a TDP reduction, ensure the requested change is possible.
        if tdpchg < 0 and mintdp - curtdp > tdpchg:
            error_info["error_code"] = 6
            error_info["error_message"] = (
                f"ERROR! Change Query Error 6: A further TDP reduction of {abs(tdpchg):.5f} cannot be achieved "
                f"as min(TDP) = {mintdp:.10f} and curr(TDP) = {curtdp:.10f}"
            )
            return error_info

        # Error 7: For a TDP augmentation, ensure the requested change is possible.
        if tdpchg > 0 and maxtdp - curtdp < tdpchg:
            error_info["error_code"] = 7
            error_info["error_message"]  = (
                f"ERROR! Change Query Error 7: A further TDP augmentation of {tdpchg:.5f} cannot be achieved "
                f"as max(TDP) = {maxtdp:.10f} and curr(TDP) = {curtdp:.10f}"
            )
            return error_info
        
            # Error 8: The chosen node is not inside the updated clusters.
        # if mark[v] <= 1:  # Only log this if the node is NOT inside the output clusters
        #     error_info["error_code"] = 8
        #     error_info["error_message"] = (
        #         "ERROR! Change Query Error 8: The chosen node is not inside the output clusters."
        #     )
        #     return error_info

        # If no error conditions occur, return a dictionary indicating no error.
        error_info["error_code"] = 0
        error_info["error_message"] = "No error"
        return error_info
    
    def counting_sort(n, maxid, cluster_sizes):
        """
        Counting sort in descending order of cluster sizes.

        Args:
            n (int): Number of clusters.
            maxid (int): Maximum cluster size.
            cluster_sizes (list or np.ndarray): List of cluster sizes.

        Returns:
            np.ndarray: Sorted indices in descending order of cluster sizes.
        """
        # Initialize the count array
        count = np.zeros(maxid + 1, dtype=int)
        
        # Count the frequency of each cluster size
        for size in cluster_sizes:
            count[size] += 1
        
        # Compute cumulative frequency for descending order
        for i in range(maxid - 1, -1, -1):
            count[i] += count[i + 1]
        
        # Initialize the sorted indices array
        sorted_indices = np.zeros(n, dtype=int)
        
        # Place indices into the sorted array
        for idx, size in enumerate(cluster_sizes):
            sorted_indices[count[size] - 1] = idx
            count[size] -= 1
        
        return sorted_indices