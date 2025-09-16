from __future__ import annotations

import os
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

from fastapi import FastAPI, HTTPException, UploadFile, File, Query
from fastapi.responses import FileResponse, PlainTextResponse, JSONResponse

from .manager import RunManager


repo_root = Path(__file__).resolve().parents[1]
manager = RunManager(repo_root)

app = FastAPI(title="W2 Runner API", version="0.1.0")


@app.post("/runs")
def create_run(input_dir: str, name: Optional[str] = None) -> Dict[str, Any]:
    """
    Create a new run from an existing input directory on the server.
    """
    p = Path(input_dir).expanduser().resolve()
    try:
        run = manager.create_run(p, name=name)
    except FileNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {
        "run_id": run.run_id,
        "status": run.status,
        "workdir": str(run.workdir),
        "started_at": run.started_at,
    }


@app.get("/runs/{run_id}")
def get_run(run_id: str) -> Dict[str, Any]:
    run = manager.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="run not found")
    lp = run.last_progress()
    return {
        "run_id": run.run_id,
        "name": run.name,
        "status": run.status,
        "created_at": run.created_at,
        "started_at": run.started_at,
        "finished_at": run.finished_at,
        "returncode": run.returncode,
        "workdir": str(run.workdir),
        "stdout_log": str(run.stdout_log),
        "error_log": str(run.error_log),
        "progress_log": str(run.progress_log),
        "last_progress": {
            "day": lp.day,
            "hour": lp.hour,
            "percent": lp.percent,
            "step": lp.step,
            "dt": lp.dt,
            "viol_percent": lp.viol_percent,
            "elapsed_days": lp.elapsed_days,
            "line": lp.line,
            "timestamp": lp.timestamp,
        } if lp else None,
    }


@app.get("/runs/{run_id}/progress")
def get_progress(run_id: str, limit: int = Query(200, ge=1, le=5000)) -> Dict[str, Any]:
    run = manager.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="run not found")
    pts = run._progress_points[-limit:]
    return {
        "count": len(pts),
        "items": [
            {
                "day": p.day,
                "hour": p.hour,
                "percent": p.percent,
                "step": p.step,
                "dt": p.dt,
                "viol_percent": p.viol_percent,
                "elapsed_days": p.elapsed_days,
                "timestamp": p.timestamp,
            }
            for p in pts
        ],
    }


@app.get("/runs/{run_id}/logs/stdout", response_class=PlainTextResponse)
def get_stdout(run_id: str, tail: Optional[int] = Query(None, ge=1, le=100000)):
    run = manager.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="run not found")
    if not run.stdout_log.exists():
        return ""
    data = run.stdout_log.read_text(encoding="utf-8", errors="ignore")
    if tail is not None:
        lines = data.splitlines()[-tail:]
        return "\n".join(lines) + ("\n" if lines else "")
    return data


@app.get("/runs/{run_id}/logs/error", response_class=PlainTextResponse)
def get_error(run_id: str):
    run = manager.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="run not found")
    if not run.error_log.exists():
        return ""
    return run.error_log.read_text(encoding="utf-8", errors="ignore")


@app.get("/runs/{run_id}/artifacts")
def list_artifacts(run_id: str, prefix: Optional[str] = None) -> Dict[str, Any]:
    run = manager.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="run not found")
    base = run.artifacts_root
    items = []
    for p in base.rglob("*"):
        if not p.is_file():
            continue
        rel = p.relative_to(base).as_posix()
        if prefix and not rel.startswith(prefix):
            continue
        st = p.stat()
        items.append({
            "path": rel,
            "size": st.st_size,
            "mtime": datetime.fromtimestamp(st.st_mtime).isoformat(),
        })
    items.sort(key=lambda x: x["path"]) 
    return {"count": len(items), "items": items}


@app.get("/runs/{run_id}/artifacts/{path:path}")
def get_artifact(run_id: str, path: str):
    run = manager.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="run not found")
    base = run.artifacts_root
    candidate = (base / path).resolve()
    # Prevent path traversal
    if not str(candidate).startswith(str(base.resolve())):
        raise HTTPException(status_code=400, detail="invalid path")
    if not candidate.exists() or not candidate.is_file():
        raise HTTPException(status_code=404, detail="file not found")
    return FileResponse(path=str(candidate))


@app.post("/runs/{run_id}/cancel")
def cancel_run(run_id: str) -> Dict[str, Any]:
    ok = manager.cancel(run_id)
    if not ok:
        raise HTTPException(status_code=404, detail="run not found")
    run = manager.get(run_id)
    return {"run_id": run_id, "status": run.status}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "8000")))
