import logging
import random
from abc import ABC, abstractmethod

import igraph

from utils.color_utils import (
    color_black,
    color_blue,
    color_cyan,
    color_green,
    color_orange,
    color_pink,
    color_red,
    color_yellow,
)
from utils.string_utils import random_string

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
logging.getLogger("matplotlib").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

MAXNODE = 300
MAXITER = 200


class Dungeon(ABC):
    def __init__(self, **dargs):
        self._runid = random_string(8)
        self.__init_graph()
        self.__init_limits(
            dargs.get("seed"), dargs.get("maxnodes", MAXNODE), dargs.get("maxiter", MAXITER)
        )
        self._show_graph = dargs.get("show_graph")
        self._debug = dargs.get("debug")
        try:
            self.generate()
        except Exception as e:
            logger.fatal("Error in dungeon generation")
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
        #  logger.debug(debugstr)
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
            logger.error(f"More than one OBJECT in {vtx.index}")
        elif len(objects) == 0:
            return None
        return objects[oidx]

    def _get_process_info(self):
        """Debugs process info"""
        logger.debug(f"Dungeon runid: {self._runid}")
        logger.debug(f"Dungeon seed: {self._seed}")
        if self._missing_gram:
            self._missing_gram.sort()
            for miss in self._missing_gram:
                logger.error(f">>>>>>>>>>>>>> MISSING: {miss}")
        logger.debug(f"Rolls: {len(self._rolls)}")
        logger.debug(f"Rolls: {self._rolls}")
        logger.debug(f"Iterations: {self._niter}")
        logger.debug(f"Vertices: {self._g.vcount()}")
        logger.debug(f"Rooms: {self._rooms}")
        logger.debug(f"Objects: {self.get_objects()}")

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


