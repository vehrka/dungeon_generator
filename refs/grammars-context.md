# Zelda-like Dungeon Grammars — Context

Context for working on `dungeon_fx11.py` (`D24`, `D30`). Sources: `refs/post24.png`, `refs/post30.png`
(grammars by fantomx11, RPG.net "Zelda dungeon generator" thread), `refs/relations/rel24.py`, `refs/relations/rel30.py`,
`refs/imgs/rel_post24.png`.

## 1. How the grammars work (both)

- **Mission graph grammar**, not a space/layout grammar. Output = directed graph of rooms + dependencies
  (keys, switches, states). No geometry.
- Context-free rewriting: start with `DungeonStart`, pick any **red** node (non-terminal), roll d20, replace with
  the matching diagram. Stop when every node is **green** (terminal).
- Diagram conventions:
  - **Blue** = previous node in the sequence (incoming anchor). **Teal** = next node (outgoing anchor).
    A rule with no teal node is a *dead-end branch* (side room).
  - **Pink** = global state (switch/lever/"and"). Dotted line = read (diamond on state side) or write
    (diamond on switch side).
  - Label on an edge (`k`, `s`, `?`, `!`, `i5`) = edge is locked/hidden and needs that item/key/discovery.
- Final step: merge consecutive `n`/`p`/`e` (Post24) or "similar" nodes (Post30) on unlocked two-way paths.
  Implemented as `_reduce_graph()` (`e`, `n`, `p` only).
- Lock/key correctness is **structural**: every rule that creates a lock also creates its key on a branch that
  forks *before* the lock from a common node. As long as every rule is fully expanded, the dungeon is solvable.

## 2. Post24 grammar (`D24`)

### Vocabulary

Non-terminals: `C` chain, `S` linear, `H` hook, `GB` bonus goal, `UI` unique item, `MI` many items,
`OL` one lock, `ML` many locks, `OM` one-key/many-locks, `OO` one-key/one-lock (boss key), `MO` many-key/many-lock
(small keys), `MM`/`MM2` switch-lock chain (toggle lever), `MS`/`MS2` multi-switch ("and" state),
`SW` switch, `SWL` switch-lock.

Terminals: `n` nothing, `p` puzzle, `e` enemy, `em` mini-boss, `eb` boss, `g` goal, items `i1` small key,
`i5` boss key, `?` dungeon item (hookshot, bombs...), `!` external item, `hp/ir/ib/ia` rewards.

### Rule summary (PNG)

| Rule | Expansion | Recursive children |
|---|---|---|
| DungeonStart | 4 layouts: OM+OO / C+OL(!)+OM+OO / UI,UI(i5),OL,OL(i5),eb / UI,OL,UI(i5),OL(i5),eb | — |
| C | 25% each H, MO, MM, MS | 1 |
| S | n / p / e / S S (25%) | 0.5 S |
| H | n + side GB | GB |
| GB | UI(hp) 10%, MI(ir/ib/ia) 90% | 1 |
| UI | (C 50% \| S) + em + item back to anchor | C or S |
| MI | (C 50% \| S) + item back to anchor | C or S |
| OL | (C 50% \| S) + locked edge + n | C or S |
| ML | OL (50%) \| n + ML + GB + OL (50%) | recursive ML |
| OM | n + UI + ML + GB + OL | 4 |
| OO | n + UI(i5) + OL(i5) + eb | 2 |
| MO | n + MI(i1) + OL(i1) | 2 |
| MM | n + SW + MM2 + GB + SWL + toggle state | 4 |
| MM2 | SWL + SW + SWL (+ MM2 + GB 50%) | 3–5 |
| MS | n + SW + MS2 + SWL + "and" state | 3 |
| MS2 | n + SW (+ MS2 50%) | 1–2 |
| SW | (C 50% \| S) + sw writes state | C or S |
| SWL | (C 50% \| S) + n, path gated by state | C or S |

### Strong points

- **Real Zelda vocabulary**: small keys vs boss key, mini-boss guarding dungeon item, heart pieces, external (`!`)
  items, toggle levers (crystal switches), multi-switch "and" doors. Closest to actual Zelda dungeon structure.
