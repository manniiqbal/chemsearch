from enum import StrEnum


class SearchInputType(StrEnum):
    """Search input type"""

    AUTO = "auto"
    NAME = "name"
    CID = "cid"
    SMILES = "smiles"
