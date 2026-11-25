"""
Offline Behavioral & STAR Interview Preparation Engine for CareerForge.
Drafts honest STAR outlines from profile.yaml (marking unstated parts with
'TODO: fill in'), manages a local YAML STAR story bank, tracks category coverage,
and provides seeded practice prompts with Anti-AI prose auditing.
"""

from __future__ import annotations

import os
import random
import re
from datetime import datetime, timezone
from importlib import resources
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple, Union

import platformdirs
import yaml

TODO_PLACEHOLDER = "TODO: fill in"

STAR_CATEGORIES: Tuple[str, ...] = (
    "leadership",
    "conflict",
    "failure",
    "teamwork",
    "ownership",
    "deadline",
    "ambiguity",
    "technical_challenge",
)

VALID_ROLES: Tuple[str, ...] = ("backend", "data", "general", "frontend")

METRIC_RE = re.compile(
    r"(?:\$\s*\d+(?:,\d{3})*(?:\.\d+)?[KMBkmb]?|\b\d+(?:,\d{3})*(?:\.\d+)?\s*(?:%|ms|s|x|k|m|b|\+)(?!\w)|\b\d{2,}(?:,\d{3})*\+?)",
    re.IGNORECASE,
)


class InterviewError(Exception):
    """Raised on invalid story bank operations, missing IDs, or invalid roles."""


