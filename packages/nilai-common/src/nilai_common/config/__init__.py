"""Configuration module for nilai-common."""

from .host import SETTINGS, HostSettings, to_bool
from .model import MODEL_CAPABILITIES, MODEL_SETTINGS, ModelCapabilities, ModelSettings


__all__ = [
    "MODEL_CAPABILITIES",
    "MODEL_SETTINGS",
    "SETTINGS",
    "HostSettings",
    "ModelCapabilities",
    "ModelSettings",
    "to_bool",
]
