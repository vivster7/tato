import xyz.abc  # noqa
from qwerty.abc import defg  # noqa

import test2
from test2.a import defg, B, D, a  # noqa


def fn():
    a()
    B().methods_are_ignored()
    E = test2.a.C + D
