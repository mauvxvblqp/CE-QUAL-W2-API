# 使用 curl 调用 /runs 的正确写法（中文）

本文解释 Bash 报错“错误的替换”的原因，并给出 3 种安全写法。

## 报错原因
你写成了：`${/home/...}`。在 Bash 中，`${...}` 只能放变量名（如 `${INP_DIR}`），不能直接写路径。所以会报“错误的替换”。

你的示例路径：`/home/felix/Codex/03_W2_Linux/DetroitReservoirV422`

## 正确写法（任选其一）

- 方式一（推荐：先定义变量再使用）

```bash
INP_DIR="/home/felix/Codex/03_W2_Linux/DetroitReservoirV422"
curl -X POST "http://127.0.0.1:8000/runs?input_dir=${INP_DIR}&name=test1"
```

- 方式二（直接写死路径）

```bash
curl -X POST "http://127.0.0.1:8000/runs?input_dir=/home/felix/Codex/03_W2_Linux/DetroitReservoirV422&name=test1"
```

- 方式三（更稳妥：自动 URL 编码，适合含空格或中文的路径）

```bash
curl -X POST -G \
  --data-urlencode "input_dir=/home/felix/Codex/03_W2_Linux/DetroitReservoirV422" \
  --data-urlencode "name=test1" \
  "http://127.0.0.1:8000/runs"
```

## 注意事项
- 整段 URL 请用引号包起来（防止 `&` 被 Bash 误解）。
- 路径里如有空格或中文，优先用“方式三”（`--data-urlencode`）。
- 变量替换要么写成 `$INP_DIR` 要么 `${INP_DIR}`，不要 `${/home/...}`。

## 健康检查（可选）
如果仍报错，先确认 API 正常运行：

```bash
curl http://127.0.0.1:8000/health
```

返回里应看到：
- `w2_bin_exists: true`
- `w2_bin_executable: true`

若不是，请先按 docs/RUN_STEPS_CN.md 的“准备环境”和“启动 API 服务”步骤处理。
