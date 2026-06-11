from __future__ import annotations

from typing import Dict, Sequence

from skillpulse.schema import ClusterRole, ExtractedSkill
from skillpulse.taxonomy import RolePrototype, load_role_prototypes


class RoleClassifier:
    def __init__(self, roles: Dict[str, RolePrototype] = None, floor: float = 2.0) -> None:
        self.roles = roles or load_role_prototypes()
        self.floor = floor

    def classify(self, title: str, skills: Sequence[ExtractedSkill]) -> ClusterRole:
        skill_ids = {skill.skill_id for skill in skills}
        normalized_title = (title or "").lower()

        best_role = "other"
        best_score = 0.0
        for role, prototype in self.roles.items():
            if role == "other":
                continue
            score = self._score(prototype, skill_ids, normalized_title)
            if score > best_score:
                best_role = role
                best_score = score

        if best_score < self.floor:
            return ClusterRole.other
        try:
            return ClusterRole(best_role)
        except ValueError:
            return ClusterRole.other

    def _score(self, prototype: RolePrototype, skill_ids: set, title: str) -> float:
        score = 0.0
        core_hits = skill_ids.intersection(prototype.core_skills)
        support_hits = skill_ids.intersection(prototype.supporting_skills)
        score += 2.0 * len(core_hits)
        score += 1.0 * len(support_hits)

        if any(keyword in title for keyword in prototype.title_keywords):
            score += 0.75
        return score