- Lock/key placement guaranteed solvable by construction (fork-before-lock pattern).
- Hierarchical: `DungeonStart` gives macro structure (boss key → boss → goal), chains fill mid-level.
- Bonus goals (`GB`) add optional side content → non-linear exploration.

### Weak points

- **Strongly supercritical** (explodes). Let `p` = probability of `C` instead of `S` in UI/MI/OL/SW/SWL
  (PNG: 0.5). Expected `C` produced by one `C` ≈ 0.25·(H:p + MO:2p + MM:~10p + MS:~4p) ≈ **4.25·p ≈ 2.1**.
  Any mean > 1 means unbounded expected growth. `MM` alone spawns ~5 new `C` on average.
- `C` is the hub (see `rel_post24.png`): almost every rule points back to `C` → one knob controls everything,
  but the knob is too hot.
- 17 non-terminals, heavy coupling → hard to reason about and tune.
- `MM`/`MM2` (toggle states) produce puzzles that are hard to read even for humans; recursive `MM2` stacks them.
- No notion of dungeon item gating progression *inside* the dungeon beyond `UI(?)` / `OL(?)` from the start rule.

### Code vs PNG divergences (`D24`)

- `p` lowered from 0.5 to **0.3** (`roll <= 30`) in UI, MI, OL, SW, SWL. Still supercritical (≈1.3).
- `MS2` recursion 25% (PNG 50%). `ML` recursion 25% (PNG 50%).
- Hard caps in `_process`: `C > 5`, `SW > 2`, `SWL > 2` → node turned into `n` instead of expanded.
- `_generate_SWL` inserts **two** `C`/`S` nodes (`fn` and `nv_t`) → doubles growth vs PNG (one C/S).
- **Bug** `_generate_S`: `if/if/if/else` instead of `if/elif` → `n` and `p` never produced; S yields `e` (90%)
  or `S S` (10%).

## 3. Post30 grammar (`D30`)

### Vocabulary

Non-terminals: `E` entrance chain, `L` layout chooser, `R` room chooser, `S` linear, `H` hook, `K` lock chain,
`MS` multi-switch, `SW` switch, `SWL` switch-lock, `GB` bonus goal.

Terminals: `e` entrance, `g` goal, `gb` bonus goal, `n` nothing, `t` trap, `m` monster, `p` puzzle,
`c` challenge (skill). Edge labels `k` (locked) and `s` (secret).

### Rule summary (PNG)

| Rule | Expansion | Recursive children |
|---|---|---|
| DungeonStart | e + E + g | 1 E |
| E | L (50%) \| L + E + R + L + extra entrance (50%) | 0.5 E, L |
| L | H 10%, K 15%, MS 15%, S 10%, L R L 15%, R + 2 parallel L + R 35% (one-way variants) | ~1.85+ L |
| R | n / t / m / p / c (20% each) | terminal only |
| S | R \| R + S (50%) | 0.5 S |
| H | R + GB (optionally secret `s` edge) | GB |
| GB | L + gb | 1 L |
| K | R + L + L(k) locked (50%) \| R + K + K + GB (50%) | **mean 1 K** |
| MS | R + SW + state lock (+ SWL + GB 50%) | SW, SWL |
| SW | L + sw (50%) \| R + L + sw + SW (50%) | 0.5 SW |
| SWL | L + state + L (50%) \| R + L + L + SWL + GB (50%) | 0.5 SWL |

### Strong points

- **Clean layering**: `E`/`L`/`S` = topology, `H`/`K`/`MS`/`SW`/`SWL` = mechanics, `R` = room content.
  `R` is a single terminal chooser → content easy to retheme (system-agnostic, RPG-friendly: traps, challenges).
- Fewer non-terminals (10), easier to read and tune.
- Explicit **loops** (`L` 14–20: two parallel paths, one-way variants) → cycles, not just trees. Good for
  Zelda-style "loop back" shortcuts.
- Multiple entrances/exits (`E`), secret edges (`s`) → interesting for tabletop.

### Weak points

- **`L` is supercritical**: 50% of L rules produce 2 `L` (mean 1.0 alone) + H/GB, K, MS, SW, SWL all emit more `L`
  (`MS` ≈ 5 L on average, `GB` always 1 L). Mean ≥ ~1.85 L per L → unbounded.
