# GM key: Combined dungeon

Seed 444 · size L · theme cyber · 26 rooms · solvable

## Rooms

1. **Jack-in point (START)**. Exits: 2
2. **Encrypted lock (puzzle)**. Exits: 1, 3
3. **Empty node / scan**. Exits: 2, 4 (locked: icebreaker 1), 5
4. **Firewall (hacking check)**. Exits: 3 (locked: icebreaker 1), 6, 7
5. **ICE**. Exits: 3, 8
6. **Encrypted lock (puzzle)**. Exits: 4, 9
7. **Empty node / scan**. Exits: 4, 9 (needs relay 1 + relay 2), 10, 11
8. **Trace trap**. Exits: 5, 12
9. **Empty node / scan**. Exits: 6, 7 (needs relay 1 + relay 2), 13
10. **Encrypted lock (puzzle)**. Exits: 7, 14
11. **Encrypted lock (puzzle)**. Exits: 7, 15
12. **Black ICE sentinel**. Exits: 8, 16
13. **Encrypted lock (puzzle)**. Exits: 9, 17
14. **Switch: relay 1**. Exits: 10
15. **Switch: relay 2**. Exits: 11
16. **Pickup: icebreaker 1**. Exits: 12
17. **Empty node / scan**. Exits: 13, 18 (locked: root key 1), 19, 20 (locked: access code 1)
18. **Core AI**. Exits: 17 (locked: root key 1), 21
19. **Trace trap**. Exits: 17, 22
20. **Trace trap**. Exits: 17 (locked: access code 1), 24 (one-way)
21. **Data core (GOAL)**. Exits: 18
22. **Pickup: access code 1**. Exits: 19
23. **ICE**. Exits: 20 (one-way), 25
24. **Trace trap**. Exits: 23 (one-way), 26
25. **Pickup: root key 1**. Exits: 23
26. **Data cache: black-market program**. Exits: 24

## Keys

| Object | Found in | Opens |
|--------|----------|-------|
| icebreaker 1 | 16 | 3 ↔ 4 |
| root key 1 | 25 | 17 ↔ 18 |
| access code 1 | 22 | 17 ↔ 20 |
| relay 1 | 14 | 7 ↔ 9 (+ relay 2) |
| relay 2 | 15 | 7 ↔ 9 (+ relay 1) |
