"""Gestion centralisée des prompts.

Chaque prompt est un fichier `prompts/<nom>.md` :

    ---
    name: write
    version: 1
    task: write
    ---
    <gabarit Jinja du message système>
    === USER ===
    <gabarit Jinja du message utilisateur>

La version (et un hash du fichier) est enregistrée avec chaque appel LLM.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader, StrictUndefined

from .config import PROMPTS_DIR

USER_SEPARATOR = "=== USER ==="
INCLUDE_RE = re.compile(r"""{%-?\s*include\s+["']([^"']+)["']""")

# Les fragments partagés (ex. règles de rédaction) vivent dans prompts/partials/ et sont inclus
# avec {% include "partials/<fichier>.md" %} ; leur contenu entre dans le hash de version.
_env = Environment(
    loader=FileSystemLoader(str(PROMPTS_DIR)),
    undefined=StrictUndefined,
    keep_trailing_newline=False,
    autoescape=False,
)


@dataclass(frozen=True)
class Prompt:
    name: str
    version: str
    task: str
    system_template: str
    user_template: str
    sha: str

    @property
    def version_label(self) -> str:
        return f"v{self.version}-{self.sha}"

    def render(self, **context) -> tuple[str, str]:
        system = _env.from_string(self.system_template).render(**context).strip()
        user = _env.from_string(self.user_template).render(**context).strip()
        return system, user


@lru_cache(maxsize=None)
def load_prompt(name: str, prompts_dir: Path = PROMPTS_DIR) -> Prompt:
    path = prompts_dir / f"{name}.md"
    raw = path.read_text(encoding="utf-8")
    if not raw.startswith("---"):
        raise ValueError(f"{path}: en-tête YAML manquant")
    _, header, body = raw.split("---", 2)
    meta = yaml.safe_load(header)
    if USER_SEPARATOR not in body:
        raise ValueError(f"{path}: séparateur '{USER_SEPARATOR}' manquant")
    system, user = body.split(USER_SEPARATOR, 1)
    return Prompt(
        name=meta["name"],
        version=str(meta["version"]),
        task=meta["task"],
        system_template=system.strip(),
        user_template=user.strip(),
        sha=_version_hash(raw, prompts_dir),
    )


def _version_hash(raw: str, prompts_dir: Path) -> str:
    digest = hashlib.sha256(raw.encode("utf-8"))
    for include in sorted(set(INCLUDE_RE.findall(raw))):
        digest.update((prompts_dir / include).read_bytes())
    return digest.hexdigest()[:8]
