import random


class DiceRoller():

    def __init__(self):
        pass

    @property
    def d2(self):
        return random.randint(1, 2)

    @property
    def d4(self):
        return random.randint(1, 4)

    @property
    def d6(self):
        return random.randint(1, 6)

    @property
    def d8(self):
        return random.randint(1, 8)

    @property
    def d10(self):
        return random.randint(1, 10)

    @property
    def d12(self):
        return random.randint(1, 12)

    @property
    def d20(self):
        return random.randint(1, 20)

    @property
    def d66(self):
        return random.randint(1, 6) * 10 + random.randint(1, 6)

    @property
    def d100(self):
        return random.randint(1, 100)

    @property
    def dsombra(self):
        dsombra = random.randint(1, 10)
        dadosq = [random.randint(1, 10) for i in range(2)]
        dadosq.sort()
        dmin, dmax = dadosq
        return f'({dsombra}) {dmax} {dmin} : {dsombra+dmax+dmin}'
