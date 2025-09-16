from __future__ import annotations

import io
import os
import re
import shutil
import threading
import time
import uuid
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from subprocess import Popen, PIPE, STDOUT
from typing import Dict, Optional, Iterable, Tuple

from .models import Run, ProgressPoint


PROGRESS_RE = re.compile(
    r"^Day\s+(?P<day>\d+)\s+\+\s+(?P<hour>\d+\.\d{2})\s+h\s+"
    r"(?P<percent>\d+\.\d)\%\s+\|\s+step\s+(?P<step>\d+)\s+\|\s+dt\s+"
    r"(?P<dt>[-\dEe+.]+)\s+s\s+\|\s+viol\s+(?P<viol>\d+\.\d)\%\s+\|\s+elapsed\s+"
    r"(?P<elapsed>\d+\.\d)\s+d$"
)


class RunManager:
    def __init__(self, repo_root: Path) -> None:
        self.repo_root = repo_root
        self.runs_root = repo_root / "runs"
        self.runs_root.mkdir(parents=True, exist_ok=True)
        self.w2_bin = (repo_root / "w2_exe_linux").resolve()
        self._lock = threading.Lock()
        self._runs: Dict[str, Run] = {}
        self._procs: Dict[str, Popen] = {}

    def _new_run_id(self) -> str:
        return uuid.uuid4().hex[:12]

    def create_run(self, input_dir: Path, name: Optional[str] = None, copy_inputs: bool = True) -> Run:
        if not input_dir.exists() or not input_dir.is_dir():
            raise FileNotFoundError(f"input_dir does not exist or is not a directory: {input_dir}")

        run_id = self._new_run_id()
        workdir = self.runs_root / run_id
        workdir.mkdir(parents=True, exist_ok=False)

        # Copy inputs into isolated workdir (MVP: simple copy; future: support zip/symlink)
        if copy_inputs:
            for p in input_dir.iterdir():
                dst = workdir / p.name
                if p.is_dir():
                    shutil.copytree(p, dst)
                else:
                    shutil.copy2(p, dst)

        stdout_log = workdir / "stdout.log"
        error_log = workdir / "w2_error.log"  # produced by model if NaN
        progress_log = workdir / "w2_progress.log"  # produced by model

        run = Run(
            run_id=run_id,
            name=name,
            workdir=workdir,
            status="created",
            stdout_log=stdout_log,
            error_log=error_log,
            progress_log=progress_log,
            artifacts_root=workdir,
        )
        with self._lock:
            self._runs[run_id] = run

        self._start_run(run)
        return run

    def _start_run(self, run: Run) -> None:
        # Launch process with workdir arg; set cwd to workdir as well
        cmd = [str(self.w2_bin), str(run.workdir)]
        env = os.environ.copy()
        run.status = "running"
        run.started_at = datetime.utcnow()

        proc = Popen(cmd, cwd=run.workdir, stdout=PIPE, stderr=STDOUT, text=True, bufsize=1)
        run.meta["pid"] = proc.pid
        with self._lock:
            self._procs[run.run_id] = proc

        t_stdout = threading.Thread(target=self._pump_stdout, args=(run, proc), daemon=True)
        t_progress = threading.Thread(target=self._tail_progress, args=(run,), daemon=True)
        t_wait = threading.Thread(target=self._wait_and_finalize, args=(run, proc), daemon=True)
        t_stdout.start()
        t_progress.start()
        t_wait.start()

        # Keep references to threads in meta for optional join/debug
        run.meta["threads"] = {
            "stdout": t_stdout.name,
            "progress": t_progress.name,
            "wait": t_wait.name,
        }

    def _pump_stdout(self, run: Run, proc: Popen) -> None:
        run.stdout_log.parent.mkdir(parents=True, exist_ok=True)
        with open(run.stdout_log, "a", encoding="utf-8", newline="\n") as f:
            if proc.stdout is None:
                return
            for line in proc.stdout:
                f.write(line)
                f.flush()

    def _tail_progress(self, run: Run) -> None:
        # Poll progress log; append parsed points
        pos = 0
        while True:
            # Stop when run is finalized and no new progress available
            if run.status in {"succeeded", "failed", "canceled"} and not run.progress_log.exists():
                break
            try:
                with open(run.progress_log, "r", encoding="utf-8", errors="ignore") as f:
                    f.seek(pos)
                    for raw in f:
                        raw = raw.rstrip("\n")
                        p = self._parse_progress_line(raw)
                        if p:
                            run.add_progress(p)
                    pos = f.tell()
            except FileNotFoundError:
                # Not yet created; wait and retry
                pass

            time.sleep(0.5)

    def _wait_and_finalize(self, run: Run, proc: Popen) -> None:
        rc = proc.wait()
        run.returncode = rc
        run.finished_at = datetime.utcnow()
        if run.status != "canceled":
            run.status = "succeeded" if rc == 0 else "failed"
        with self._lock:
            self._procs.pop(run.run_id, None)

    def _parse_progress_line(self, line: str) -> Optional[ProgressPoint]:
        m = PROGRESS_RE.match(line.strip())
        if not m:
            return None
        try:
            return ProgressPoint(
                day=int(m.group("day")),
                hour=float(m.group("hour")),
                percent=float(m.group("percent")),
                step=int(m.group("step")),
                dt=float(m.group("dt")),
                viol_percent=float(m.group("viol")),
                elapsed_days=float(m.group("elapsed")),
                line=line,
            )
        except Exception:
            return None

    # Public query methods
    def get(self, run_id: str) -> Optional[Run]:
        with self._lock:
            return self._runs.get(run_id)

    def list_ids(self) -> Iterable[str]:
        with self._lock:
            return list(self._runs.keys())

    def cancel(self, run_id: str) -> bool:
        run = self.get(run_id)
        if not run:
            return False
        proc = self._procs.get(run_id)
        if proc and proc.poll() is None:
            try:
                proc.terminate()
            except Exception:
                pass
        run.status = "canceled"
        run.finished_at = datetime.utcnow()
        return True
