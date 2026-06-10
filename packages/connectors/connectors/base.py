from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime

from connectors.types import IntegrationType


@dataclass
class SyncResult:
    success: bool
    records_synced: int = 0
    message: str = ""
    synced_at: datetime = field(default_factory=datetime.utcnow)


class BaseConnector(ABC):
    """Contratto base per tutti i connettori di integrazione."""

    integration_type: IntegrationType

    @abstractmethod
    async def validate_credentials(self, credentials: dict) -> bool:
        """Verifica che le credenziali siano valide."""

    @abstractmethod
    async def sync(self, project_id: str) -> SyncResult:
        """Sincronizza i dati dell'integrazione per un progetto."""
