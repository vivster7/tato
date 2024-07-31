from libcst.codemod import CodemodTest
from tato.tato import ReorderFileCodemod


class TestMultipass(CodemodTest):
    TRANSFORM = ReorderFileCodemod

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
                
            def c():
                pass
                
            def b():
                c()

            def a():
                b()
        """

        self.assertCodemod(before, after)
