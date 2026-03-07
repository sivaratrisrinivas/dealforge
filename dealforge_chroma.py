"""Dealforge-specific Chroma integrations."""

from chromadb.config import System
from chromadb.telemetry.product import ProductTelemetryClient, ProductTelemetryEvent


class NoOpProductTelemetry(ProductTelemetryClient):
    """Disable Chroma product telemetry completely."""

    def __init__(self, system: System):
        super().__init__(system)

    def capture(self, event: ProductTelemetryEvent) -> None:
        return None
