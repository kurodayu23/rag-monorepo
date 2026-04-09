from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from .lobster_skill import LobsterFetcherSkill
from .qt_annotator_skill import QtAnnotatorSkill


@dataclass
class Agent:
    qt_annotator: QtAnnotatorSkill
    lobster: LobsterFetcherSkill

    def run(self, action: str, **kwargs: Any) -> Any:
        """
        A tiny “skill router”.

        This is intentionally small: for portfolio interviews, the point is showing
        how you structure tool-like steps behind a single entry.
        """
        if action == "annotate-qt":
            file_path: str = kwargs["file_path"]
            return self.qt_annotator.execute(file_path)
        if action == "harvest":
            target_range: int = kwargs["target_range"]
            return self.lobster.harvest(target_range=target_range)
        raise ValueError(f"Unknown action: {action}")

