"""Modèles pour les Repos (stockage des logs)."""
from pydantic import BaseModel, Field
from typing import List, Optional


class RepoPath(BaseModel):
    """Chemin de stockage dans un repo."""
    path: str = Field(..., description="Chemin absolu sur le filesystem")
    retention_days: int = Field(default=365, ge=1)
    compression: bool = True
    high_availability: Optional[bool] = False


class Repo(BaseModel):
    """Référentiel de stockage Logpoint.
    
    Un repo définit où et combien de temps les logs sont stockés.
    C'est la ressource fondamentale - tout le reste dépend des repos.
    """
    name: str = Field(..., pattern=r"^[a-zA-Z0-9_-]+$")
    paths: List[RepoPath] = Field(..., min_length=1)
    description: Optional[str] = None
    enabled: bool = True
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "default",
                "paths": [
                    {
                        "path": "/opt/immune/storage/default",
                        "retention_days": 365,
                        "compression": True
                    }
                ],
                "enabled": True
            }
        }
