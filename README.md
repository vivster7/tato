# tato

[![PyPI - Version](https://img.shields.io/pypi/v/tato.svg)](https://pypi.org/project/tato)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/tato.svg)](https://pypi.org/project/tato)

-----

Tato is an autoformatter for Python files. In contrast to other autoformatters,
tato formats the organization/layout of a file. It tries to organize files into
four sections: imports, constants, classes, and functions.

Here's a (contrived) example to illustrate the idea
<img width="971" 
     alt="Image showing source code before and after running tato." 
     src="https://github.com/user-attachments/assets/f3d41f13-af5b-483d-a848-8475d0c63fe5">


## Quick start

```console
pip install tato
tato format <path_to_file>
```
- Tato should be used alongside other autoformatters like black or ruff.
- Tato is probably too disruptive to run on save.
- If the output from tato is confusing, consider splitting the file into smaller
chunks and running tato on each chunk.
- It's fine (even encouraged) to use tato to "reset" a file, but then apply the
finishing touches manually. It'll never be better than a thoughtful layout, but
it's often much better than random layouts.

## Motivation

In large, mature codebases, it's common to encounter files that lack a coherent
structure. While the initial version of a file may have been crafted with care
and logical organization, the structure often erodes over time.

Tato offers a reset button. It provides consistency by deterministically 
organizing the file. It's probably not the optimal layout, but the consistency
should reduce the cognitive load required to understand the code.


## Layout details

Tato organizes files into four main sections:

1. Imports
2. Constants
3. Classes
4. Functions

**Imports:** Tato preserves the original import order, deferring to specialized tools like isort or ruff for import sorting.

**Constants:** Moved to the top of the file, constants typically have brief definitions and serve as key control points for program behavior.

**Classes:** Arranged according to their inheritance hierarchy, with base classes appearing first.

**Functions:** Placed in the final section and sorted by call hierarchy. This ordering puts the `main()` function first, so the most important functions are at the top.

### Handling Interdependencies:
In many cases, strict adherence to this four-section layout may not be possible due to interdependencies. For instance, a constant might rely on a class or function definition. In such situations, Tato will elevate the necessary definitions to maintain file validity. These elevated definitions form valid subsections of (constants, classes, functions), though most fields in these subsections are typically empty.

It's probably a good sign to break up a file if it has too many subsections.