class D30(Dungeon):
    def _dungeonstart(self):
        """Generates the initial layout of the dungeon"""
        sv = self._g.vs[0]
        gv = self._g.vs[1]
        self._insert_room_btw(sv, gv, "E")
        return

    def _process(self):
        """Main graph processor

        Tries to substitute every red vertex with the correspondent sequence.

        Finishes after 200 iterations or if the graph has 1 000 vertices
        """
        missing_gram = []
        while True:
            self._niter += 1
            # get all the red vertices
            #  self.plot_dungeon(debug=True)
            red_vertices = self._g.vs.select(color_eq=color_red, reviewed_eq=False)
            if not red_vertices:
                break
            rv = red_vertices[0]
            rv["reviewed"] = True
            rv_type = rv["type"]
            if rv_type == "E":
                self._generate_E(rv)
            elif rv_type == "GB":
                self._generate_GB(rv)
            elif rv_type == "H":
                self._generate_H(rv)
            elif rv_type == "K":
                self._generate_K(rv)
            elif rv_type == "L":
                if self._rooms.get("L") > 15:
                    self._format_nv(rv, "n", color_green)
                else:
                    self._generate_L(rv)
            elif rv_type == "MS":
                self._generate_MS(rv)
            elif rv_type == "R":
                self._generate_R(rv)
            elif rv_type == "S":
                self._generate_S(rv)
            elif rv_type == "SW":
                if self._rooms.get("SW") > 5:
                    self._format_nv(rv, "n", color_green)
                else:
                    self._generate_SW(rv)
            elif rv_type == "SWL":
                if self._rooms.get("SWL") > 5:
                    self._format_nv(rv, "n", color_green)
                else:
                    self._generate_SWL(rv)
            else:
                if rv_type not in missing_gram:
                    missing_gram.append(rv_type)
            if self._g.vcount() > self._maxnode or self._niter > self._maxiter:
                break
        return

    def _generate_E(self, rv):
        """Entrance

        Arguments
            rv int:  Reference vertex

        """
        voi = self._g.neighbors(rv, "in")[0]
        vdi = self._g.neighbors(rv, "out")[0]

        roll = self.d100
        if roll <= 50:
            fn = ln = self._insert_room_btw(voi, vdi, "L")
        else:
            fn = self._insert_room_btw(voi, vdi, "E")
            nr = self._insert_room_btw(fn, vdi, "R")
            ln = self._insert_room_btw(nr, vdi, "L")
            nl2 = self._insert_room_end(nr, "L")
            self._insert_room_end(nl2, "EXIT", color=color_yellow)
        self._remove_room(rv, fn, ln)
        return

    def _generate_GB(self, rv):
        """Bonus Goal

        Arguments
            rv int:  Reference vertex

        """
        voi = self._g.neighbors(rv, "in")[0]

        #  fn = self._insert_room_end(voi, "L")
        fn = self._insert_room_end(voi, "n", color=color_green)
        self._insert_room_end(fn, "gb", color=color_green)
        self._remove_room(rv, fn)
        return

    def _generate_H(self, rv):
        """Hook

        Arguments
            rv int:  Reference vertex

        """
        voi = self._g.neighbors(rv, "in")[0]
        vdi = self._g.neighbors(rv, "out")[0]

        fn = self._insert_room_btw(voi, vdi, "R")
        ng = self._insert_room_end(fn, "GB")
        roll = self.d100
        if roll > 50:
            self._insert_room_btw(fn, ng, "s", color=color_black)
        self._remove_room(rv, fn)
        return

    def _generate_K(self, rv):
        """Lock

        Arguments
            rv int:  Reference vertex

        """
        voi = self._g.neighbors(rv, "in")[0]
        vdi = self._g.neighbors(rv, "out")[0]

        fn = self._insert_room_btw(voi, vdi, "R")
        roll = self.d100
        if roll <= 50:
            ln = self._insert_room_btw(fn, vdi, "L")
            sl = self._insert_room_end(fn, "L")

            nkeys = self._get_object_type_count("key") + 1
            key = self._add_object_dungeon("key", f"key {nkeys}")

            self._insert_room_end(sl, "k", name=f"Get {key.name}", color=color_cyan, object=key)
            self._insert_room_btw(fn, ln, "k", name=f"Use {key.name}", color=color_blue, object=key)
        else:
            ln = self._insert_room_btw(fn, vdi, "K")
            ng = self._insert_room_end(fn, "K")
            self._insert_room_end(ng, "GB")

        self._remove_room(rv, fn, ln)
        return

    def _generate_L(self, rv):
        """Layout

        Arguments
            rv int:  Reference vertex

        """
        voi = self._g.neighbors(rv, "in")[0]
        vdi = self._g.neighbors(rv, "out")[0]

        roll = self.d100
        if roll <= 10:
            fn = self._insert_room_btw(voi, vdi, "H")
            ln = fn
        elif roll <= 25:
            fn = self._insert_room_btw(voi, vdi, "K")
            ln = fn
        elif roll <= 40:
            fn = self._insert_room_btw(voi, vdi, "MS")
            ln = fn
        elif roll <= 50:
            fn = self._insert_room_btw(voi, vdi, "S")
            ln = fn
        elif roll <= 65:
            fn = self._insert_room_btw(voi, vdi, "L")
            rn = self._insert_room_btw(fn, vdi, "R")
            ln = self._insert_room_btw(rn, vdi, "L")
        elif roll <= 75:
            fn = self._insert_room_btw(voi, vdi, "R")
            rn = self._insert_room_btw(fn, vdi, "L")  # oneway entrance
            ln = self._insert_room_btw(rn, vdi, "R")
            self._insert_room_btw(fn, ln, "L")
        elif roll <= 85:
            fn = self._insert_room_btw(voi, vdi, "R")
            rn = self._insert_room_btw(fn, vdi, "L")  # oneway entrance
            ln = self._insert_room_btw(rn, vdi, "R")
            self._insert_room_btw(fn, ln, "L")  # oneway return
        else:
            fn = self._insert_room_btw(voi, vdi, "R")
            rn = self._insert_room_btw(fn, vdi, "L")
            ln = self._insert_room_btw(rn, vdi, "R")
            self._insert_room_btw(fn, ln, "L")
        self._remove_room(rv, fn, ln)
        return

    def _generate_MS(self, rv):
        """Multi switch

        Arguments
            rv int:  Reference vertex

        """
        voi = self._g.neighbors(rv, "in")[0]
        vdi = self._g.neighbors(rv, "out")[0]

        fn = self._insert_room_btw(voi, vdi, "R")
        nsws = self._get_object_type_count("switch") + 1
        switch = self._add_object_dungeon("switch", f"switch {nsws}")
        self._insert_room_end(fn, "SW", object=switch)
        ln = self._insert_room_btw(fn, vdi, f"Check {switch.name}", color=color_pink)
        roll = self.d100
        if roll > 50:
            ns = self._insert_room_end(fn, "SWL", object=switch)
            self._insert_room_end(ns, "GB")
        self._remove_room(rv, fn, ln)

    def _generate_R(self, rv):
        """Room chooser

        Arguments
            rv int:  Reference vertex

        """
        voi = self._g.neighbors(rv, "in")[0]
        vdi = self._g.neighbors(rv, "out")[0]

        roll = self.d100
        if roll <= 20:
            type = "n"
        elif roll <= 40:
            type = "t"
        elif roll <= 60:
            type = "m"
        elif roll <= 80:
            type = "p"
        else:
            type = "c"
        fn = self._insert_room_btw(voi, vdi, type, color=color_green)
        self._remove_room(rv, fn)

    def _generate_S(self, rv):
        """Linear

        Arguments
            rv int:  Reference vertex

        """
        voi = self._g.neighbors(rv, "in")[0]
        vdi = self._g.neighbors(rv, "out")[0]

        fn = self._insert_room_btw(voi, vdi, "R")
        roll = self.d100
        if roll > 50:
            ln = self._insert_room_btw(fn, vdi, "S")
        else:
            ln = fn
        self._remove_room(rv, fn, ln)

    def _generate_SW(self, rv):
        """Switch

        Arguments
            rv int:  Reference vertex

        """
        voi = self._g.neighbors(rv, "in")[0]

        switch = self._get_object_vertex(rv)
        roll = self.d100
        if roll <= 50:
            fn = self._insert_room_end(voi, "L")
            self._insert_room_end(fn, f"{switch.name}", color=color_pink)
        else:
            fn = self._insert_room_end(voi, "R")
            nl = self._insert_room_end(fn, "L")
            self._insert_room_end(nl, f"{switch.name}", color=color_pink)
            nl = self._insert_room_end(fn, "SW", object=switch)
        self._remove_room(rv, fn)

    def _generate_SWL(self, rv):
        """Switch Lock

        Arguments
            rv int:  Reference vertex

        """
        voi = self._g.neighbors(rv, "in")[0]
        vdi = self._g.neighbors(rv, "out")[0]

        switch = self._get_object_vertex(rv)
        roll = self.d100
        if roll <= 50:
            fn = self._insert_room_btw(voi, vdi, "L")
            ns = self._insert_room_btw(fn, vdi, f"{switch.name}", color=color_pink)
            ln = self._insert_room_btw(ns, vdi, "L")
        else:
            fn = self._insert_room_btw(voi, vdi, "R")
            nl1 = self._insert_room_btw(fn, vdi, "L")
            ns = self._insert_room_btw(nl1, vdi, f"{switch.name}", color=color_pink)
            ln = self._insert_room_btw(ns, vdi, "L")
            nsw = self._insert_room_end(fn, "SWL", object=switch)
            self._insert_room_end(nsw, "GB")
        self._remove_room(rv, fn, ln)


