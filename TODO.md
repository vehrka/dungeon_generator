# TODO

Recommended order: 2, 3 → 7, 8. Item 1 depends on whether D24/D30 are still wanted.

## Generation quality

- [x] 1. **Fix or retire D24/D30.** Retired: marked legacy, `--combined` is the CLI default. Both grammars grow without bound (ρ > 1, see `refs/grammars-context.md`).
  `CAPS` and `_red_cleanup` can drop the key half of a lock/key pair, so the dungeon becomes unsolvable.
  Either port them to the data format of `grammar/combined.py` with d20 ranges tuned to ρ < 1, or mark them
  legacy and make `--combined` the CLI default.
- [x] 2. **Check solvability during generation.** Done for Combined: `unsolvable_reasons()` in `utils/graph_utils.py` runs after every generation and logs the GOAL/blocking locks; reports, no re-roll (keeps seed → dungeon). Blind for D24/D30 (their locks aren't `lock`/`gate` vertices). Move `reachable()` from `tests/test_combined.py` into the
  library. When limits are hit, check the actual result instead of only warning "may be unsolvable"; re-roll or
  report the lock that has no key.
- [x] 3. **Never stop halfway through a lock rule.** Done for Combined: on limits, `DCombined._finish()` expands the remaining non-terminals with `finish_variant` (`FINISH` in `grammar/combined.py`); lock rules still roll and get their keys. Legacy D24/D30 keep `_red_cleanup`. On `maxnodes`/`maxiter`, finish the remaining non-terminals
  with their terminal variants (L → room, S → end) instead of turning them into `n`.
- [x] 4. **Pacing.** Done for Combined: R rooms expand last, once the layout is final; `paced_room_variant` picks their content from `PACING` (`grammar/combined.py`) by progress between START and the boss, rooms within `NEAR_BOSS` steps of em/eb use the hardest tier. The `R` room chooser ignores position. Weight room content by distance from START: easier
  early, challenges and traps near the mini-boss and boss.
- [x] 5. **Merge step.** Done: `MERGE_TYPES` adds `t`, `c`; rooms merge only across two-way edges and the merged room keeps the edge attributes (the old rewiring turned one-way edges into two-way). `_reduce_graph` only merges `e`, `n`, `p`. Combined also produces `t` and `c`: merge
  them too, or document why not.
- [x] 6. **Independent rolls.** Done: `Dungeon._roll` uses `random.Random(seed).randint`; `d20` is its own roll. Same seed gives a different dungeon than before. The `d100` pool uses `random.sample(range(1, 101), 50)` × 4, so there are no
  repeats inside each block of 50, and `d20` derives from it. This skews the odds away from the documented
  ranges. Use `random.Random(seed).randint`.

## Output

- [x] 7. **JSON export** of the graph: Done: `--json PATH` (`utils/dungeon_json.py`), gates are nodes with `requires`; objects list `found_in`/`opens`. Legacy D24/D30 locks export as rooms. rooms, edges, objects, and which gate needs which object. Base for any
  consumer (e.g. a FoundryVTT module).
- [x] 8. **GM key in Markdown.** Done: `--key PATH` (`utils/dungeon_key.py`), built on the JSON export; gates appear as exit conditions, not numbered rooms. Numbered room list with exits, contents and a "key in room X opens room Y"
  table.
- [ ] 9. **Room graph to map.** Grid placement (BFS layering plus collision fixes), then a simple map or Foundry
  scene walls. Large; possibly a separate project.
- [ ] 10. **Themes as data.** Swappable room labels and reward tables. Replace the `cyberpuzze.py` stub with a
  cyber theme on top of the Combined grammar.

## Code health

- [ ] 11. **CLI.** ~~`--post24` no-op~~ (fixed with item 1: mutually exclusive group). Root logger is forced to DEBUG; tie it to `--debug`. Replace the TODO docstring in `main`.
- [ ] 12. **Seed.** `if seed` treats `--seed 0` as no seed: use `is not None`.
- [ ] 13. **`_remove_room`.** Returns early on `igraph.InternalError` while rewiring, which can leave a
  half-connected vertex behind with no warning.
- [ ] 14. **Dead code.** `utils/dice_roller.py` is unused; `relations/` holds one-off scripts. Delete them or
  move them to `refs/`.
- [ ] 15. **Lint config.** pre-commit black uses line length 100; pyproject and `.flake8` use 120. Pick one
  (consider ruff).
- [ ] 16. **Type hints** on all functions and classes.
- [x] 17. **README.** Done: version 2.0.0 in README, pyproject and changelog; the legend has a Combined section. Version 1.0.1 and date 2021-12-08 conflict with pyproject version 0.1.0. The legend
  doesn't cover the Combined grammar.
- [ ] 18. **Tests.** D24/D30 solvability tests marked `xfail` to record the known bug; a regression test that
  pins one seed to its output.
