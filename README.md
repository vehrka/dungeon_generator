# Dungeon Generator

**version:** 1.0.1

**date:** 2021-12-08

based on the grammar defined by [fantomx11](https://forum.rpg.net/index.php?members/fantomx11.74669/) in the [RPG.net forum](https://forum.rpg.net/index.php?threads/necro-my-zelda-dungeon-generator.827119/)

## Install

Use [uv](https://docs.astral.sh/uv/) for creating the virtual environment with

```bash
$ uv sync
```

## Usage

Launch the CLI script

```bash
$ uv run python dungeon_generator_cli.py
```

```bash
usage: dungeon_generator_cli.py [-h] [--post24] [--post30] [--combined]
                                [--size {S,M,L}] [--seed SEED]
                                [--maxnodes MAXNODES] [--maxiter MAXITER]
                                [--show-graph] [--no-reduce] [--debug]

options:
  -h, --help           show this help message and exit
  --post24             Generate a Dungeon using the Post24 Grammar
  --post30             Generate a Dungeon using the Post30 Grammar
  --combined           Generate a Dungeon using the Combined Grammar
                       (grammar/combined.py)
  --size {S,M,L}       Size preset for the Combined Grammar
  --seed SEED          Seed for the dungeon
  --maxnodes MAXNODES  Maximum number of nodes to include
  --maxiter MAXITER    Maximum number of iterations to perform
  --show-graph         Shows graph on generation
  --no-reduce          Does not reduce n,e,p adjacent elements
  --debug              Debug information
```

### Examples

Running the command

```bash
$ uv run python dungeon_generator_cli.py --post30 --seed 15143
```

will result in something similar to this graph

![Post 30 Seed 15143](./img/post30_seed15143.png)

Generate a medium sized dungeon with the Combined grammar

```bash
$ uv run python dungeon_generator_cli.py --combined --size M --seed 15143 --show-graph
```

### Legend

#### Post24

**GOAL:** Dungeon Goal

**START:** Initial position

**e:** Enemy

**eb:** Main Boss

**em:** Mini Boss

**external:** Object from outside the Dungeon

**n:** Nothing/Explore

**p:** Puzzle

**sw:** Switch (Lever, etc)

#### Post30

**EXIT:** Another Entrance/Exit

**GOAL:** Dungeon Goal

**START:** Initial position

**c:** Challenge (Skill check)

**gb:** Bonus goal

**m:** Monster

**n:** Nothing/Explore

**p:** Puzzle

**t:** Trap

#### Combined

Merges both grammars (`grammar/combined.py`): Post30 structure (layouts, loops, one-way paths,
secret paths, extra entrances) with Post24 locks (small keys, boss key, dungeon item behind a
mini-boss, switches, toggle levers, bonus goals). Every lock's key is placed on a branch that forks
before the lock, so every dungeon is solvable.

**Rooms**

**START:** Initial position

**GOAL:** Dungeon Goal

**EXIT:** Another Entrance/Exit

**n:** Nothing/Explore

**e:** Enemy

**t:** Trap

**p:** Puzzle

**c:** Challenge (Skill check)

**em:** Mini Boss

**eb:** Main Boss

**gb:** Bonus goal

**Pickups and switches**

**key:** Small key

**bosskey:** Boss key

**item:** Dungeon item

**switch:** Switch (all must be hit to open a state gate)

**lever:** Toggle lever (ON / OFF)

**Gates**

**lock:** Locked door, needs the named object

**gate:** State or toggle gate, needs the switches or the lever position

**s:** Secret path (bombable wall)

**Size presets** (`--size`), approximate number of nodes over 2000 runs

| Preset | p10 | median | p90 |
|--------|-----|--------|-----|
| S      | 10  | 14     | 20  |
| M      | 13  | 20     | 34  |
| L      | 18  | 30     | 51  |

The full grammar sheet can be rendered with Graphviz

```bash
$ uv run python -m grammar.render --output refs/combined.png
```

![Combined grammar](./refs/combined.png)

## Relations

A simple analisis of the grammar elements relations can be found in the folder `relations`

### Usage

```bash
$ uv run python relations/rel24.py
```

## Changelog

* v1.0.1 Refill dice pool when it runs out (try --seed 17848)
* v1.0 Initial release
