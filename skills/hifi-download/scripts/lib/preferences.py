"""User preferences management for MusicMaster.

Tracks user intent for each service:
- enabled: User wants to use this service
- disabled: User explicitly chose not to use this service
- not_configured: Service not set up yet (user hasn't decided)
"""

import os
import json
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict
from pathlib import Path


@dataclass
class ServicePreference:
    """Preference for a single service."""
    status: str = "not_configured"  # enabled | disabled | not_configured
    reason: Optional[str] = None    # Why disabled (user provided)

    def is_enabled(self) -> bool:
        return self.status == "enabled"

    def is_disabled(self) -> bool:
        return self.status == "disabled"

    def is_not_configured(self) -> bool:
        return self.status == "not_configured"


@dataclass
class Preferences:
    """User preferences for all services."""
    spotify: ServicePreference = field(default_factory=ServicePreference)
    lastfm: ServicePreference = field(default_factory=ServicePreference)
    qobuz: ServicePreference = field(default_factory=ServicePreference)
    tidal: ServicePreference = field(default_factory=ServicePreference)

    @classmethod
    def get_preferences_path(cls) -> Path:
        """Get path to preferences file."""
        # Try skill directory first
        script_dir = Path(__file__).parent.parent.parent
        return script_dir / ".preferences.json"

    @classmethod
    def load(cls) -> "Preferences":
        """Load preferences from file."""
        prefs_path = cls.get_preferences_path()

        if not prefs_path.exists():
            return cls()

        try:
            with open(prefs_path, 'r') as f:
                data = json.load(f)

            prefs = cls()
            for service in ['spotify', 'lastfm', 'qobuz', 'tidal']:
                if service in data:
                    service_data = data[service]
                    setattr(prefs, service, ServicePreference(
                        status=service_data.get('status', 'not_configured'),
                        reason=service_data.get('reason')
                    ))
            return prefs
        except (json.JSONDecodeError, KeyError):
            return cls()

    def save(self) -> None:
        """Save preferences to file."""
        prefs_path = self.get_preferences_path()

        data = {}
        for service in ['spotify', 'lastfm', 'qobuz', 'tidal']:
            pref = getattr(self, service)
            data[service] = {
                'status': pref.status,
                'reason': pref.reason
            }

        with open(prefs_path, 'w') as f:
            json.dump(data, f, indent=2)

    def enable_service(self, service: str) -> None:
        """Mark a service as enabled."""
        if hasattr(self, service):
            setattr(self, service, ServicePreference(status="enabled"))
            self.save()

    def disable_service(self, service: str, reason: Optional[str] = None) -> None:
        """Mark a service as explicitly disabled by user."""
        if hasattr(self, service):
            setattr(self, service, ServicePreference(status="disabled", reason=reason))
            self.save()

    def get_summary(self) -> Dict[str, str]:
        """Get a summary of all service statuses."""
        return {
            'spotify': self._format_status(self.spotify),
            'lastfm': self._format_status(self.lastfm),
            'qobuz': self._format_status(self.qobuz),
            'tidal': self._format_status(self.tidal),
        }

    def _format_status(self, pref: ServicePreference) -> str:
        """Format a single service status."""
        if pref.status == "enabled":
            return "enabled"
        elif pref.status == "disabled":
            if pref.reason:
                return f"disabled ({pref.reason})"
            return "disabled (user choice)"
        else:
            return "not_configured"
