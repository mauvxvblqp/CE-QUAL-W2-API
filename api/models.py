from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any


RunStatus = str  # created | running | succeeded | failed | canceled


@dataclass
class ProgressPoint:
    day: int
    hour: float
    percent: float
    step: int
    dt: float
    viol_percent: float
    elapsed_days: float
    line: str
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Run:
    run_id: str
    name: Optional[str]
    workdir: Path
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    status: RunStatus = "created"
    returncode: Optional[int] = None
    stdout_log: Path = field(default=Path())
    error_log: Path = field(default=Path())
    progress_log: Path = field(default=Path())
    artifacts_root: Path = field(default=Path())
    meta: Dict[str, Any] = field(default_factory=dict)
    _progress_points: List[ProgressPoint] = field(default_factory=list)

    def add_progress(self, p: ProgressPoint) -> None:
        self._progress_points.append(p)

    def last_progress(self) -> Optional[ProgressPoint]:
        return self._progress_points[-1] if self._progress_points else None

