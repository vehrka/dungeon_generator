import igraph

from utils.graph_utils import Dungeon


class Cyber(Dungeon):
    """Cyber dungeon (stub)"""

    def _dungeonstart(self) -> None:
        """Generat the initial layout of the dungeon"""
        self._insert_room_btw(0, 1, "ENTRANCE")
        return

    def _expand_vertex(self, rv: igraph.Vertex) -> bool:
        func = {
            "ENTRANCE": self._generate_ENTRANCE,
        }.get(rv["type"])

        if func is None:
            return False

        func(rv)
        return True

    def _generate_ENTRANCE(self, rv: igraph.Vertex) -> None:
        """Entrance

        Arguments
            rv int:  Reference vertex

        """
        voi = self._g.neighbors(rv, "in")[0]
        vdi = self._g.neighbors(rv, "out")[0]

        roll = (self.d100 % 6) + 1

        self.logger.debug(f"ROLL: {roll}")

        for _ in range(roll):
            fn = ln = self._insert_room_btw(voi, vdi, "E")

        self._remove_room(rv, fn, ln)
        return
