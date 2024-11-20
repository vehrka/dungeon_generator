from utils.graph_utils import Dungeon

from utils.color_utils import (
    color_red,
)


class Cyber(Dungeon):
    def _dungeonstart(self):
        """Generat the initial layout of the dungeon"""
        sv = self._g.vs[0]
        gv = self._g.vs[1]
        self._insert_room_btw(sv, gv, "ENTRANCE")
        return

    def _rv_processor(self, rv):
        func = {
            "ENTRANCE": self._generate_ENTRANCE,
        }.get(rv["type"], None)

        if func is None:
            return None

        return func(rv)

    def _process(self):
        """Main graph processor

        Tries to substitute every red vertex with the correspondent sequence.

        Finishes after 200 iterations or if the graph has 1 000 vertices
        """
        missing_gram = set()
        while True:
            self._niter += 1
            # get all the red vertices
            #  self.plot_dungeon(debug=True)
            red_vertices = self._g.vs.select(color_eq=color_red, reviewed_eq=False)
            if not red_vertices:
                break
            rv = red_vertices[0]
            rv["reviewed"] = True
            status = self._rv_processor(rv)
            if status is None:
                missing_gram.add(rv["type"])
            if self._g.vcount() > self._maxnode or self._niter > self._maxiter:
                break
        if missing_gram:
            self.logger.error(f"Missing grammar for {missing_gram}")
        return

    def _generate_ENTRANCE(self, rv):
        """Entrance

        Arguments
            rv int:  Reference vertex

        """
        voi = self._g.neighbors(rv, "in")[0]
        vdi = self._g.neighbors(rv, "out")[0]

        roll = (self.d100 % 6)+1

        self.logger.debug(f"ROLL: {roll}")

        for _ in range(roll):
            fn = ln = self._insert_room_btw(voi, vdi, "E")

        self._remove_room(rv, fn, ln)
        return
