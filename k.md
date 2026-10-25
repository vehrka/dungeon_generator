# GM key: Combined dungeon

Seed 4 · size L · 49 rooms · solvable

## Rooms

1. **Entrance (START)**. Exits: 2
2. **Trap**. Exits: 1, 3
3. **Enemy**. Exits: 2, 4, 5
4. **Extra entrance (EXIT)**. Exits: 3
5. **Nothing / explore**. Exits: 3, 6, 7 (locked: dungeon item 1)
6. **Puzzle**. Exits: 5, 8
7. **Nothing / explore**. Exits: 5 (locked: dungeon item 1), 9, 10 (locked: small key 2)
8. **Mini-boss**. Exits: 6, 11
9. **Enemy**. Exits: 7, 12
10. **Trap**. Exits: 7 (locked: small key 2), 13 (needs switch 2), 14
11. **Pickup: dungeon item 1**. Exits: 8
12. **Pickup: small key 2**. Exits: 9
13. **Enemy**. Exits: 10 (needs switch 2), 15
14. **Enemy**. Exits: 10, 16
15. **Nothing / explore**. Exits: 13, 17 (locked: boss key 1), 18 (locked: small key 1), 19
16. **Switch: switch 2**. Exits: 14
17. **Boss**. Exits: 15 (locked: boss key 1), 20
18. **Challenge (skill check)**. Exits: 15 (locked: small key 1), 21
19. **Challenge (skill check)**. Exits: 15, 22 (needs switch 1), 23
20. **Dungeon goal (GOAL)**. Exits: 17
21. **Pickup: boss key 1**. Exits: 18
22. **Pickup: small key 1**. Exits: 19 (needs switch 1)
23. **Challenge (skill check)**. Exits: 19, 24, 25
24. **Challenge (skill check)**. Exits: 23, 27 (one-way)
25. **Challenge (skill check)**. Exits: 23, 29 (one-way)
26. **Enemy**. Exits: 24 (one-way), 30
27. **Nothing / explore**. Exits: 26 (needs switch 3 + switch 4, one-way), 31, 32
28. **Enemy**. Exits: 25 (one-way), 30
29. **Nothing / explore**. Exits: 33 (locked: small key 3), 34 (lever 1 ON), 35 (lever 1 OFF, open at start), 36
30. **Puzzle**. Exits: 26, 28, 37
31. **Switch: switch 4**. Exits: 27
32. **Enemy**. Exits: 27, 38
33. **Puzzle**. Exits: 28 (one-way), 29 (locked: small key 3)
34. **Enemy**. Exits: 29 (lever 1 ON), 39
35. **Bonus goal: arrows**. Exits: 29 (lever 1 OFF, open at start)
36. **Trap**. Exits: 29, 40, 41
37. **Switch: switch 1**. Exits: 30
38. **Switch: switch 3**. Exits: 32
39. **Pickup: small key 3**. Exits: 34
40. **Nothing / explore**. Exits: 36, 42 (locked: small key 4), 43
41. **Nothing / explore**. Exits: 36, 44 (locked: small key 5), 45
42. **Nothing / explore**. Exits: 40 (locked: small key 4), 46
43. **Challenge (skill check)**. Exits: 40, 47
44. **Nothing / explore**. Exits: 41 (locked: small key 5), 46
45. **Puzzle**. Exits: 41, 48
46. **Challenge (skill check)**. Exits: 42, 44, 49
47. **Pickup: small key 4**. Exits: 43
48. **Pickup: small key 5**. Exits: 45
49. **Lever: lever 1 (starts OFF)**. Exits: 46

## Keys

| Object | Found in | Opens |
|--------|----------|-------|
| dungeon item 1 | 11 | 5 ↔ 7 |
| boss key 1 | 21 | 15 ↔ 17 |
| small key 1 | 22 | 15 ↔ 18 |
| small key 2 | 12 | 7 ↔ 10 |
| switch 1 | 37 | 19 ↔ 22 |
| switch 2 | 16 | 10 ↔ 13 |
| switch 3 | 38 | 27 → 26 (+ switch 4) |
| switch 4 | 31 | 27 → 26 (+ switch 3) |
| small key 3 | 39 | 29 ↔ 33 |
| lever 1 | 49 | 29 ↔ 34 (ON), 29 ↔ 35 (OFF) |
| small key 4 | 47 | 40 ↔ 42 |
| small key 5 | 48 | 41 ↔ 44 |
