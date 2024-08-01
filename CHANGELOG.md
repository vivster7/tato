# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
- Ignore usages of imports when topological sorting
- Allow multiple passes of codemod until stable.


## [0.0.5] - 2024-07-31

### Fixed
- Ignore self-edges; Fixes bug causing top-level nodes to disappear.
- Generically, fixes the bug where nodes were appearing out of order by hardening the concept of a Section.

## [0.0.4] - 2024-07-31

### Fixed
- Functions will correctly be sorted before classes is the function is used in the class scope.


## [0.0.3] - 2024-07-30

### Changed
- Order functions by leafs last.
- Secondarily order nodes by their first access.


## [0.0.2] - 2024-07-30

### Changed
- Robustly handle most top-level nodes in a module body.
- Order should be more deterministic
- Use libcst codemod interface instead of click


## [0.0.1] - 2024-07-29

### Added
- Initial release