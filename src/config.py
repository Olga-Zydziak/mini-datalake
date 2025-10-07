"""Application configuration using pydantic settings."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables."""

    dest_bucket: str = Field(..., alias="DEST_BUCKET")
    project_id: str = Field(..., alias="PROJECT_ID")
    metadata_prefix: str = Field("metadata/", alias="METADATA_PREFIX")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="",
        case_sensitive=False,
        validate_default=True,
        protected_namespaces=("settings_",),
    )

    def normalized_prefix(self) -> str:
        """Ensure the metadata prefix always ends with a slash."""

        prefix = self.metadata_prefix.strip()
        if prefix and not prefix.endswith("/"):
            prefix = f"{prefix}/"
        return prefix


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached settings instance."""

    return Settings()  # type: ignore[call-arg]


__all__ = ["Settings", "get_settings"]
