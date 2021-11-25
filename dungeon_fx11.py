import igraph
import logging

from abc import ABC, abstractmethod
from utils.dice_roller import DiceRoller
from utils.string_utils import random_string
from utils.color_utils import (
    color_blue,
    color_cyan,
    color_green,
    color_orange,
    color_pink,
    color_red,
    color_yellow,
)


logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S'
)
logging.getLogger('matplotlib').setLevel(logging.WARNING)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class Dungeon(ABC):
    def __init__(self):
        self._dice = DiceRoller()
        self.__init_graph()
        self.generate()
        return

    def __init_graph(self):
        self._g = igraph.Graph(directed=True)
        self._objects = []
        self._rooms = {}
        return

    def generate(self):
        """Generates a new dungeon"""
        if len(self._g.vs) > 0:
            self.__init_graph()
        self._g.add_vertices(2)
        self._format_nv(self._g.vs[0], "st", color_yellow, "START")
        self._format_nv(self._g.vs[1], "gl", color_orange, "GOAL")
        self._dungeonstart()
        self._process()
        self._reduce_graph()
        self.plot_dungeon()
        return

    def get_graph(self):
        """Returns the igraph object"""
        return self._g

    def plot_dungeon(self, glayout="lgl"):
        """Plots the dungeon graph"""
        import matplotlib.pyplot as plt

        self._g.to_undirected()

        #  layout = self._g.layout(layout="davidson_harel")
        #  layout = self._g.layout(layout="graphopt")
        #  layout = self._g.layout(layout="kamada_kawai")
        #  layout = self._g.layout(layout="dh")
        #  layout = self._g.layout(layout="dh")
        #  layout = self._g.layout(layout="kk")
        #  layout = self._g.layout(layout="lgl")
        layout = self._g.layout(layout=glayout)

        fig, ax = plt.subplots()

        visual_style = {}
        visual_style["layout"] = layout
        visual_style["bbox"] = (300, 300)
        visual_style["margin"] = 20
        visual_style["target"] = ax
        visual_style["vertex_label"] = self._g.vs["name"]
        visual_style["vertex_label_size"] = 15
        visual_style["vertex_label_dist"] = 10
        visual_style["vertex_color"] = self._g.vs["color"]
        visual_style["vertex_shape"] = "rectangle"
        visual_style["vertex_size"] = 12

        igraph.plot(self._g, **visual_style)
        plt.show()

    def get_objects(self):
        """Returns the list of objects in the dungeon"""
        lnames = [obj.name for obj in self._objects]
        return ','.join(lnames)

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
        self._g.add_edges([(vdi, nv.index)])
        self._count_room(type)
        return nv.index

    def _format_nv(self, nv, type, color, name, object=None):
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
        nv["name"] = name
        nv["uid"] = random_string(8)
        debugstr = f'Node {nv.index}\ntype: {type}\ncolor: {color}\nname: {name}'
        if object:
            nv["objects"] = [object]
            debugstr += f'\nobject: {object}'
        #  logger.debug(debugstr)
        return

    def _get_object_vertex(self, vtx, oidx=0):
        """Retrieve an object from the vertex based on the object index

        Arguments:
            vtx: Vertex object
            oidx: Index of the object to retrieve

        Returns:
            Object in the index
        """
        objects = [obj for obj in vtx['objects']]
        if len(objects) > 1:
            logger.error(f'More than one OBJECT in {vtx.index}')
        return objects[oidx]

    @abstractmethod
    def _process(self):
        """Needs to be implemented in the child class"""
        pass

    def _reduce_graph(self):
        """Finds repeated (contiguous) elements of type e,n,p and simplifies them"""
        reduce_element_list = ['e', 'n', 'p']
        for re in reduce_element_list:
            niter = 0
            while True:
                if niter > 15:
                    break
                # set of elements of the type that connect with elements of the type
                re_set = {
                    ele
                    for con in self._g.vs.select(type=re)
                    for ele in con.neighbors()
                    if ele['type'] == re
                }
                if not re_set:
                    break
                # get a random element connected with another element of the same type
                vs = re_set.pop()
                try:
                    # get edge that comes in
                    ln = vs.neighbors("in")[0]
                except IndexError:
                    niter += 1
                    continue
                fn = vs.neighbors("out")[0]
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
            return f'Type: {self.type} :: Name: {self.name} :: {self.uid}'


