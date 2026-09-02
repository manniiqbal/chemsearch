from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    pubchem_base_url: str = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"
    connect_timeout_seconds: float = 6.0
    read_timeout_seconds: float = 12.0
    max_retries: int = 3
    frontend_origin: str = "http://localhost:3000"
    frontend_origin_regex: str = r"https://.*\.vercel\.app"


settings = Settings()
