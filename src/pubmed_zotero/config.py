"""Strict validation of versioned search configuration."""

import re
from pathlib import Path

import yaml

from .models import Search


class ConfigurationError(ValueError):
    pass


def load_searches(path: Path) -> list[Search]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError):
        raise ConfigurationError("Sökkonfigurationen kunde inte läsas.") from None
    if not isinstance(data, dict) or set(data) != {"searches"}:
        raise ConfigurationError("Förväntade en searches-lista.")
    rows = data["searches"]
    if not isinstance(rows, list) or not rows:
        raise ConfigurationError("Minst en sökning krävs.")
    result = []
    seen = set()
    required = {
        "id",
        "title",
        "query",
        "version",
        "description",
        "enabled",
        "lookback_days",
    }
    for row in rows:
        if not isinstance(row, dict) or set(row) != required:
            raise ConfigurationError("En sökning har saknade eller okända fält.")
        for key in required - {"enabled", "lookback_days"}:
            if not isinstance(row[key], str) or not row[key].strip():
                raise ConfigurationError(
                    "Sökningens textfält måste vara icke-tomma strängar."
                )
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", row["id"]):
            raise ConfigurationError("Ogiltigt sök-ID.")
        if row["id"] in seen:
            raise ConfigurationError("Sök-ID måste vara unika.")
        if type(row["enabled"]) is not bool or type(row["lookback_days"]) is not int:
            raise ConfigurationError("enabled ska vara bool och lookback_days heltal.")
        if not 1 <= row["lookback_days"] <= 365:
            raise ConfigurationError("lookback_days måste vara mellan 1 och 365.")
        seen.add(row["id"])
        result.append(Search(**row))
    return result
