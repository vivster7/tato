from libcst.codemod import CodemodTest
from tato.tato import ReorderFileCodemod


class TestMultipass(CodemodTest):
    TRANSFORM = ReorderFileCodemod

    def test_unknown_constants_ordering(self) -> None:
        before = """
            if True:
                PEANUT = 2
            else:
                PEANUT = 2
            BUTTER = PEANUT * 1
        """
        after = """
            if True:
                PEANUT = 2
            else:
                PEANUT = 2
            BUTTER = PEANUT * 1
        """
        self.assertCodemod(before, after)

    def test_constants_unknown_ordering(self) -> None:
        before = """
            FLOWER = 1
            if True:
                WATER = FLOWER + 1
            else:
                WATER = FLOWER + 1
        """
        after = """
            FLOWER = 1
            if True:
                WATER = FLOWER + 1
            else:
                WATER = FLOWER + 1
        """
        self.assertCodemod(before, after)

    def test_function_ordering(self) -> None:
        before = """
            def second():
                pass
                
            def first():
                pass
                
            def main():
                first()
                second()
        """
        after = """
            def main():
                first()
                second()

            def first():
                pass
            def second():
                pass
        """
        self.assertCodemod(before, after)

    def test_multiple_symbols(self) -> None:
        before = """
            from x.y import z
            PEANUT = 1

            class One:
                pass
                    
            class Two(One):
                pass
                
            ALMOND = PEANUT + 1

            def a():
                b()

            def b():
                c()

            def c():
                pass
        """
        after = """
            from x.y import z
            PEANUT = 1
            
            ALMOND = PEANUT + 1

            class One:
                pass
                    
            class Two(One):
                pass
                
            def a():
                b()

            def b():
                c()

            def c():
                pass
        """

        self.assertCodemod(before, after)

    def test_mashed_potato(self) -> None:
        before = """
            import random

            def peel(vegetable):
                return vegetable[1:-1]

            def chop(vegetable):
                return list(vegetable)

            def mash(veg_pieces):
                random.shuffle(veg_pieces)
                return ''.join(veg_pieces)

            def prepare(vegetable):
                peeled = peel(vegetable)
                return chop(peeled)

            def mashed_potatoes(vegetable):
                prepared = prepare(vegetable)
                return mash(prepared)

            if __name__ == "__main__":
                potato = ' potato '
                print(mashed_potatoes(potato))
        """
        after = """
            import random

            def mashed_potatoes(vegetable):
                prepared = prepare(vegetable)
                return mash(prepared)

            def prepare(vegetable):
                peeled = peel(vegetable)
                return chop(peeled)

            def mash(veg_pieces):
                random.shuffle(veg_pieces)
                return ''.join(veg_pieces)

            def peel(vegetable):
                return vegetable[1:-1]

            def chop(vegetable):
                return list(vegetable)

            if __name__ == "__main__":
                potato = ' potato '
                print(mashed_potatoes(potato))
        """
        self.assertCodemod(before, after)
