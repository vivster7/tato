from pathlib import Path

from libcst.codemod import CodemodTest
from tato.tato import ReorderFileCodemod


class TestAnimals(CodemodTest):
    TRANSFORM = ReorderFileCodemod

    def test_large_animal(self) -> None:
        self.maxDiff = None
        folder = Path(__file__).parent
        before = (folder / "before.py").read_text()
        after = (folder / "after.py").read_text()

        self.assertCodemod(before, after)
