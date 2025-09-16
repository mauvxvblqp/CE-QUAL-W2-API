# Repository Guidelines

## Project Structure & Module Organization
Keep primary Fortran 90 sources in the repository root (`*.f90`). Shared modules belong in `w2modules.f90`; create a new file only for cohesive, reusable module sets. Preprocessor toggles live in `preprocessor_definitions.fpp`. Build artifacts land under `build/obj/` and `build/mod/`; the Linux binary is `./w2_exe_linux`. Windows-specific files remain in `W2 model/` and should not be edited for CLI work.

## Build, Test, and Development Commands
Run `make renames` to normalize file names and extensions before committing. Build the CLI executable with `make w2_exe_linux`; set a custom compiler as needed, e.g., `make FC=/opt/intel/oneapi/compiler/2025.2/bin/ifx w2_exe_linux`. Clean artifacts with `make clean`. Execute the model via `./w2_exe_linux`, ensuring required input data sit in the working directory.

## Coding Style & Naming Conventions
Use free-form Fortran 90 with 2–4 space indentation and line lengths near 100 characters. File names should be lowercase with underscores (run `make renames` to enforce). Gate Windows-only dependencies with the `CLI_ONLY` preprocessor flag. Add concise comments only when logic is non-obvious.

## Testing Guidelines
There is no automated test suite. Validate changes by running benchmark scenarios and comparing mass balance, temperatures, and tracer outputs. Document the input set, expected metrics, and any numeric tolerances alongside your change.

## Commit & Pull Request Guidelines
Write commits with imperative, ≤50-character subjects. Reference issues as `#<id>` when relevant. Pull requests must summarize motivation, list build/run steps, and provide validation evidence (inputs used, before/after metrics). Note any impacts to `CLI_ONLY` or compiler compatibility, and avoid committing proprietary input data or large outputs.

## Security & Configuration Tips
Do not version large binaries or proprietary datasets; rely on `.gitignore`. If Intel libraries are missing at runtime, source `/opt/intel/oneapi/setvars.sh` or specify the full `ifx` path so the linker records the correct runtime library path.
