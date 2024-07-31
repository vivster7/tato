from pathlib import Path

from libcst.codemod import CodemodTest
from tato.tato import ReorderFileCodemod


class TestFilesystem(CodemodTest):
    TRANSFORM = ReorderFileCodemod

    def test_large_filesystem(self) -> None:
        self.maxDiff = None
        folder = Path(__file__).parent
        before = (folder / "before.py").read_text()
        after = (folder / "after.py").read_text()

        self.assertCodemod(before, after)
