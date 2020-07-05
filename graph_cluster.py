"""

Implementation of:

A. Hollocou, J. Maudet, T. Bonald, M Lelarge 2017.
'A Streaming Algorithm for Graph Clustering'
Algorithm 1, p. 4
(https://arxiv.org/pdf/1712.04337v1.pdf)

"""

from collections import defaultdict


def new_graph(v_max, edges):
    degree = defaultdict(int)
    volume = defaultdict(int)
    community = defaultdict(int)
    k = 1

    for i, j in edges:
        if not community[i]:
            community[i] = k
            k += 1
        if not community[j]:
            community[j] = k
            k += 1

        degree[i] += 1
        degree[j] += 1

        volume[community[i]] += 1
        volume[community[j]] += 1

        if volume[community[i]] <= v_max and volume[community[j]] <= v_max:
            if volume[community[i]] <= volume[community[j]]:
                volume[community[j]] += degree[i]
                volume[community[i]] -= degree[i]
                community[i] = community[j]
            else:
                volume[community[i]] += degree[j]
                volume[community[j]] -= degree[j]
                community[j] = community[i]

    return community




def update_graph_once():
    pass


if __name__ == "__main__":
    test_edges = [(1, 2), (2, 3), (3, 1), (2, 4), (4, 5), (5, 6), (6, 4)]
    # test_edges = [(1, 2), (2, 3), (3, 1), (4, 5), (5, 6), (6, 4), (2, 4)]
    test_edges = [(1, 2), (2, 3), (3, 1), (2, 4), (4, 5), (5, 6), (6, 4),
            (7, 8), (8, 9), (9, 10), (10, 7), (9, 7), (7, 6), (8, 3)]
    test_vmax = 1
    for i in range(20):
        print(f"{test_vmax}:")
        d = new_graph(test_vmax, test_edges)
        test_vmax += 1
        for x in d.values():
            print(x, end=" ")
        print()