class D24(Dungeon):
    def _dungeonstart(self):
        """Generates the initial layout of the dungeon"""
        sv = self._g.vs[0]
        gv = self._g.vs[1]

        roll = self.d100
        if roll <= 25:
            nkeys = self._get_object_type_count("key") + 1
            key = self._add_object_dungeon("key", f"key {nkeys}")

            nv = self._insert_room_btw(sv, gv, "OM", object=key)
            self._insert_room_btw(nv, gv, "OO")
        elif roll <= 50:
            nbangs = self._get_object_type_count("bang") + 1
            nkeys = self._get_object_type_count("key") + 1
            external = self._add_object_dungeon("bang", f"external {nbangs}")
            hp = self._add_object_dungeon("hp", "Heart piece")
            key = self._add_object_dungeon("key", f"key {nkeys}")

            nv_c = self._insert_room_btw(sv, gv, "C")
            nv_ol = self._insert_room_end(nv_c, "OL", object=external)
            self._insert_room_end(nv_ol, "UI", object=hp)
            nv_om = self._insert_room_btw(nv_c, gv, "OM", object=key)
            self._insert_room_btw(nv_om, gv, "OO")
        elif roll <= 75:
            nkeys = self._get_object_type_count("key") + 1
            key = self._add_object_dungeon("key", f"key {nkeys}")
            i5 = self._add_object_dungeon("i5", "Boss key")

            nv_ol1 = self._insert_room_btw(sv, gv, "OL", object=key)
            nv_ol2 = self._insert_room_btw(nv_ol1, gv, "OL", object=i5)
            self._insert_room_btw(nv_ol2, gv, "eb", color=color_green)
            self._insert_room_end(sv, "UI", object=key)
            self._insert_room_end(sv, "UI", object=i5)
        else:
            nkeys = self._get_object_type_count("key") + 1
            key = self._add_object_dungeon("key", f"key {nkeys}")
            i5 = self._add_object_dungeon("i5", "Boss key")

            nv_oli = self._insert_room_btw(sv, gv, "OL", object=i5)
            self._insert_room_btw(nv_oli, gv, "eb", color=color_green)
            self._insert_room_end(sv, "UI", object=key)
            nv_ui = self._insert_room_end(sv, "UI", object=i5)
            self._insert_room_btw(sv, nv_ui, "OL", object=key)
        return

    def _process(self):
        """Main graph processor

        Tries to substitute every red vertex with the correspondent sequence.

        The number of C sequences is reduced to a max of 5.

        The number of SW and SWL sequences is reduced to a max of 2.

        Finishes after 200 iterations or if the graph has 1 000 vertices
        """
        missing_gram = []
        while True:
            self._niter += 1
            # get all the red vertices
            red_vertices = self._g.vs.select(color_eq=color_red, reviewed_eq=False)
            if not red_vertices:
                break
            rv = red_vertices[0]
            rv["reviewed"] = True
            rv_type = rv["type"]
            if rv_type == "C":
                if self._rooms.get("C") > 5:
                    self._format_nv(rv, "n", color_green)
                else:
                    self._generate_C(rv)
            elif rv_type == "GB":
                self._generate_GB(rv)
            elif rv_type == "H":
                self._generate_H(rv)
            elif rv_type == "MI":
                self._generate_MI(rv)
            elif rv_type == "ML":
                self._generate_ML(rv)
            elif rv_type == "MM":
                self._generate_MM(rv)
            elif rv_type == "MM2":
                self._generate_MM2(rv)
            elif rv_type == "MO":
                self._generate_MO(rv)
            elif rv_type == "MS":
                self._generate_MS(rv)
            elif rv_type == "MS2":
                self._generate_MS2(rv)
            elif rv_type == "OL":
                self._generate_OL(rv)
            elif rv_type == "OM":
                self._generate_OM(rv)
            elif rv_type == "OO":
                self._generate_OO(rv)
            elif rv_type == "S":
                self._generate_S(rv)
            elif rv_type == "SW":
                if self._rooms.get("SW") > 2:
                    self._format_nv(rv, "n", color_green)
                else:
                    self._generate_SW(rv)
            elif rv_type == "SWL":
                if self._rooms.get("SWL") > 2:
                    self._format_nv(rv, "n", color_green)
                else:
                    self._generate_SWL(rv)
            elif rv_type == "UI":
                self._generate_UI(rv)
            else:
                if rv_type not in missing_gram:
                    missing_gram.append(rv_type)
            # max num of iter
            if self._g.vcount() > self._maxnode or self._niter > self._maxiter:
                break
        return

    def _retrieve_bang(self, rv):
        """Tries to retrieve an external object for the vertex"""
        # retrieve !
        nbang = self._get_object_type_count("bang") + 1
        if nbang == 1:
            bang = self._add_object_dungeon("bang", f"external {nbang}")
        else:
            bang = self._get_object_vertex(rv, type="bang")
            if not bang:
                bang = self._get_dungeon_object_type("bang")
        return bang

    def _generate_C(self, rv):
        """Chain

        Arguments
            rv int:  Reference vertex

        """
        voi = self._g.neighbors(rv, "in")[0]
        vdi = self._g.neighbors(rv, "out")[0]

        roll = self.d100
        if roll <= 25:
            type = "H"
        elif roll <= 50:
            type = "MO"
        elif roll <= 75:
            type = "MM"
        else:
            type = "MS"
        fn = self._insert_room_btw(voi, vdi, type)
        self._remove_room(rv, fn)
        return

    def _generate_GB(self, rv):
        """Bonus Goal Sequence

        Arguments
            rv int:  Reference vertex

        """
        voi = self._g.neighbors(rv, "in")[0]

        roll = self.d100
        if roll <= 25:
            gbobj = self._add_object_dungeon("hp", "Heart piece")
            type = "UI"
        elif roll <= 50:
            gbobj = self._add_object_dungeon("ir", "Rupees")
            type = "MI"
        elif roll <= 75:
            gbobj = self._add_object_dungeon("ib", "Bombs")
            type = "MI"
        else:
            gbobj = self._add_object_dungeon("ia", "Arrows")
            type = "MI"
        fn = self._insert_room_end(voi, type, object=gbobj)
        self._remove_room(rv, fn)
        return

    def _generate_H(self, rv):
        """Hook sequence

        Arguments
            rv int:  Reference vertex

        """
        voi = self._g.neighbors(rv, "in")[0]
        vdi = self._g.neighbors(rv, "out")[0]

        fn = self._insert_room_btw(voi, vdi, "n", color=color_green)
        self._insert_room_end(fn, "GB")
        self._remove_room(rv, fn, fn)
        return

    def _generate_OL(self, rv):
        """One lock sequence

        Arguments
            rv int:  Reference vertex

        """
        voi = self._g.neighbors(rv, "in")[0]
        vdi = self._g.neighbors(rv, "out")[0]

        olobj = self._get_object_vertex(rv)

        roll = self.d100
        if roll <= 30:
            type = "C"
        else:
            type = "S"
        fn = self._insert_room_btw(voi, vdi, type)
        nv_k = self._insert_room_btw(fn, vdi, f"Use {olobj.name}", color=color_blue)
        ln = self._insert_room_btw(nv_k, vdi, "n", color=color_green)
        self._remove_room(rv, fn, ln)
        return

    def _generate_OM(self, rv):
        """One key to many lock

        Arguments
            rv int:  Reference vertex

        """
        voi = self._g.neighbors(rv, "in")[0]
        vdi = self._g.neighbors(rv, "out")[0]

        key = self._get_object_vertex(rv)

        fn = self._insert_room_btw(voi, vdi, "n", color=color_green)
        self._insert_room_end(fn, "UI", object=key)
        nv_ml = self._insert_room_end(fn, "ML", object=key)
        self._insert_room_end(nv_ml, "GB")
        ln = self._insert_room_btw(fn, vdi, "OL", object=key)
        self._remove_room(rv, fn, ln)
        return

    def _generate_OO(self, rv):
        """One key to one lock

        Arguments
            rv int:  Reference vertex

        """
        voi = self._g.neighbors(rv, "in")[0]
        vdi = self._g.neighbors(rv, "out")[0]

        fn = self._insert_room_btw(voi, vdi, "n", color=color_green)
        ooobj = self._add_object_dungeon("i5", "Boss key")
        self._insert_room_end(fn, "UI", object=ooobj)
        nv_ol = self._insert_room_btw(fn, vdi, "OL", object=ooobj)
        ln = self._insert_room_btw(nv_ol, vdi, "eb", color=color_green)
        self._remove_room(rv, fn, ln)
        return

    def _generate_MI(self, rv):
        """Many items

        Arguments
            rv int:  Reference vertex

        """
        voi = self._g.neighbors(rv, "in")[0]

        roll = self.d100
        if roll <= 30:
            type = "C"
        else:
            type = "S"
        fn = self._insert_room_end(voi, type)

        miobject = self._get_object_vertex(rv)

        self._insert_room_btw(fn, voi, f"Get {miobject.name}", color=color_cyan)
        self._remove_room(rv, fn)
        return

    def _generate_ML(self, rv):
        """Many lock sequence

        Arguments
            rv int:  Reference vertex

        """
        voi = self._g.neighbors(rv, "in")[0]
        vdi = self._g.neighbors(rv, "out")[0]

        roll = self.d100
        if roll <= 75:
            type = "OL"
            color = color_red
            mlobject = self._get_object_vertex(rv)
        else:
            type = "n"
            color = color_green
            mlobject = None
        fn = ln = self._insert_room_btw(voi, vdi, type, object=mlobject, color=color)
        if roll > 75:
            mlobject = self._get_object_vertex(rv)
            nv_ml = self._insert_room_end(fn, "ML", object=mlobject)
            self._insert_room_end(nv_ml, "GB")
            ln = self._insert_room_btw(fn, vdi, "OL", object=mlobject)
        self._remove_room(rv, fn, ln)
        return

    def _generate_MM(self, rv):
        """Switch lock chain

        Arguments
            rv int:  Reference vertex

        """
        voi = self._g.neighbors(rv, "in")[0]
        vdi = self._g.neighbors(rv, "out")[0]

        fn = self._insert_room_btw(voi, vdi, "n", color=color_green)

        ntog = self._get_object_type_count("tog") + 1
        tog = self._add_object_dungeon("tog", f"lever {ntog}")

        nv_sw = self._insert_room_end(fn, "SW", object=tog)
        nv_tog = self._insert_room_end(nv_sw, f"Check {tog.name}", color=color_pink)
        nv_mm2 = self._insert_room_btw(fn, nv_tog, "MM2", object=tog)

        bang = self._retrieve_bang(rv)

        self._insert_room_btw(nv_mm2, nv_tog, f"Use {bang.name}", color=color_cyan)
        self._insert_room_end(nv_mm2, "GB")
        ln = self._insert_room_btw(fn, vdi, "SWL", object=tog)
        self._g.add_edges([(ln, nv_tog)])

        self._remove_room(rv, fn, ln)
        return

    def _generate_MM2(self, rv):
        """Switch lock chain II

        Arguments
            rv int:  Reference vertex

        """
        voi = self._g.neighbors(rv, "in")[0]
        vdi = self._g.neighbors(rv, "out")[0]

        obj = self._get_object_vertex(rv)
        if not obj:
            obj = self._get_dungeon_object_type("tog")

        fn = self._insert_room_btw(voi, vdi, "SWL", object=obj)
        nv_swe = self._insert_room_end(fn, "SW", object=obj)

        self._insert_room_btw(fn, nv_swe, f"Switch {obj.name}", color=color_pink)

        bang = self._retrieve_bang(rv)

        nv_bang = self._insert_room_btw(fn, nv_swe, f"Use {bang.name}", color=color_cyan)
        ln = self._insert_room_btw(fn, vdi, "SWL", object=obj)
        self._g.add_edges([(nv_bang, ln)])

        roll = self.d100
        if roll > 50:
            nv_mm = self._insert_room_end(nv_bang, "MM2", object=obj)
            self._insert_room_end(nv_mm, "GB")

        self._remove_room(rv, fn, ln)
        return

    def _generate_MO(self, rv):
        """Many key many lock

        Arguments
            rv int:  Reference vertex

        """
        voi = self._g.neighbors(rv, "in")[0]
        vdi = self._g.neighbors(rv, "out")[0]

        fn = self._insert_room_btw(voi, vdi, "n", color=color_green)

        nkeys = self._get_object_type_count("i1") + 1
        moobj = self._add_object_dungeon("i1", f"small key {nkeys}")
        self._insert_room_end(fn, "MI", object=moobj)
        ln = self._insert_room_btw(fn, vdi, "OL", object=moobj)
        self._remove_room(rv, fn, ln)
        return

    def _generate_MS(self, rv):
        """Multi switch sequence

        Arguments
            rv int:  Reference vertex

        """
        voi = self._g.neighbors(rv, "in")[0]
        vdi = self._g.neighbors(rv, "out")[0]

        fn = self._insert_room_btw(voi, vdi, "n", color=color_green)
        nv_sw = self._insert_room_end(fn, "SW")
        nv_and = self._insert_room_end(nv_sw, "and", color=color_pink)
        ms2 = self._insert_room_btw(fn, nv_and, "MS2")
        self._g.add_edges([(ms2, nv_and)])
        ln = self._insert_room_btw(fn, vdi, "SWL")
        self._g.add_edges([(ln, nv_and)])

        self._remove_room(rv, fn, ln)
        return

    def _generate_MS2(self, rv):
        """Multi switch sequence II

        Arguments
            rv int:  Reference vertex

        """
        voi = self._g.neighbors(rv, "in")[0]
        vdi = self._g.neighbors(rv, "out")[0]

        fn = self._insert_room_btw(voi, vdi, "n", color=color_green)
        nv_sw = self._insert_room_end(fn, "SW")
        nv_and = self._insert_room_end(nv_sw, "and", color=color_pink)

        roll = self.d100
        if roll > 75:
            self._insert_room_btw(fn, nv_and, "MS2")

        self._remove_room(rv, fn)
        return

    def _generate_S(self, rv):
        """Linear sequence

        Arguments
            rv int:  Reference vertex

        """
        voi = self._g.neighbors(rv, "in")[0]
        vdi = self._g.neighbors(rv, "out")[0]

        roll = self.d100
        if roll <= 30:
            type = "n"
            color = color_green
        if roll <= 60:
            type = "p"
            color = color_green
        if roll <= 90:
            type = "e"
            color = color_green
        else:
            type = "S"
            color = color_red
        fn = ln = self._insert_room_btw(voi, vdi, type, color=color)
        if roll > 90:
            ln = self._insert_room_btw(fn, vdi, "S")
        self._remove_room(rv, fn, ln)
        return

    def _generate_SW(self, rv):
        """Switch sequence

        Arguments
            rv int:  Reference vertex

        """
        voi = self._g.neighbors(rv, "in")[0]

        roll = self.d100
        if roll <= 30:
            type = "C"
        else:
            type = "S"
        fn = self._insert_room_end(voi, type)
        obj = self._get_object_vertex(rv)
        if obj is None:
            ntog = self._get_object_type_count("and") + 1
            obj = self._add_object_dungeon("and", f"and {ntog}")
        self._insert_room_btw(fn, voi, f"Touch {obj.name}", color=color_pink)
        self._remove_room(rv, fn)
        return

    def _generate_SWL(self, rv):
        """Switch-lock sequence

        Arguments
            rv int:  Reference vertex

        """
        voi = self._g.neighbors(rv, "in")[0]
        vdi = self._g.neighbors(rv, "out")[0]

        roll = self.d100
        if roll <= 30:
            type = "C"
        else:
            type = "S"
        ln = self._insert_room_btw(voi, vdi, "n", color=color_green)
        fn = self._insert_room_btw(voi, ln, type)
        nv_t = self._insert_room_btw(voi, ln, type)

        nv = self._g.add_vertex()
        obj = self._get_object_vertex(rv)
        if not obj:
            ntog = self._get_object_type_count("and") + 1
            obj = self._add_object_dungeon("and", f"and {ntog}")
        self._format_nv(nv, "sw", color=color_pink, name=f"Touch {obj.name}")
        self._g.add_edges([(nv_t, nv.index), (nv.index, ln)])

        self._remove_room(rv, fn, ln)
        return

    def _generate_UI(self, rv):
        """Unique item

        Arguments
            rv int:  Reference vertex

        """
        voi = self._g.neighbors(rv, "in")[0]

        roll = self.d100
        if roll <= 30:
            type = "C"
        else:
            type = "S"
        fn = self._insert_room_end(voi, type)
        nv_em = self._insert_room_end(fn, "em", color=color_green)

        uiobject = self._get_object_vertex(rv)

        self._insert_room_btw(nv_em, voi, f"Get {uiobject.name}", object=uiobject, color=color_cyan)
        self._remove_room(rv, fn)
        return
