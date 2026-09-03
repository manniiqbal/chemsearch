from rdkit import Chem
from rdkit.Chem import rdDepictor, rdMolDescriptors

from app.domain.errors import InvalidMoleculeError


class RDKitService:
    """
    Service for handling RDKit molecule operations (SMILES and InChI).
    """

    def __init__(self) -> None:
        self._svg_cache: dict[tuple[str, tuple[int, int]], str] = {}

    def validate_molecule(self, molecule: str) -> Chem.Mol:
        """
        Validate and parse a SMILES string.

        Args:
            molecule (str): SMILES representation.

        Returns:
            Chem.Mol: RDKit molecule object.

        Raises:
            InvalidMoleculeError: If input is invalid or parsing fails.
        """
        if not molecule or not isinstance(molecule, str):
            raise InvalidMoleculeError("Molecule must be a non-empty string.")

        mol = Chem.MolFromSmiles(molecule)
        if mol is None:
            raise InvalidMoleculeError("Invalid molecule format.")

        return mol

    def canonicalise_molecule(self, smiles: str) -> str:
        """
        Return the canonical SMILES for a given SMILES string.

        Args:
            smiles (str): SMILES to canonicalise.

        Returns:
            str: Canonical SMILES.

        Raises:
            InvalidMoleculeError: If the input is invalid.
        """
        mol = self.validate_molecule(smiles)
        return Chem.MolToSmiles(mol, canonical=True)

    def mol_to_canonical_smiles(self, mol: Chem.Mol) -> str:
        """
        Convert an RDKit molecule to its canonical SMILES representation.

        Args:
            mol (Chem.Mol): RDKit molecule object.

        Returns:
            str: Canonical SMILES representation.
        """
        return Chem.MolToSmiles(mol, canonical=True)

    def molecular_formula(self, smiles: str) -> str:
        """Return a molecular formula for reagent identity checks."""
        return rdMolDescriptors.CalcMolFormula(self.validate_molecule(smiles))

    def render_molecule_svg(
        self,
        smiles: str,
        size: tuple[int, int] = (300, 300),
    ) -> str:
        """
        Render a molecule as a 2D SVG depiction.

        Args:
            smiles (str): SMILES representation.
            size (tuple[int, int]): Canvas size in pixels as (width, height).

        Returns:
            str: SVG markup for the molecular diagram.

        Raises:
            InvalidMoleculeError: If the SMILES string is invalid or cannot be
                parsed.
        """
        cache_key = (smiles, size)
        cached = self._svg_cache.get(cache_key)
        if cached is not None:
            return cached

        from rdkit.Chem.Draw import rdMolDraw2D

        mol = self.validate_molecule(smiles)
        rdDepictor.Compute2DCoords(mol)

        drawer = rdMolDraw2D.MolDraw2DSVG(size[0], size[1])
        options = drawer.drawOptions()
        options.clearBackground = False
        options.setAtomPalette(
            {
                6: (0.78, 0.86, 0.88),
                7: (0.20, 0.76, 0.84),
                8: (0.98, 0.45, 0.45),
                9: (0.35, 0.85, 0.68),
                15: (0.98, 0.70, 0.30),
                16: (0.95, 0.82, 0.28),
                17: (0.35, 0.85, 0.68),
                35: (0.76, 0.48, 0.92),
                53: (0.62, 0.48, 0.88),
            }
        )
        drawer.DrawMolecule(mol)
        drawer.FinishDrawing()

        svg = drawer.GetDrawingText()
        if len(self._svg_cache) >= 512:
            self._svg_cache.pop(next(iter(self._svg_cache)))
        self._svg_cache[cache_key] = svg
        return svg
