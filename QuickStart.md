# QuickStart

## Prerequisites
- Linux host (Ubuntu/Debian examples) with Python 3.10+ and a Fortran compiler.
- Install base tools: `sudo apt update && sudo apt install git build-essential python3-venv unzip`.
- Optional but recommended: install Intel OneAPI, then run `source /opt/intel/oneapi/setvars.sh` so `ifx` and runtime libraries are available.

## Clone and Build CE-QUAL-W2
- Prepare a workspace: `mkdir -p /opt/w2 && cd /opt/w2`.
- Clone the repo: `git clone https://<your-repo-url>.git CE-QUAL-W2-Linux && cd CE-QUAL-W2-Linux`.
- Normalize file names: `make renames`.
- Compile the Linux binary:
  - With Intel: `make FC=/opt/intel/oneapi/compiler/2025.2/bin/ifx w2_exe_linux`
  - Or default: `make w2_exe_linux`
- Verify `./w2_exe_linux` exists and is executable.

## Set Up the API Environment
- Create a venv: `python3 -m venv .venv && source .venv/bin/activate`.
- Install Python deps: `pip install --upgrade pip && pip install -r requirements.txt`.
- Create the run workspace: `mkdir -p runs` (the API copies inputs and outputs here).

## Smoke Test Locally
- Start uvicorn: `UVICORN_PORT=8000 uvicorn api.main:app --host 0.0.0.0 --port ${UVICORN_PORT:-8000}`.
- Check health: `curl http://127.0.0.1:8000/health` should report `w2_bin_exists: true`.
- Use an input folder or .zip and call `/runs` or `/runs/upload` to confirm a run can start and logs appear under `runs/<run-id>/`.

## Run as a System Service
- Create a dedicated user and own the install path, e.g. `sudo useradd -r -m -d /opt/w2 w2` plus `sudo chown -R w2:w2 /opt/w2/CE-QUAL-W2-Linux`.
- Add `/etc/systemd/system/w2-api.service`:
  ```
  [Unit]
  Description=W2 Runner API
  After=network.target

  [Service]
  Type=simple
  WorkingDirectory=/opt/w2/CE-QUAL-W2-Linux
  Environment="PATH=/opt/w2/CE-QUAL-W2-Linux/.venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin"
  Environment="LD_LIBRARY_PATH=/opt/intel/oneapi/compiler/2025.2/lib"
  ExecStart=/opt/w2/CE-QUAL-W2-Linux/.venv/bin/uvicorn api.main:app --host 0.0.0.0 --port 8000
  Restart=on-failure
  User=w2
  Group=w2

  [Install]
  WantedBy=multi-user.target
  ```
- Enable and start: `sudo systemctl daemon-reload && sudo systemctl enable --now w2-api.service`.
- Tail logs: `sudo journalctl -u w2-api.service -f`.

## Optional: Reverse Proxy & HTTPS
- Install Nginx: `sudo apt install nginx`.
- Configure `/etc/nginx/sites-available/w2-api` to proxy 80/443 to `127.0.0.1:8000`.
- Obtain TLS certs with Let’s Encrypt: `sudo certbot --nginx -d your.domain.com`.
- Enable the site and reload Nginx: `sudo ln -s /etc/nginx/sites-available/w2-api /etc/nginx/sites-enabled/ && sudo nginx -t && sudo systemctl reload nginx`.

## Updates and Maintenance
- To deploy new code:
  ```
  cd /opt/w2/CE-QUAL-W2-Linux
  git pull
  make w2_exe_linux
  source .venv/bin/activate
  pip install -r requirements.txt
  sudo systemctl restart w2-api.service
  ```
- Watch disk usage of `runs/` and archive or delete old case directories.
- If Intel runtime libraries cannot be found, double-check `LD_LIBRARY_PATH` or call `setvars.sh` within the systemd unit.
