# Imports are not definitions
import xyz.abc  # noqa
from qwerty.abc import defg  # noqa


def a():
    pass


class B:
    def methods_are_ignored(self):
        pass


C = 123


if True:
    D = None
else:
    D = 234
