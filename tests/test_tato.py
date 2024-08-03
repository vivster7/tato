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

    def test_readme_example(self) -> None:
        before = """
            def _stripped_str_to_int(s):
                return int(s.strip())

            import random
            def jumble(string):
                return random.choice(_stripped_str_to_int(string))

            MAGIC_NUMBER = 42
            class Vegetable:
                ...

            class Potato(Vegetable):
                expiration_days = MAGIC_NUMBER
        """
        after = """
            import random

            MAGIC_NUMBER = 42
            class Vegetable:
                ...

            class Potato(Vegetable):
                expiration_days = MAGIC_NUMBER
            def jumble(string):
                return random.choice(_stripped_str_to_int(string))
            def _stripped_str_to_int(s):
                return int(s.strip())
        """
        self.assertCodemod(before, after)

    def test_playground(self) -> None:
        before = """
            def a(): b()
            def b(): pass

            ABC = a()
        """
        after = """
            def a(): b()
            def b(): pass

            ABC = a()
            """
        self.assertCodemod(before, after)
