import dataclasses


@dataclasses.dataclass(frozen=True)
class Definition:
    id: str
    file_id: str
    fully_qualified_name: str
    start_line: int
    start_col: int


@dataclasses.dataclass(frozen=True)
class Reference:
    id: str
    file_id: str
    fully_qualified_name: str
    start_line: int
    start_col: int


@dataclasses.dataclass(frozen=True)
class DefRef:
    id: str
    definition_id: str
    reference_id: str


@dataclasses.dataclass(frozen=True)
class File:
    id: str
    path: str
    module: str
    package: str

    # Prefer using filecache to create this object.


@dataclasses.dataclass(frozen=True)
class DefDef:
    id: str
    from_definition_id: str
    to_definition_id: str
