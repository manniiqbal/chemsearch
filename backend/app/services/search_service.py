from app.domain.errors import (
    InvalidInputError,
    InvalidMoleculeError,
    MoleculeNotFoundError,
    PubChemRateLimitError,
    TemporaryPubChemError,
)
from app.domain.search_input_type import SearchInputType
from app.domain.search_result import SearchOutcome, SearchResult
from app.integrations.pubchem_client import PubChemClient
from app.integrations.pubchem_errors import (
    PubChemMalformedResponseError,
    PubChemNotFoundError,
    PubChemTemporaryError,
)
from app.integrations.pubchem_errors import (
    PubChemRateLimitError as PubChemRateLimitClientError,
)
from app.services.rdkit_service import RDKitService


class SearchService:
    def __init__(
        self,
        pubchem_client: PubChemClient,
        rdkit_service: RDKitService,
    ):
        self.pubchem_client = pubchem_client
        self.rdkit_service = rdkit_service

    def _resolve_input_type(
        self,
        requested_input_type: SearchInputType,
        query: str,
    ) -> SearchInputType:
        if requested_input_type == SearchInputType.AUTO:
            if query.isdigit():
                return SearchInputType.CID

            return SearchInputType.NAME

        return requested_input_type

    async def search(
        self,
        query: str,
        requested_input_type: SearchInputType,
    ) -> SearchOutcome:
        resolved_input_type = self._resolve_input_type(
            requested_input_type,
            query,
        )

        try:
            if resolved_input_type == SearchInputType.NAME:
                pubchem_record = await self.pubchem_client.lookup_by_name(query)

                canonical_smiles = self.rdkit_service.canonicalise_molecule(pubchem_record.smiles)

                molecule = SearchResult(
                    canonical_smiles=canonical_smiles,
                    cid=pubchem_record.cid,
                    name=pubchem_record.title,
                    molecular_formula=pubchem_record.molecular_formula,
                    molecular_weight=pubchem_record.molecular_weight,
                    structure_svg=self.rdkit_service.render_molecule_svg(canonical_smiles),
                )

            elif resolved_input_type == SearchInputType.CID:
                try:
                    cid = int(query)
                except ValueError:
                    raise InvalidInputError("CID must be a whole number") from None

                if cid <= 0:
                    raise InvalidInputError("CID must be positive")

                pubchem_record = await self.pubchem_client.lookup_by_cid(cid)

                canonical_smiles = self.rdkit_service.canonicalise_molecule(pubchem_record.smiles)

                molecule = SearchResult(
                    canonical_smiles=canonical_smiles,
                    cid=pubchem_record.cid,
                    name=pubchem_record.title,
                    molecular_formula=pubchem_record.molecular_formula,
                    molecular_weight=pubchem_record.molecular_weight,
                    structure_svg=self.rdkit_service.render_molecule_svg(canonical_smiles),
                )

            elif resolved_input_type == SearchInputType.SMILES:
                canonical_smiles = self.rdkit_service.canonicalise_molecule(query)

                structure_svg = self.rdkit_service.render_molecule_svg(canonical_smiles)

                molecule = SearchResult(
                    canonical_smiles=canonical_smiles,
                    cid=None,
                    name=None,
                    molecular_formula=None,
                    molecular_weight=None,
                    structure_svg=structure_svg,
                )

            else:
                raise InvalidInputError("Requested search type is not supported")

        except PubChemNotFoundError as e:
            raise MoleculeNotFoundError(str(e)) from e

        except (
            PubChemTemporaryError,
            PubChemMalformedResponseError,
        ) as e:
            raise TemporaryPubChemError(str(e)) from e

        except PubChemRateLimitClientError as e:
            raise PubChemRateLimitError(str(e)) from e

        except InvalidMoleculeError as e:
            raise InvalidInputError(str(e)) from e

        return SearchOutcome(
            query=query,
            requested_input_type=requested_input_type,
            resolved_input_type=resolved_input_type,
            molecule=molecule,
            warnings=[],
        )
