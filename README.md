# tato

[![PyPI - Version](https://img.shields.io/pypi/v/tato.svg)](https://pypi.org/project/tato)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/tato.svg)](https://pypi.org/project/tato)

-----

Tato is an autoformatter for Python code. In contrast to other autoformatters,
tato formats the organization/layout of a file. It organizes the order of
functions/classes/symbols according to their dependency structure.

Here's a (contrived) example to illustrate the idea
```py
## Before running `tato`
def _stripped_str_to_int(s):
    return int(s.strip())

import random
def jumble(string):
    return random.choice(_stripped_str_to_int(string))

MAGIC_NUMBER = 42
class Vegetable:
    ...

class Potato(Vegetable):
    expiration_days = MAGIC_NUMER


## After running `tato`
import random

MAGIC_NUMBER = 42
class Vegetable:
    ...

class Potato(Vegetable):
    expiration_days = MAGIC_NUMBER

def _stripped_str_to_int(s):
    return int(s.strip())

def jumble(string):
    return random.choice(_stripped_str_to_int(string))
```

## Quick start

```console
pip install tato
tato <path_to_file>
```
- Tato should be used alongside other autoformatters like black or ruff.
- Tato is probably too disruptive to run on save.
- If the output from tato is confusing, consider splitting the file into smaller
chunks and running tato on each chunk.

## Motivation

In large, mature codebases, it's common to encounter files that lack a coherent structure. While the initial version of a file may have been crafted with care
and logical organization, the structure often erodes over time due to various
factors: Incremental bugfixes, partial refactorings, quick feature additions,
etc.

As the structure collapses, developers often resort to a "precision tactical
strike" approach when modifying these files, inserting new code wherever it
seems least disruptive rather than where it logically belongs.

Tato offers a reset button. It provides consistency by deterministically 
organizing the file. It's probably not the optimal layout, but the consistency
should reduce the cognitive load required to understand the code.


## Layout details

Tato organizes files into four main sections:

1. Imports
2. Constants
3. Classes
4. Functions

Imports: Tato preserves the original import order, deferring to specialized tools like isort or ruff for import sorting.

Constants: Moved to the top of the file, constants typically have brief definitions and serve as key control points for program behavior.

Classes: Arranged according to their inheritance hierarchy, with base classes appearing first.

Functions: Placed in the final section and sorted by call hierarchy. This structure puts the main function first, prioritizing the most crucial information. (Note: Classes aren't organized this way as their inheritance is evaluated at import time.)

### Handling Interdependencies:
In some cases, strict adherence to this four-section layout may not be possible due to interdependencies. For instance, a constant might rely on a class or function definition. In such situations, Tato will elevate the necessary definitions to maintain file validity. These elevated definitions form valid subsections of (constants, classes, functions), though most fields in these subsections are typically empty.
