import logging
import random
import tempfile
from abc import ABC, abstractmethod
from pathlib import Path

import igraph

from utils.color_utils import (
    color_green,
    color_orange,
    color_red,
    color_yellow,
)
from utils.dot_utils import run_dot
from utils.dungeon_render import dungeon_dot
from utils.string_utils import random_string

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
logging.getLogger("matplotlib").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

MAXNODE = 300
MAXITER = 200
GATE_TYPES = ("lock", "gate")


def _objects(vertex):
    """Objects of the vertex, empty when the graph has no objects attribute"""
    return (vertex["objects"] if "objects" in vertex.attributes() else None) or []


def can_enter(vertex, collected):
    """A gate can be entered when its objects were collected. OFF gates start open"""
    if vertex["type"] not in GATE_TYPES or vertex["name"].endswith(" OFF"):
        return True
    return all(obj.uid in collected for obj in _objects(vertex))


def _neighbours(graph):
    """Walkable neighbours of each vertex: edges are two-way unless oneway is set"""
    oneway = graph.es["oneway"] if "oneway" in graph.es.attributes() else [False] * graph.ecount()
    neighbours = {v.index: set() for v in graph.vs}
    for edge, one in zip(graph.es, oneway):
        neighbours[edge.source].add(edge.target)
        if not one:
            neighbours[edge.target].add(edge.source)
    return neighbours


def _explore(graph, neighbours):
    """Vertices reachable from START and the uids of the objects collected on the way"""
    start = graph.vs.find(name="START").index
    collected = set()
    reached = {start}
    changed = True
    while changed:
        changed = False
        stack = list(reached)
        while stack:
            vertex = graph.vs[stack.pop()]
            if vertex["type"] not in GATE_TYPES:
                collected.update(obj.uid for obj in _objects(vertex))
            for nxt in neighbours[vertex.index]:
                if nxt not in reached and can_enter(graph.vs[nxt], collected):
                    reached.add(nxt)
                    stack.append(nxt)
                    changed = True
    return reached, collected


def reachable(graph):
    """Vertices reachable from START collecting every object found on the way"""
    return _explore(graph, _neighbours(graph))[0]


def unsolvable_reasons(graph):
    """Reasons why the dungeon cannot be finished: empty if it can

    Reports an unreachable GOAL and every closed gate next to the reachable area with
    the objects it is missing.
    """
    neighbours = _neighbours(graph)
    reached, collected = _explore(graph, neighbours)
    reasons = []
    if graph.vs.find(name="GOAL").index not in reached:
        reasons.append("GOAL unreachable")
    blocked = sorted({nxt for vi in reached for nxt in neighbours[vi] if nxt not in reached})
    for vi in blocked:
        gate = graph.vs[vi]
        missing = [obj.name for obj in _objects(gate) if obj.uid not in collected]
        reasons.append(f"{gate['name']} needs {' + '.join(missing)}")
    # gates repeated between several rooms share the name
    return list(dict.fromkeys(reasons))


