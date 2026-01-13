import json
import os
from typing import List, Optional, Dict, Any
from .vpn_model import VPNModel

class VPNModelManager:
    def __init__(self, models_dir: str = "config/vpn_models"):
        self.models_dir = models_dir
        if not os.path.exists(self.models_dir):
            os.makedirs(self.models_dir)

    def _get_model_filepath(self, model_id: str) -> str:
        return os.path.join(self.models_dir, f"{model_id}.json")

    def save_model(self, model: VPNModel) -> bool:
        """Saves a VPNModel to a JSON file."""
        filepath = self._get_model_filepath(model.model_id)
        try:
            with open(filepath, "w") as f:
                json.dump(model.to_dict(), f, indent=4)
            return True
        except IOError as e:
            print(f"Error saving model {model.model_id}: {e}")
            return False

    def load_model(self, model_id: str) -> Optional[VPNModel]:
        """Loads a VPNModel from a JSON file by its ID."""
        filepath = self._get_model_filepath(model_id)
        if not os.path.exists(filepath):
            return None
        try:
            with open(filepath, "r") as f:
                data = json.load(f)
            return VPNModel.from_dict(data)
        except (IOError, json.JSONDecodeError) as e:
            print(f"Error loading model {model_id}: {e}")
            return None

    def delete_model(self, model_id: str) -> bool:
        """Deletes a VPNModel JSON file by its ID."""
        filepath = self._get_model_filepath(model_id)
        if not os.path.exists(filepath):
            print(f"Error deleting model: {model_id} not found.")
            return False
        try:
            os.remove(filepath)
            return True
        except OSError as e:
            print(f"Error deleting model {model_id}: {e}")
            return False

    def list_models(self) -> List[VPNModel]:
        """Lists all available VPNModels by loading them from the models directory."""
        models: List[VPNModel] = []
        if not os.path.exists(self.models_dir):
            return models
        
        for filename in os.listdir(self.models_dir):
            if filename.endswith(".json"):
                model_id = filename[:-5] # Remove .json extension
                model = self.load_model(model_id)
                if model:
                    models.append(model)
        return models

    def get_available_model_ids(self) -> List[str]:
        """Returns a list of model_ids for all available VPNModels."""
        model_ids: List[str] = []
        if not os.path.exists(self.models_dir):
            return model_ids
        
        for filename in os.listdir(self.models_dir):
            if filename.endswith(".json"):
                model_ids.append(filename[:-5]) # Remove .json extension
        return model_ids


