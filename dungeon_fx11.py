import igraph
import random
import string

from utils.dice_roller import DiceRoller


class Dungeon:
    def __init__(self, dtype="p24"):
        self.__g = igraph.Graph()
        self.__dice = DiceRoller()
        self.__dungeon_type = dtype
        self.generate()
        return

    def generate(self):
        self.__g.add_vertices(2)
        self.__g.vs["name"] = ["START", "GOAL"]
        self.__g.vs["type"] = ["START", "GOAL"]
        self.__g.vs["color"] = ["green", "green"]
        if self.__dungeon_type == "p24":
            self.__dungeonstart24()
            self.__process()
            self.get_dungeon()
            self.get_graph()
        else:
            print("Post 30 dungeon type still under development")
        return

    def get_dungeon(self):
        print(self.__g)
        return

    def get_graph(self):
        import matplotlib.pyplot as plt

        layout = self.__g.layout(layout="kk")
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
            niter += 1
            # get all the red vertex
            red_vertex = self.__g.vs.select(color_eq="red")
            # for each red vertex, process its type
            for rv in red_vertex:
                rv_type = rv["type"][:2]
                nei = self.__g.neighbors(rv)
                voi = min(nei)
                vdi = max(nei)
                if rv_type == "OM":
                    self.__generate_OM(rv, voi, vdi)
            # max num of iter
            if niter > 0:
                break

    def __dungeonstart24(self):
        """Generates the initial layout of the dungeon"""
        sv = self.__g.vs.find("START").index
        gv = self.__g.vs.find("GOAL").index
        basic_layout_roll = self.__dice.d20

        #  basic_layout_roll = 1

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

    def __generate_OM(self, rv, voi, vdi):
        """One key to many lock

        Attrs:
            rv int:  Reference vertex
            voi int: Vertex Origin Index
            vdi int: Vertex Destination Index

        """
        nv_n = self.__insert_room_btw(voi, vdi, "n", color="green")
        self.__insert_room_end(nv_n, "UI(?)")
        nv_ml = self.__insert_room_end(nv_n, "ML(?)")
        self.__insert_room_end(nv_ml, "GB()")
        self.__insert_room_btw(nv_n, vdi, "OL(?)")
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
        self.__g.add_edges([(nv.index, vdi)])
        return nv.index

    def __format_nv(self, nv, type, color, name):
        """Gives a new vertex a basic format"""
        nv["type"] = type
        nv["color"] = color
        if not name:
            #  name = self.__random_string()
            name = type
        nv["name"] = name
        return

    def __random_string(self, lenght=5):
        """Generates a random string for a room name"""
        return "".join(
            random.SystemRandom().choice(string.ascii_letters + string.digits)
            for _ in range(lenght)
        )