class Dungeon(ABC):
    # Grammar name shown in the plot title
    NAME = "Dungeon"

    def __init__(self, **dargs):
        seed = dargs.get("seed")
        self._debug = dargs.get("debug")
        self._reduce = dargs.get("reduce", True)
        self._show_graph = dargs.get("show_graph")
        self._output = dargs.get("output")
        self.logger = logger

        self._runid = random_string(8)
        self._seed = int(seed) if seed else random.randint(1, 20000)
        self._maxnode = dargs.get("maxnodes", MAXNODE) - 1
        self._maxiter = dargs.get("maxiter", MAXITER) - 1
        self._niter = 0
        self._missing_gram = set()
        self._rolls = []
        self.__fill_rolls(self._seed)

        try:
            self.generate()
        except Exception:
            self.logger.fatal("Error in dungeon generation")
            self._get_process_info()
            raise

    def __init_graph(self):
        """Initializes de Graph, Objects and Rooms"""
        self._g = igraph.Graph(directed=True)
        self._objects = []
        self._rooms = {}

    def __fill_rolls(self, seed):
        """Fills the rolls pool using the seed"""
        random.seed(seed)
        self._irolls = [roll for _ in range(4) for roll in random.sample(range(1, 101), 50)]

    @property
    def d100(self):
        """Get a d100 roll from the pool"""
        if not self._irolls:
            self.__fill_rolls(self._seed + self._niter)
        roll = self._irolls.pop()
        self._rolls.append(roll)
        return roll

    def generate(self):
        """Generates a new dungeon"""
        self.__init_graph()
        self._g.add_vertices(2)
        self._format_nv(self._g.vs[0], "st", color_yellow, "START")
        self._format_nv(self._g.vs[1], "gl", color_orange, "GOAL")
        self._dungeonstart()
        self._process()
        if self._reduce:
            self._red_cleanup()
            self._reduce_graph()
        reasons = unsolvable_reasons(self._g)
        if reasons:
            self.logger.warning(f"Dungeon unsolvable: {'; '.join(reasons)}")
        if self._debug:
            self._get_process_info()
        if self._show_graph or self._output:
            self.plot_dungeon()

    def get_graph(self):
        """Returns the igraph object"""
        return self._g

    def plot_dungeon(self):
        """Renders the dungeon graph with Graphviz: saves it to the output file (png, svg, pdf)
        and shows it when show_graph is set"""
        source = dungeon_dot(self._g, f"{self.NAME} dungeon", self._plot_subtitle())
        if self._output:
            run_dot(source, self._output)
        if self._show_graph:
            import matplotlib.image as mpimg
            import matplotlib.pyplot as plt

            with tempfile.TemporaryDirectory() as tmp:
                image = mpimg.imread(run_dot(source, Path(tmp) / "dungeon.png"))
            height, width = image.shape[:2]
            fig = plt.figure(figsize=(width / 110, height / 110), dpi=110)
            ax = fig.add_axes((0, 0, 1, 1))
            ax.imshow(image)
            ax.axis("off")
            plt.show()

    def _plot_subtitle(self):
        """Text next to the plot title"""
        return f"seed {self._seed}"

    def get_objects(self):
        """Returns a str with the objects in the dungeon"""
        return ",".join(obj.name for obj in self._objects)

    def _add_object_dungeon(self, type, name=None):
        """Adds an objet to the dungeon"""
        aod = self.__dobject(type, name or type)
        self._objects.append(aod)
        return aod

    def _new_object(self, type, name):
        """Adds an object named with its number among the objects of the type"""
        return self._add_object_dungeon(type, f"{name} {self._get_object_type_count(type) + 1}")

    def _anchors(self, rv):
        """Returns the first in-neighbour and the first out-neighbour (None if dead end) of the vertex"""
        outs = self._g.neighbors(rv, "out")
        return self._g.neighbors(rv, "in")[0], outs[0] if outs else None

    def _count_room(self, type):
        """Count the rooms by type in the dungeon"""
        self._rooms[type] = self._rooms.get(type, 0) + 1

    @abstractmethod
    def _dungeonstart(self):
        """Needs to be implemented in the child class"""

    @abstractmethod
    def _expand_vertex(self, rv):
        """Replaces a red vertex with its grammar sequence. Returns False if there is no grammar for it"""

    def _format_nv(self, nv, type, color, name=None, object=None):
        """Gives a new vertex a basic format

        Arguments:
            nv vertex: Vertex object to be modified
            type str: Type identifier for the vertex
            color str: Color of the vertex
            name str: Name of the vertex (defaults to type)
            object dobject: Object of the vertex
        """
        nv["type"] = type
        nv["color"] = color
        nv["name"] = name or type
        nv["reviewed"] = False
        if object:
            nv["objects"] = [object]

    def _get_dungeon_object_type(self, type, oidx=0):
        """Given a type return the first object in the Dungeon"""
        lobjs = [oobj for oobj in self._objects if oobj.type == type]
        return lobjs[oidx] if lobjs else None

    def _get_object_type_count(self, type):
        """Given a type return the number of objects of the type in the Dungeon"""
        return sum(1 for oobj in self._objects if oobj.type == type)

    def _get_object_vertex(self, vtx, type=None, oidx=0):
        """Retrieve an object from the vertex based on the object index

        Arguments:
            vtx: Vertex object
            type: Filter objects by type
            oidx: Index of the object to retrieve

        Returns:
            Object in the index
        """
        objects = [obj for obj in vtx["objects"] or [] if type is None or obj.type == type]
        if not objects:
            return None
        if len(objects) > 1:
            self.logger.error(f"More than one OBJECT in {vtx.index}")
        return objects[oidx]

    def _get_process_info(self):
        """Debugs process info"""
        self.logger.debug(f"Dungeon runid: {self._runid}")
        self.logger.debug(f"Dungeon seed: {self._seed}")
        for miss in sorted(self._missing_gram):
            self.logger.error(f">>>>>>>>>>>>>> MISSING: {miss}")
        self.logger.debug(f"Rolls: {len(self._rolls)}")
        self.logger.debug(f"Rolls: {self._rolls}")
        self.logger.debug(f"Iterations: {self._niter}")
        self.logger.debug(f"Vertices: {self._g.vcount()}")
        self.logger.debug(f"Rooms: {self._rooms}")
        self.logger.debug(f"Objects: {self.get_objects()}")

    def _insert_room_btw(
        self, voi, vdi, type, name=None, object=None, color=color_red, break_conn=True
    ):
        """Insert a room in the graph between two elements

        Arguments
            voi int: Vertex Origin Index
            vdi int: Vertex Destination Index
            type str: Type of the room
            name str: Name of the room
            object dobject: Dungeon object to include in the room
            color str: Color of the room
            break_conn bool: Theh new room breaks the existing connection

        Returns:
            int : new vertex index
        """
        if break_conn and self._g.are_adjacent(voi, vdi):
            self._g.delete_edges(self._g.get_eid(voi, vdi))
        nv = self._add_room(type, name, object, color)
        self._g.add_edges([(voi, nv), (nv, vdi)])
        return nv

    def _insert_room_end(self, vdi, type, name=None, object=None, color=color_red):
        """Insert a room in the graph at the end of a room

        Arguments
            vdi int: Vertex Destination Index
            type str: Type of the room
            name str: Name of the room
            object dobject: Dungeon object to include in the room
            color str: Color of the room

        Returns:
            int : new vertex index
        """
        nv = self._add_room(type, name, object, color)
        self._g.add_edge(vdi, nv)
        return nv

    def _add_room(self, type, name, object, color):
        """Adds an unconnected counted room and returns its index"""
        nv = self._g.add_vertex()
        self._format_nv(nv, type, color, name, object)
        self._count_room(type)
        return nv.index

    def _next_red_vertex(self):
        """Returns the first red vertex not reviewed yet, or None"""
        for idx, (color, reviewed) in enumerate(zip(self._g.vs["color"], self._g.vs["reviewed"])):
            if color == color_red and reviewed is False:
                return self._g.vs[idx]
        return None

    def _process(self):
        """Main graph processor

        Expands every red vertex with its grammar sequence until none is left or the
        maximum number of vertices or iterations is reached.
        """
        while True:
            self._niter += 1
            rv = self._next_red_vertex()
            if rv is None:
                break
            rv["reviewed"] = True
            if not self._expand_vertex(rv):
                self._missing_gram.add(rv["type"])
            if self._g.vcount() > self._maxnode or self._niter > self._maxiter:
                self.logger.warning("Limits reached before the end of the expansion")
                self._finish()
                break
        if self._missing_gram:
            self.logger.error(f"Missing grammar for {self._missing_gram}")

    def _finish(self):
        """Called when the limits are reached. Red vertices left are turned into n by _red_cleanup"""

    def _red_cleanup(self):
        """Converts all the red nodes to n type"""
        for rv in self._g.vs.select(color_eq=color_red):
            self._format_nv(rv, "n", color_green)

    def _reduce_graph(self):
        """Finds repeated (contiguous) elements of type e,n,p and simplifies them"""
        for re in ("e", "n", "p"):
            while True:
                # set of elements of the type that connect with elements of the type
                re_set = {
                    ele
                    for con in self._g.vs.select(type_eq=re, reviewed_eq=False)
                    for ele in con.neighbors("out")
                    if ele["type"] == re and ele["reviewed"] is False
                }
                if not re_set:
                    break
                # first element (by index) connected with another element of the same type
                vs = min(re_set, key=lambda v: v.index)
                vs["reviewed"] = True
                try:
                    # get edge that comes in
                    ln = vs.neighbors("in")[0]
                    fn = vs.neighbors("out")[0]
                except IndexError:
                    continue
                if len({vs, fn, ln}) < 3:
                    self._g.simplify(combine_edges="first")
                    continue
                self._remove_room(vs, fn, ln)
        self._g.simplify(combine_edges="first")

    def _remove_room(self, rv, fn, ln=None):
        """Checks if the room still has connections and changes them to the new room, then removes the room

        Arguments:
            rv: Vertex to remove
            fn: Index of first new node
            ln: Index of last new node
        """
        rvi = rv.index
        # All the IN and OUT vertices
        lo = self._g.neighbors(rv, "in")
        ld = self._g.neighbors(rv, "out")
        ln = ln or fn
        # for each connection that exists with the vertex to remove
        for vi in lo + ld:
            lnr = ()
            # check if it comes from the origin
            if vi in lo:
                # are the new nodes to be connected already connected
                if not self._g.are_adjacent(vi, fn):
                    lnr = (vi, fn)
                try:
                    eid = self._g.get_eid(vi, rvi)
                except igraph.InternalError:
                    return
            # it comes from the destination
            else:
                if not self._g.are_adjacent(ln, vi):
                    lnr = (ln, vi)
                eid = self._g.get_eid(rvi, vi)
            # add a new connection
            if lnr:
                self._g.add_edges([lnr])
            # remove old connection
            self._g.delete_edges(eid)
        # remove old vertex
        self._g.delete_vertices(rv)

    class __dobject:
        """Subclass to store objects"""

        def __init__(self, type, name):
            self.type = type
            self.name = name
            self.uid = random_string(8)

        def __repr__(self):
            return f"Type: {self.type} :: Name: {self.name} :: {self.uid}"
