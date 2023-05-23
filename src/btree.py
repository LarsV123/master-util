import pygraphviz as pgv
from networkx.drawing.nx_agraph import to_agraph
import networkx as nx
from faker import Faker


"""
Temporary file to test out the pygraphviz library and see if it can be used to
generate a graph of the B-Tree structure.

It needs this setup:
```
sudo apt-get install graphviz graphviz-dev
pip install black matplotlib pygraphviz faker
```
"""

# Create a Faker instance to generate fake data
faker = Faker()

# Create a new graph and add nodes/edges to it
G = nx.DiGraph()

# Create a list of the names of internal nodes and leaf nodes
internal_nodes = ["A-D", "E-Z"]
leaf_nodes = ["Alice", "Bob", "Alex", "Charles", "Eve", "Karen"]

# Create a list of the actual table contents the leaf nodes represent
table = []
for i in range(len(leaf_nodes)):
    pk = faker.random_int(min=1, max=1000)
    name = leaf_nodes[i]
    # phone_number = faker.phone_number()
    email = f"{name.lower()}_{pk}@example.com"
    table.append((pk, name, email))

# Sort table by primary key
table.sort(key=lambda x: x[0])
print(table)

# # Create a table subgraph
# for i, entry in enumerate(table):
#     node_label = f"{entry[0]}: {entry[1]}\n{entry[2]}"
#     G.add_node(f"Entry{i}", label=node_label, shape="rectangle")

# # Add edges between table entries
# table_edges = [(f"Entry{i}", f"Entry{i+1}") for i in range(len(table) - 1)]
# G.add_edges_from(table_edges, color="black", dir="none")


# Level 1
G.add_node("A-Z", shape="rectangle", style="dashed")

# Level 2
for internal_node in internal_nodes:
    G.add_node(internal_node, shape="rectangle", style="dashed")

# Level 3 (leaves)
for leaf_node in leaf_nodes:
    G.add_node(leaf_node, shape="rectangle")

# Add edges from root to internal nodes
G.add_edge("A-Z", "A-D")
G.add_edge("A-Z", "E-Z")

# Add edges from internal nodes to leaf nodes
for leaf_node in leaf_nodes[:4]:
    G.add_edge("A-D", leaf_node)
for leaf_node in leaf_nodes[4:]:
    G.add_edge("E-Z", leaf_node)

# Add edges between leaf nodes with arrows
leaf_edges = list(zip(leaf_nodes[:-1], leaf_nodes[1:]))
G.add_edges_from(leaf_edges, style="dashed", dir="none")
# for i in range(len(leaf_nodes) - 1):
#     G.add_edge(leaf_nodes[i], leaf_nodes[i + 1], style="dashed", arrowhead="none")

# Convert to a graphviz agraph
A = to_agraph(G)

# Create subgraphs for each rank
A.add_subgraph(["A-Z"], rank="same")
A.add_subgraph(internal_nodes, rank="same")
A.add_subgraph(leaf_nodes, rank="same")

# Create a table subgraph
SG = A.add_subgraph([f"Entry{i}" for i in range(len(table))], name="cluster_0")
SG.graph_attr["rank"] = "same"
# SG.graph_attr["color"] = "white"  # to make the subgraph boundary invisible

for i, entry in enumerate(table):
    node_label = f"{entry[0]}: {entry[1]}\n{entry[2]}"
    G.add_node(f"Entry{i}", label=node_label, shape="rectangle")

# Add edges between table entries
table_edges = [(f"Entry{i}", f"Entry{i+1}") for i in range(len(table) - 1)]
SG.add_edges_from(table_edges, color="black", dir="none")

A.graph_attr["ratio"] = "fill"
A.graph_attr[
    "size"
] = "10,5!"  # Set the size to the width and height you want, e.g., 8 by 5 inches
A.graph_attr["rankdir"] = "TB"
A.graph_attr[
    "ranksep"
] = "1.0"  # adjust this value to increase or decrease the distance between levels

# Render the graph to a file (you can also use other formats like 'png', 'pdf', etc.)
A.layout(prog="dot")
A.draw("btree.png")
