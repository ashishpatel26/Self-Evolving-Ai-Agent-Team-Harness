"""Persistent file system K (component 3), built on agno.fs.FileSystem (database-backed, durable, versioned).

Layout inside the namespace:  LEARNINGS.md  EVOLUTION.md  teams/vN/{design,scorecard,evals}.json
"""
import json
import re

from agno.fs import FileSystem

from eat.schemas import ScoreCard, TeamDesign


class TeamFS:
    """Thin domain helpers over an Agno FileSystem. Agents get `.fs` directly as `Agent(filesystem=...)`."""

    def __init__(self, db, name: str):
        self.name = name
        self.fs = FileSystem(backend=db, namespace=name)

    def read(self, path: str) -> str:
        return self.fs.read(path) or ""

    def add_learnings(self, version: int, lessons: list[str]) -> None:
        known = self.read("LEARNINGS.md")
        for lesson in lessons:
            if lesson not in known:  # the same failure is not recorded twice
                self.fs.append("LEARNINGS.md", f"- [v{version}] {lesson}\n")

    def log_evolution(self, version: int, reflection: str, design: TeamDesign) -> None:
        self.fs.append("EVOLUTION.md", f"## v{version} -> v{design.version} ({design.coordination})\n{reflection}\n"
                                       f"stages={design.stages}\nrationale: {design.rationale}\n\n")

    def save(self, version: int, name: str, model_or_dict) -> None:
        body = model_or_dict.model_dump_json(indent=2) if hasattr(model_or_dict, "model_dump_json") else json.dumps(model_or_dict, indent=2, default=str)
        self.fs.write(f"teams/v{version}/{name}.json", body)

    def save_team(self, design: TeamDesign, card: ScoreCard | None = None) -> None:
        self.save(design.version, "design", design)
        if card:
            self.save(card.version, "scorecard", card)

    def context_for(self, design: TeamDesign) -> str:
        """What a new team reads before starting: the files its design says to read."""
        return "\n\n".join(f"### {f}\n{self._compact(self.read(f))}" for f in design.reads if self.read(f))

    @staticmethod
    def _compact(text: str, keep: int = 20) -> str:
        """Context management for K: every RULE line plus only the newest observations."""
        lines = text.splitlines()
        rules = [l for l in lines if "RULE:" in l]
        return "\n".join(rules + [l for l in lines if "RULE:" not in l][-keep:])

    def _versions(self, name: str) -> list[int]:
        found = (int(m.group(1)) for f in self.fs.list("teams") if (m := re.match(rf"teams/v(\d+)/{name}\.json", f.path)))
        return sorted(found)

    def history(self) -> list[ScoreCard]:
        return [ScoreCard.model_validate_json(self.read(f"teams/v{v}/scorecard.json")) for v in self._versions("scorecard")]

    def latest_design(self) -> TeamDesign | None:
        versions = self._versions("design")
        return TeamDesign.model_validate_json(self.read(f"teams/v{versions[-1]}/design.json")) if versions else None
