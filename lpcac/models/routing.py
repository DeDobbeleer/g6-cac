"""Modèles pour les Routing Policies (où router les logs)."""
from pydantic import BaseModel, Field
from typing import List, Optional, Literal


class RoutingCondition(BaseModel):
    """Condition pour matcher des logs.
    
    Exemples:
    - device_type=firewall AND severity=high
    - msg contains "authentication failure"
    - source_ip in [10.0.0.0/8]
    """
    field: str = Field(..., description="Champ à matcher (device_type, msg, source_ip...)")
    operator: Literal["equals", "contains", "in", "regex", "greaterthan", "exists"] = "equals"
    values: Optional[List[str]] = None
    value: Optional[str] = None
    
    def __str__(self) -> str:
        if self.values:
            return f"{self.field} {self.operator} {self.values}"
        return f"{self.field} {self.operator} {self.value}"


class RoutingAction(BaseModel):
    """Action à effectuer quand la condition match."""
    target_repo: str = Field(..., description="Nom du repo cible")
    priority: int = Field(default=50, ge=1, le=100, description="Priorité (1=haute, 100=basse)")
    stop_processing: bool = Field(default=False, description="Arrêter le routing si match")


class RoutingPolicy(BaseModel):
    """Politique de routage des logs vers les repos.
    
    Définit : "Si les logs matchent ces conditions, les envoyer vers ce repo".
    Ordre d'évaluation : par priorité (1 en premier).
    """
    name: str = Field(..., pattern=r"^[a-zA-Z0-9_-]+$")
    description: Optional[str] = None
    enabled: bool = True
    priority: int = Field(default=50, ge=1, le=100)
    conditions: List[RoutingCondition] = Field(..., min_length=1)
    actions: RoutingAction
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "critical-logs",
                "priority": 10,
                "conditions": [
                    {"field": "severity", "operator": "in", "values": ["high", "critical"]}
                ],
                "actions": {
                    "target_repo": "alerts",
                    "stop_processing": False
                }
            }
        }
