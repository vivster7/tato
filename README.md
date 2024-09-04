# tato

[![PyPI - Version](https://img.shields.io/pypi/v/tato.svg)](https://pypi.org/project/tato)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/tato.svg)](https://pypi.org/project/tato)

-----

Tato is Python file layout formatter. In contrast to other autoformatters,
tato only formats the organization/layout of a file. It tries to organize files
into four sections: imports, constants, classes, and functions.

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

In large, mature codebases, it’s common to encounter files that lack a coherent
structure. While the initial version of a file may have been thoughtfully 
crafted with a logical organization, this structure often erodes over time. 
(There are many reasons for this erosion, but that’s a topic for another time.)

Tato offers a reset button, providing consistency by deterministically 
organizing the file. While it may not be the optimal layout, this consistency
should reduce the cognitive load required to understand the code.

## Layout details

Tato organizes files into four main sections:

1.	Imports
2.	Constants
3.	Classes
4.	Functions

**Imports:** Tato preserves the original import order, leaving the task of 
sorting to tools like isort or ruff.

**Constants:** Constants are moved to the top of the file. Typically, these have
brief definitions and act as key control points for program behavior.

**Classes:** Classes are arranged according to their inheritance hierarchy, with
base classes appearing first.

**Functions:** Functions are placed in the final section and sorted by call 
hierarchy. This order places the `main()` function first, ensuring that the most 
important functions appear at the top.

### Handling Interdependencies
Strict adherence to this four-section layout may not always be possible due to 
interdependencies. For example, a constant might depend on a class or function 
definition. In such cases, Tato will elevate the necessary definitions to 
maintain file validity. These elevated definitions form valid subsections 
(constants, classes, functions), although most fields in these subsections are
typically empty.

If a file has too many subsections, it’s likely a sign that it should be broken
 up.