class D24(Dungeon):
    def _dungeonstart(self):
        """Generates the initial layout of the dungeon"""
        sv = self._g.vs[0]
        gv = self._g.vs[1]

        basic_layout_roll = self._dice.d100
        if basic_layout_roll <= 25:
            key = self._add_object_dungeon("key", "key 1")

            nv = self._insert_room_btw(sv, gv, "OM", object=key)
            self._insert_room_btw(nv, gv, "OO")
        elif basic_layout_roll <= 50:
            external = self._add_object_dungeon("bang", "external 1")
            hp = self._add_object_dungeon("hp", "Heart piece")
            key = self._add_object_dungeon("key", "key 1")

            nv_c = self._insert_room_btw(sv, gv, "C")
            nv_ol = self._insert_room_end(nv_c, "OL", object=external)
            self._insert_room_end(nv_ol, "UI", object=hp)
            nv_om = self._insert_room_btw(nv_c, gv, "OM", object=key)
            self._insert_room_btw(nv_om, gv, "OO")
        elif basic_layout_roll <= 75:
            key = self._add_object_dungeon("key", "key 1")
            i5 = self._add_object_dungeon("i5", "Boss key")

            nv_ol1 = self._insert_room_btw(sv, gv, "OL", object=key)
            nv_ol2 = self._insert_room_btw(nv_ol1, gv, "OL", object=i5)
            self._insert_room_btw(nv_ol2, gv, "eb", color=color_green)
            self._insert_room_end(sv, "UI", object=key)
            self._insert_room_end(sv, "UI", object=i5)
        else:
            key = self._add_object_dungeon("key", "key 1")
            i5 = self._add_object_dungeon("i5", "Boss key")

            nv_oli = self._insert_room_btw(sv, gv, "OL", object=i5)
            self._insert_room_btw(nv_oli, gv, "eb", color=color_green)
            self._insert_room_end(sv, "UI", object=key)
            nv_ui = self._insert_room_end(sv, "UI", object=i5)
            self._insert_room_btw(sv, nv_ui, "OL", object=key)
        #  logger.debug(f'Generate a {int(basic_layout_roll/25)+1}')
        return

    def _process(self):
        """Main graph processor

        Tries to substitute every red vertex with the correspondent sequence.

        The number of C sequences is reduced to a max of 5.

        The number of SW and SWL sequences is reduced to a max of 2.

        Finishes after 200 iterations or if the graph has 1 000 vertices
        """
        missing = []
        niter = 0
        while True:
            niter += 1
            # get all the red vertices
            red_vertex = self._g.vs.select(color_eq=color_red)
            if not red_vertex:
                break
            rv = red_vertex[0]
            rv_type = rv["type"]
            if rv_type == "C":
                if self._rooms.get("C") > 5:
                    rv["type"] = rv["name"] = "n"
                    rv["color"] = color_green
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
                    rv["type"] = rv["name"] = "n"
                    rv["color"] = color_green
                else:
                    self._generate_SW(rv)
            elif rv_type == "SWL":
                if self._rooms.get("SWL") > 2:
                    rv["type"] = rv["name"] = "n"
                    rv["color"] = color_green
                else:
                    self._generate_SWL(rv)
            elif rv_type == "UI":
                self._generate_UI(rv)
            else:
                if rv_type not in missing:
                    missing.append(rv_type)
            # max num of iter
            if self._g.vcount() > 1000 or niter > 200:
                break
        missing.sort()
        for miss in missing:
            logger.error(f">>>>>>>>>>>>>> MISSING: {miss}")
        #  logger.debug(f"Iterations: {niter}")
        #  logger.debug(f"Vertices: {self._g.vcount()}")
        #  logger.debug(f"Rooms: {self._rooms}")
        #  logger.debug(f"Objects: {self.get_objects()}")
        #  logger.debug("Finished process")
        return

    def _generate_C(self, rv):
        """Chain

        Arguments
            rv int:  Reference vertex

        """
        voi = self._g.neighbors(rv, "in")[0]
        vdi = self._g.neighbors(rv, "out")[0]

        roll = self._dice.d100
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

        roll = self._dice.d100
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

        roll = self._dice.d100
        if roll <= 30:
            type = "C"
        else:
            type = "S"
        fn = self._insert_room_btw(voi, vdi, type)
        olobj = self._get_object_vertex(rv)
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

        roll = self._dice.d100
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

        roll = self._dice.d100
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
        nv_sw = self._insert_room_end(fn, "SW")
        nv_tog = self._insert_room_end(nv_sw, "tog", color=color_pink)
        nv_mm2 = self._insert_room_btw(fn, nv_tog, "MM2")
        # retrieve !
        self._insert_room_btw(nv_mm2, nv_tog, "Use !", color=color_cyan)
        self._insert_room_end(nv_mm2, "GB")
        ln = self._insert_room_btw(fn, vdi, "SWL")
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

        fn = self._insert_room_btw(voi, vdi, "SWL")
        nv_swe = self._insert_room_end(fn, "SW")
        self._insert_room_btw(fn, nv_swe, "Check switch", color=color_pink)
        nv_bang = self._insert_room_btw(fn, nv_swe, "Use !", color=color_cyan)
        ln = self._insert_room_btw(fn, vdi, "SWL")
        self._g.add_edges([(nv_bang, ln)])

        roll = self._dice.d100
        if roll > 50:
            nv_mm = self._insert_room_end(nv_bang, "MM2")
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

        moobj = self._add_object_dungeon("i1", "Small key")
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
        self._insert_room_btw(fn, nv_and, "MS2")
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

        roll = self._dice.d100
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

        roll = self._dice.d100
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

        roll = self._dice.d100
        if roll <= 30:
            type = "C"
        else:
            type = "S"
        fn = self._insert_room_end(voi, type)
        self._insert_room_btw(fn, voi, "switch", color=color_pink)
        self._remove_room(rv, fn)
        return

    def _generate_SWL(self, rv):
        """Switch-lock sequence

        Arguments
            rv int:  Reference vertex

        """
        voi = self._g.neighbors(rv, "in")[0]
        vdi = self._g.neighbors(rv, "out")[0]

        roll = self._dice.d100
        if roll <= 30:
            type = "C"
        else:
            type = "S"
        ln = self._insert_room_btw(voi, vdi, "n", color=color_green)
        fn = self._insert_room_btw(voi, ln, type)
        nv_t = self._insert_room_btw(voi, ln, type)

        nv = self._g.add_vertex()
        self._format_nv(nv, "", color=color_pink, name="")
        self._g.add_edges([(nv_t, nv.index), (nv.index, ln)])

        self._remove_room(rv, fn, ln)
        return

    def _generate_UI(self, rv):
        """Unique item

        Arguments
            rv int:  Reference vertex

        """
        voi = self._g.neighbors(rv, "in")[0]

        roll = self._dice.d100
        if roll <= 30:
            type = "C"
        else:
            type = "S"
        fn = self._insert_room_end(voi, type)
        nv_em = self._insert_room_end(fn, "em", color=color_green)

        uiobject = self._get_object_vertex(rv)

        self._insert_room_btw(
            nv_em, voi, f"Get {uiobject.name}", object=uiobject, color=color_cyan
        )
        self._remove_room(rv, fn)
        return
