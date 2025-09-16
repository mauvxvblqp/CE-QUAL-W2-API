# 运行步骤（API 与本地）

英文版指南: [Quick Start (English)](QuickStart.md)

面向零基础用户的完整步骤，帮助在本机编译、启动 API，并运行 CE‑QUAL‑W2（Linux CLI）。

## 1. 准备环境
- 需要：Linux、Intel oneAPI Fortran (`ifx`)、GNU Make、Python 3.10+。
- 推荐先加载 Intel 环境（可避免链接库问题）：
  - `source /opt/intel/oneapi/setvars.sh`
- 进入仓库根目录并规范化文件名：
  - `make renames`
- 编译二进制：
  - 直接编译：`make w2_exe_linux`
  - 或指定编译器路径：`make FC=/opt/intel/oneapi/compiler/2025.2/bin/ifx w2_exe_linux`
- 验证：`ls -l ./w2_exe_linux` 应存在且可执行。

## 2. 准备输入数据
- 将一套有效的 W2 输入文件放到同一文件夹（例如 `/data/my_case/`），确保包含 `w2_con.npt` 及对应的外部数据文件。
- 记下该绝对路径，后续会用到（示例：`INP_DIR=/data/my_case`）。

## 3. 启动 API 服务
- 创建并安装依赖（不会污染系统环境）：
  - `python3 -m venv api/.venv`
  - `api/.venv/bin/pip install -r requirements.txt`
- 启动服务（默认 8000 端口）：
  - `api/.venv/bin/uvicorn api.main:app --host 0.0.0.0 --port 8000`
- 健康检查（新开一个终端执行）：
  - `curl http://127.0.0.1:8000/health`
  - 返回中 `w2_bin_exists: true` 且 `w2_bin_executable: true` 表示可用。

## 4. 通过 API 启动一次运行
- 使用现有输入目录：
  - `curl -X POST "http://127.0.0.1:8000/runs?input_dir=${INP_DIR}&name=test1"`
  - 返回 JSON 中的 `run_id` 用于后续查询。
- 或上传 ZIP 并运行：
  - `curl -F "file=@/path/to/inputs.zip" "http://127.0.0.1:8000/runs/upload?name=test2"`

## 5. 查询状态、进度与日志
- 运行详情：`curl http://127.0.0.1:8000/runs/<run_id>`
- 进度点：`curl "http://127.0.0.1:8000/runs/<run_id>/progress?limit=100"`
- 实时日志（尾部 200 行）：`curl "http://127.0.0.1:8000/runs/<run_id>/logs/stdout?tail=200"`

## 6. 获取输出文件
- 列表：`curl http://127.0.0.1:8000/runs/<run_id>/artifacts`
- 下载某个文件：`curl -OJ "http://127.0.0.1:8000/runs/<run_id>/artifacts/<相对路径>"`

## 7. 取消运行
- `curl -X POST http://127.0.0.1:8000/runs/<run_id>/cancel`

## 8. 直接运行（不经 API）
- 执行：`./w2_exe_linux /绝对路径/到/输入目录`
- 观察输出：标准输出与 `w2_progress.log`、`w2_error.log`（若出现 NaN 会生成）。

## 9. 常见问题
- 链接库警告 `libintlc.so.5`：先执行 `source /opt/intel/oneapi/setvars.sh`，或编译时使用完整 `ifx` 路径（Makefile 会自动加 rpath）。
- 权限被拒绝：`chmod +x ./w2_exe_linux`。
- 端口占用：更换为 `--port 8001` 并改用对应 URL。
- curl 的 URL 写法与变量替换示例：见 [docs/curl_post_runs_cn.md](curl_post_runs_cn.md)。
