from pydantic import BaseModel, Field


class PubChemPropertyRecord(BaseModel):
    cid: int = Field(..., alias="CID", description="PubChem Compound ID")
    smiles: str = Field(..., alias="SMILES", description="SMILES representation of the compound")
    title: str | None = Field(default=None, alias="Title", description="Title of the compound")
    molecular_formula: str | None = Field(
        default=None, alias="MolecularFormula", description="Molecular formula of the compound"
    )
    molecular_weight: float | None = Field(
        default=None, alias="MolecularWeight", description="Molecular weight of the compound"
    )


class PropertyTable(BaseModel):
    properties: list[PubChemPropertyRecord] = Field(..., alias="Properties")


class PubChemResponse(BaseModel):
    property_table: PropertyTable = Field(..., alias="PropertyTable")
