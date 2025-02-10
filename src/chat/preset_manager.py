import os
import json
from typing import Dict, List, Optional

class Preset:
    def __init__(self, name: str, api_key: str, base_url: str, model: str, max_chars_per_second: Optional[int] = None):
        self.name = name
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.max_chars_per_second = max_chars_per_second

    def to_dict(self) -> Dict:
        result = {
            "name": self.name,
            "api_key": self.api_key,
            "base_url": self.base_url,
            "model": self.model
        }
        if self.max_chars_per_second is not None:
            result["max_chars_per_second"] = self.max_chars_per_second
        return result

    @classmethod
    def from_dict(cls, data: Dict) -> 'Preset':
        return cls(
            name=data["name"],
            api_key=data["api_key"],
            base_url=data["base_url"],
            model=data["model"],
            max_chars_per_second=data.get("max_chars_per_second")
        )

class PresetManager:
    def __init__(self, preset_file: str):
        self.preset_file = os.path.expanduser(preset_file)
        os.makedirs(os.path.dirname(self.preset_file), exist_ok=True)
        if not os.path.exists(self.preset_file):
            # Create empty file
            with open(self.preset_file, "w", encoding="utf-8") as f:
                pass

    def add_preset(self, name: str, api_key: str, base_url: str, model: str, max_chars_per_second: Optional[int] = None) -> None:
        """Add a new preset or update existing one."""
        preset = Preset(name, api_key, base_url, model, max_chars_per_second)
        
        # Read existing presets
        presets = self.list_presets()
        
        # Remove existing preset with same name if exists
        presets = [p for p in presets if p.name != name]
        
        # Add new preset
        presets.append(preset)
        
        # Write all presets back
        self._write_presets(presets)

    def list_presets(self) -> List[Preset]:
        """List all presets."""
        presets = []
        if os.path.getsize(self.preset_file) > 0:
            with open(self.preset_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        presets.append(Preset.from_dict(data))
        return presets

    def delete_preset(self, name: str) -> bool:
        """Delete a preset by name. Returns True if deleted, False if not found."""
        presets = self.list_presets()
        original_count = len(presets)
        presets = [p for p in presets if p.name != name]
        if len(presets) < original_count:
            self._write_presets(presets)
            return True
        return False

    def get_preset(self, name: str) -> Optional[Preset]:
        """Get a preset by name."""
        presets = self.list_presets()
        for preset in presets:
            if preset.name == name:
                return preset
        return None

    def _write_presets(self, presets: List[Preset]) -> None:
        """Write presets to file."""
        with open(self.preset_file, "w", encoding="utf-8") as f:
            for preset in presets:
                f.write(json.dumps(preset.to_dict()) + "\n")
