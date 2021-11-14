import igraph
import random
import string

from utils.dice_roller import DiceRoller


class Dungeon:
    def __init__(self, dtype="p24"):
        self.__g = igraph.Graph(directed=True)
        self.__dice = DiceRoller()
        self.__dungeon_type = dtype
        self.generate()
        return

    def generate(self):
        self.__g.add_vertices(2)
        self.__format_nv(self.__g.vs[0], 'START', 'green', 'START-0')
        self.__format_nv(self.__g.vs[1], 'GOAL', 'green', 'GOAL-1')

        if self.__dungeon_type == "p24":
            self.__dungeonstart24()
        else:
            print("Post 30 dungeon type still under development")
            return

        self.__process()
        self.get_graph()
        return

    def get_dungeon(self):
        print(self.__g)
        return

    def get_graph(self):
        import matplotlib.pyplot as plt

        layout = self.__g.layout(layout="lgl")
        fig, ax = plt.subplots()

        visual_style = {}
        visual_style["layout"] = layout
        visual_style["bbox"] = (300, 300)
        visual_style["margin"] = 20
        visual_style["target"] = ax
        visual_style["vertex_label"] = self.__g.vs["name"]
        visual_style["vertex_color"] = self.__g.vs["color"]

        igraph.plot(self.__g, **visual_style)
        plt.show()

    def __process(self):
        niter = 0
        while True:
            #  self.get_dungeon()
            niter += 1
            # get all the red vertex
            red_vertex = self.__g.vs.select(color_eq="red")
            rv = red_vertex[0]
            rv_type = rv["type"].split("(")[0]
            if rv_type == "C":
                self.__generate_C(rv)
            elif rv_type == "OL":
                self.__generate_OL(rv)
            elif rv_type == "OM":
                self.__generate_OM(rv)
            elif rv_type == "OO":
                self.__generate_OO(rv)
            elif rv_type == "UI":
                self.__generate_UI(rv)
            # max num of iter
            if niter > 100:
                break

    def __dungeonstart24(self):
        """Generates the initial layout of the dungeon"""
        sv = self.__g.vs[0]
        gv = self.__g.vs[1]
        basic_layout_roll = self.__dice.d20

        basic_layout_roll = 6

        if basic_layout_roll <= 5:
            nv = self.__insert_room_btw(sv, gv, "OM(?)")
            self.__insert_room_btw(nv, gv, "OO()")
        elif basic_layout_roll <= 10:
            nv_c = self.__insert_room_btw(sv, gv, "C")
            nv_ol = self.__insert_room_end(nv_c, "OL(!)")
            self.__insert_room_end(nv_ol, "UI(hp)")
            nv_om = self.__insert_room_btw(nv_c, gv, "OM(?)")
            self.__insert_room_btw(nv_om, gv, "OO()")
        elif basic_layout_roll <= 15:
            nv_ol1 = self.__insert_room_btw(sv, gv, "OL(?)")
            nv_ol2 = self.__insert_room_btw(nv_ol1, gv, "OL(i5)")
            self.__insert_room_btw(nv_ol2, gv, "eb", color="green")
            self.__insert_room_end(sv, "UI(?)")
            self.__insert_room_end(sv, "UI(i5)")
        else:
            nv_oli = self.__insert_room_btw(sv, gv, "OL(i5)")
            self.__insert_room_btw(nv_oli, gv, "eb", color="green")
            self.__insert_room_end(sv, "UI(?)")
            nv_ui = self.__insert_room_end(sv, "UI(i5)")
            self.__insert_room_btw(sv, nv_ui, "OL(?)")
        return

    def __generate_C(self, rv):
        """Chain

        Attrs:
            rv int:  Reference vertex

        """
        voi = self.__g.neighbors(rv, 'in')[0]
        vdi = self.__g.neighbors(rv, 'out')[0]

        roll = self.__dice.d20
        if roll <= 5:
            type = "H()"
        if roll <= 10:
            type = "MO()"
        if roll <= 15:
            type = "MM()"
        else:
            type = "MS()"
        fn = self.__insert_room_btw(voi, vdi, type)
        self.__remove_room(rv, fn)
        return

    def __generate_OL(self, rv):
        """One lock sequence

        Attrs:
            rv int:  Reference vertex

        """
        voi = self.__g.neighbors(rv, 'in')[0]
        vdi = self.__g.neighbors(rv, 'out')[0]

        fn = self.__insert_room_btw(voi, vdi, "n", color="green")
        roll = self.__dice.d20
        if roll <= 10:
            type = "C()"
        else:
            type = "S()"
        ln = self.__insert_room_btw(fn, vdi, type)
        self.__remove_room(rv, fn, ln)
        return

    def __generate_OM(self, rv):
        """One key to many lock

        Attrs:
            rv int:  Reference vertex

        """
        voi = self.__g.neighbors(rv, 'in')[0]
        vdi = self.__g.neighbors(rv, 'out')[0]

        fn = self.__insert_room_btw(voi, vdi, "n", color="green")
        self.__insert_room_end(fn, "UI(?)")
        nv_ml = self.__insert_room_end(fn, "ML(?)")
        self.__insert_room_end(nv_ml, "GB()")
        ln = self.__insert_room_btw(fn, vdi, "OL(?)")
        self.__remove_room(rv, fn, ln)
        return

    def __generate_OO(self, rv):
        """One key to one lock

        Attrs:
            rv int:  Reference vertex

        """
        voi = self.__g.neighbors(rv, 'in')[0]
        vdi = self.__g.neighbors(rv, 'out')[0]

        fn = self.__insert_room_btw(voi, vdi, "n", color="green")
        self.__insert_room_end(fn, "UI(i5)")
        nv_ol = self.__insert_room_btw(fn, vdi, "OL(i5)")
        ln = self.__insert_room_btw(nv_ol, vdi, "eb", color="green")
        self.__remove_room(rv, fn, ln)
        return

    def __generate_UI(self, rv):
        """Unique item

        Attrs:
            rv int:  Reference vertex

        """
        voi = self.__g.neighbors(rv, 'in')[0]

        roll = self.__dice.d20
        if roll <= 10:
            type = "C()"
        else:
            type = "S()"
        fn = self.__insert_room_end(voi, type)
        nv_em = self.__insert_room_end(fn, "em", color="green")
        self.__insert_room_btw(nv_em, voi, "?")
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
        lvoi = self.__g.neighbors(rv, 'in')
        lvdi = self.__g.neighbors(rv, 'out')
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
        self, voi, vdi, type, name=None, color="red", break_conn=True
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
        self.__format_nv(nv, type, color, name)
        self.__g.add_edges([(voi, nv.index), (nv.index, vdi)])
        return nv.index

    def __insert_room_end(self, vdi, type, name=None, color="red"):
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
        self.__format_nv(nv, type, color, name)
        self.__g.add_edges([(vdi, nv.index)])
        return nv.index

    def __format_nv(self, nv, type, color, name):
        """Gives a new vertex a basic format"""
        nv["type"] = type
        nv["color"] = color
        if not name:
            name = f'{type}-{nv.index}'
        nv["name"] = name
        nv["uid"] = self.__random_string(8)
        return

    def __random_string(self, lenght=5):
        """Generates a random string for a room name"""
        return "".join(
            random.SystemRandom().choice(string.ascii_letters + string.digits)
            for _ in range(lenght)
        )