def utc_now_iso() -> str:
    """Returns current UTC timestamp in Python 3.10+ compatible ISO format."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def get_stories_path(explicit_path: Optional[str] = None) -> str:
    """
    Resolves STAR story bank YAML path:
    1. Explicit path argument
    2. CAREERFORGE_STORIES env var
    3. CAREERFORGE_DATA_DIR/stories.yaml env var
    4. platformdirs user data dir/stories.yaml
    """
    if explicit_path:
        path = explicit_path
    elif os.environ.get("CAREERFORGE_STORIES"):
        path = os.environ["CAREERFORGE_STORIES"]
    elif os.environ.get("CAREERFORGE_DATA_DIR"):
        path = os.path.join(os.environ["CAREERFORGE_DATA_DIR"], "stories.yaml")
    else:
        data_dir = platformdirs.user_data_dir("careerforge", appauthor=False)
        path = os.path.join(data_dir, "stories.yaml")

    parent = os.path.dirname(os.path.abspath(path))
    if parent:
        os.makedirs(parent, exist_ok=True)
    return path


def normalize_tags(tags: Optional[Union[str, Iterable[str]]]) -> List[str]:
    """Normalizes comma-separated or iterable category tags cleanly."""
    if not tags:
        return []
    raw_items: List[str] = []
    if isinstance(tags, str):
        raw_items = tags.split(",")
    else:
        for item in tags:
            if isinstance(item, str):
                raw_items.extend(item.split(","))
            elif item is not None:
                raw_items.append(str(item))

    seen = set()
    cleaned: List[str] = []
    for item in raw_items:
        norm = item.strip().lower().replace(" ", "_")
        if norm and norm not in seen:
            seen.add(norm)
            cleaned.append(norm)
    return cleaned


def extract_metrics(text: str) -> List[str]:
    """Extracts concrete metric expressions present verbatim in a bullet or summary."""
    if not text:
        return []
    matches = [m.group(0).strip() for m in METRIC_RE.finditer(text)]
    seen = set()
    ordered: List[str] = []
    for tok in matches:
        if tok not in seen:
            seen.add(tok)
            ordered.append(tok)
    return ordered


def _short_title(text: str, max_words: int = 8) -> str:
    words = text.strip().rstrip(".").split()
    if len(words) <= max_words:
        return " ".join(words)
    return " ".join(words[:max_words]) + "..."


def _flatten_bullet_text(bullet: Any) -> str:
    if isinstance(bullet, dict):
        prefix = str(bullet.get("bold_prefix", "") or "").strip()
        body = str(bullet.get("text", "") or "").strip()
        if prefix and body:
            return f"{prefix} {body}"
        return prefix or body
    return str(bullet or "").strip()


def draft_stories_from_profile(
    profile_data: Dict[str, Any],
    limit: int = 8,
) -> List[Dict[str, Any]]:
    """
    Drafts STAR outlines strictly from verified experience bullets and projects
    in profile.yaml. Metric-bearing items are ranked first. Any STAR element
    not present verbatim in the profile is set to 'TODO: fill in'.
    """
    candidates: List[Tuple[int, int, Dict[str, Any]]] = []
    order = 0

    experiences = profile_data.get("work_experience") or profile_data.get("experience") or []
    for exp in experiences:
        if not isinstance(exp, dict):
            continue
        role_title = str(exp.get("title") or exp.get("role") or "").strip()
        company = str(exp.get("company") or "").strip()
        duration = str(exp.get("duration") or exp.get("period") or "").strip()
        location = str(exp.get("location") or "").strip()

        sit_parts: List[str] = []
        if role_title and company:
            sit_parts.append(f"{role_title} at {company}")
        elif company or role_title:
            sit_parts.append(company or role_title)
        if duration:
            sit_parts.append(f"({duration})")
        if location:
            sit_parts.append(f"[{location}]")
        situation = " ".join(sit_parts) if sit_parts else TODO_PLACEHOLDER

        for bullet in exp.get("bullets") or []:
            bullet_text = _flatten_bullet_text(bullet)
            if not bullet_text:
                continue
            metrics = extract_metrics(bullet_text)
            has_metric = len(metrics) > 0
            label_base = company or role_title or "Experience"
            title = f"{label_base}: {_short_title(bullet_text)}"
            result = (
                f"{TODO_PLACEHOLDER} (profile cites metrics: {', '.join(metrics)})"
                if metrics
                else TODO_PLACEHOLDER
            )
            outline = {
                "title": title,
                "source_type": "experience",
                "source_ref": situation,
                "has_metric": has_metric,
                "inferred_metrics": metrics,
                "situation": situation,
                "task": TODO_PLACEHOLDER,
                "action": bullet_text,
                "result": result,
                "tags": [],
            }
            candidates.append((1 if has_metric else 0, -order, outline))
            order += 1

    projects = profile_data.get("featured_projects") or profile_data.get("projects") or []
    for proj in projects:
        if not isinstance(proj, dict):
            continue
        proj_title = str(proj.get("title") or proj.get("name") or "").strip()
        tech_stack = str(proj.get("tech_stack") or proj.get("tech") or "").strip()
        desc = str(proj.get("description") or "").strip()
        proj_bullets = [_flatten_bullet_text(b) for b in (proj.get("bullets") or []) if _flatten_bullet_text(b)]
        action_text = desc or "; ".join(proj_bullets)
        if not proj_title and not action_text:
            continue

        metrics = extract_metrics(action_text)
        has_metric = len(metrics) > 0
        if proj_title and tech_stack:
            situation = f"Project: {proj_title} ({tech_stack})"
        elif proj_title:
            situation = f"Project: {proj_title}"
        else:
            situation = TODO_PLACEHOLDER

        title = f"Project: {proj_title or _short_title(action_text)}"
        result = (
            f"{TODO_PLACEHOLDER} (profile cites metrics: {', '.join(metrics)})"
            if metrics
            else TODO_PLACEHOLDER
        )
        outline = {
            "title": title,
            "source_type": "project",
            "source_ref": situation,
            "has_metric": has_metric,
            "inferred_metrics": metrics,
            "situation": situation,
            "task": TODO_PLACEHOLDER,
            "action": action_text if action_text else TODO_PLACEHOLDER,
            "result": result,
            "tags": [],
        }
        candidates.append((1 if has_metric else 0, -order, outline))
        order += 1

    candidates.sort(key=lambda item: (item[0], item[1]), reverse=True)
    if limit and limit > 0:
        candidates = candidates[:limit]
    return [item[2] for item in candidates]


class StoryBank:
    """YAML-backed local persistence for STAR behavioral stories."""

    def __init__(self, stories_path: Optional[str] = None) -> None:
        self.path = get_stories_path(stories_path)

    def load(self) -> Dict[str, Any]:
        if not os.path.exists(self.path):
            return {"version": 1, "stories": []}
        with open(self.path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f) or {}
        if not isinstance(raw, dict):
            raise InterviewError(f"Corrupt stories file at '{self.path}': expected YAML mapping.")
        stories = raw.get("stories")
        if stories is None:
            stories = []
        if not isinstance(stories, list):
            raise InterviewError(f"Corrupt stories file at '{self.path}': 'stories' must be a list.")
        return {"version": int(raw.get("version", 1)), "stories": stories}

    def save(self, data: Dict[str, Any]) -> None:
        parent = os.path.dirname(os.path.abspath(self.path))
        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True)

    def add_story(
        self,
        title: str,
        situation: Optional[str] = None,
        task: Optional[str] = None,
        action: Optional[str] = None,
        result: Optional[str] = None,
        tags: Optional[Union[str, Iterable[str]]] = None,
        source_ref: Optional[str] = None,
    ) -> Dict[str, Any]:
        clean_title = (title or "").strip()
        if not clean_title:
            raise InterviewError("Story title cannot be empty.")

        data = self.load()
        stories = data["stories"]
        existing_ids = [int(s["id"]) for s in stories if str(s.get("id", "")).isdigit()]
        next_id = (max(existing_ids) + 1) if existing_ids else 1
        now = utc_now_iso()

        entry: Dict[str, Any] = {
            "id": next_id,
            "title": clean_title,
            "situation": (situation or "").strip() or TODO_PLACEHOLDER,
            "task": (task or "").strip() or TODO_PLACEHOLDER,
            "action": (action or "").strip() or TODO_PLACEHOLDER,
            "result": (result or "").strip() or TODO_PLACEHOLDER,
            "tags": normalize_tags(tags),
            "created_at": now,
            "updated_at": now,
        }
        if source_ref:
            entry["source_ref"] = source_ref.strip()

        stories.append(entry)
        self.save(data)
        return entry

    def save_drafts(self, drafts: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
        """Saves draft outlines into stories.yaml, skipping duplicate titles."""
        data = self.load()
        existing_titles = {str(s.get("title", "")).strip().lower() for s in data["stories"]}
        added: List[Dict[str, Any]] = []
        skipped = 0
        for draft in drafts:
            t_key = str(draft.get("title", "")).strip().lower()
            if not t_key or t_key in existing_titles:
                skipped += 1
                continue
            saved = self.add_story(
                title=draft["title"],
                situation=draft.get("situation"),
                task=draft.get("task"),
                action=draft.get("action"),
                result=draft.get("result"),
                tags=draft.get("tags"),
                source_ref=draft.get("source_ref"),
            )
            added.append(saved)
            existing_titles.add(t_key)
        return {"added_count": len(added), "skipped_count": skipped, "added": added}

    def list_stories(self, tag: Optional[str] = None) -> List[Dict[str, Any]]:
        stories = self.load()["stories"]
        if tag:
            target = tag.strip().lower().replace(" ", "_")
            return [s for s in stories if target in normalize_tags(s.get("tags"))]
        return stories

    def get_story(self, story_id: Union[int, str]) -> Optional[Dict[str, Any]]:
        target = str(story_id).strip()
        for story in self.load()["stories"]:
            if str(story.get("id")) == target:
                return story
        return None

    def edit_story(
        self,
        story_id: Union[int, str],
        title: Optional[str] = None,
        situation: Optional[str] = None,
        task: Optional[str] = None,
        action: Optional[str] = None,
        result: Optional[str] = None,
        tags: Optional[Union[str, Iterable[str]]] = None,
    ) -> Dict[str, Any]:
        target = str(story_id).strip()
        data = self.load()
        for story in data["stories"]:
            if str(story.get("id")) == target:
                if title is not None:
                    if not title.strip():
                        raise InterviewError("Story title cannot be empty.")
                    story["title"] = title.strip()
                if situation is not None:
                    story["situation"] = situation.strip() or TODO_PLACEHOLDER
                if task is not None:
                    story["task"] = task.strip() or TODO_PLACEHOLDER
                if action is not None:
                    story["action"] = action.strip() or TODO_PLACEHOLDER
                if result is not None:
                    story["result"] = result.strip() or TODO_PLACEHOLDER
                if tags is not None:
                    story["tags"] = normalize_tags(tags)
                story["updated_at"] = utc_now_iso()
                self.save(data)
                return story
        raise InterviewError(f"Story ID '{story_id}' not found in '{self.path}'.")

    def coverage_report(self) -> Dict[str, Any]:
        stories = self.load()["stories"]
        counts: Dict[str, int] = {cat: 0 for cat in STAR_CATEGORIES}
        story_ids_by_cat: Dict[str, List[Any]] = {cat: [] for cat in STAR_CATEGORIES}
        custom_counts: Dict[str, int] = {}

        for story in stories:
            sid = story.get("id")
            tags = normalize_tags(story.get("tags"))
            for t in tags:
                if t in counts:
                    counts[t] += 1
                    story_ids_by_cat[t].append(sid)
                else:
                    custom_counts[t] = custom_counts.get(t, 0) + 1

        uncovered = [cat for cat in STAR_CATEGORIES if counts[cat] == 0]
        covered = [cat for cat in STAR_CATEGORIES if counts[cat] > 0]
        incomplete_todo_count = sum(
            1
            for s in stories
            if any(TODO_PLACEHOLDER in str(s.get(field, "")) for field in ("situation", "task", "action", "result"))
        )

        return {
            "stories_path": self.path,
            "total_stories": len(stories),
            "incomplete_todo_stories": incomplete_todo_count,
            "categories": [
                {
                    "category": cat,
                    "count": counts[cat],
                    "covered": counts[cat] > 0,
                    "story_ids": story_ids_by_cat[cat],
                }
                for cat in STAR_CATEGORIES
            ],
            "covered_categories": covered,
            "uncovered_categories": uncovered,
            "custom_tags": custom_counts,
        }


def load_questions(role: str = "general") -> Dict[str, Any]:
    """Loads curated behavioral interview questions for a given role bank."""
    role_key = (role or "general").strip().lower()
    if role_key not in VALID_ROLES:
        raise InterviewError(
            f"Unknown role bank '{role}'. Valid options: {', '.join(VALID_ROLES)}."
        )

    filename = f"{role_key}.yaml"
    try:
        q_file = resources.files("careerforge.data").joinpath("questions", filename)
        content = q_file.read_text(encoding="utf-8")
    except Exception:
        local_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "data",
            "questions",
            filename,
        )
        if not os.path.exists(local_path):
            raise InterviewError(f"Question bank file '{filename}' not found.")
        with open(local_path, "r", encoding="utf-8") as f:
            content = f.read()

    data = yaml.safe_load(content) or {}
    questions = data.get("questions") or []
    return {
        "role": data.get("role", role_key),
        "description": data.get("description", ""),
        "questions": questions,
    }


def select_practice_questions(
    role: str = "general",
    seed: Optional[int] = None,
    count: int = 1,
    category: Optional[str] = None,
) -> Dict[str, Any]:
    """Selects practice questions deterministically when a seed is provided."""
    if count < 1:
        raise InterviewError("Question count must be at least 1.")

    bank = load_questions(role=role)
    pool = list(bank["questions"])

    if category:
        cat_norm = category.strip().lower().replace(" ", "_")
        pool = [q for q in pool if str(q.get("category", "")).strip().lower() == cat_norm]
        if not pool:
            raise InterviewError(
                f"No questions found in '{role}' bank for category '{cat_norm}'."
            )

    rng = random.Random(seed) if seed is not None else random.Random()
    picked = rng.sample(pool, min(count, len(pool)))
    return {
        "role": bank["role"],
        "seed": seed,
        "pool_size": len(pool),
        "questions": picked,
    }


def combine_story_text(story: Dict[str, Any]) -> str:
    """Joins populated STAR fields for Anti-AI prose auditing, omitting placeholders."""
    parts: List[str] = []
    for field in ("situation", "task", "action", "result"):
        val = str(story.get(field) or "").strip()
        if val and not val.startswith(TODO_PLACEHOLDER):
            parts.append(val)
    return " ".join(parts).strip()
