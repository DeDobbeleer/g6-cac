"""Modèles pour les Processing Policies (pipeline complète)."""
from pydantic import BaseModel, Field
from typing import List, Optional, Literal


class PipelineStep(BaseModel):
    """Une étape du pipeline de traitement.
    
    Le pipeline définit l'ordre : routing -> normalization -> enrichment -> storage
    """
    step: Literal["routing", "normalization", "enrichment", "processing", "storage", "alerting"]
    policy_ref: Optional[str] = Field(None, description="Nom de la policy à appliquer")
    repo_ref: Optional[str] = Field(None, description="Pour step=storage, nom du repo")
    optional: bool = Field(default=False, description="Si True, l'étape peut échouer sans bloquer")
    condition: Optional[str] = Field(None, description="Condition d'exécution (expression simple)")


class ProcessingPolicy(BaseModel):
    """Politique de traitement complète (pipeline).
    
    Ordonne les étapes : où router, comment normaliser, quels enrichissements,
    et où stocker au final. C'est le "maître" du pipeline.
    """
    name: str = Field(..., pattern=r"^[a-zA-Z0-9_-]+$")
    description: Optional[str] = None
    enabled: bool = True
    
    # Le pipeline ordonné
    pipeline: List[PipelineStep] = Field(
        ...,
        min_length=1,
        description="Ordre des étapes de traitement"
    )
    
    # Mode de gestion des erreurs
    on_error: Literal["drop", "quarantine", "continue", "alert"] = "quarantine"
    
    # Quota/limite
    max_events_per_second: Optional[int] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "standard-processing",
                "pipeline": [
                    {"step": "routing", "policy_ref": "critical-logs-first"},
                    {"step": "normalization", "policy_ref": "auto-detect-format"},
                    {"step": "enrichment", "policy_ref": "geoip-lookup", "optional": True},
                    {"step": "storage", "repo_ref": "default"}
                ],
                "on_error": "quarantine"
            }
        }
