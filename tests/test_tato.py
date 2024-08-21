from tato.tato import ReorderFileCodemod

from testlib.codemod import TatoCodemodTest


class TestTato(TatoCodemodTest):
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
        self.assertCodemodWithCache(
            before,
            after,
        )

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
        self.assertCodemodWithCache(before, after)

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

        self.assertCodemodWithCache(before, after)

    def test_imports_index_are_ignored(self) -> None:
        before = """
            import abc
            def fn(): pass
            constant = abc.g() + fn()
        """
        after = """
            import abc
            def fn(): pass
            constant = abc.g() + fn()
        """
        self.assertCodemodWithCache(before, after)

    def test_imports_include_type_checking_blocks(self) -> None:
        before = """
            import logging
            
            if TYPE_CHECKING:
                from . import unit_of_work

            logger = logging.getLogger(__name__)
        """
        after = """
            import logging

            if TYPE_CHECKING:
                from . import unit_of_work

            logger = logging.getLogger(__name__)
        """
        self.assertCodemodWithCache(before, after)

    def test_module_docstring_appears_before_imports(self) -> None:
        before = """
            \"\"\"
            module docstring

            very long
            \"\"\"
            import logging
        """
        after = """
            \"\"\"
            module docstring

            very long
            \"\"\"
            import logging
        """
        self.assertCodemodWithCache(before, after)

    def test_constants_placed_after_all_used_definitions(self) -> None:
        before = """
            def fn1(): pass
            def fn2(): pass
            def fn3(): pass
            ABC = [fn1(), fn2()]
        """
        after = """
            def fn3(): pass
            def fn1(): pass
            def fn2(): pass
            ABC = [fn1(), fn2()]
            """
        self.assertCodemodWithCache(before, after)

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
        self.assertCodemodWithCache(before, after)

    def test_classes_with_cycle(self) -> None:
        before = """
            class A:
                def __init__(self):
                    self.b = B()
            class B:
                def __init__(self):
                    self.a = A()
        """
        after = """
            class A:
                def __init__(self):
                    self.b = B()
            class B:
                def __init__(self):
                    self.a = A()
        """
        self.assertCodemodWithCache(before, after)

    def test_sections_simple(self) -> None:
        before = """
            def eggs(): pass
            BACON = 1
            class Toats: pass
            import breakfast
        """
        after = """
            import breakfast
            BACON = 1
            class Toats: pass
            def eggs(): pass
            """
        self.assertCodemodWithCache(before, after)

    def test_function_order_by_deps_last(self) -> None:
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
        self.assertCodemodWithCache(before, after)
    
    def test_function_order_by_deps_last2(self) -> None:
        before = """
            def main():
                first()
                second()

            def second():
                pass
                
            def first():
                pass
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
        self.assertCodemodWithCache(before, after)

    def test_subsections_1(self) -> None:
        before = """
            class Batter: pass
            def water(b: Batter): pass
            WATER = water()
            class Cookie: pass
            def milk(c: Cookie): water(c)
        """
        after = """
            class Batter: pass
            class Cookie: pass
            def water(b: Batter): pass
            WATER = water()
            def milk(c: Cookie): water(c)
        """
        self.assertCodemodWithCache(before, after)

    def test_functions_decorator_sorts_first(self) -> None:
        before = """
            def decorator(func):
                def wrapper(*args, **kwargs):
                    return func(*args, **kwargs)
                return wrapper

            @decorator
            def fn():
                pass
        """
        after = """
            def decorator(func):
                def wrapper(*args, **kwargs):
                    return func(*args, **kwargs)
                return wrapper

            @decorator
            def fn():
                pass
        """
        self.assertCodemodWithCache(before, after)

    def test_functions_as_default_args_in_globalscope(self) -> None:
        before = """
            def fn(): pass
            def fn2(f = fn): pass
        """
        after = """
            def fn(): pass
            def fn2(f = fn): pass
        """
        self.assertCodemodWithCache(before, after)

    def test_classes_decorated(self) -> None:
        before = """
            def decorator(): pass
            @decorator
            class A: pass
        """
        after = """
            def decorator(): pass
            @decorator
            class A: pass
        """
        self.assertCodemodWithCache(before, after)

    def test_playground(self) -> None:
        before = """
            def decorator(): pass
            @decorator
            class A: pass
        """
        after = """
            def decorator(): pass
            @decorator
            class A: pass
        """
        self.assertCodemodWithCache(before, after)
