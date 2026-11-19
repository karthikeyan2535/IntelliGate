"""
Curated 100-Problem Competitive Coding Benchmark Dataset.
Category Distribution:
- Arrays and Strings: 20 problems
- Dynamic Programming: 20 problems
- Graphs: 20 problems
- Trees and Data Structures: 15 problems
- Greedy and Binary Search: 15 problems
- Debugging and Code Repair: 10 problems
Total = 100 benchmark problems with train/test separation (70 calibration / 30 held-out test).
"""
from __future__ import annotations

from typing import List, Dict, Any


def get_curated_benchmark_problems() -> List[Dict[str, Any]]:
    problems = []

    # ──────────────────────────────────────────────────────────────────────────
    # 1. ARRAYS AND STRINGS (20 Problems: benchmark-as-01 to benchmark-as-20)
    # ──────────────────────────────────────────────────────────────────────────
    as_defs = [
        ("Two Sum Sorted", "Given sorted array and target sum, return 1-based indices.", "3 9\n2 7 11\n", "1 2\n", "easy"),
        ("Valid Palindrome Alphanumeric", "Check if phrase is palindrome ignoring case and non-alphanumeric.", "A man, a plan, a canal: Panama\n", "true\n", "easy"),
        ("Longest Substring Without Repeating", "Length of longest substring without repeating characters.", "abcabcbb\n", "3\n", "medium"),
        ("String Compression Run-Length", "Compress string using counts of repeated characters.", "aabcccccaaa\n", "a2b1c5a3\n", "easy"),
        ("Maximum Product Subarray", "Find contiguous subarray having largest product.", "4\n2 3 -2 4\n", "6\n", "medium"),
        ("Subarray Sum Equals K", "Count total contiguous subarrays whose sum equals k.", "3 2\n1 1 1\n", "2\n", "medium"),
        ("Product of Array Except Self", "Return array such that out[i] is product of all elements except num[i].", "4\n1 2 3 4\n", "24 12 8 6\n", "medium"),
        ("Rotate Array Right by K Steps", "Rotate array to right by k steps in-place.", "7 3\n1 2 3 4 5 6 7\n", "5 6 7 1 2 3 4\n", "medium"),
        ("Group Anagrams Sorted", "Group strings that are anagrams together.", "eat tea tan ate nat bat\n", "ate eat tea\nbat\nnat tan\n", "medium"),
        ("Container With Most Water", "Find two lines that together with x-axis forms a container of max water.", "9\n1 8 6 2 5 4 8 3 7\n", "49\n", "medium"),
        ("Trap Rain Water 1D", "Compute how much water elevation map is able to trap after raining.", "12\n0 1 0 2 1 0 1 3 2 1 2 1\n", "6\n", "hard"),
        ("Merge Sorted Array In-Place", "Merge nums2 into nums1 as one sorted array.", "3 3\n1 2 3\n2 5 6\n", "1 2 2 3 5 6\n", "easy"),
        ("Spiral Matrix Traversal", "Return all elements of matrix in spiral order.", "3 3\n1 2 3\n4 5 6\n7 8 9\n", "1 2 3 6 9 8 7 4 5\n", "medium"),
        ("Set Matrix Zeroes In-Place", "If an element is 0, set its entire row and column to 0.", "3 3\n1 1 1\n1 0 1\n1 1 1\n", "1 0 1\n0 0 0\n1 0 1\n", "medium"),
        ("Longest Common Prefix", "Find longest common prefix string amongst an array of strings.", "flower flow flight\n", "fl\n", "easy"),
        ("Valid Anagram Hash Check", "Check if t is an anagram of s.", "anagram nagaram\n", "true\n", "easy"),
        ("Reverse Words in String", "Reverse the order of words with single space separation.", "the sky is blue\n", "blue is sky the\n", "medium"),
        ("Find First and Last Position in Sorted", "Find starting and ending position of a given target value in sorted array.", "6 8\n5 7 7 8 8 10\n", "3 4\n", "medium"),
        ("Minimum Window Substring", "Find smallest substring containing all characters of pattern.", "ADOBECODEBANC ABC\n", "BANC\n", "hard"),
        ("Sliding Window Maximum K", "Find max value in every sliding window of size k.", "8 3\n1 3 -1 -3 5 3 6 7\n", "3 3 5 5 6 7\n", "hard"),
    ]
    for i, (t, s, inp, exp, diff) in enumerate(as_defs):
        split = "test" if i % 3 == 0 else "calibration"
        problems.append({
            "id": f"benchmark-as-{i+1:02d}",
            "title": t,
            "statement": f"{s}\n\nInput format:\nRead from standard input.\nOutput format:\nPrint result to standard output.",
            "constraints": "1 <= N <= 200,000. Time limit: 2.0s, Memory limit: 256MB.",
            "algorithm_category": "arrays_strings",
            "difficulty": diff,
            "benchmark_split": split,
            "sample_input": inp,
            "sample_expected": exp,
        })

    # ──────────────────────────────────────────────────────────────────────────
    # 2. DYNAMIC PROGRAMMING (20 Problems: benchmark-dp-01 to benchmark-dp-20)
    # ──────────────────────────────────────────────────────────────────────────
    dp_defs = [
        ("Climbing Stairs Ways", "Distinct ways to climb n stairs taking 1 or 2 steps.", "3\n", "3\n", "easy"),
        ("Coin Change Fewest Coins", "Fewest number of coins needed to make up amount.", "3 11\n1 2 5\n", "3\n", "medium"),
        ("Longest Increasing Subsequence Length", "Length of the longest strictly increasing subsequence.", "8\n10 9 2 5 3 7 101 18\n", "4\n", "medium"),
        ("0-1 Knapsack Classic", "Maximum value of items fitting in knapsack of capacity W.", "3 50\n60 100 120\n10 20 30\n", "220\n", "medium"),
        ("Longest Common Subsequence", "Length of longest common subsequence of two strings.", "abcde ace\n", "3\n", "medium"),
        ("Edit Distance Levenshtein", "Minimum operations to convert word1 to word2.", "horse ros\n", "3\n", "medium"),
        ("House Robber Max Loot", "Max money you can rob tonight without alerting adjacent houses.", "4\n1 2 3 1\n", "4\n", "medium"),
        ("Partition Equal Subset Sum", "Can array be partitioned into two subsets with equal sum?", "4\n1 5 11 5\n", "true\n", "medium"),
        ("Unique Paths in Grid", "Number of unique paths from top-left to bottom-right moving down/right.", "3 7\n", "28\n", "medium"),
        ("Minimum Path Sum Grid", "Find a path from top-left to bottom-right minimizing sum of numbers.", "3 3\n1 3 1\n1 5 1\n4 2 1\n", "7\n", "medium"),
        ("Word Break Feasibility", "Can string be segmented into space-separated dictionary words?", "leetcode\n2\nleet code\n", "true\n", "medium"),
        ("Maximal Square in Matrix", "Find largest square containing only 1s and return its area.", "4 5\n1 0 1 0 0\n1 0 1 1 1\n1 1 1 1 1\n1 0 0 1 0\n", "4\n", "medium"),
        ("Best Time to Buy and Sell Stock with Cooldown", "Max profit with transaction cooldown period of 1 day.", "5\n1 2 3 0 2\n", "3\n", "medium"),
        ("Decode Ways Digits", "Number of ways to decode digit string to letters A-Z.", "226\n", "3\n", "medium"),
        ("Target Sum Expression Signs", "Ways to assign + or - signs so sum equals target.", "5 3\n1 1 1 1 1\n", "5\n", "medium"),
        ("Coin Change II Total Ways", "Number of combinations that make up the given amount.", "3 5\n1 2 5\n", "4\n", "medium"),
        ("Burst Balloons DP", "Max coins collected by bursting balloons wisely.", "4\n3 1 5 8\n", "167\n", "hard"),
        ("Russian Doll Envelopes", "Max envelopes you can Russian doll (fit one inside another).", "4\n5 4\n6 4\n6 7\n2 3\n", "3\n", "hard"),
        ("Palindrome Partitioning II Min Cuts", "Min cuts needed for palindrome partitioning of string.", "aab\n", "1\n", "hard"),
        ("Interleaving String DP", "Determine whether s3 is formed by an interleaving of s1 and s2.", "aabcc dbbca aadbbcbcac\n", "true\n", "medium"),
    ]
    for i, (t, s, inp, exp, diff) in enumerate(dp_defs):
        split = "test" if i % 3 == 0 else "calibration"
        problems.append({
            "id": f"benchmark-dp-{i+1:02d}",
            "title": t,
            "statement": f"{s}\n\nStandard competitive programming format.",
            "constraints": "1 <= N <= 100,000. Time limit: 2.0s, Memory limit: 256MB.",
            "algorithm_category": "dynamic_programming",
            "difficulty": diff,
            "benchmark_split": split,
            "sample_input": inp,
            "sample_expected": exp,
        })

    # ──────────────────────────────────────────────────────────────────────────
    # 3. GRAPHS (20 Problems: benchmark-gr-01 to benchmark-gr-20)
    # ──────────────────────────────────────────────────────────────────────────
    gr_defs = [
        ("Breadth-First Search Traversal", "BFS traversal of unweighted graph starting from node 0.", "4 4\n0 1\n0 2\n1 2\n2 3\n", "0 1 2 3\n", "easy"),
        ("Connected Components Count", "Count number of connected components in undirected graph.", "5 3\n0 1\n1 2\n3 4\n", "2\n", "medium"),
        ("Dijkstra Shortest Path", "Shortest path from source 0 to all vertices in non-negative weighted graph.", "3 3\n0 1 4\n1 2 3\n0 2 8\n", "0 4 7\n", "medium"),
        ("Course Schedule Cycle Detection", "Is it possible to finish all courses without dependency cycle?", "2 1\n1 0\n", "true\n", "medium"),
        ("Course Schedule II Topological Order", "Return topological sort ordering of courses.", "4 4\n1 0\n2 0\n3 1\n3 2\n", "0 1 2 3\n", "medium"),
        ("Number of Islands 2D Grid", "Count islands (groups of 1s connected horizontally/vertically).", "4 5\n1 1 0 0 0\n1 1 0 0 0\n0 0 1 0 0\n0 0 0 1 1\n", "3\n", "medium"),
        ("Rotting Oranges Multisource BFS", "Minimum minutes until no fresh orange remains.", "3 3\n2 1 1\n1 1 0\n0 1 1\n", "4\n", "medium"),
        ("Word Ladder Shortest Transformation", "Length of shortest transformation sequence from begin to end word.", "hit cog\n6\nhot dot dog lot log cog\n", "5\n", "hard"),
        ("Clone Graph Deep Copy", "Return deep copy of connected undirected graph.", "4 4\n1 2\n2 3\n3 4\n4 1\n", "1 2 3 4\n", "medium"),
        ("Network Delay Time Bellman/Dijkstra", "Time taken for all nodes to receive signal from source.", "3 4 2\n2 1 1\n2 3 1\n3 4 1\n", "2\n", "medium"),
        ("Is Graph Bipartite 2-Coloring", "Can graph vertices be partitioned into two independent sets?", "4 4\n0 1\n0 3\n1 2\n2 3\n", "true\n", "medium"),
        ("Cheapest Flights Within K Stops", "Cheapest flight price from src to dst with at most k stops.", "4 3 0 3 1\n0 1 100\n1 2 100\n2 3 100\n0 2 500\n", "500\n", "medium"),
        ("Reconstruct Itinerary Eulerian Path", "Reconstruct itinerary in lexical order using all tickets once.", "4\nMUC LHR\nJFK MUC\nSFO SJC\nLHR SFO\n", "JFK MUC LHR SFO SJC\n", "hard"),
        ("Alien Dictionary Topological Sort", "Derive alphabetical order of alien language characters.", "5\nwrt wrf er ett rftt\n", "wertf\n", "hard"),
        ("Critical Connections Tarjan Bridges", "Find all critical connections (bridges) in network.", "4 4\n0 1\n1 2\n2 0\n1 3\n", "1 3\n", "hard"),
        ("Surrounded Regions Flood Fill", "Capture all regions surrounded by 'X' in grid.", "4 4\nX X X X\nX O O X\nX X O X\nX O X X\n", "X X X X\nX X X X\nX X X X\nX O X X\n", "medium"),
        ("Pacific Atlantic Water Flow", "Coordinates where rain water can flow to both oceans.", "3 3\n1 2 2\n3 2 3\n2 2 4\n", "0 2\n1 0\n1 1\n1 2\n2 0\n2 1\n2 2\n", "medium"),
        ("Minimum Spanning Tree Kruskal", "Total weight of minimum spanning tree.", "4 5\n0 1 10\n0 2 6\n0 3 5\n1 3 15\n2 3 4\n", "19\n", "medium"),
        ("Shortest Path in Binary Matrix", "Length of shortest clear path in binary matrix 8-directionally.", "2 2\n0 1\n1 0\n", "2\n", "medium"),
        ("Evaluate Division Graph Path", "Calculate query equations based on given ratio edges.", "2\na b 2.0\nb c 3.0\n1\na c\n", "6.0\n", "medium"),
    ]
    for i, (t, s, inp, exp, diff) in enumerate(gr_defs):
        split = "test" if i % 3 == 0 else "calibration"
        problems.append({
            "id": f"benchmark-gr-{i+1:02d}",
            "title": t,
            "statement": f"{s}\n\nInput format:\nStandard graph representation.\nOutput format:\nValues space-separated or lines.",
            "constraints": "V <= 50,000, E <= 150,000. Time limit: 2.0s, Memory limit: 256MB.",
            "algorithm_category": "graphs",
            "difficulty": diff,
            "benchmark_split": split,
            "sample_input": inp,
            "sample_expected": exp,
        })

    # ──────────────────────────────────────────────────────────────────────────
    # 4. TREES AND DATA STRUCTURES (15 Problems: benchmark-td-01 to benchmark-td-15)
    # ──────────────────────────────────────────────────────────────────────────
    td_defs = [
        ("Binary Tree Level Order Traversal", "Return level order traversal of nodes values.", "3 9 20 -1 -1 15 7\n", "3\n9 20\n15 7\n", "medium"),
        ("Lowest Common Ancestor BST", "Find LCA of two given nodes in Binary Search Tree.", "6 2 8 0 4 7 9 -1 -1 3 5\n2 8\n", "6\n", "easy"),
        ("Validate Binary Search Tree", "Determine if binary tree is valid BST.", "2 1 3\n", "true\n", "medium"),
        ("Invert Binary Tree Mirror", "Invert a binary tree and return its root representation.", "4 2 7 1 3 6 9\n", "4 7 2 9 6 3 1\n", "easy"),
        ("Binary Tree Maximum Path Sum", "Find maximum path sum of any non-empty path in binary tree.", "3 9 20 -1 -1 15 7\n", "42\n", "hard"),
        ("Serialize and Deserialize Binary Tree", "Design algorithm to serialize and deserialize binary tree.", "1 2 3 -1 -1 4 5\n", "1 2 3 null null 4 5\n", "hard"),
        ("Implement Trie Prefix Tree", "Implement insert, search, and startsWith operations.", "insert apple\nsearch apple\nsearch app\nstartsWith app\n", "null true false true\n", "medium"),
        ("Merge K Sorted Lists Min-Heap", "Merge k sorted linked lists and return as one sorted list.", "3\n1 4 5\n1 3 4\n2 6\n", "1 1 2 3 4 4 5 6\n", "hard"),
        ("Find Median from Data Stream", "Continuous median query over streaming integers.", "add 1\nadd 2\nfindMedian\nadd 3\nfindMedian\n", "1.5 2.0\n", "hard"),
        ("Kth Largest Element in Array QuickSelect", "Find kth largest element in unsorted array.", "6 2\n3 2 1 5 6 4\n", "5\n", "medium"),
        ("LRU Cache Implementation", "Design LRU cache with capacity, get, and put methods.", "capacity 2\nput 1 1\nput 2 2\nget 1\nput 3 3\nget 2\n", "null null 1 null -1\n", "medium"),
        ("Min Stack Constant Time", "Design a stack that supports push, pop, top, and getMin in O(1).", "push -2\npush 0\npush -3\ngetMin\npop\ntop\ngetMin\n", "-3 0 -2\n", "medium"),
        ("Construct Binary Tree Preorder Inorder", "Construct tree given preorder and inorder traversals.", "3 9 20 15 7\n9 3 15 20 7\n", "3 9 20 null null 15 7\n", "medium"),
        ("Diameter of Binary Tree", "Length of the longest path between any two nodes in a tree.", "5\n1 2 3 4 5\n", "3\n", "easy"),
        ("Range Sum Query Mutable Segment Tree", "Range sum queries with point updates.", "5\n1 3 5\nsum 0 2\nupdate 1 2\nsum 0 2\n", "9 8\n", "medium"),
    ]
    for i, (t, s, inp, exp, diff) in enumerate(td_defs):
        split = "test" if i % 3 == 0 else "calibration"
        problems.append({
            "id": f"benchmark-td-{i+1:02d}",
            "title": t,
            "statement": f"{s}\n\nTree and advanced data structures problem.",
            "constraints": "1 <= N <= 100,000. Time limit: 2.0s, Memory limit: 256MB.",
            "algorithm_category": "trees_data_structures",
            "difficulty": diff,
            "benchmark_split": split,
            "sample_input": inp,
            "sample_expected": exp,
        })

    # ──────────────────────────────────────────────────────────────────────────
    # 5. GREEDY AND BINARY SEARCH (15 Problems: benchmark-gb-01 to benchmark-gb-15)
    # ──────────────────────────────────────────────────────────────────────────
    gb_defs = [
        ("Binary Search Sorted Array", "Search target in sorted array in O(log n).", "6 9\n-1 0 3 5 9 12\n", "4\n", "easy"),
        ("Search in Rotated Sorted Array", "Find index of target in rotated sorted array.", "7 0\n4 5 6 7 0 1 2\n", "4\n", "medium"),
        ("Find Peak Element Logarithmic", "Find peak element strictly greater than neighbors.", "4\n1 2 3 1\n", "2\n", "medium"),
        ("Koko Eating Bananas Minimum Speed", "Minimum integer speed k to eat all bananas within h hours.", "4 8\n3 6 7 11\n", "4\n", "medium"),
        ("Capacity To Ship Packages In D Days", "Least weight capacity of ship to ship all packages within d days.", "10 5\n1 2 3 4 5 6 7 8 9 10\n", "15\n", "medium"),
        ("Median of Two Sorted Arrays", "Overall median of two sorted arrays in O(log(m+n)).", "2 2\n1 3\n2 4\n", "2.5\n", "hard"),
        ("Non-overlapping Intervals Greedy", "Min intervals to remove to make remainder non-overlapping.", "4\n1 2\n2 3\n3 4\n1 3\n", "1\n", "medium"),
        ("Jump Game Reachability", "Can you reach the last index starting at index 0?", "5\n2 3 1 1 4\n", "true\n", "medium"),
        ("Jump Game II Minimum Jumps", "Minimum number of jumps to reach last index.", "5\n2 3 1 1 4\n", "2\n", "medium"),
        ("Gas Station Circular Route", "Starting gas station index to travel around circuit once.", "5\n1 2 3 4 5\n3 4 5 1 2\n", "3\n", "medium"),
        ("Task Scheduler CPU Cooling Intervals", "Least number of units of time to finish all tasks with cooldown n.", "6 2\nA A A B B B\n", "8\n", "medium"),
        ("Candy Distribution Minimum Sum", "Minimum candies to distribute to children satisfying rating rule.", "3\n1 0 2\n", "5\n", "hard"),
        ("Split Array Largest Sum Binary Search", "Minimize the largest sum among m non-empty subarrays.", "5 2\n7 2 5 10 8\n", "18\n", "hard"),
        ("Assign Cookies Greedy Optimization", "Maximize number of content children satisfied with cookies.", "3 2\n1 2 3\n1 1\n", "1\n", "easy"),
        ("Partition Labels Max Substrings", "Partition string so each letter appears in at most one part.", "ababcbacadefegdehijhklij\n", "9 7 8\n", "medium"),
    ]
    for i, (t, s, inp, exp, diff) in enumerate(gb_defs):
        split = "test" if i % 3 == 0 else "calibration"
        problems.append({
            "id": f"benchmark-gb-{i+1:02d}",
            "title": t,
            "statement": f"{s}\n\nGreedy decision or binary search monotonic domain.",
            "constraints": "1 <= N <= 200,000. Time limit: 2.0s, Memory limit: 256MB.",
            "algorithm_category": "greedy_binary_search",
            "difficulty": diff,
            "benchmark_split": split,
            "sample_input": inp,
            "sample_expected": exp,
        })

    # ──────────────────────────────────────────────────────────────────────────
    # 6. DEBUGGING AND CODE REPAIR (10 Problems: benchmark-db-01 to benchmark-db-10)
    # ──────────────────────────────────────────────────────────────────────────
    db_defs = [
        ("Fix Off-by-One Loop Bounds", "Repair off-by-one index loop condition causing IndexError.", "3\n10 20 30\n", "60\n", "easy"),
        ("Repair Zero Division Edge Case", "Repair division without check when denominator is zero.", "0 10\n", "0\n", "easy"),
        ("Fix Integer Overflow 32-bit", "Repair multiplication overflow for values exceeding 2^31 - 1.", "100000 100000\n", "10000000000\n", "medium"),
        ("Fix Null Pointer on Empty Root", "Fix crash when tree or linked list head is null/empty.", "0\n", "null\n", "easy"),
        ("Fix Infinite Recursion Base Case", "Supply missing base case to prevent stack overflow.", "5\n", "120\n", "medium"),
        ("Repair Incorrect Float Equality", "Repair floating-point comparison with epsilon tolerance.", "0.1 0.2 0.3\n", "true\n", "medium"),
        ("Fix Unhandled Negative Modulo", "Repair remainder operator producing negative values.", "-7 3\n", "2\n", "medium"),
        ("Fix Hash Collision State Mutation", "Repair mutable object used as dictionary key.", "set 2\n", "ok\n", "medium"),
        ("Repair Deadlock Thread Ordering", "Order mutex locking to prevent circular resource deadlocks.", "run\n", "completed\n", "hard"),
        ("Fix Memory Leak Discard Buffer", "Close buffer leaks in repetitive high-frequency loop.", "10000\n", "clean\n", "medium"),
    ]
    for i, (t, s, inp, exp, diff) in enumerate(db_defs):
        split = "test" if i % 3 == 0 else "calibration"
        problems.append({
            "id": f"benchmark-db-{i+1:02d}",
            "title": t,
            "statement": f"{s}\n\nProvide the corrected, working code without errors.",
            "constraints": "Standard execution. Time limit: 2.0s, Memory limit: 256MB.",
            "algorithm_category": "debugging_repair",
            "difficulty": diff,
            "benchmark_split": split,
            "sample_input": inp,
            "sample_expected": exp,
        })

    return problems
