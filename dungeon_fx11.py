import math

from grammar.combined import GATE_KINDS, GRAMMAR, choose_variant
from utils.color_utils import (
    color_black,
    color_blue,
    color_cyan,
    color_green,
    color_pink,
    color_red,
    color_yellow,
)
from utils.graph_utils import Dungeon


def pick(roll, table):
    """Returns the value of the first (top, value) entry of the table with roll <= top"""
    return next(value for top, value in table if roll <= top)


class CodedDungeon(Dungeon):
    """Dungeon whose grammar rules are the _generate_<type> methods of the class"""

    # Maximum number of rooms of a type before it is replaced by an empty room
    CAPS = {}

    def _expand_vertex(self, rv):
        rtype = rv["type"]
        generate = getattr(self, f"_generate_{rtype}", None)
        if generate and self._rooms.get(rtype, 0) < self.CAPS.get(rtype, math.inf):
            generate(rv)
            return True
        self._format_nv(rv, "n", color_green)
        return generate is not None


class D30(CodedDungeon):
    NAME = "Post30"
    CAPS = {"L": 16, "SW": 6, "SWL": 6}

    def _dungeonstart(self):
        """Generates the initial layout of the dungeon"""
        self._insert_room_btw(0, 1, "E")

    def _generate_E(self, rv):
        """Entrance"""
        voi, vdi = self._anchors(rv)
        if self.d100 <= 50:
            fn = ln = self._insert_room_btw(voi, vdi, "L")
        else:
            fn = self._insert_room_btw(voi, vdi, "E")
            nr = self._insert_room_btw(fn, vdi, "R")
            ln = self._insert_room_btw(nr, vdi, "L")
            nl2 = self._insert_room_end(nr, "L")
            self._insert_room_end(nl2, "EXIT", color=color_yellow)
        self._remove_room(rv, fn, ln)

    def _generate_GB(self, rv):
        """Bonus Goal"""
        voi, _ = self._anchors(rv)
        fn = self._insert_room_end(voi, "n", color=color_green)
        self._insert_room_end(fn, "gb", color=color_green)
        self._remove_room(rv, fn)

    def _generate_H(self, rv):
        """Hook"""
        voi, vdi = self._anchors(rv)
        fn = self._insert_room_btw(voi, vdi, "R")
        ng = self._insert_room_end(fn, "GB")
        if self.d100 > 50:
            self._insert_room_btw(fn, ng, "s", color=color_black)
        self._remove_room(rv, fn)

    def _generate_K(self, rv):
        """Lock"""
        voi, vdi = self._anchors(rv)
        fn = self._insert_room_btw(voi, vdi, "R")
        if self.d100 <= 50:
            ln = self._insert_room_btw(fn, vdi, "L")
            sl = self._insert_room_end(fn, "L")
            key = self._new_object("key", "key")
            self._insert_room_end(sl, "k", name=f"Get {key.name}", color=color_cyan, object=key)
            self._insert_room_btw(fn, ln, "k", name=f"Use {key.name}", color=color_blue, object=key)
        else:
            ln = self._insert_room_btw(fn, vdi, "K")
            ng = self._insert_room_end(fn, "K")
            self._insert_room_end(ng, "GB")
        self._remove_room(rv, fn, ln)

    def _generate_L(self, rv):
        """Layout"""
        voi, vdi = self._anchors(rv)
        roll = self.d100
        if roll <= 50:
            fn = ln = self._insert_room_btw(
                voi, vdi, pick(roll, ((10, "H"), (25, "K"), (40, "MS"), (50, "S")))
            )
        elif roll <= 65:
            fn = self._insert_room_btw(voi, vdi, "L")
            rn = self._insert_room_btw(fn, vdi, "R")
            ln = self._insert_room_btw(rn, vdi, "L")
        else:
            # loop: the one-way entrance (66-75) and one-way return (76-85) are drawn as plain loops
            fn = self._insert_room_btw(voi, vdi, "R")
            rn = self._insert_room_btw(fn, vdi, "L")
            ln = self._insert_room_btw(rn, vdi, "R")
            self._insert_room_btw(fn, ln, "L")
        self._remove_room(rv, fn, ln)

    def _generate_MS(self, rv):
        """Multi switch"""
        voi, vdi = self._anchors(rv)
        fn = self._insert_room_btw(voi, vdi, "R")
        switch = self._new_object("switch", "switch")
        self._insert_room_end(fn, "SW", object=switch)
        ln = self._insert_room_btw(fn, vdi, f"Check {switch.name}", color=color_pink)
        if self.d100 > 50:
            ns = self._insert_room_end(fn, "SWL", object=switch)
            self._insert_room_end(ns, "GB")
        self._remove_room(rv, fn, ln)

    def _generate_R(self, rv):
        """Room chooser"""
        voi, vdi = self._anchors(rv)
        type = pick(self.d100, ((20, "n"), (40, "t"), (60, "m"), (80, "p"), (100, "c")))
        fn = self._insert_room_btw(voi, vdi, type, color=color_green)
        self._remove_room(rv, fn)

    def _generate_S(self, rv):
        """Linear"""
        voi, vdi = self._anchors(rv)
        fn = ln = self._insert_room_btw(voi, vdi, "R")
        if self.d100 > 50:
            ln = self._insert_room_btw(fn, vdi, "S")
        self._remove_room(rv, fn, ln)

    def _generate_SW(self, rv):
        """Switch"""
        voi, _ = self._anchors(rv)
        switch = self._get_object_vertex(rv)
        if self.d100 <= 50:
            fn = self._insert_room_end(voi, "L")
            self._insert_room_end(fn, switch.name, color=color_pink)
        else:
            fn = self._insert_room_end(voi, "R")
            nl = self._insert_room_end(fn, "L")
            self._insert_room_end(nl, switch.name, color=color_pink)
            self._insert_room_end(fn, "SW", object=switch)
        self._remove_room(rv, fn)

    def _generate_SWL(self, rv):
        """Switch Lock"""
        voi, vdi = self._anchors(rv)
        switch = self._get_object_vertex(rv)
        if self.d100 <= 50:
            fn = nl = self._insert_room_btw(voi, vdi, "L")
        else:
            fn = self._insert_room_btw(voi, vdi, "R")
            nl = self._insert_room_btw(fn, vdi, "L")
        ns = self._insert_room_btw(nl, vdi, switch.name, color=color_pink)
        ln = self._insert_room_btw(ns, vdi, "L")
        if fn != nl:
            nsw = self._insert_room_end(fn, "SWL", object=switch)
            self._insert_room_end(nsw, "GB")
        self._remove_room(rv, fn, ln)


