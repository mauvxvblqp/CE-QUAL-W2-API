from __future__ import annotations

import os
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
import tempfile
import shutil

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
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {
        "run_id": run.run_id,
        "status": run.status,
        "workdir": str(run.workdir),
        "started_at": run.started_at,
    }


@app.post("/runs/upload")
async def upload_and_run(file: UploadFile = File(...), name: Optional[str] = None) -> Dict[str, Any]:
    """
    Upload a ZIP of input files and start a run.
    The archive contents are copied into an isolated workdir.
    """
    if not file.filename or not file.filename.lower().endswith('.zip'):
        raise HTTPException(status_code=400, detail="Only .zip files are supported")

    # Save to a temporary file then unpack and delegate to create_run
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_zip = Path(tmpdir) / file.filename
        content = await file.read()
        tmp_zip.write_bytes(content)
        extract_dir = Path(tmpdir) / "extracted"
        extract_dir.mkdir(parents=True, exist_ok=True)
        # Safe unzip to avoid path traversal
        import zipfile
        try:
            with zipfile.ZipFile(tmp_zip, 'r') as zf:
                for member in zf.infolist():
                    # Normalize and check destination
                    member_path = Path(member.filename)
                    if member_path.is_absolute():
                        raise HTTPException(status_code=400, detail="Zip contains absolute paths")
                    dest = (extract_dir / member_path).resolve()
                    if not str(dest).startswith(str(extract_dir.resolve())):
                        raise HTTPException(status_code=400, detail="Zip contains invalid paths (..)")
                    if member.is_dir():
                        dest.mkdir(parents=True, exist_ok=True)
                        continue
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    with zf.open(member, 'r') as src, open(dest, 'wb') as dst:
                        shutil.copyfileobj(src, dst)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to unpack zip: {e}")

        # If the zip contains a single top-level folder, use it; otherwise use extract_dir
        entries = [p for p in extract_dir.iterdir() if p.is_dir() or p.is_file()]
        if len(entries) == 1 and entries[0].is_dir():
            input_root = entries[0]
        else:
            input_root = extract_dir

        try:
            run = manager.create_run(input_root, name=name)
        except FileNotFoundError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except RuntimeError as e:
            raise HTTPException(status_code=500, detail=str(e))

    return {
        "run_id": run.run_id,
        "status": run.status,
        "workdir": str(run.workdir),
        "started_at": run.started_at,
        "source": "upload",
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


@app.get("/runs")
def list_runs() -> Dict[str, Any]:
    ids = manager.list_ids()
    items = []
    for rid in ids:
        r = manager.get(rid)
        if not r:
            continue
        items.append({
            "run_id": rid,
            "name": r.name,
            "status": r.status,
            "created_at": r.created_at,
            "started_at": r.started_at,
            "finished_at": r.finished_at,
            "returncode": r.returncode,
        })
    items.sort(key=lambda x: (x["created_at"] or datetime.min), reverse=True)
    return {"count": len(items), "items": items}


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


@app.get("/health")
def health() -> Dict[str, Any]:
    w2_path = manager.w2_bin
    return {
        "status": "ok",
        "w2_bin": str(w2_path),
        "w2_bin_exists": w2_path.exists(),
        "w2_bin_executable": os.access(w2_path, os.X_OK) if w2_path.exists() else False,
        "runs_root": str(manager.runs_root),
    }

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "8000")))
