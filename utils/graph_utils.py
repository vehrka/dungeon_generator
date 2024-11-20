import logging
import random
from abc import ABC, abstractmethod

import igraph

from utils.string_utils import random_string

from utils.color_utils import (
    color_green,
    color_red,
    color_orange,
    color_yellow,
)

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
logging.getLogger("matplotlib").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

MAXNODE = 300
MAXITER = 200


class Dungeon(ABC):
    def __init__(self, **dargs):
        maxiter = dargs.get("maxiter", MAXITER)
        maxnodes = dargs.get("maxnodes", MAXNODE)
        seed = dargs.get("seed")
        self._debug = dargs.get("debug")
        self._reduce = dargs.get("reduce", True)
        self._show_graph = dargs.get("show_graph")

        self._runid = random_string(8)
        self.__init_graph()
        self.__init_limits(seed, maxnodes, maxiter)
        self.logger = logger

        try:
            self.generate()
        except Exception as e:
            self.logger.fatal("Error in dungeon generation")
            self._get_process_info()
            raise e
        return

    def __init_limits(self, seed, maxnode, maxiter):
        if not seed:
            seed = random.randint(1, 20000)
        else:
            seed = int(seed)
        self.__fill_rolls(seed)
        self._niter = 0
        self._missing_gram = []
        self._maxnode = maxnode - 1
        self._maxiter = maxiter - 1
        self._rolls = []
        self._seed = seed

    def __init_graph(self):
        """Initializes de Graph, Objects and Rooms"""
        self._g = igraph.Graph(directed=True)
        self._objects = []
        self._rooms = {}
        return

    def __fill_rolls(self, seed):
        """Fills the rolls pool using the seed"""
        random.seed(seed)
        self._irolls = (
            random.sample(range(1, 101), 50)
            + random.sample(range(1, 101), 50)
            + random.sample(range(1, 101), 50)
            + random.sample(range(1, 101), 50)
        )
        return

    @property
    def d100(self):
        """Get a d100 roll from the pool"""
        try:
            roll = self._irolls.pop()
        except IndexError:
            self.__fill_rolls(self._seed + self._niter)
            roll = self.d100
        self._rolls.append(roll)
        return roll

    def generate(self):
        """Generates a new dungeon"""
        if len(self._g.vs) > 0:
            self.__init_graph()
        self._g.add_vertices(2)
        self._format_nv(self._g.vs[0], "st", color_yellow, "START")
        self._format_nv(self._g.vs[1], "gl", color_orange, "GOAL")
        self._dungeonstart()
        self._process()
        if self._reduce:
            self._red_cleanup()
            self._reduce_graph()
        if self._debug:
            self._get_process_info()
        if self._show_graph:
            self.plot_dungeon()
        return

    def get_graph(self):
        """Returns the igraph object"""
        return self._g

    def plot_dungeon(self, glayout="fr", debug=False):
        """Plots the dungeon graph"""
        import matplotlib.pyplot as plt

        filename = f"debug/img/{self._runid}_{self._niter:04}.png"
        plt.title = f"Iter: {self._niter:04}"

        #  glayout = "davidson_harel"
        #  glayout = "dh"
        #  glayout = "graphopt"
        #  glayout = "kamada_kawai"
        #  glayout = "kk"
        #  glayout = "lgl"
        #  glayout = "fr"
        layout = self._g.layout(layout=glayout)

        fig, ax = plt.subplots()

        visual_style = {}
        visual_style["layout"] = layout
        visual_style["bbox"] = (300, 300)
        visual_style["margin"] = 20

        if debug:
            visual_style["target"] = filename
        else:
            visual_style["target"] = ax
        visual_style["vertex_label"] = self._g.vs["name"]
        visual_style["vertex_label_size"] = 15
        visual_style["vertex_label_dist"] = 10
        visual_style["vertex_color"] = self._g.vs["color"]
        visual_style["vertex_shape"] = "rectangle"
        visual_style["vertex_size"] = 12

        igraph.plot(self._g, **visual_style)
        if not debug:
            plt.show()
        else:
            plt.close()

    def get_objects(self):
        """Returns a str with the objects in the dungeon"""
        lnames = [obj.name for obj in self._objects]
        return ",".join(lnames)

    def _add_object_dungeon(self, type, name=None):
        """Adds an objet to the dungeon"""
        if not name:
            name = type
        aod = self.__dobject(type, name)
        self._objects.append(aod)
        return aod

    def _count_room(self, type):
        """Count the rooms by type in the dungeon"""
        if self._rooms.get(type):
            self._rooms[type] += 1
        else:
            self._rooms[type] = 1
        return

    @abstractmethod
    def _dungeonstart(self):
        """Needs to be implemented in the child class"""
        pass

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
        if not name:
            name = type
        #  nv["name"] = f"{name} - {nv.index}"
        nv["name"] = name
        nv["reviewed"] = False
        nv["uid"] = random_string(8)
        debugstr = f"Node {nv.index}\ntype: {type}\ncolor: {color}\nname: {name}"
        if object:
            nv["objects"] = [object]
            debugstr += f"\nobject: {object}"
        #  self.logger.debug(debugstr)
        return

    def _get_dungeon_object_type(self, type, oidx=0):
        """Given a type return the first object in the Dungeon"""
        lobjs = [oobj for oobj in self._objects if oobj.type == type]
        if len(lobjs) == 0:
            return None
        return lobjs[oidx]

    def _get_object_type_count(self, type):
        """Given a type return the number of objects of the type in the Dungeon"""
        lobjs = [oobj for oobj in self._objects if oobj.type == type]
        return len(lobjs)

    def _get_object_vertex(self, vtx, type=None, oidx=0):
        """Retrieve an object from the vertex based on the object index

        Arguments:
            vtx: Vertex object
            type: Filter objects by type
            oidx: Index of the object to retrieve

        Returns:
            Object in the index
        """
        if vtx["objects"] is None:
            return None
        if type:
            objects = [obj for obj in vtx["objects"] if obj.type == type]
        else:
            objects = [obj for obj in vtx["objects"]]
        if len(objects) > 1:
            self.logger.error(f"More than one OBJECT in {vtx.index}")
        elif len(objects) == 0:
            return None
        return objects[oidx]

    def _get_process_info(self):
        """Debugs process info"""
        self.logger.debug(f"Dungeon runid: {self._runid}")
        self.logger.debug(f"Dungeon seed: {self._seed}")
        if self._missing_gram:
            self._missing_gram.sort()
            for miss in self._missing_gram:
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
        if break_conn and self._g.are_connected(voi, vdi):
            eid = self._g.get_eid(voi, vdi)
            self._g.delete_edges(eid)
        nv = self._g.add_vertex()
        self._format_nv(nv, type, color, name, object)
        self._g.add_edges([(voi, nv.index), (nv.index, vdi)])
        self._count_room(type)
        return nv.index

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
        nv = self._g.add_vertex()
        self._format_nv(nv, type, color, name, object)
        self._g.add_edge(vdi, nv.index)
        self._count_room(type)
        return nv.index

    @abstractmethod
    def _process(self):
        """Needs to be implemented in the child class"""
        pass

    def _red_cleanup(self):
        """Converts all the red nodes to n type"""
        red_vertices = self._g.vs.select(color_eq=color_red)
        if not red_vertices:
            return
        for rv in red_vertices:
            self._format_nv(rv, "n", color_green)
        return

    def _reduce_graph(self):
        """Finds repeated (contiguous) elements of type e,n,p and simplifies them"""
        reduce_element_list = ["e", "n", "p"]
        for re in reduce_element_list:
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
                # get a random element connected with another element of the same type
                vs = re_set.pop()
                vs["reviewed"] = True
                try:
                    # get edge that comes in
                    ln = vs.neighbors("in")[0]
                    fn = vs.neighbors("out")[0]
                except IndexError:
                    continue
                if len(set((vs, fn, ln))) < 3:
                    self._g.simplify()
                    continue
                self._remove_room(vs, fn, ln)
        self._g.simplify()

    def _remove_room(self, rv, fn, ln=None):
        """Checks if the room still has connections and changes them to the new room, then removes the room

        Arguments:
            rv: Vertex to remove
            fn: Index of first new node
            ln: Index of last new node
        """
        rvi = rv.index
        # All the IN vertices
        lvoi = self._g.neighbors(rv, "in")
        # All the OUT vertices
        lvdi = self._g.neighbors(rv, "out")
        if not ln:
            ln = fn
        # Check that the list exists or create
        lo = lvoi if lvoi else []
        ld = lvdi if lvdi else []
        lnr = ()
        # for each connection that exists with the vertex to remove
        for vi in lo + ld:
            # check if it comes from the origin
            if vi in lo:
                # are the new nodes to be connected already connected
                if not self._g.are_connected(vi, fn):
                    lnr = (vi, fn)
                try:
                    eid = self._g.get_eid(vi, rvi)
                except Exception:
                    return
            # check if it comes from the destination
            elif vi in ld:
                # are the new nodes to be connected already connected
                if not self._g.are_connected(ln, vi):
                    lnr = (ln, vi)
                eid = self._g.get_eid(rvi, vi)
            # add a new connection
            if lnr:
                self._g.add_edges([lnr])
            # remove old connection
            self._g.delete_edges(eid)
        # remove old vertex
        self._g.delete_vertices(rv)
        return

    class __dobject:
        """Subclass to store objects"""

        def __init__(self, type, name):
            self.type = type
            self.name = name
            self.uid = random_string(8)

        def __repr__(self):
            return f"Type: {self.type} :: Name: {self.name} :: {self.uid}"