class D24(CodedDungeon):
    NAME = "Post24"
    CAPS = {"C": 6, "SW": 3, "SWL": 3}

    def _dungeonstart(self):
        """Generates the initial layout of the dungeon"""
        sv, gv = 0, 1
        roll = self.d100
        if roll <= 25:
            key = self._new_object("key", "key")
            nv = self._insert_room_btw(sv, gv, "OM", object=key)
            self._insert_room_btw(nv, gv, "OO")
        elif roll <= 50:
            external = self._new_object("bang", "external")
            hp = self._add_object_dungeon("hp", "Heart piece")
            key = self._new_object("key", "key")
            nv_c = self._insert_room_btw(sv, gv, "C")
            nv_ol = self._insert_room_end(nv_c, "OL", object=external)
            self._insert_room_end(nv_ol, "UI", object=hp)
            nv_om = self._insert_room_btw(nv_c, gv, "OM", object=key)
            self._insert_room_btw(nv_om, gv, "OO")
        elif roll <= 75:
            key = self._new_object("key", "key")
            i5 = self._add_object_dungeon("i5", "Boss key")
            nv_ol1 = self._insert_room_btw(sv, gv, "OL", object=key)
            nv_ol2 = self._insert_room_btw(nv_ol1, gv, "OL", object=i5)
            self._insert_room_btw(nv_ol2, gv, "eb", color=color_green)
            self._insert_room_end(sv, "UI", object=key)
            self._insert_room_end(sv, "UI", object=i5)
        else:
            key = self._new_object("key", "key")
            i5 = self._add_object_dungeon("i5", "Boss key")
            nv_oli = self._insert_room_btw(sv, gv, "OL", object=i5)
            self._insert_room_btw(nv_oli, gv, "eb", color=color_green)
            self._insert_room_end(sv, "UI", object=key)
            nv_ui = self._insert_room_end(sv, "UI", object=i5)
            self._insert_room_btw(sv, nv_ui, "OL", object=key)

    def _chain_or_linear(self):
        """Rolls between a chain (30%) and a linear sequence"""
        return "C" if self.d100 <= 30 else "S"

    def _retrieve_bang(self, rv):
        """Tries to retrieve an external object for the vertex"""
        if not self._get_object_type_count("bang"):
            return self._new_object("bang", "external")
        return self._get_object_vertex(rv, type="bang") or self._get_dungeon_object_type("bang")

    def _generate_C(self, rv):
        """Chain"""
        voi, vdi = self._anchors(rv)
        type = pick(self.d100, ((25, "H"), (50, "MO"), (75, "MM"), (100, "MS")))
        fn = self._insert_room_btw(voi, vdi, type)
        self._remove_room(rv, fn)

    def _generate_GB(self, rv):
        """Bonus Goal Sequence"""
        voi, _ = self._anchors(rv)
        otype, oname, type = pick(
            self.d100,
            (
                (25, ("hp", "Heart piece", "UI")),
                (50, ("ir", "Rupees", "MI")),
                (75, ("ib", "Bombs", "MI")),
                (100, ("ia", "Arrows", "MI")),
            ),
        )
        gbobj = self._add_object_dungeon(otype, oname)
        fn = self._insert_room_end(voi, type, object=gbobj)
        self._remove_room(rv, fn)

    def _generate_H(self, rv):
        """Hook sequence"""
        voi, vdi = self._anchors(rv)
        fn = self._insert_room_btw(voi, vdi, "n", color=color_green)
        self._insert_room_end(fn, "GB")
        self._remove_room(rv, fn)

    def _generate_OL(self, rv):
        """One lock sequence"""
        voi, vdi = self._anchors(rv)
        olobj = self._get_object_vertex(rv)
        fn = self._insert_room_btw(voi, vdi, self._chain_or_linear())
        nv_k = self._insert_room_btw(fn, vdi, f"Use {olobj.name}", color=color_blue)
        ln = self._insert_room_btw(nv_k, vdi, "n", color=color_green)
        self._remove_room(rv, fn, ln)

    def _generate_OM(self, rv):
        """One key to many lock"""
        voi, vdi = self._anchors(rv)
        key = self._get_object_vertex(rv)
        fn = self._insert_room_btw(voi, vdi, "n", color=color_green)
        self._insert_room_end(fn, "UI", object=key)
        nv_ml = self._insert_room_end(fn, "ML", object=key)
        self._insert_room_end(nv_ml, "GB")
        ln = self._insert_room_btw(fn, vdi, "OL", object=key)
        self._remove_room(rv, fn, ln)

    def _generate_OO(self, rv):
        """One key to one lock"""
        voi, vdi = self._anchors(rv)
        fn = self._insert_room_btw(voi, vdi, "n", color=color_green)
        ooobj = self._add_object_dungeon("i5", "Boss key")
        self._insert_room_end(fn, "UI", object=ooobj)
        nv_ol = self._insert_room_btw(fn, vdi, "OL", object=ooobj)
        ln = self._insert_room_btw(nv_ol, vdi, "eb", color=color_green)
        self._remove_room(rv, fn, ln)

    def _generate_MI(self, rv):
        """Many items"""
        voi, _ = self._anchors(rv)
        fn = self._insert_room_end(voi, self._chain_or_linear())
        miobject = self._get_object_vertex(rv)
        self._insert_room_btw(fn, voi, f"Get {miobject.name}", color=color_cyan)
        self._remove_room(rv, fn)

    def _generate_ML(self, rv):
        """Many lock sequence"""
        voi, vdi = self._anchors(rv)
        mlobject = self._get_object_vertex(rv)
        if self.d100 <= 75:
            fn = ln = self._insert_room_btw(voi, vdi, "OL", object=mlobject)
        else:
            fn = self._insert_room_btw(voi, vdi, "n", color=color_green)
            nv_ml = self._insert_room_end(fn, "ML", object=mlobject)
            self._insert_room_end(nv_ml, "GB")
            ln = self._insert_room_btw(fn, vdi, "OL", object=mlobject)
        self._remove_room(rv, fn, ln)

    def _generate_MM(self, rv):
        """Switch lock chain"""
        voi, vdi = self._anchors(rv)
        fn = self._insert_room_btw(voi, vdi, "n", color=color_green)
        tog = self._new_object("tog", "lever")
        nv_sw = self._insert_room_end(fn, "SW", object=tog)
        nv_tog = self._insert_room_end(nv_sw, f"Check {tog.name}", color=color_pink)
        nv_mm2 = self._insert_room_btw(fn, nv_tog, "MM2", object=tog)
        bang = self._retrieve_bang(rv)
        self._insert_room_btw(nv_mm2, nv_tog, f"Use {bang.name}", color=color_cyan)
        self._insert_room_end(nv_mm2, "GB")
        ln = self._insert_room_btw(fn, vdi, "SWL", object=tog)
        self._g.add_edges([(ln, nv_tog)])
        self._remove_room(rv, fn, ln)

    def _generate_MM2(self, rv):
        """Switch lock chain II"""
        voi, vdi = self._anchors(rv)
        obj = self._get_object_vertex(rv) or self._get_dungeon_object_type("tog")
        fn = self._insert_room_btw(voi, vdi, "SWL", object=obj)
        nv_swe = self._insert_room_end(fn, "SW", object=obj)
        self._insert_room_btw(fn, nv_swe, f"Switch {obj.name}", color=color_pink)
        bang = self._retrieve_bang(rv)
        nv_bang = self._insert_room_btw(fn, nv_swe, f"Use {bang.name}", color=color_cyan)
        ln = self._insert_room_btw(fn, vdi, "SWL", object=obj)
        self._g.add_edges([(nv_bang, ln)])
        if self.d100 > 50:
            nv_mm = self._insert_room_end(nv_bang, "MM2", object=obj)
            self._insert_room_end(nv_mm, "GB")
        self._remove_room(rv, fn, ln)

    def _generate_MO(self, rv):
        """Many key many lock"""
        voi, vdi = self._anchors(rv)
        fn = self._insert_room_btw(voi, vdi, "n", color=color_green)
        moobj = self._new_object("i1", "small key")
        self._insert_room_end(fn, "MI", object=moobj)
        ln = self._insert_room_btw(fn, vdi, "OL", object=moobj)
        self._remove_room(rv, fn, ln)

    def _generate_MS(self, rv):
        """Multi switch sequence"""
        voi, vdi = self._anchors(rv)
        fn = self._insert_room_btw(voi, vdi, "n", color=color_green)
        nv_sw = self._insert_room_end(fn, "SW")
        nv_and = self._insert_room_end(nv_sw, "and", color=color_pink)
        ms2 = self._insert_room_btw(fn, nv_and, "MS2")
        self._g.add_edges([(ms2, nv_and)])
        ln = self._insert_room_btw(fn, vdi, "SWL")
        self._g.add_edges([(ln, nv_and)])
        self._remove_room(rv, fn, ln)

    def _generate_MS2(self, rv):
        """Multi switch sequence II"""
        voi, vdi = self._anchors(rv)
        fn = self._insert_room_btw(voi, vdi, "n", color=color_green)
        nv_sw = self._insert_room_end(fn, "SW")
        nv_and = self._insert_room_end(nv_sw, "and", color=color_pink)
        if self.d100 > 75:
            self._insert_room_btw(fn, nv_and, "MS2")
        self._remove_room(rv, fn)

    def _generate_S(self, rv):
        """Linear sequence"""
        voi, vdi = self._anchors(rv)
        roll = self.d100
        if roll <= 90:
            type = pick(roll, ((30, "n"), (60, "p"), (90, "e")))
            fn = ln = self._insert_room_btw(voi, vdi, type, color=color_green)
        else:
            fn = self._insert_room_btw(voi, vdi, "S")
            ln = self._insert_room_btw(fn, vdi, "S")
        self._remove_room(rv, fn, ln)

    def _generate_SW(self, rv):
        """Switch sequence"""
        voi, _ = self._anchors(rv)
        fn = self._insert_room_end(voi, self._chain_or_linear())
        obj = self._get_object_vertex(rv) or self._new_object("and", "and")
        self._insert_room_btw(fn, voi, f"Touch {obj.name}", color=color_pink)
        self._remove_room(rv, fn)

    def _generate_SWL(self, rv):
        """Switch-lock sequence"""
        voi, vdi = self._anchors(rv)
        type = self._chain_or_linear()
        ln = self._insert_room_btw(voi, vdi, "n", color=color_green)
        fn = self._insert_room_btw(voi, ln, type)
        nv_t = self._insert_room_btw(voi, ln, type)
        obj = self._get_object_vertex(rv) or self._new_object("and", "and")
        nv = self._g.add_vertex()
        self._format_nv(nv, "sw", color=color_pink, name=f"Touch {obj.name}")
        self._g.add_edges([(nv_t, nv.index), (nv.index, ln)])
        self._remove_room(rv, fn, ln)

    def _generate_UI(self, rv):
        """Unique item"""
        voi, _ = self._anchors(rv)
        fn = self._insert_room_end(voi, self._chain_or_linear())
        nv_em = self._insert_room_end(fn, "em", color=color_green)
        uiobject = self._get_object_vertex(rv)
        self._insert_room_btw(nv_em, voi, f"Get {uiobject.name}", object=uiobject, color=color_cyan)
        self._remove_room(rv, fn)


