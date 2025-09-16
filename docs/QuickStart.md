# Quick Start (English)

Chinese version: [运行步骤（API 与本地）](RUN_STEPS_CN.md)

Follow these steps to build the model, start the HTTP API, and run a case.

## Requirements
- Linux, Intel oneAPI Fortran (ifx), GNU Make, Python 3.10+.
- Optional (recommended): `source /opt/intel/oneapi/setvars.sh` to avoid linker warnings (e.g., libintlc).

## Build the binary
- Normalize filenames: `make renames`
- Build: `make w2_exe_linux`
- Or with explicit compiler path:
  - `make FC=/opt/intel/oneapi/compiler/2025.2/bin/ifx w2_exe_linux`
- Verify: `ls -l ./w2_exe_linux` should exist and be executable.

## Start the API
- Create a virtual environment and install deps:
  - `python3 -m venv api/.venv`
  - `api/.venv/bin/pip install -r requirements.txt`
- Run the server (default: port 8000):
  - `api/.venv/bin/uvicorn api.main:app --host 0.0.0.0 --port 8000`
- Health check (new terminal): `curl http://127.0.0.1:8000/health`
  - Expect `w2_bin_exists: true` and `w2_bin_executable: true`.

## Launch a run
- From an existing input directory (server-side path):
  - `curl -X POST "http://127.0.0.1:8000/runs?input_dir=/abs/path/to/inputs&name=demo"`
- Or upload a ZIP and run:
  - `curl -F "file=@/path/to/inputs.zip" "http://127.0.0.1:8000/runs/upload?name=demo_zip"`

## Inspect and manage
- Status: `curl http://127.0.0.1:8000/runs/<run_id>`
- Progress: `curl "http://127.0.0.1:8000/runs/<run_id>/progress?limit=200"`
- Stdout tail: `curl "http://127.0.0.1:8000/runs/<run_id>/logs/stdout?tail=200"`
- Error log: `curl http://127.0.0.1:8000/runs/<run_id>/logs/error`
- Artifacts list: `curl http://127.0.0.1:8000/runs/<run_id>/artifacts`
- Download artifact: `curl -OJ "http://127.0.0.1:8000/runs/<run_id>/artifacts/<relative_path>"`
- Cancel: `curl -X POST http://127.0.0.1:8000/runs/<run_id>/cancel`

## Notes
- Each run copies inputs into `runs/<run_id>` and executes `./w2_exe_linux <workdir>`.
- Progress is parsed from `w2_progress.log` (also echoed to stdout).
- For `libintlc.so.5` warnings, source oneAPI env or build with a full `ifx` path so rpath is added by the Makefile.
