class SearchError(Exception):
    """Base class for search errors."""

    category: str = "search_error"

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class ReactionError(Exception):
    """Base class for reaction errors."""

    category: str = "reaction_error"

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class InvalidMoleculeError(SearchError):
    """Raised when the molecule is invalid."""

    category: str = "invalid_molecule_error"


class InvalidInputError(SearchError):
    """Raised when the input is invalid."""

    category: str = "invalid_input_error"


class MoleculeNotFoundError(SearchError):
    """Raised when a molecule is not found."""

    category: str = "molecule_not_found_error"


class TemporaryPubChemError(SearchError):
    """Raised when PubChem is temporarily unavailable."""

    category: str = "temporary_pubchem_error"


class PubChemRateLimitError(SearchError):
    """Raised when PubChem rate limit is exceeded."""

    category: str = "pubchem_rate_limit_error"


class InvalidReactionRuleError(ReactionError):
    """Raised when a reaction rule is invalid."""

    category: str = "invalid_reaction_rule_error"


class InvalidReactionInputError(ReactionError):
    category: str = "invalid_reaction_input"


class PredictionUnavailableError(ReactionError):
    category: str = "prediction_unavailable"