class DCombined(Dungeon):
    """Dungeon generated with the combined grammar (grammar/combined.py)

    The grammar is applied as data: each non-terminal is replaced by the subgraph of the
    chosen variant. The "prev" anchor connects to every in-neighbour of the replaced vertex
    and "next" to every out-neighbour, so vertices with several connections (hubs, loops)
    are expanded without losing edges. Gates (locks, states, secrets) become vertices
    between their endpoints, as in D24 and D30.
    """

    NAME = "Combined"

    def __init__(self, **dargs):
        self._preset = dargs.get("size", "M")
        super().__init__(**dargs)

    def _plot_subtitle(self):
        return f"size {self._preset} · {super()._plot_subtitle()}"

    @property
    def d20(self):
        """Get a d20 roll from the d100 pool"""
        return (self.d100 - 1) // 5 + 1

    def _dungeonstart(self):
        """Applies the Start rule between the START and GOAL vertices"""
        variant = choose_variant("Start", self._preset, self.d20)
        self._apply_variant(variant, [(0, False)], [(1, False)])

    def _expand_vertex(self, rv):
        """Replaces the vertex with the subgraph of a variant of its rule"""
        if rv["type"] not in GRAMMAR:
            return False
        variant = choose_variant(rv["type"], self._preset, self.d20)
        rvi = rv.index
        edges = self._g.es
        ins = [
            (edges[eid].source, bool(edges[eid]["oneway"]))
            for eid in sorted(self._g.incident(rvi, "in"))
        ]
        outs = [
            (edges[eid].target, bool(edges[eid]["oneway"]))
            for eid in sorted(self._g.incident(rvi, "out"))
        ]
        self._apply_variant(variant, ins, outs)
        self._g.delete_vertices(rvi)
        return True

    def _apply_variant(self, variant, ins, outs):
        """Adds the variant subgraph connected to the anchors

        Arguments:
            variant dict: Variant of a grammar rule
            ins list: (vertex index, oneway) of the vertices connected to the "prev" anchor
            outs list: (vertex index, oneway) of the vertices connected to the "next" anchor
        """
        objects = {
            oid: self._new_object(otype, oname)
            for oid, (otype, oname) in variant["objects"].items()
        }
        vmap = {
            nid: self._add_grammar_vertex(kind, label, objects)
            for nid, kind, label in variant["nodes"]
        }
        for src, dst, kind, *oids in variant["edges"]:
            gate_objects = [objects[oid] for oid in oids]
            sources = ins if src == "prev" else [(vmap[src], False)]
            targets = outs if dst == "next" else [(vmap[dst], False)]
            for svi, s_oneway in sources:
                for dvi, d_oneway in targets:
                    self._add_link(svi, dvi, kind, gate_objects, s_oneway or d_oneway)

    def _add_grammar_vertex(self, kind, label, objects):
        """Adds a vertex for a grammar node and returns its index"""
        if kind == "nt":
            return self._add_room(label, None, None, color_red)
        if kind == "item":
            obj = objects[label]
            return self._add_room(obj.type, f"Get {obj.name}", obj, color_cyan)
        if kind == "switch":
            obj = objects[label]
            return self._add_room(obj.type, obj.name, obj, color_pink)
        if kind == "special":
            return self._add_room(label.lower(), label, None, color_yellow)
        return self._add_room(label, None, None, color_green)

    def _add_link(self, svi, dvi, kind, gate_objects, oneway):
        """Connects two vertices, inserting a gate vertex for locks, states and secrets"""
        oneway = oneway or kind == "one"
        if kind not in GATE_KINDS:
            self._g.add_edge(svi, dvi, oneway=oneway)
            return
        names = " + ".join(obj.name for obj in gate_objects)
        gate = self._g.add_vertex()
        if kind == "lock":
            self._format_nv(gate, "lock", color_blue, name=f"Use {names}")
        elif kind == "secret":
            self._format_nv(gate, "s", color_black, name="secret")
        else:
            state = "" if kind == "state" else f" {kind.upper()}"
            self._format_nv(gate, "gate", color_pink, name=f"Check {names}{state}")
        if kind != "secret":
            gate["objects"] = list(gate_objects)
        self._g.add_edge(svi, gate.index, oneway=oneway)
        self._g.add_edge(gate.index, dvi, oneway=False)
