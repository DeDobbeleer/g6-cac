"""Modèles pour les Normalization Policies (parser/normaliser)."""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal


class ParserRule(BaseModel):
    """Règle de parsing pour extraire des champs.
    
    Supporte les formats communs : syslog, JSON, CSV, key-value, regex.
    """
    name: str
    pattern: str = Field(..., description="Pattern de parsing (regex, grok-like)")
    source_format: Literal["syslog", "json", "csv", "kv", "cef", "leef", "custom"] = "syslog"
    target_fields: Dict[str, str] = Field(
        default_factory=dict,
        description="Mapping champ_source -> champ_logpoint"
    )
    
    # Pour les formats structurés (JSON, CEF...)
    field_mapping: Optional[Dict[str, str]] = None


class NormalizationPolicy(BaseModel):
    """Politique de normalisation des logs.
    
    Transforme les logs bruts en format standard Logpoint.
    Peut référencer des packages externes (Windows, Linux, Firewall...).
    """
    name: str = Field(..., pattern=r"^[a-zA-Z0-9_-]+$")
    description: Optional[str] = None
    enabled: bool = True
    priority: int = Field(default=50, ge=1, le=100)
    
    # Matching - sur quels logs appliquer cette policy
    match_conditions: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Conditions pour matcher (device_type, log_source, etc.)"
    )
    
    # Règles de parsing
    parser_rules: List[ParserRule] = Field(default_factory=list)
    
    # Référence à un package externe (optionnel)
    package_ref: Optional[str] = Field(
        None,
        description="Référence à un package de normalisation externe"
    )
    
    # Champs normalisés à produire
    output_schema: List[str] = Field(
        default_factory=list,
        description="Champs attendus en sortie (device_type, src_ip, dst_ip, action...)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "windows-security",
                "match_conditions": [
                    {"log_source": "Microsoft-Windows-Security-Auditing"}
                ],
                "package_ref": "windows-security-package",
                "output_schema": ["event_id", "subject_user", "target_user", "logon_type"]
            }
        }
