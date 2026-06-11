from __future__ import annotations

import re
from typing import Dict, Iterable, List, Sequence, Set

from skillpulse.schema import ExtractedSkill
from skillpulse.taxonomy import SkillDef, load_skill_taxonomy


_CONTEXT_CUES = (
    "需求",
    "條件",
    "技能",
    "熟悉",
    "精通",
    "經驗",
    "requirements",
    "skills",
    "required",
    "experience",
    "familiar",
)


class SkillExtractor:
    def __init__(self, skills: Dict[str, SkillDef] = None) -> None:
        self.skills = skills or load_skill_taxonomy()

    def extract(self, text: str) -> List[ExtractedSkill]:
        found: List[ExtractedSkill] = []
        seen: Set[str] = set()
        source = text or ""
        lower = source.lower()

        for skill in self.skills.values():
            if skill.skill_id in seen:
                continue
            if self._skill_matches(skill, source, lower):
                found.append(
                    ExtractedSkill(
                        skill_id=skill.skill_id,
                        name=skill.name,
                        facet=skill.facet,
                        ai_era=skill.ai_era,
                    )
                )
                seen.add(skill.skill_id)

        found.sort(key=lambda item: (item.facet, item.name.lower()))
        return found

    def _skill_matches(self, skill: SkillDef, source: str, lower: str) -> bool:
        for alias in skill.aliases:
            spans = list(_find_alias_spans(alias, source, lower))
            if not spans:
                continue
            if not skill.require_context:
                return True
            if any(_has_requirement_context(lower, start, end) for start, end in spans):
                return True
        return False


def extract_skill_ids(text: str, skills: Dict[str, SkillDef] = None) -> List[str]:
    return [skill.skill_id for skill in SkillExtractor(skills).extract(text)]


def ai_inflected(skills: Sequence[ExtractedSkill]) -> bool:
    return any(skill.ai_era for skill in skills)


def facets_present(skills: Sequence[ExtractedSkill]) -> List[int]:
    return sorted({skill.facet for skill in skills})


def _find_alias_spans(alias: str, source: str, lower: str) -> Iterable[tuple]:
    alias_clean = alias.strip()
    if not alias_clean:
        return []

    if _contains_cjk(alias_clean):
        haystack = lower
        needle = alias_clean.lower()
        start = haystack.find(needle)
        spans = []
        while start >= 0:
            spans.append((start, start + len(needle)))
            start = haystack.find(needle, start + len(needle))
        return spans

    needle = alias_clean.lower()
    pattern = _alias_pattern(needle)
    return [(match.start(), match.end()) for match in re.finditer(pattern, lower)]


def _alias_pattern(alias: str) -> str:
    escaped = re.escape(alias)
    if re.fullmatch(r"[a-z0-9+#.]+", alias):
        return r"(?<![a-z0-9])" + escaped + r"(?![a-z0-9])"
    return r"(?<![a-z0-9])" + escaped + r"(?![a-z0-9])"


def _contains_cjk(text: str) -> bool:
    return any("\u4e00" <= ch <= "\u9fff" for ch in text)


def _has_requirement_context(lower: str, start: int, end: int, window: int = 160) -> bool:
    left = max(0, start - window)
    right = min(len(lower), end + window)
    nearby = lower[left:right]
    return any(cue in nearby for cue in _CONTEXT_CUES)
