import json
from typing import List, Dict, Any, Optional

class VPNModel:
    def __init__(self,
                 model_id: str,
                 model_name: str,
                 vpn_client_type: str,
                 description: str = "",
                 logical_fields: Optional[List[Dict[str, Any]]] = None,
                 automation_steps: Optional[List[Dict[str, Any]]] = None):
        self.model_id = model_id
        self.model_name = model_name
        self.vpn_client_type = vpn_client_type
        self.description = description
        self.logical_fields: List[Dict[str, Any]] = logical_fields if logical_fields is not None else []
        self.automation_steps: List[Dict[str, Any]] = automation_steps if automation_steps is not None else []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "model_id": self.model_id,
            "model_name": self.model_name,
            "vpn_client_type": self.vpn_client_type,
            "description": self.description,
            "logical_fields": self.logical_fields,
            "automation_steps": self.automation_steps
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VPNModel":
        return cls(
            model_id=data.get("model_id", ""),
            model_name=data.get("model_name", ""),
            vpn_client_type=data.get("vpn_client_type", ""),
            description=data.get("description", ""),
            logical_fields=data.get("logical_fields", []),
            automation_steps=data.get("automation_steps", [])
        )

    def __repr__(self) -> str:
        return f"VPNModel(model_id='{self.model_id}', model_name='{self.model_name}')"

