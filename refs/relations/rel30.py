import igraph
import matplotlib.pyplot as plt

g = igraph.Graph(directed=True)

vlist = [
    "E",
    "GB",
    "H",
    "K",
    "L",
    "MS",
    "R",
    "S",
    "SW",
    "SWL",
]

for vname in vlist:
    g.add_vertex(vname)

relations = {
    "E": ["E", "R", "L"],
    "GB": ["L"],
    "H": ["GB", "R"],
    "K": ["R", "L", "K", "GB"],
    "L": ["H", "K", "MS", "S", "L", "R"],
    "MS": ["R", "SW", "GB"],
    "S": ["R", "S"],
    "SW": ["L", "R", "SW"],
    "SWL": ["R", "L", "SWL", "GB"],
}

for rel in relations.keys():
    vo = g.vs.find(name=rel)
    for des in relations[rel]:
        vd = g.vs.find(name=des)
        g.add_edges([(vo.index, vd.index)])

dgr = [(vt["name"], g.degree(vt)) for vt in g.vs]
print(f'Degree: {dgr}')
ebs = g.edge_betweenness()
max_eb = max(ebs)
btwns = [
    (g.vs[et[0]]["name"], g.vs[et[1]]["name"])
    for et in [g.es[idx].tuple for idx, eb in enumerate(ebs) if eb == max_eb]
]
print(f'Betweenness: {btwns}')

layout = g.layout(layout="circle")
fig, ax = plt.subplots()

visual_style = {}
visual_style["layout"] = layout
visual_style["bbox"] = (300, 300)
visual_style["margin"] = 100
visual_style["target"] = ax
visual_style["vertex_label"] = g.vs["name"]
visual_style["vertex_label_size"] = 15
visual_style["vertex_label_dist"] = 10
visual_style["vertex_size"] = 12

igraph.plot(g, **visual_style)
plt.show()
