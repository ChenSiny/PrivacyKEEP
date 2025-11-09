# 运动隐私保护演示系统

一个包含前端 (Vue3 + Vite) 与后端 (FastAPI + SQLite + SQLAlchemy) 的教学/演示项目，展示如何在运动轨迹场景中应用差分隐私与环签名概念，实现匿名热力图与排行榜。

## 功能概览

- 差分隐私热力图：前端将轨迹点映射到网格并添加噪声，仅上传区块编号与加噪权重。
- 环签名排行榜（简化版）：模拟环的公钥集合与“签名”验证逻辑，实现匿名成绩提交。
- 实时轨迹模拟：前端以真实时间节奏（约 5–8 米/秒）生成虚拟跑步轨迹并动态计算距离/配速。
- 预置演示数据：后端在没有真实热力图数据时返回一组示例区块，便于首次展示。

## 目录结构

```text
backend/
  app/
    database.py      # 数据库引擎与 SessionLocal
    models.py        # ORM 模型 (User, Ring, HeatmapData, GroupScore)
    schemas.py       # Pydantic 模型
    routers/         # FastAPI 路由 (heatmap, leaderboard)
    services/        # 服务层 (heatmap, ring, crypto)
  main.py            # FastAPI 应用入口
frontend/
  src/               # Vue3 组件与工具
    views/DemoView.vue
    components/MapComponent.vue, DataCards.vue 等
    utils/ (api.js, gps.js, crypto.js, dp.js)
```

## 运行环境要求

- Python ≥ 3.10
- Node.js ≥ 16 (建议 18+)

## 后端快速启动

```bash
cd backend
pip install -r requirements.txt  # 若 coincurve 安装失败仍可运行：它有降级逻辑
uvicorn main:app --reload --port 8000
# 访问: http://localhost:8000/docs 查看接口文档
```

## 前端快速启动

```bash
cd frontend
npm install
npm run dev
# 访问: http://localhost:3000
```

## 主要数据流程

1. 前端实时生成虚拟轨迹点 (每秒 1 个)。
2. 运动结束后：
  - 轨迹点网格化 → 添加拉普拉斯噪声 (差分隐私)
  - 上传 `/api/heatmap/data` 仅包含 { x, y, weight }
3. 请求环 `/api/leaderboard/request-ring` 获得 ring_id 与环公钥集合。
4. 构造成绩消息并生成模拟环签名 (浏览器 SHA-512 十六进制占位)。
5. 提交成绩 `/api/leaderboard/submit-score`，后端验证格式与环存在性后存储。
6. 获取排行榜与聚合热力图展示。

## 关键接口示例 (curl)

```bash
# 上传热力图数据
curl -X POST http://localhost:8000/api/heatmap/data \
  -H 'Content-Type: application/json' \
  -d '{"anonymous_id":"demoUser","data":[{"x":100,"y":100,"weight":3.2}]}'

# 请求环
curl -X POST http://localhost:8000/api/leaderboard/request-ring \
  -H 'Content-Type: application/json' \
  -d '{"anonymous_id":"demoUser","public_key":"mock_pub_123","user_level":"medium"}'

# 提交成绩 (伪签名示例)
curl -X POST http://localhost:8000/api/leaderboard/submit-score \
  -H 'Content-Type: application/json' \
  -d '{"ring_id":"<替换实际ring_id>","total_distance":2.5,"average_pace":6.2,"signature":"'$(python - <<'PY'
import hashlib;print(hashlib.sha512(b'demo').hexdigest())
PY)'"}'
```

## 环签名与安全简化说明

- 当前实现使用 SHA-512 生成的十六进制字符串作为“模拟签名”，用于接口演示。
- 真实场景需替换为正式环签名算法 (例如 LSAG / BLS 变体)。
- 前端与后端均不存储真实用户身份，仅使用 `anonymous_id`。数据库中公钥列表随机打乱以增强匿名性。

## 真实运动统计逻辑

- 距离：采用 Haversine 公式累加相邻点距离。
- 配速：`(elapsed_seconds/60) / total_km`。
- 实时轨迹每秒推进，模拟自然运动节奏。

## 隐私注意事项 (教学场景)

| 层面 | 措施 | 说明 |
|------|------|------|
| 位置信息 | 网格化 + 差分隐私 | 不发送原始 GPS 坐标 |
| 排行榜 | 环签名匿名成绩 | 不关联真实用户身份 |
| 数据最小化 | 仅区块与权重 | 减少敏感数据面 |

## 常见问题

1. 环签名 400/422：前端需刷新并确保签名为 128 位十六进制；查看浏览器 console 是否有 `await`。
2. 地图 NaN 错误：确保轨迹点生成后不为空；已添加防护逻辑。
3. `coincurve` 安装失败：使用了降级路径，不影响启动。

## 发布到 GitHub

```bash
# 位于项目根目录 /prodemo
git init
# 确认已生成 .gitignore 和 README.md
git add .
git commit -m "feat: initial import of sports privacy demo"
# 在 GitHub 创建空仓库 (例如: yourname/sports-privacy-demo)，然后：
git branch -M main
git remote add origin git@github.com:yourname/sports-privacy-demo.git
# 或 https:// 替换为 SSH
# 推送
git push -u origin main
```

## 后续可扩展方向

- 引入真正的环签名库 (Crypto升级)。
- 增加用户会话与 API Key 访问控制。
- 添加单元测试与 CI。
- 使用更精确的网格或地理编码方案（如 S2 / H3）。

---
如需脚本自动化演示或测试集成，请在 issue 中提出或继续对话。
