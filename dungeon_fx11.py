import igraph
import logging

from utils.dice_roller import DiceRoller
from utils.string_utils import random_string


logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
logging.getLogger('matplotlib').setLevel(logging.WARNING)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

color_black = "black"
color_blue = "#0072b2"  # "rgb(0, 114, 178)"
color_cyan = "#56b4e9"  # "rgb(86, 180, 233)"
color_green = "#009e73"  # "rgb(0, 158, 115)"
color_orange = "#e69f00"  # "rgb(230, 159, 0)"
color_pink = "#cc79a7"  # "rgb(204, 121, 167)"
color_red = "#d55e00"  # "rgb(213, 94, 0)"
color_yellow = "#f0e442"  # "rgb(240, 228, 66)"


class Dungeon:
    def __init__(self, dtype="p24"):
        self.__g = igraph.Graph(directed=True)
        self.__dice = DiceRoller()
        self.__dungeon_type = dtype
        self.__objects = []
        self.generate()
        return

    def generate(self):
        self.__g.add_vertices(2)
        self.__format_nv(self.__g.vs[0], "st", color_yellow, "START")
        self.__format_nv(self.__g.vs[1], "gl", color_orange, "GOAL")

        if self.__dungeon_type == "p24":
            self.__dungeonstart24()
        else:
            logger.info("Post 30 dungeon type still under development")
            return

        self.__process()
        self.get_graph()
        return

    def get_dungeon(self):
        return self.__g

    def get_graph(self, layout="lgl"):
        import matplotlib.pyplot as plt

        #  layout = self.__g.layout(layout="davidson_harel")
        #  layout = self.__g.layout(layout="graphopt")
        #  layout = self.__g.layout(layout="kamada_kawai")
        #  layout = self.__g.layout(layout="lgl")

        fig, ax = plt.subplots()

        visual_style = {}
        visual_style["layout"] = layout
        visual_style["bbox"] = (300, 300)
        visual_style["margin"] = 20
        visual_style["target"] = ax
        visual_style["vertex_label"] = self.__g.vs["name"]
        visual_style["vertex_label_size"] = 15
        visual_style["vertex_label_dist"] = 10
        visual_style["vertex_color"] = self.__g.vs["color"]
        visual_style["vertex_shape"] = "rectangle"
        visual_style["vertex_size"] = 12

        igraph.plot(self.__g, **visual_style)
        plt.show()

    def __dungeonstart24(self):
        """Generates the initial layout of the dungeon"""
        sv = self.__g.vs[0]
        gv = self.__g.vs[1]

        basic_layout_roll = self.__dice.d100
        basic_layout_roll = 1
        if basic_layout_roll <= 25:
            key = self.dobject("key", "key 1")

            self.__objects.append(key)

            nv = self.__insert_room_btw(sv, gv, "OM", object=key)
            self.__insert_room_btw(nv, gv, "OO")
        elif basic_layout_roll <= 50:
            external = self.dobject("bang", "external 1")
            hp = self.dobject("hp", "Heart piece")
            key = self.dobject("key", "key 1")

            self.__objects.append(hp)
            self.__objects.append(external)
            self.__objects.append(key)

            nv_c = self.__insert_room_btw(sv, gv, "C")
            nv_ol = self.__insert_room_end(nv_c, "OL", object=external)
            self.__insert_room_end(nv_ol, "UI", object=hp)
            nv_om = self.__insert_room_btw(nv_c, gv, "OM", object=key)
            self.__insert_room_btw(nv_om, gv, "OO")
        elif basic_layout_roll <= 75:
            key = self.dobject("key", "key 1")
            i5 = self.dobject("i5", "Boss key")

            self.__objects.append(i5)
            self.__objects.append(key)

            nv_ol1 = self.__insert_room_btw(sv, gv, "OL", object=key)
            nv_ol2 = self.__insert_room_btw(nv_ol1, gv, "OL", object=i5)
            self.__insert_room_btw(nv_ol2, gv, "eb", color=color_green)
            self.__insert_room_end(sv, "UI", object=key)
            self.__insert_room_end(sv, "UI", object=i5)
        else:
            key = self.dobject("key", "key 1")
            i5 = self.dobject("i5", "Boss key")

            self.__objects.append(i5)
            self.__objects.append(key)

            nv_oli = self.__insert_room_btw(sv, gv, "OL", object=i5)
            self.__insert_room_btw(nv_oli, gv, "eb", color=color_green)
            self.__insert_room_end(sv, "UI", object=key)
            nv_ui = self.__insert_room_end(sv, "UI", object=i5)
            self.__insert_room_btw(sv, nv_ui, "OL", object=key)
        return

    def __process(self):
        missing = []
        niter = 0
        while True:
            niter += 1
            # get all the red vertex
            red_vertex = self.__g.vs.select(color_eq=color_red)
            if not red_vertex:
                logger.info("End of dungeon process")
                break
            rv = red_vertex[0]
            rv_type = rv["type"]
            # logger.debug(rv_type)
            if rv_type == "C":
                self.__generate_C(rv)
            elif rv_type == "GB":
                self.__generate_GB(rv)
            elif rv_type == "H":
                self.__generate_H(rv)
            elif rv_type == "MI":
                self.__generate_MI(rv)
            elif rv_type == "ML":
                self.__generate_ML(rv)
            elif rv_type == "MM":
                self.__generate_MM(rv)
            elif rv_type == "MM2":
                self.__generate_MM2(rv)
            elif rv_type == "MO":
                self.__generate_MO(rv)
            elif rv_type == "MS":
                self.__generate_MS(rv)
            elif rv_type == "MS2":
                self.__generate_MS2(rv)
            elif rv_type == "OL":
                self.__generate_OL(rv)
            elif rv_type == "OM":
                self.__generate_OM(rv)
            elif rv_type == "OO":
                self.__generate_OO(rv)
            elif rv_type == "S":
                self.__generate_S(rv)
            elif rv_type == "SW":
                self.__generate_SW(rv)
            elif rv_type == "SWL":
                self.__generate_SWL(rv)
            elif rv_type == "UI":
                self.__generate_UI(rv)
            else:
                if rv_type not in missing:
                    missing.append(rv_type)
            # max num of iter
            if self.__g.vcount() > 1000 or niter > 5:
                logger.info(f"Finished process - Vertices: {self.__g.vcount()} Iterations: {niter}")
                break
        missing.sort()
        for miss in missing:
            logger.error(f">>>>>>>>>>>>>> MISSING: {miss}")

    def __generate_C(self, rv):
        """Chain

        Attrs:
            rv int:  Reference vertex

        """
        voi = self.__g.neighbors(rv, "in")[0]
        vdi = self.__g.neighbors(rv, "out")[0]

        roll = self.__dice.d100
        if roll <= 25:
            type = "H"
        if roll <= 50:
            type = "MO"
        if roll <= 75:
            type = "MM"
        else:
            type = "MS"
        fn = self.__insert_room_btw(voi, vdi, type)
        self.__remove_room(rv, fn)
        return

    def __generate_GB(self, rv):
        """Bonus Goal Sequence

        Attrs:
            rv int:  Reference vertex

        """
        voi = self.__g.neighbors(rv, "in")[0]

        roll = self.__dice.d100
        if roll <= 25:
            type = "UI(hp)"
        if roll <= 50:
            type = "MI(ir)"
        if roll <= 75:
            type = "MI(ib)"
        else:
            type = "MI(ia)"
        fn = self.__insert_room_end(voi, type)
        self.__remove_room(rv, fn)
        return

    def __generate_H(self, rv):
        """Hook sequence

        Attrs:
            rv int:  Reference vertex

        """
        voi = self.__g.neighbors(rv, "in")[0]
        vdi = self.__g.neighbors(rv, "out")[0]

        fn = self.__insert_room_btw(voi, vdi, "n", color=color_green)
        self.__insert_room_end(fn, "GB()")
        self.__remove_room(rv, fn, fn)
        return

    def __generate_OL(self, rv):
        """One lock sequence

        Attrs:
            rv int:  Reference vertex

        """
        voi = self.__g.neighbors(rv, "in")[0]
        vdi = self.__g.neighbors(rv, "out")[0]

        roll = self.__dice.d100
        if roll <= 50:
            type = "C()"
        else:
            type = "S()"
        fn = self.__insert_room_btw(voi, vdi, type)
        nv_k = self.__insert_room_btw(fn, vdi, "Use ?", color=color_blue)
        ln = self.__insert_room_btw(nv_k, vdi, "n", color=color_green)
        self.__remove_room(rv, fn, ln)
        return

    def __generate_OM(self, rv):
        """One key to many lock

        Attrs:
            rv int:  Reference vertex

        """
        voi = self.__g.neighbors(rv, "in")[0]
        vdi = self.__g.neighbors(rv, "out")[0]

        keys = [key for key in rv['objects'] if key.type == 'key']
        if len(keys) > 1:
            logger.error('More than One Key')
        key = keys[0]

        fn = self.__insert_room_btw(voi, vdi, "n", color=color_green)
        self.__insert_room_end(fn, "UI", object=key)
        nv_ml = self.__insert_room_end(fn, "ML", object=key)
        self.__insert_room_end(nv_ml, "GB")
        ln = self.__insert_room_btw(fn, vdi, "OL", object=key)
        self.__remove_room(rv, fn, ln)
        return

    def __generate_OO(self, rv):
        """One key to one lock

        Attrs:
            rv int:  Reference vertex

        """
        voi = self.__g.neighbors(rv, "in")[0]
        vdi = self.__g.neighbors(rv, "out")[0]

        fn = self.__insert_room_btw(voi, vdi, "n", color=color_green)
        self.__insert_room_end(fn, "UI(i5)")
        nv_ol = self.__insert_room_btw(fn, vdi, "OL(i5)")
        ln = self.__insert_room_btw(nv_ol, vdi, "eb", color=color_green)
        self.__remove_room(rv, fn, ln)
        return

    def __generate_MI(self, rv):
        """Many items

        Attrs:
            rv int:  Reference vertex

        """
        voi = self.__g.neighbors(rv, "in")[0]

        roll = self.__dice.d100
        if roll <= 50:
            type = "C()"
        else:
            type = "S()"
        fn = self.__insert_room_end(voi, type)
        self.__insert_room_btw(fn, voi, "Get M?", color=color_cyan)
        self.__remove_room(rv, fn)
        return

    def __generate_ML(self, rv):
        """Many lock sequence

        Attrs:
            rv int:  Reference vertex

        """
        voi = self.__g.neighbors(rv, "in")[0]
        vdi = self.__g.neighbors(rv, "out")[0]

        roll = self.__dice.d100
        if roll <= 75:
            type = "OL(?)"
            color = color_red
        else:
            type = "n"
            color = color_green
        fn = ln = self.__insert_room_btw(voi, vdi, type, color=color)
        if roll > 75:
            nv_ml = self.__insert_room_end(fn, "ML(?)")
            self.__insert_room_end(nv_ml, "GB()")
            ln = self.__insert_room_btw(fn, vdi, "OL(?)")
        self.__remove_room(rv, fn, ln)
        return

    def __generate_MM(self, rv):
        """Switch lock chain

        Attrs:
            rv int:  Reference vertex

        """
        voi = self.__g.neighbors(rv, "in")[0]
        vdi = self.__g.neighbors(rv, "out")[0]

        fn = self.__insert_room_btw(voi, vdi, "n", color=color_green)
        nv_sw = self.__insert_room_end(fn, "SW()")
        nv_tog = self.__insert_room_end(nv_sw, "tog", color=color_pink)
        nv_mm2 = self.__insert_room_btw(fn, nv_tog, "MM2()")
        self.__insert_room_btw(nv_mm2, nv_tog, "!", color=color_cyan)
        self.__insert_room_end(nv_mm2, "GB()")
        ln = self.__insert_room_btw(fn, vdi, "SWL()")
        self.__g.add_edges([(ln, nv_tog)])

        self.__remove_room(rv, fn, ln)
        return

    def __generate_MM2(self, rv):
        """Switch lock chain II

        Attrs:
            rv int:  Reference vertex

        """
        voi = self.__g.neighbors(rv, "in")[0]
        vdi = self.__g.neighbors(rv, "out")[0]

        fn = self.__insert_room_btw(voi, vdi, "SWL()")
        nv_swe = self.__insert_room_end(fn, "SW()")
        self.__insert_room_btw(fn, nv_swe, "", color=color_pink)
        nv_bang = self.__insert_room_btw(fn, nv_swe, "!", color=color_cyan)
        ln = self.__insert_room_btw(fn, vdi, "SWL()")
        self.__g.add_edges([(nv_bang, ln)])

        roll = self.__dice.d100
        if roll > 50:
            nv_mm = self.__insert_room_end(nv_bang, "MM2()")
            self.__insert_room_end(nv_mm, "GB()")

        self.__remove_room(rv, fn, ln)
        return

    def __generate_MO(self, rv):
        """Many key many lock

        Attrs:
            rv int:  Reference vertex

        """
        voi = self.__g.neighbors(rv, "in")[0]
        vdi = self.__g.neighbors(rv, "out")[0]

        fn = self.__insert_room_btw(voi, vdi, "n", color=color_green)
        self.__insert_room_end(fn, "MI(i1)")
        ln = self.__insert_room_btw(fn, vdi, "OL(i1)")
        self.__remove_room(rv, fn, ln)
        return

    def __generate_MS(self, rv):
        """Multi switch sequence

        Attrs:
            rv int:  Reference vertex

        """
        voi = self.__g.neighbors(rv, "in")[0]
        vdi = self.__g.neighbors(rv, "out")[0]

        fn = self.__insert_room_btw(voi, vdi, "n", color=color_green)
        nv_sw = self.__insert_room_end(fn, "SW()")
        nv_and = self.__insert_room_end(nv_sw, "and", color=color_pink)
        self.__insert_room_btw(fn, nv_and, "MS2()")
        ln = self.__insert_room_btw(fn, vdi, "SWL()")
        self.__g.add_edges([(ln, nv_and)])

        self.__remove_room(rv, fn, ln)
        return

    def __generate_MS2(self, rv):
        """Multi switch sequence II

        Attrs:
            rv int:  Reference vertex

        """
        voi = self.__g.neighbors(rv, "in")[0]
        vdi = self.__g.neighbors(rv, "out")[0]

        fn = self.__insert_room_btw(voi, vdi, "n", color=color_green)
        nv_sw = self.__insert_room_end(fn, "SW()")
        nv_and = self.__insert_room_end(nv_sw, "and", color=color_pink)

        roll = self.__dice.d100
        if roll > 75:
            self.__insert_room_btw(fn, nv_and, "MS2()")

        self.__remove_room(rv, fn)
        return

    def __generate_S(self, rv):
        """Linear sequence

        Attrs:
            rv int:  Reference vertex

        """
        voi = self.__g.neighbors(rv, "in")[0]
        vdi = self.__g.neighbors(rv, "out")[0]

        roll = self.__dice.d100
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
            type = "S()"
            color = color_red
        fn = ln = self.__insert_room_btw(voi, vdi, type, color=color)
        if roll > 90:
            ln = self.__insert_room_btw(fn, vdi, "S()")
        self.__remove_room(rv, fn, ln)
        return

    def __generate_SW(self, rv):
        """Switch sequence

        Attrs:
            rv int:  Reference vertex

        """
        voi = self.__g.neighbors(rv, "in")[0]

        roll = self.__dice.d100
        if roll <= 50:
            type = "C()"
        else:
            type = "S()"
        fn = self.__insert_room_end(voi, type)
        self.__insert_room_btw(fn, voi, "sw", color=color_green)
        self.__remove_room(rv, fn)
        return

    def __generate_SWL(self, rv):
        """Switch-lock sequence

        Attrs:
            rv int:  Reference vertex

        """
        voi = self.__g.neighbors(rv, "in")[0]
        vdi = self.__g.neighbors(rv, "out")[0]

        roll = self.__dice.d100
        if roll <= 50:
            type = "C()"
        else:
            type = "S()"
        ln = self.__insert_room_btw(voi, vdi, "n", color=color_green)
        fn = self.__insert_room_btw(voi, ln, type)
        nv_t = self.__insert_room_btw(voi, ln, type)

        nv = self.__g.add_vertex()
        self.__format_nv(nv, "", color=color_pink, name="")
        self.__g.add_edges([(nv_t, nv.index), (nv.index, ln)])

        self.__remove_room(rv, fn, ln)
        return

    def __generate_UI(self, rv):
        """Unique item

        Attrs:
            rv int:  Reference vertex

        """
        voi = self.__g.neighbors(rv, "in")[0]

        roll = self.__dice.d100
        if roll <= 50:
            type = "C()"
        else:
            type = "S()"
        fn = self.__insert_room_end(voi, type)
        nv_em = self.__insert_room_end(fn, "em", color=color_green)

        objects = [obj for obj in rv['objects']]
        if len(objects) > 1:
            logger.error('More than one OBJECT in UI')
        uiobject = objects[0]

        self.__insert_room_btw(nv_em, voi, f"Get {uiobject.name}", object=uiobject, color=color_cyan)
        self.__remove_room(rv, fn)
        return

    def __remove_room(self, rv, fn, ln=None):
        """Checks if the room still has connections and changes to the new room, then removes the room

        Arguments:
            rv: Vertex to remove
            fn: Index of first new node
            ln: Index of last new node
        """
        rvi = rv.index
        lvoi = self.__g.neighbors(rv, "in")
        lvdi = self.__g.neighbors(rv, "out")
        if not ln:
            ln = fn
        lo = lvoi if lvoi else []
        ld = lvdi if lvdi else []
        lnr = ()
        for vi in lo + ld:
            if vi in lo:
                if not self.__g.are_connected(vi, fn):
                    lnr = (vi, fn)
                eid = self.__g.get_eid(vi, rvi)
            elif vi in ld:
                if not self.__g.are_connected(ln, vi):
                    lnr = (ln, vi)
                eid = self.__g.get_eid(rvi, vi)
            if lnr:
                self.__g.add_edges([lnr])
            self.__g.delete_edges(eid)

        self.__g.delete_vertices(rv)
        return

    def __insert_room_btw(
        self, voi, vdi, type, name=None, object=None, color=color_red, break_conn=True
    ):
        """Insert a room in the graph between two elements

        Attrs:
            voi int: Vertex Origin Index
            vdi int: Vertex Destination Index
            type str: Type of the room
            name str: Name of the room
            color str: Color of the room
            break_conn bool: Theh new room breaks the existing connection

        Returns:
            int : new vertex index
        """
        if break_conn and self.__g.are_connected(voi, vdi):
            eid = self.__g.get_eid(voi, vdi)
            self.__g.delete_edges(eid)
        nv = self.__g.add_vertex()
        self.__format_nv(nv, type, color, name, object)
        self.__g.add_edges([(voi, nv.index), (nv.index, vdi)])
        return nv.index

    def __insert_room_end(self, vdi, type, name=None, object=None, color=color_red):
        """Insert a room in the graph at the end of a room

        Attrs:
            vdi int: Vertex Destination Index
            type str: Type of the room
            name str: Name of the room
            color str: Color of the room

        Returns:
            int : new vertex index
        """
        nv = self.__g.add_vertex()
        self.__format_nv(nv, type, color, name, object)
        self.__g.add_edges([(vdi, nv.index)])
        return nv.index

    def __format_nv(self, nv, type, color, name, object=None):
        """Gives a new vertex a basic format"""
        nv["type"] = type
        nv["color"] = color
        if not name:
            name = type
        nv["name"] = name
        nv["uid"] = random_string(8)
        debugstr = f'Node {nv.index}\ntype: {type}\ncolor: {color}\nname: {name}'
        if object:
            if "objects" not in nv.attribute_names() or nv["objects"] is None:
                nv["objects"] = [object]
            else:
                nv["objects"].append(object)
            debugstr += f'\nobject: {object}'
        # logger.debug(debugstr)
        return

    class dobject:
        def __init__(self, type, name):
            self.type = type
            self.name = name
            self.uid = random_string(8)

        def __repr__(self):
            return f'Type: {self.type} :: Name: {self.name} :: {self.uid}'
