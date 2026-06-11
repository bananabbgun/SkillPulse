from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping

import yaml

from skillpulse.paths import TAXONOMY_DIR


@dataclass(frozen=True)
class SkillDef:
    skill_id: str
    name: str
    facet: int
    ai_era: bool
    aliases: List[str]
    require_context: bool = False


@dataclass(frozen=True)
class RolePrototype:
    role: str
    in_cluster: bool
    title_keywords: List[str]
    core_skills: List[str]
    supporting_skills: List[str]


def _load_yaml(path: Path) -> Mapping[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        loaded = yaml.safe_load(fh)
    if not isinstance(loaded, dict):
        raise ValueError(f"Expected YAML mapping in {path}")
    return loaded


def load_skill_taxonomy(path: Path = TAXONOMY_DIR / "skills_v1.yaml") -> Dict[str, SkillDef]:
    data = _load_yaml(path)
    facets = data.get("facets", {})
    skills: Dict[str, SkillDef] = {}

    for row in data.get("skills", []):
        facet = int(row["facet"])
        facet_ai = bool(facets.get(facet, {}).get("ai_era", False))
        skill_id = str(row["id"])
        skills[skill_id] = SkillDef(
            skill_id=skill_id,
            name=str(row["name"]),
            facet=facet,
            ai_era=bool(row.get("ai_era", facet_ai)),
            aliases=[str(alias) for alias in row.get("aliases", [])],
            require_context=bool(row.get("require_context", False)),
        )
    return skills


def load_role_prototypes(path: Path = TAXONOMY_DIR / "roles_v1.yaml") -> Dict[str, RolePrototype]:
    data = _load_yaml(path)
    roles: Dict[str, RolePrototype] = {}
    for role, row in data.get("roles", {}).items():
        roles[str(role)] = RolePrototype(
            role=str(role),
            in_cluster=bool(row.get("in_cluster", False)),
            title_keywords=[str(item).lower() for item in row.get("title_keywords", [])],
            core_skills=[str(item) for item in row.get("core_skills", [])],
            supporting_skills=[str(item) for item in row.get("supporting_skills", [])],
        )
    return roles


def iter_skills_by_facet(skills: Mapping[str, SkillDef], facet: int) -> Iterable[SkillDef]:
    return (skill for skill in skills.values() if skill.facet == facet)

