from pydantic import BaseModel, Field, field_validator

from app.domain.search_input_type import SearchInputType


class MoleculeSearchRequest(BaseModel):
    """Molecule search request"""

    query: str = Field(..., min_length=1, max_length=100, description="Search query")
    input_type: SearchInputType = SearchInputType.AUTO

    @field_validator("query")
    @classmethod
    def validate_query(cls, value: str) -> str:
        """Validate query"""
        cleaned_value = value.strip()
        if not cleaned_value:
            raise ValueError("Query cannot be empty")
        return cleaned_value
