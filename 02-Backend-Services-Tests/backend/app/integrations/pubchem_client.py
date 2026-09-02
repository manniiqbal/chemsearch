import asyncio

import httpx

from app.core.config import settings
from app.integrations.pubchem_errors import (
    PubChemMalformedResponseError,
    PubChemNotFoundError,
    PubChemRateLimitError,
    PubChemTemporaryError,
)
from app.integrations.pubchem_models import PubChemPropertyRecord, PubChemResponse


class PubChemClient:
    def __init__(self) -> None:
        self.base_url = settings.pubchem_base_url
        self.timeout = httpx.Timeout(
            settings.read_timeout_seconds,
            connect=settings.connect_timeout_seconds,
        )
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout,
        )

    async def _get(
        self,
        endpoint: str,
        params: dict | None = None,
    ) -> httpx.Response:
        for attempt in range(settings.max_retries + 1):
            try:
                response = await self.client.get(endpoint, params=params)

                if response.status_code == 429:
                    if attempt == settings.max_retries:
                        raise PubChemRateLimitError("PubChem rate limit exceeded after retries")

                    retry_after = response.headers.get("Retry-After")
                    if retry_after is not None:
                        delay = float(retry_after)
                    else:
                        delay = 2**attempt

                    await asyncio.sleep(delay)
                    continue

                elif response.status_code in range(500, 600):
                    if attempt == settings.max_retries:
                        raise PubChemTemporaryError(
                            f"PubChem returned status {response.status_code} after retries"
                        )

                    retry_after = response.headers.get("Retry-After")
                    if retry_after is not None:
                        delay = float(retry_after)
                    else:
                        delay = 2**attempt

                    await asyncio.sleep(delay)
                    continue

                else:
                    return response

            except httpx.RequestError as e:
                if attempt == settings.max_retries:
                    raise PubChemTemporaryError(f"Network error contacting PubChem: {e}") from e

                delay = 2**attempt
                await asyncio.sleep(delay)

    def _parse_property_response(
        self,
        response: httpx.Response,
        description: str,
    ) -> PubChemPropertyRecord:
        if response.status_code == 404:
            raise PubChemNotFoundError(f"No compound found for {description}")

        if response.status_code != 200:
            raise PubChemTemporaryError(
                f"PubChem returned unexpected status {response.status_code}"
            )

        try:
            data = response.json()
            parsed = PubChemResponse.model_validate(data)

        except (ValueError, TypeError) as e:
            raise PubChemMalformedResponseError(f"Could not parse PubChem response: {e}") from e

        if not parsed.property_table.properties:
            raise PubChemMalformedResponseError(
                f"PubChem response for {description} contained no properties"
            )

        return parsed.property_table.properties[0]

    async def lookup_by_name(
        self,
        name: str,
    ) -> PubChemPropertyRecord:
        properties = "SMILES,Title,MolecularFormula,MolecularWeight"

        endpoint = f"/compound/name/{name}/property/{properties}/JSON"

        response = await self._get(endpoint)

        return self._parse_property_response(
            response,
            f"name '{name}'",
        )

    async def lookup_by_cid(
        self,
        cid: int,
    ) -> PubChemPropertyRecord:
        properties = "SMILES,Title,MolecularFormula,MolecularWeight"

        endpoint = f"/compound/cid/{cid}/property/{properties}/JSON"

        response = await self._get(endpoint)

        return self._parse_property_response(
            response,
            f"CID '{cid}'",
        )

    async def close(self) -> None:
        await self.client.aclose()