- **`K` is critical** (mean exactly 1 `K` per `K`): terminates eventually but with a heavy tail → occasional huge
  key chains.
- No boss, mini-boss, dungeon item, or key *types* → loses the Zelda "get item X, use it to reach boss" arc.
  Keys are generic `k`; no reward for exploration besides `gb`.
- No pacing: room content uniform random, independent of depth/position.

### Code vs PNG divergences (`D30`)

- Caps in `_process`: `L > 15`, `SW > 5`, `SWL > 5` → turned into `n`.
- `GB` uses `n + gb` instead of `L + gb` (commented-out line) → manual growth reduction.
- `_generate_L` branches 66–75, 76–85, 86–100 are **identical** → one-way/two-way distinction lost.
  All igraph edges are directed; two-way vs one-way not modelled anywhere.

## 4. Why dungeons come out too big / uncontrolled

1. **Branching factor > 1** in core recursive symbols (`C` in Post24, `L` in Post30). A grammar is a multi-type
   Galton–Watson process: build matrix `M[i][j]` = expected count of symbol j produced by one expansion of i.
   Expected size is finite only if spectral radius `ρ(M) < 1`; then expected count of each symbol = `(I − M)⁻¹`.
   Both grammars have `ρ > 1`.
2. **Context-free choices**: rule selection ignores depth, current size, remaining budget, items already placed.
3. **Caps are post-hoc and global**: counts include every room ever created; once reached, the symbol becomes `n`.
   Red nodes are processed lowest-index-first, so early branches get fully expanded and late ones are stubs →
   lopsided dungeons.
4. **Caps and iteration limits break solvability.** Converting an unexpanded non-terminal to `n`
   (caps, or `_red_cleanup` after `maxiter`/`maxnodes`) can drop the key half of a lock/key pair:
   - Post30: capped `SW` → no switch placed but `Check switch N` lock remains → unsolvable.
   - Post24: unexpanded `UI(key)`/`MI(i1)` → lock with no key; unexpanded `OL(key)` → key with no lock.
5. No size target parameter: only `maxnodes` (default 300) and `maxiter` (200) hard stops.

## 5. Usefulness for Zelda-like puzzle dungeons

| Aspect | Post24 | Post30 |
|---|---|---|
| Zelda authenticity (keys, boss key, item, mini-boss) | High | Low |
| Readability / tuning | Low (17 symbols, hub `C`) | Medium-high |
| Cycles / shortcuts | Few (states only) | Yes (`L` diamonds) |
| Size control | Very poor (ρ ≈ 2) | Poor (ρ ≈ 2, K critical) |
| Retheming content | Fixed vocabulary | Easy (`R`) |
| Tabletop use | Good if small | Good if small |

Best use: Post24's **lock vocabulary** (OO boss key, MO small keys, UI item from mini-boss) on top of Post30's
**structure** (`L`/`R` split, loops).

## 6. Control levers (ideas, ordered by effort)

- **Tune to subcritical**: make every recursive rule's expected self-production < 1; compute `ρ(M)` with a small
  script to verify. Cheapest fix.
- **Depth decay**: probability of recursive alternative × `decay^depth` (store `depth` on vertices).
- **Budget-aware rules**: pass remaining room budget; when budget low, force terminal alternatives (`R`, `S`→`R`,
  `L`→`R`) *at expansion time* instead of capping afterwards. Keeps lock/key pairs whole.
- **Mechanic quotas**: decide up front "2 key locks, 1 switch puzzle, 1 hook, 1 item gate" and only allow those
  rules while quota remains (Dormans-style "recipes": ordered list of rule applications).
- **Atomic lock/key expansion**: never cut a rule half-way; if limits hit, roll back or pick the terminal variant.
- **Mission → space**: separate mission graph (this) from spatial layout (grid embedding) to bound physical size.
- Alternatives worth reading: Joris Dormans, *Adventures in Level Design* (mission/space grammars, recipes);
  Boris the Brave, *Cyclic Dungeon Generation* (Unexplored) — starts from a cycle, inserts lock/key into it,
  size bounded by design; Ron Gilbert's puzzle dependency charts (generate backwards from goal).
