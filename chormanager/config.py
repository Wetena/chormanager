"""Configuration management for ChorManager."""

import yaml
import json
from pathlib import Path
from functools import lru_cache

CONFIG_DIR = Path(__file__).parent.parent / "config"


def get_state_file():
    """Get the state file for storing runtime state (e.g., last active project).
    
    Returns:
        Path: Path to state.json file.
    """
    return get_data_dir() / "state.json"


def load_state():
    """Load application state from JSON file.
    
    Returns:
        dict: State dictionary.
    """
    state_file = get_state_file()
    if state_file.exists():
        with open(state_file, encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_state(state: dict):
    """Save application state to JSON file.
    
    Args:
        state: State dictionary to save.
    """
    state_file = get_state_file()
    with open(state_file, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def get_last_active_project_id():
    """Get the ID of the last active project.
    
    Returns:
        str: Project ID or None.
    """
    state = load_state()
    return state.get("last_active_project_id")


def set_last_active_project_id(project_id: str):
    """Set the ID of the last active project.
    
    Args:
        project_id: Project ID to store.
    """
    state = load_state()
    state["last_active_project_id"] = project_id
    save_state(state)


def get_last_active_event_id():
    """Get the ID of the last active event."""
    state = load_state()
    return state.get("last_active_event_id")


def set_last_active_event_id(event_id: str):
    """Set the ID of the last active event."""
    state = load_state()
    state["last_active_event_id"] = event_id
    save_state(state)


def get_last_active_besetzung_id():
    """Get the ID of the last active besetzung."""
    state = load_state()
    return state.get("last_active_besetzung_id")


def set_last_active_besetzung_id(besetzung_id: str):
    """Set the ID of the last active besetzung."""
    state = load_state()
    state["last_active_besetzung_id"] = besetzung_id
    save_state(state)


def get_theme():
    """Get the selected theme (light or dark).
    
    Returns:
        str: Theme name ("light" or "dark").
    """
    state = load_state()
    return state.get("theme", "light")


def set_theme(theme: str):
    """Set the selected theme.
    
    Args:
        theme: Theme name ("light" or "dark").
    """
    state = load_state()
    state["theme"] = theme
    save_state(state)


def get_app_dir() -> Path:
    """Get the application directory (where chormanager is installed).
    
    Returns:
        Path: The application directory.
    """
    return Path(__file__).parent.parent


def get_data_dir() -> Path:
    """Get the data directory for storing app data.
    
    By default, uses a 'data' subdirectory within the app directory.
    This ensures all data stays with the program.
    
    Returns:
        Path: The data directory.
    """
    return get_app_dir() / "data"


@lru_cache(maxsize=1)
def _load_voice_groups_raw():
    """Load raw voice groups from YAML."""
    config_file = CONFIG_DIR / "voice_groups.yaml"
    try:
        with open(config_file, encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except (FileNotFoundError, yaml.YAMLError):
        return []
    groups = data.get("voice_groups", []) if data else []
    return sorted(groups, key=lambda g: g.get("order", 0))


def load_voice_groups():
    """Load voice groups from YAML configuration.
    
    Returns:
        list: List of voice group dictionaries sorted by order.
    """
    return _load_voice_groups_raw()


@lru_cache(maxsize=1)
def _load_fields_raw():
    """Load raw field definitions from YAML."""
    config_file = CONFIG_DIR / "fields.yaml"
    try:
        with open(config_file, encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except (FileNotFoundError, yaml.YAMLError):
        return []
    fields = data.get("fields", []) if data else []
    return sorted(fields, key=lambda f: f.get("order", 0))


def load_fields():
    """Load field definitions from YAML configuration.
    
    Returns:
        list: List of field dictionaries sorted by order.
    """
    return _load_fields_raw()


@lru_cache(maxsize=1)
def _load_app_config_raw():
    """Load raw application configuration from YAML."""
    config_file = CONFIG_DIR / "app.yaml"
    try:
        with open(config_file, encoding="utf-8") as f:
            config = yaml.safe_load(f) or {}
    except (FileNotFoundError, yaml.YAMLError):
        config = {}
    
    config.setdefault("database", {}).setdefault("filename", "chor.db")
    config.setdefault("backup", {}).setdefault("enabled", True)
    config.setdefault("backup", {}).setdefault("on_start", True)
    config.setdefault("backup", {}).setdefault("before_save", True)
    config.setdefault("backup", {}).setdefault("max_backups", 10)
    config.setdefault("logging", {}).setdefault("enabled", True)
    config.setdefault("logging", {}).setdefault("level", "INFO")
    
    return config


def load_app_config():
    """Load application configuration from YAML.
    
    Returns:
        dict: Application configuration dictionary.
    """
    return _load_app_config_raw()


def reload_config():
    """Clear config cache and reload from disk."""
    _load_voice_groups_raw.cache_clear()
    _load_fields_raw.cache_clear()
    _load_app_config_raw.cache_clear()
    
    return load_app_config()


def get_voice_group_choices():
    """Get voice groups as choices for dropdown.
    
    Returns:
        list: List of (name, display_name) tuples.
    """
    groups = load_voice_groups()
    return [(g["name"], g["name"]) for g in groups]


def get_field_by_name(name: str):
    """Get field definition by name.
    
    Args:
        name: Field name.
        
    Returns:
        dict: Field definition or None.
    """
    fields = load_fields()
    for field in fields:
        if field["name"] == name:
            return field
    return None


def get_required_fields():
    """Get list of required field names.
    
    Returns:
        list: List of required field names.
    """
    fields = load_fields()
    return [f["name"] for f in fields if f.get("required", False)]


# Voice group color cache (theme-aware)
_vg_color_cache: dict = {}
_vg_color_theme: str | None = None


def _load_voice_group_colors() -> list:
    """Load voice group colors from voice_groups.json (theme-aware).
    
    Returns:
        list: List of voice group color dicts with 'id' and 'color' keys.
    """
    global _vg_color_cache, _vg_color_theme

    current_theme = get_theme()

    if _vg_color_theme == current_theme and _vg_color_cache:
        return _vg_color_cache

    config_file = CONFIG_DIR / "voice_groups.json"
    try:
        with open(config_file, encoding="utf-8") as f:
            data = json.load(f)
        theme_data = data.get("themes", {}).get(current_theme, {})
        colors = theme_data.get("colors", [])
        if colors:
            _vg_color_cache = colors
            _vg_color_theme = current_theme
            return colors
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        pass

    # Hardcoded fallback (light theme)
    _vg_color_cache = [
        {"id": "Sopran 1", "color": "#E5C84B"}, {"id": "Sopran 2", "color": "#B8A23A"},
        {"id": "Alt 1", "color": "#C75B5B"}, {"id": "Alt 2", "color": "#9B5B6B"},
        {"id": "Tenor 1", "color": "#6BA888"}, {"id": "Tenor 2", "color": "#5B8A6B"},
        {"id": "Bass 1", "color": "#6B8AA8"}, {"id": "Bass 2", "color": "#5B6B8A"},
    ]
    _vg_color_theme = current_theme
    return _vg_color_cache


def get_voice_group_color(voice_group_id: str, theme: str | None = None) -> str:
    """Get hex color for a voice group (theme-aware, cached).
    
    Args:
        voice_group_id: Voice group name (e.g. "Sopran 1").
        theme: Optional theme override ("light"/"dark"). Defaults to current theme.
    
    Returns:
        str: Hex color code (e.g. "#E5C84B").
    """
    if theme is not None:
        _clear_vg_color_cache()
        global _vg_color_theme
        _vg_color_theme = theme

    colors = _load_voice_group_colors()
    for vg in colors:
        if vg.get("id") == voice_group_id:
            return vg["color"]
    return "#cccccc"


def _clear_vg_color_cache():
    """Clear the voice group color cache."""
    global _vg_color_cache, _vg_color_theme
    _vg_color_cache = {}
    _vg_color_theme = None


def get_text_color() -> str:
    """Get the current theme text color.
    
    Returns:
        str: Hex text color.
    """
    current_theme = get_theme()
    config_file = CONFIG_DIR / "voice_groups.json"
    try:
        with open(config_file, encoding="utf-8") as f:
            data = json.load(f)
        return data.get("themes", {}).get(current_theme, {}).get("text", "#1A1A1A")
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        return "#1A1A1A"
