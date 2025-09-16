# This is a port of the CE-QUAL-W2 model to linux
Original content is available on http://www.ce.pdx.edu/w2/
Note, the branch 'vanilla' contains the non-modified code, and master branch contains the patched code.
Appropriate tags (per release) are placed on all branches (currently v4.1)

## 快速入口
- 快速开始（中文）: [docs/RUN_STEPS_CN.md](docs/RUN_STEPS_CN.md)
- Quick Start (English): [docs/QuickStart.md](docs/QuickStart.md)
- API 文档（Swagger UI）: http://127.0.0.1:8000/docs
- 贡献者指南: [AGENTS.md](AGENTS.md)
- curl 调用示例（中文）: [docs/curl_post_runs_cn.md](docs/curl_post_runs_cn.md)

## Changes from vanilla version
1. Added a preprocessor flag to remove any dependency on windows UI contents
1. Added a Makefile to compile on Linux

## Instructions for compiling windows CLI only:
1. Create a new release type in the VS project, and enable the preprocessor flag `CLI_ONLY=1`

## Instructions for compiling in Linux:
1. Install Intel oneAPI ifx (LLVM Fortran) and GNU Make.
1. Ensure `ifx` is on your PATH, or pass it explicitly with `FC`.
1. Run `make renames` — normalizes source names (fixes `.F90`→`.f90`, spaces→`_`).
1. Build: `make w2_exe_linux` or `make FC=/opt/intel/oneapi/compiler/2025.2/bin/ifx w2_exe_linux`.
   - Artifacts: objects in `build/obj/`, module files in `build/mod/`, binary `./w2_exe_linux`.
   - If you see linker warnings about `libintlc.so.5`, either source oneAPI env (`source /opt/intel/oneapi/setvars.sh`) or pass an explicit compiler path via `FC`. The Makefile will add an rpath to the compiler `lib` directory when `FC` points to `.../bin/ifx`.

## CLI progress (Linux builds)
- When built for CLI (`CLI_ONLY`), the model prints an in-place progress line to stdout during runs (day/hour, percent, step, `dt`).
- A simple run log `w2_progress.log` is also written in the working directory for later inspection.
- Progress output is updated at the same cadence as the existing screen update logic.

Fields shown:
- `Day <d> + <h> h` — simulated day and hour.
- `<percent>%` — progress between `TMSTRT` and `TMEND`.
- `step <NIT>` and `dt <DLT> s` — current step index and timestep.
- `viol <NV/NIT*100%>` — percentage of timestep constraint violations.
- `elapsed <ELTMJD> d` — elapsed simulated days since start.

NaN diagnostics (CLI):
- If a NaN is detected in core state arrays, the model appends a record to `w2_error.log` and writes a full restart snapshot to `w2_nan_rso.opt`, then stops. The snapshot contains the full model state needed for debugging/restarts.

## Known issues:
1. Compiling with gfortran doesn't work due to syntax used for some of the printouts
1. Compiling and linking with OpenMP and MKL is causing some issues right now. These flags are noted in the Makefile but are currently disabled (if enabling with ifx, use `-qopenmp` and consider `-qmkl`).

## API Runner (MVP)
- A minimal HTTP API is provided in `api/` to launch and monitor CLI runs of `w2_exe_linux`.
- Tech: FastAPI + Uvicorn; subprocess-based execution with per-run working directories under `runs/`.

Usage:
- Install deps in venv:
  - `python3 -m venv api/.venv && api/.venv/bin/pip install -r requirements.txt`
- Start API: `api/.venv/bin/uvicorn api.main:app --host 0.0.0.0 --port 8000`
- Swagger UI: http://127.0.0.1:8000/docs

Examples (curl):
- Create run (existing dir):
  - `curl -X POST "http://127.0.0.1:8000/runs?input_dir=/abs/path/to/inputs&name=test1"`
- Upload ZIP and run:
  - `curl -F "file=@/path/to/inputs.zip" "http://127.0.0.1:8000/runs/upload?name=test2"`
- Status: `curl http://127.0.0.1:8000/runs/<run_id>`
- Progress: `curl "http://127.0.0.1:8000/runs/<run_id>/progress?limit=200"`
- Stdout (tail): `curl "http://127.0.0.1:8000/runs/<run_id>/logs/stdout?tail=200"`
- Error log: `curl http://127.0.0.1:8000/runs/<run_id>/logs/error`
- Artifacts list: `curl http://127.0.0.1:8000/runs/<run_id>/artifacts`
- Download artifact: `curl -OJ "http://127.0.0.1:8000/runs/<run_id>/artifacts/<relative_path>"`
- Cancel: `curl -X POST http://127.0.0.1:8000/runs/<run_id>/cancel`

Notes:
- Each run copies the contents of the specified `input_dir` into an isolated working directory under `runs/{run_id}` and executes `w2_exe_linux {workdir}` with `cwd=workdir`.
- Progress is parsed from `w2_progress.log` and also available in `stdout.log`.
- This MVP maintains run state in-memory; consider adding persistence and resource limits for production.
