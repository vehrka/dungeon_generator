from utils.graph_utils import Dungeon

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
