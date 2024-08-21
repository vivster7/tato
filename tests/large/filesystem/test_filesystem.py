from pathlib import Path

from tato.tato import ReorderFileCodemod

from testlib.codemod import TatoCodemodTest


class TestFilesystem(TatoCodemodTest):
    TRANSFORM = ReorderFileCodemod

    def test_large_filesystem(self) -> None:
        self.maxDiff = None
        folder = Path(__file__).parent
        before = (folder / "before.py").read_text()
        after = (folder / "after.py").read_text()

        self.assertCodemodWithCache(before, after)
