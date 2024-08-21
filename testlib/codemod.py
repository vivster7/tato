from pathlib import Path
from tempfile import NamedTemporaryFile

from libcst.codemod import CodemodContext, CodemodTest
from libcst.metadata import FullRepoManager


class TatoCodemodTest(CodemodTest):
    def assertCodemodWithCache(self, before: str, after: str):
        with NamedTemporaryFile() as f:
            p = Path(f.name)
            manager = FullRepoManager(
                p.parent, [(str(p))], self.TRANSFORM.get_inherited_dependencies()
            )
            self.assertCodemod(
                before,
                after,
                context_override=CodemodContext(
                    filename=f.name,
                    metadata_manager=manager,
                ),
            )
