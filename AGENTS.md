# Repository Guidelines

## Project Structure & Module Organization
Primary Fortran 90 sources live in the repository root (e.g., `model_driver.f90`). Shared modules belong in `w2modules.f90`; introduce a new file only when adding a cohesive module package. Preprocessor toggles go into `preprocessor_definitions.fpp`. Compiled objects land under `build/obj/` and module files under `build/mod/`. Linux artifacts target the `w2_exe_linux` executable in the project root. Windows-only assets remain in `W2 model/` and should not be touched for CLI work.

## Build, Test, and Development Commands
Run `make renames` to normalize file names and extensions before committing. Build the CLI binary with `make w2_exe_linux`; override the compiler when needed (e.g., `make FC=/opt/intel/oneapi/compiler/2025.2/bin/ifx w2_exe_linux`). Clean artifacts via `make clean`. Execute the model with `./w2_exe_linux`, ensuring required input datasets sit beside the binary. Source `/opt/intel/oneapi/setvars.sh` if Intel runtime libraries are missing.

## Coding Style & Naming Conventions
Write free-form Fortran 90 with 2–4 space indentation and ~100-character lines. Keep filenames lowercase with underscores—re-run `make renames` if unsure. Gate Windows-specific logic behind the `CLI_ONLY` preprocessor flag. Add concise comments only where logic is non-obvious; favor self-documenting procedures otherwise.

## Testing Guidelines
There is no automated test harness. Validate changes by running benchmark scenarios and comparing mass balance, temperature, and tracer outputs against known baselines. Document the input set, expected metrics, and any numeric tolerances in your change notes so reviewers can reproduce results.

## Commit & Pull Request Guidelines
Use imperative commit subjects ≤50 characters and reference issues as `#<id>` when applicable. Pull requests should explain motivation, enumerate build/run steps (`make renames`, `make w2_exe_linux`, execution command), and summarize validation evidence (inputs, before/after metrics, tolerances). Note any effects on `CLI_ONLY` behavior or compiler compatibility. Do not commit large binaries or proprietary datasets—ensure outputs stay out of version control.

## Security & Configuration Tips
Rely on the existing `.gitignore` to exclude build artifacts. Avoid versioning external datasets; instead, document where to obtain them. When linking with Intel toolchains, prefer full compiler paths so the runtime library path is embedded correctly.
