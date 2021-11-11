import igraph
import random
import string

from utils.dice_roller import DiceRoller


class Dungeon:
    def __init__(self):
        self.__g = igraph.Graph()
        self.__dice = DiceRoller()
        self.generate()
        return

    def get_dungeon(self):
        print(self.__g)
        return

    def generate(self):
        self.__g.add_vertices(2)
        self.__g.vs["name"] = ["START", "GOAL"]
        self.__g.vs["type"] = ["START", "GOAL"]
        self.__g.vs["color"] = ["green", "green"]
        self.__dungeonstart()
        self.get_dungeon()
        return

    def __dungeonstart(self):
        """Generates the initial layout of the dungeon"""
        sv = self.__g.vs.find("START").index
        gv = self.__g.vs.find("GOAL").index
        basic_layout_roll = self.__dice.d20
        if basic_layout_roll <= 5:
            nv = self.__insert_room_btw(sv, gv, "OM(?)")
            self.__insert_room_btw(nv, gv, "OO()")
        elif basic_layout_roll <= 10:
            nv_c = self.__insert_room_btw(sv, gv, "C")
            nv = self.__insert_room_end(nv_c, "OL(!)")
            self.__insert_room_end(nv, "UI(hp)")
            nv = self.__insert_room_btw(nv_c, gv, "OM(?)")
            self.__insert_room_btw(nv, gv, "OO()")
        elif basic_layout_roll <= 15:
            nv = self.__insert_room_btw(sv, gv, "OL(?)")
            nv = self.__insert_room_btw(nv, gv, "OL(i5)")
            nv = self.__insert_room_btw(nv, gv, "eb", color="green")
            self.__insert_room_end(sv, "UI(?)")
            self.__insert_room_end(sv, "UI(i5)")
        else:
            nv = self.__insert_room_btw(sv, gv, "OL(i5)")
            nv = self.__insert_room_btw(nv, gv, "eb", color="green")
            self.__insert_room_end(sv, "UI(?)")
            nv = self.__insert_room_end(sv, "UI(i5)")
            self.__insert_room_btw(sv, nv, "OL(?)")
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

    def __insert_room_end(
        self, vdi, type, name=None, color="red"
    ):
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
