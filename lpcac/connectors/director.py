"""Connecteur pour l'API Director (mode MSSP)."""
import httpx
from typing import Optional, Dict, Any, List
from pydantic import BaseModel


class OperationResult(BaseModel):
    """Résultat d'une opération async."""
    request_id: str
    status: str  # queued, in_progress, completed, failed
    success: Optional[bool] = None
    message: Optional[str] = None
    resource_id: Optional[str] = None


class DirectorConnector:
    """Client pour l'API Director Logpoint.
    
    Base URL: https://{api-server}/configapi/{pool_uuid}/{logpoint_id}
    
    Notes:
    - Toutes les modifications sont async (nécessitent polling)
    - Pas de bulk operations (1 requête par ressource)
    - Rate limiting inconnu -> implementer backoff
    """
    
    def __init__(self, base_url: str, token: str, pool_uuid: str, timeout: int = 60):
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.pool_uuid = pool_uuid
        self.timeout = timeout
        self.client = httpx.Client(
            headers={"Authorization": f"Bearer {token}"},
            timeout=timeout
        )
    
    def _make_url(self, logpoint_id: str, endpoint: str) -> str:
        """Construit l'URL complète."""
        return f"{self.base_url}/configapi/{self.pool_uuid}/{logpoint_id}/{endpoint}"
    
    # ============================================================
    # REPOS
    # ============================================================
    
    def list_repos(self, logpoint_id: str) -> List[Dict[str, Any]]:
        """Liste tous les repos d'un logpoint."""
        url = self._make_url(logpoint_id, "Repos")
        response = self.client.get(url)
        response.raise_for_status()
        return response.json()
    
    def get_repo(self, logpoint_id: str, repo_id: str) -> Dict[str, Any]:
        """Récupère un repo par ID."""
        url = self._make_url(logpoint_id, f"Repos/{repo_id}")
        response = self.client.get(url)
        response.raise_for_status()
        return response.json()
    
    def create_repo(self, logpoint_id: str, repo_data: Dict[str, Any]) -> OperationResult:
        """Crée un nouveau repo (opération async)."""
        url = self._make_url(logpoint_id, "Repos")
        response = self.client.post(url, json=repo_data)
        response.raise_for_status()
        return self._parse_async_response(response.json())
    
    def update_repo(self, logpoint_id: str, repo_id: str, repo_data: Dict[str, Any]) -> OperationResult:
        """Modifie un repo existant (opération async)."""
        url = self._make_url(logpoint_id, f"Repos/{repo_id}")
        response = self.client.put(url, json=repo_data)
        response.raise_for_status()
        return self._parse_async_response(response.json())
    
    def delete_repo(self, logpoint_id: str, repo_id: str) -> OperationResult:
        """Supprime un repo (opération async)."""
        url = self._make_url(logpoint_id, f"Repos/{repo_id}")
        response = self.client.delete(url)
        response.raise_for_status()
        return self._parse_async_response(response.json())
    
    # ============================================================
    # ROUTING POLICIES
    # ============================================================
    
    def list_routing_policies(self, logpoint_id: str) -> List[Dict[str, Any]]:
        """Liste les routing policies."""
        url = self._make_url(logpoint_id, "Policies")
        response = self.client.get(url)
        response.raise_for_status()
        data = response.json()
        # Filtrer pour n'avoir que les routing
        return [p for p in data if p.get("type") == "routing"]
    
    # ============================================================
    # NORMALIZATION POLICIES
    # ============================================================
    
    def list_normalization_policies(self, logpoint_id: str) -> List[Dict[str, Any]]:
        """Liste les normalization policies."""
        url = self._make_url(logpoint_id, "NormalizationPolicies")
        response = self.client.get(url)
        response.raise_for_status()
        return response.json()
    
    # ============================================================
    # PROCESSING POLICIES
    # ============================================================
    
    def list_processing_policies(self, logpoint_id: str) -> List[Dict[str, Any]]:
        """Liste les processing policies."""
        url = self._make_url(logpoint_id, "ProcessPolicies")
        response = self.client.get(url)
        response.raise_for_status()
        return response.json()
    
    # ============================================================
    # UTILS
    # ============================================================
    
    def _parse_async_response(self, data: Dict[str, Any]) -> OperationResult:
        """Parse la réponse async Director."""
        # Format attendu: {"status": "Success", "message": "/monitorapi/.../request_id"}
        request_id = data.get("request_id") or data.get("message", "").split("/")[-1]
        return OperationResult(
            request_id=request_id,
            status="queued",
            message=data.get("message")
        )
    
    def check_operation_status(self, logpoint_id: str, request_id: str) -> OperationResult:
        """Vérifie le statut d'une opération async."""
        url = f"{self.base_url}/monitorapi/{self.pool_uuid}/{logpoint_id}/orders/{request_id}"
        response = self.client.get(url)
        response.raise_for_status()
        data = response.json()
        return OperationResult(
            request_id=request_id,
            status=data.get("status", "unknown"),
            success=data.get("success"),
            message=data.get("message")
        )
    
    def close(self):
        """Ferme le client HTTP."""
        self.client.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
