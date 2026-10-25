import igraph
import matplotlib.pyplot as plt

g = igraph.Graph(directed=True)

vlist = [
    "C",
    "GB",
    "H",
    "MI",
    "ML",
    "MM",
    "MM2",
    "MO",
    "MS",
    "MS2",
    "OL",
    "OM",
    "OO",
    "S",
    "SW",
    "SWL",
    "UI",
]

for vname in vlist:
    g.add_vertex(vname)

relations = {
    "C": ["H", "MO", "MM", "MS"],
    "GB": ["UI", "MI"],
    "H": ["GB"],
    "MI": ["C", "S"],
    "ML": ["OL", "ML", "GB"],
    "MM": ["SW", "MM2", "GB", "SWL"],
    "MM2": ["SWL", "SW", "MM2", "GB"],
    "MO": ["MI", "OL"],
    "MS": ["SW", "MS2", "SWL"],
    "MS2": ["SW", "MS2"],
    "OL": ["C", "S"],
    "OM": ["UI", "ML", "GB", "OL"],
    "OO": ["UI", "OL"],
    "S": ["S"],
    "SW": ["C", "S"],
    "SWL": ["C", "S"],
    "UI": ["C", "S"],
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
