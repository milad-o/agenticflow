"""Resource registry for AgenticFlow."""

from typing import Any, Dict, Optional, Callable
from langchain_core.retrievers import BaseRetriever
from langchain_core.vectorstores import VectorStore
from pydantic import BaseModel


class ResourceMetadata(BaseModel):
    """Metadata for registered resources."""
    name: str
    resource_type: str  # "retriever", "vectorstore", "database", etc.
    description: str = ""
    factory: Optional[Callable[..., Any]] = None
    config: Dict[str, Any] = {}


class ResourceRegistry:
    """Registry for managing data connectors and resources."""
    
    def __init__(self) -> None:
        self._resources: Dict[str, ResourceMetadata] = {}
        self._instances: Dict[str, Any] = {}
        self._listeners: Dict[str, Callable[[str, ResourceMetadata], None]] = {}
    
    def register_resource(
        self,
        name: str,
        resource_type: str,
        factory: Callable[..., Any],
        description: str = "",
        config: Optional[Dict[str, Any]] = None
    ) -> None:
        """Register a resource factory."""
        meta = ResourceMetadata(
            name=name,
            resource_type=resource_type,
            description=description,
            factory=factory,
            config=config or {}
        )
        self._resources[name] = meta
        # notify listeners
        for cb in list(self._listeners.values()):
            try:
                cb("register_resource", meta)
            except Exception:
                pass
    
    def get_resource(self, name: str) -> Any:
        """Get a resource instance by name."""
        if name in self._instances:
            return self._instances[name]
            
        if name not in self._resources:
            raise ValueError(f"Resource '{name}' not registered")
            
        metadata = self._resources[name]
        if not metadata.factory:
            raise ValueError(f"Resource '{name}' has no factory function")
            
        resource = metadata.factory(**metadata.config)
        self._instances[name] = resource
        return resource
    
    def list_resources(self) -> Dict[str, ResourceMetadata]:
        """List all registered resources."""
        return self._resources.copy()

    def add_listener(self, callback: Callable[[str, ResourceMetadata], None]) -> str:
        import uuid as _uuid
        lid = str(_uuid.uuid4())
        self._listeners[lid] = callback
        return lid

    def remove_listener(self, listener_id: str) -> None:
        self._listeners.pop(listener_id, None)
    
    def get_resources_by_type(self, resource_type: str) -> Dict[str, Any]:
        """Get all resources of a specific type."""
        resources = {}
        for name, metadata in self._resources.items():
            if metadata.resource_type == resource_type:
                resources[name] = self.get_resource(name)
        return resources