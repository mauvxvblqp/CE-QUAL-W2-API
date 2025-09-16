# W2 Runner API 部署步骤

## 1. 准备环境
- 目标服务器安装 Linux (Ubuntu/Debian 示例)。需要 Python 3.10+ 和 Fortran 编译器。
- 更新系统并装工具：`sudo apt update && sudo apt install git build-essential python3-venv unzip`。
- 若使用 Intel OneAPI，按官方指引安装并执行 `source /opt/intel/oneapi/setvars.sh` 以启用 ifx 及运行库。

## 2. 获取代码并编译模型
- 创建部署目录：`mkdir -p /opt/w2 && cd /opt/w2`。
- 克隆仓库：`git clone https://<your-repo-url>.git CE-QUAL-W2-Linux && cd CE-QUAL-W2-Linux`。
- 首次运行 `make renames` 规范文件名大小写。
- 编译 Linux 可执行文件：
  - Intel 编译器：`make FC=/opt/intel/oneapi/compiler/2025.2/bin/ifx w2_exe_linux`
  - 或默认编译器：`make w2_exe_linux`
- 构建完成后确认 `./w2_exe_linux` 存在且 `chmod +x w2_exe_linux` 不报错。

## 3. 配置 Python API
- 创建虚拟环境：`python3 -m venv .venv && source .venv/bin/activate`。
- 安装依赖：`pip install --upgrade pip && pip install -r requirements.txt`。
- 创建运行目录：`mkdir -p runs`，API 会把每次模拟的输入与输出写到这里。

## 4. 本地验证与调试
- 启动开发服务：`UVICORN_PORT=8000 uvicorn api.main:app --host 0.0.0.0 --port ${UVICORN_PORT:-8000}`。
- 使用 `curl http://127.0.0.1:8000/health` 检查返回信息：`w2_bin_exists` 为 true 表示模型可执行文件可用。
- 准备一个包含 W2 输入文件的目录或 zip，调用 `/runs` 或 `/runs/upload` 验证可创建运行任务。

## 5. 以 systemd 守护进程运行
- 创建系统用户及目录权限，例如：`sudo useradd -r -m -d /opt/w2 w2` 并 `sudo chown -R w2:w2 /opt/w2/CE-QUAL-W2-Linux`。
- 新建 `/etc/systemd/system/w2-api.service`：
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
- 重新加载并启动：`sudo systemctl daemon-reload && sudo systemctl enable --now w2-api.service`。
- 查看日志：`sudo journalctl -u w2-api.service -f`。

## 6. 配置 Nginx 反向代理与 HTTPS（可选）
- 安装 Nginx：`sudo apt install nginx`。
- 在 `/etc/nginx/sites-available/w2-api` 配置反向代理，将 80/443 转发到 `127.0.0.1:8000`。
- 使用 Let’s Encrypt 获取证书：`sudo certbot --nginx -d your.domain.com`。
- 软链启用并重载：`sudo ln -s /etc/nginx/sites-available/w2-api /etc/nginx/sites-enabled/ && sudo nginx -t && sudo systemctl reload nginx`。

## 7. 更新与维护
- 更新代码：
  ```
  cd /opt/w2/CE-QUAL-W2-Linux
  git pull
  make w2_exe_linux
  source .venv/bin/activate
  pip install -r requirements.txt
  sudo systemctl restart w2-api.service
  ```
- 监控 `runs/` 目录磁盘占用，定期归档或清理旧运行。
- 若出现 Intel 运行时库缺失，检查 `LD_LIBRARY_PATH` 或在 systemd 服务中显式调用 `setvars.sh`。
