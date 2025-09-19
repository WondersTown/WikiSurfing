import networkx as nx

# 1. Create a sample graph
G = nx.fast_gnp_random_graph(n=100, p=0.05, seed=42)

# 2. Define your center node
center_node = 42

# Create the personalization dictionary
# It gives all the starting "weight" to your center node.
personalization_dict = {node: 0 for node in G.nodes()}
personalization_dict[center_node] = 1

# 3. Run Personalized PageRank
# The `personalization` parameter biases the random walks to start from your center node.
ppr_scores = nx.pagerank(G, alpha=0.85, personalization=personalization_dict)

# 4. Sort the nodes by their score
# We exclude the center node itself from the results, as it will have the highest score.
sorted_ppr = sorted(ppr_scores.items(), key=lambda item: item[1], reverse=True)

# 5. Select and print the top 10 related nodes
print(f"Top 10 nodes most related to node {center_node}:")
top_10_related = []
for node, score in sorted_ppr:
    if node != center_node: # Exclude the center node itself
        top_10_related.append((node, score))
    if len(top_10_related) == 10:
        break

for node, score in top_10_related:
    print(f"Node {node}: {score:.5f}")