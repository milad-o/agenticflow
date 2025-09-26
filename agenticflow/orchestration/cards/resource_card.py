"""
Resource Card

Enhanced metadata layer for system and environment resources.
Provides information about paths, configurations, credentials, and other external resources.
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Any, Set, Optional, Union
from datetime import datetime

from .base_card import BaseCard, CardType, CardMetadata, MatchingCriteria
from ...core.resource_manager import ResourceType


class ResourceCard(BaseCard):
    """
    Enhanced metadata card for resources.
    
    Represents system resources like file paths, directories, configurations,
    credentials, and other environmental assets that agents need to work with.
    """
    
    def __init__(
        self,
        resource_name: str,
        description: str,
        resource_type: ResourceType,
        resource_path: Optional[str] = None,
        resource_data: Optional[Dict[str, Any]] = None,
        access_patterns: List[str] = None,
        format_info: Dict[str, Any] = None,
        constraints: Dict[str, Any] = None,
        access_level: str = "read",
        dependencies: List[str] = None,
        metadata: CardMetadata = None
    ):
        # Generate card_id from resource name and type
        card_id = f"resource:{resource_type.value}:{resource_name}"
        
        super().__init__(
            card_id=card_id,
            name=resource_name,
            description=description,
            card_type=CardType.RESOURCE,
            metadata=metadata
        )
        
        self.resource_type = resource_type
        self.resource_path = resource_path
        self.resource_data = resource_data or {}
        self.access_patterns = access_patterns or []
        self.format_info = format_info or {}
        self.constraints = constraints or {}
        self.access_level = access_level  # read, write, admin
        self.dependencies = dependencies or []
        
        # Auto-extract capabilities based on resource properties
        self.capabilities = self._extract_capabilities()
        
        # Cache resource status
        self._cached_status = None
        self._status_timestamp = None
    
    def _extract_capabilities(self) -> List[str]:
        """Extract capabilities from resource properties."""
        capabilities = []
        
        # Base capability from resource type
        capabilities.append(f"resource_type:{self.resource_type.value}")
        
        # Access level capabilities
        capabilities.append(f"access:{self.access_level}")
        
        if self.access_level in ["write", "admin"]:
            capabilities.append("mutable")
        else:
            capabilities.append("read_only")
        
        # Path-based capabilities
        if self.resource_path:
            path = Path(self.resource_path)
            
            if path.is_file():
                capabilities.append("file_resource")
                # File type capabilities
                suffix = path.suffix.lower()
                if suffix:
                    capabilities.append(f"format:{suffix[1:]}")  # Remove dot
            elif path.is_dir():
                capabilities.append("directory_resource")
            
            # Path pattern capabilities
            if any(pattern in str(path) for pattern in ["config", "settings"]):
                capabilities.append("configuration")
            if any(pattern in str(path) for pattern in ["data", "input", "output"]):
                capabilities.append("data_source")
            if any(pattern in str(path) for pattern in ["temp", "cache"]):
                capabilities.append("temporary")
        
        # Format-based capabilities
        for format_type in self.format_info.keys():
            capabilities.append(f"format:{format_type}")
        
        # Access pattern capabilities
        for pattern in self.access_patterns:
            capabilities.append(f"pattern:{pattern}")
        
        return capabilities
    
    def calculate_match_score(self, criteria: MatchingCriteria) -> float:
        """Calculate match score based on criteria."""
        score = 0.0
        
        # Required capabilities - must have all
        resource_capabilities = set(self.get_capabilities())
        required = criteria.required_capabilities
        
        if required and not required.issubset(resource_capabilities):
            return 0.0  # Missing required capabilities
        
        if required:
            score += 0.5  # Higher base score for resources
        
        # Preferred capabilities - bonus points
        preferred = criteria.preferred_capabilities
        if preferred:
            overlap = len(preferred.intersection(resource_capabilities))
            score += 0.3 * (overlap / len(preferred))
        
        # Excluded capabilities - penalty
        excluded = criteria.excluded_capabilities
        if excluded:
            excluded_present = len(excluded.intersection(resource_capabilities))
            score -= 0.3 * (excluded_present / len(excluded))
        
        # Resource type matching
        if hasattr(criteria, 'resource_type'):
            if criteria.resource_type == self.resource_type.value:
                score += 0.2
        
        # Access level matching
        if hasattr(criteria, 'access_level'):
            if self._access_level_compatible(criteria.access_level):
                score += 0.1
        
        return max(0.0, min(1.0, score))
    
    def _access_level_compatible(self, required_level: str) -> bool:
        """Check if resource access level is compatible with requirement."""
        level_hierarchy = {"read": 0, "write": 1, "admin": 2}
        
        required_rank = level_hierarchy.get(required_level, 0)
        our_rank = level_hierarchy.get(self.access_level, 0)
        
        return our_rank >= required_rank
    
    def get_capabilities(self) -> Set[str]:
        """Get all capabilities provided by this resource."""
        return set(self.capabilities)
    
    def get_dependencies(self) -> List[str]:
        """Get dependencies required by this resource."""
        return self.dependencies.copy()
    
    def is_available(self) -> bool:
        """Check if resource is currently available."""
        # Use cached status if recent
        now = datetime.utcnow()
        if (self._cached_status is not None and 
            self._status_timestamp and 
            (now - self._status_timestamp).seconds < 60):
            return self._cached_status
        
        available = self._check_availability()
        self._cached_status = available
        self._status_timestamp = now
        
        return available
    
    def _check_availability(self) -> bool:
        """Actually check resource availability."""
        if self.resource_type == ResourceType.FILE_SYSTEM:
            if self.resource_path:
                return Path(self.resource_path).exists()
            return True
        
        elif self.resource_type == ResourceType.CONFIGURATION:
            # Check if configuration is valid/accessible
            if self.resource_path:
                try:
                    path = Path(self.resource_path)
                    if path.exists():
                        with open(path) as f:
                            json.load(f)  # Basic validation for JSON configs
                        return True
                except (json.JSONDecodeError, PermissionError):
                    return False
            elif self.resource_data:
                return True  # In-memory config is available
            return False
        
        elif self.resource_type == ResourceType.NETWORK:
            # For network resources, assume available unless proven otherwise
            return True
        
        elif self.resource_type == ResourceType.DATABASE:
            # Would need connection testing - assume available for now
            return True
        
        return True
    
    def get_size(self) -> Optional[int]:
        """Get resource size if applicable."""
        if self.resource_type == ResourceType.FILE_SYSTEM and self.resource_path:
            try:
                path = Path(self.resource_path)
                if path.is_file():
                    return path.stat().st_size
                elif path.is_dir():
                    return sum(f.stat().st_size for f in path.rglob('*') if f.is_file())
            except (OSError, PermissionError):
                pass
        
        return None
    
    def get_last_modified(self) -> Optional[datetime]:
        """Get last modification time if applicable."""
        if self.resource_type == ResourceType.FILE_SYSTEM and self.resource_path:
            try:
                path = Path(self.resource_path)
                if path.exists():
                    return datetime.fromtimestamp(path.stat().st_mtime)
            except (OSError, PermissionError):
                pass
        
        return None
    
    def get_format_schema(self) -> Optional[Dict[str, Any]]:
        """Get format schema if available."""
        if "json_schema" in self.format_info:
            return self.format_info["json_schema"]
        
        # Try to infer schema from resource data
        if self.resource_data and self.resource_type == ResourceType.CONFIGURATION:
            return self._infer_schema(self.resource_data)
        
        return None
    
    def _infer_schema(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Infer basic JSON schema from data structure."""
        def infer_type(value):
            if isinstance(value, bool):
                return {"type": "boolean"}
            elif isinstance(value, int):
                return {"type": "integer"}
            elif isinstance(value, float):
                return {"type": "number"}
            elif isinstance(value, str):
                return {"type": "string"}
            elif isinstance(value, list):
                if value:
                    return {"type": "array", "items": infer_type(value[0])}
                else:
                    return {"type": "array"}
            elif isinstance(value, dict):
                properties = {k: infer_type(v) for k, v in value.items()}
                return {"type": "object", "properties": properties}
            else:
                return {"type": "string"}
        
        return infer_type(data)
    
    def validate_access(self, operation: str) -> bool:
        """Validate if an operation is allowed on this resource."""
        if operation == "read":
            return self.access_level in ["read", "write", "admin"]
        elif operation == "write":
            return self.access_level in ["write", "admin"]
        elif operation == "admin":
            return self.access_level == "admin"
        
        return False
    
    def get_access_constraints(self) -> Dict[str, Any]:
        """Get access constraints for this resource."""
        constraints = self.constraints.copy()
        
        # Add derived constraints
        constraints["access_level"] = self.access_level
        constraints["available"] = self.is_available()
        
        size = self.get_size()
        if size is not None:
            constraints["size_bytes"] = size
        
        return constraints
    
    def matches_pattern(self, pattern: str) -> bool:
        """Check if resource matches an access pattern."""
        if pattern in self.access_patterns:
            return True
        
        # Check pattern against path
        if self.resource_path:
            import fnmatch
            return fnmatch.fnmatch(self.resource_path, pattern)
        
        # Check pattern against name
        import fnmatch
        return fnmatch.fnmatch(self.name, pattern)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with resource-specific information."""
        base_dict = super().to_dict()
        base_dict.update({
            "resource_type": self.resource_type.value,
            "resource_path": self.resource_path,
            "resource_data_keys": list(self.resource_data.keys()) if self.resource_data else [],
            "access_patterns": self.access_patterns,
            "format_info": self.format_info,
            "constraints": self.get_access_constraints(),
            "access_level": self.access_level,
            "dependencies": self.dependencies,
            "is_available": self.is_available(),
            "size": self.get_size(),
            "last_modified": self.get_last_modified().isoformat() if self.get_last_modified() else None
        })
        return base_dict
    
    @classmethod
    def create_from_path(
        cls, 
        path: Union[str, Path], 
        name: Optional[str] = None,
        description: Optional[str] = None,
        access_level: str = "read"
    ) -> 'ResourceCard':
        """
        Create a ResourceCard from a file system path.
        
        Args:
            path: Path to the resource
            name: Optional custom name (defaults to path name)
            description: Optional description
            access_level: Access level for the resource
            
        Returns:
            ResourceCard instance
        """
        path_obj = Path(path)
        resource_name = name or path_obj.name
        
        if not description:
            if path_obj.is_file():
                description = f"File resource: {path_obj.name}"
            elif path_obj.is_dir():
                description = f"Directory resource: {path_obj.name}"
            else:
                description = f"Path resource: {path}"
        
        # Determine format info
        format_info = {}
        if path_obj.is_file():
            suffix = path_obj.suffix.lower()
            if suffix == '.json':
                format_info['json'] = True
            elif suffix == '.csv':
                format_info['csv'] = True
            elif suffix in ['.txt', '.md']:
                format_info['text'] = True
            elif suffix in ['.yml', '.yaml']:
                format_info['yaml'] = True
        
        # Infer access patterns
        access_patterns = []
        if "config" in str(path_obj).lower():
            access_patterns.append("configuration")
        if any(keyword in str(path_obj).lower() for keyword in ["data", "input", "output"]):
            access_patterns.append("data_access")
        if any(keyword in str(path_obj).lower() for keyword in ["temp", "cache"]):
            access_patterns.append("temporary_access")
        
        metadata = CardMetadata(
            source="filesystem",
            confidence=0.95,
            tags={"filesystem", "auto_generated"}
        )
        
        return cls(
            resource_name=resource_name,
            description=description,
            resource_type=ResourceType.FILE_SYSTEM,
            resource_path=str(path_obj.absolute()),
            access_patterns=access_patterns,
            format_info=format_info,
            access_level=access_level,
            metadata=metadata
        )
    
    @classmethod
    def create_from_config(
        cls,
        config_name: str,
        config_data: Dict[str, Any],
        description: Optional[str] = None,
        access_level: str = "read"
    ) -> 'ResourceCard':
        """
        Create a ResourceCard from configuration data.
        
        Args:
            config_name: Name of the configuration
            config_data: Configuration data dictionary
            description: Optional description
            access_level: Access level for the configuration
            
        Returns:
            ResourceCard instance
        """
        description = description or f"Configuration resource: {config_name}"
        
        # Analyze configuration structure
        format_info = {"json": True}
        if "schema" in config_data:
            format_info["json_schema"] = config_data["schema"]
        
        access_patterns = ["configuration"]
        
        # Determine if this is a sensitive configuration
        sensitive_keys = {"password", "key", "secret", "token", "credential"}
        if any(key.lower() in sensitive_keys for key in config_data.keys()):
            access_patterns.append("sensitive")
        
        metadata = CardMetadata(
            source="configuration",
            confidence=1.0,
            tags={"configuration", "in_memory"}
        )
        
        return cls(
            resource_name=config_name,
            description=description,
            resource_type=ResourceType.CONFIGURATION,
            resource_data=config_data,
            access_patterns=access_patterns,
            format_info=format_info,
            access_level=access_level,
            metadata=metadata
        )