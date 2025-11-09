# 运动隐私保护演示系统 (PrivacyKEEP)

一个包含前端 (Vue3 + Vite) 与后端 (FastAPI + SQLite + SQLAlchemy) 的教学/演示项目，展示在运动轨迹场景中应用差分隐私、匿名群组与环签名概念，实现匿名热力图与群组排行榜。当前版本重点在“数据最小化 + 前端差分隐私 + 匿名成绩聚合”，并已为升级真实环签名算法预留结构。

## 当前功能概览

| 模块 | 功能 | 要点 |
|------|------|------|
| 登录与群组 | `/api/user/login` 首次登录分配固定群组 | 稳定 group_name，不因后续请求变化 |
| 差分隐私热力图 | 前端网格化 + 拉普拉斯噪声后仅上传 `{x,y,weight}` | 后端无原始 GPS，纯聚合 |
| 匿名环成绩 | 简化“环签名”占位（SHA-512 长哈希） | 结构可替换为真正环签名 (Roadmap) |
| 群组排行榜 | 按群组聚合平均距离/配速 + 成员数 | 自动种子填充多群组、多成员 |
| 轨迹模拟 | 平滑随机游走（限制最大转向、越界回拉） | 接近自然运动路线，无硬调头 |
| 初始地图视图 | 以起点为中心的 10x10 网格占位 + 后续真实热力图窗口化 | 避免空白闪烁与过度暴露 |
| 数据格式化 | 排行榜距离/配速两位小数 (后端 round + 前端 format2) | 统一展示、防浮点噪点 |
| 提示反馈 | 轻量 Toast（登录 / 群组分配 / 上传成功 / 错误） | 无需额外库，易替换 |
| 数据种子 | 自动填充若空排行榜（可通过 `?seed=false` 禁用） | 演示更丰满，展示匿名聚合价值 |
| SQLite 迁移 | 启动时自动补齐新增列 (group_name / user_anonymous_id) | 无需手动删库，幂等 ALTER |

### Roadmap（即将迭代）

1. 真正环签名 (Ed25519 Schnorr 风格 / LSAG 原型)。
2. k-匿名区块过滤：成员数 < k 的热力格合并或屏蔽。
3. 隐私预算选择 (动态 ε) 与隐私会计。
4. 数据生命周期与定期清理（减少长期重识别风险）。
5. 前端本地真实环签名生成（无私钥上行）。
6. 接入访问控制与速率限制。

## 目录结构

```text
backend/
  app/
    database.py      # 数据库引擎与 SessionLocal
    models.py        # ORM 模型 (User, Ring, HeatmapData, GroupScore)
    schemas.py       # Pydantic 模型
    routers/         # FastAPI 路由 (heatmap, leaderboard, user)
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

## 数据流程概览

1. 运动中：客户端每秒生成当前位置点 → 本地数组（不上传）。
2. 结束：网格化 (gpsToGrid) + 差分隐私处理 (Laplace 噪声) → 净化区块列表。
3. 上传：POST `/api/heatmap/data`（仅 x,y,weight）。
4. 获取/生成环：POST `/api/leaderboard/request-ring` 返回 ring_id + 公钥列表 + 群组名。
5. 生成简化环签名占位（当前：SHA-512 哈希） → POST `/api/leaderboard/submit-score`。
6. 后端聚合：按 group_name 统计平均距离/配速与成员数 → GET `/api/leaderboard`。
7. 地图展示：登录或起点出现时自动缩放到 10x10 方格视窗；若无真实数据显示占位栅格。

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

当前环签名模块为“占位演示”级别：

| 现状 | 描述 |
|------|------|
| 签名形式 | SHA-512 哈希 (长度≥128 hex) 仅作结构验证 |
| 匿名性 | 通过环成员混合公钥 + 不暴露签名者索引提供基本混淆 |
| 验证逻辑 | 长度检查 + 公钥集合规模检查 |
| 缺失能力 | 不具备真实不可链接性 / 防重放 / key image |

Roadmap 将引入：Ed25519 Schnorr 环签名原型 → （可选）MLSAG → 纯前端私钥管理。

## 真实运动统计逻辑

- 距离：采用 Haversine 公式累加相邻点距离。
- 配速：`(elapsed_seconds/60) / total_km`。
- 实时轨迹每秒推进，模拟自然运动节奏。

## 隐私与数据最小化要点

| 层面 | 已采取措施 | 说明 | 后续改进 |
|------|------------|------|----------|
| GPS 原始点 | 不上行 | 上传前网格化 + 加噪 | 可加 k-匿名格过滤 |
| 匿名标识 | `anonymous_id` 随机/可编辑 | 不含真实身份字段 | 增加模式校验防敏感输入 |
| 差分隐私 | Laplace 噪声 (ε=1.0) | 客户端预处理 | 引入隐私预算选择和会计 |
| 环签名 | 混合公钥 + 哈希占位 | 弱匿名演示 | 替换为真实环签名算法 |
| 成绩展示 | 群组平均值 | 无单用户历史接口 | 加入异常值截尾、分箱 |
| 数据库结构 | 仅必要列 | 无地理原始轨迹 | 增加定期归档清理 |
| 初始地图 | 占位 10x10 | 降低空视图泄露 | 起点模糊/延迟显示 |
| 成员计数 | distinct 匿名ID | 避免重复用户放大统计 | 加重复检测与最小阈值 |

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

1. 真正环签名实现（Ed25519 Schnorr / LSAG）。
2. k-匿名与差分隐私预算界面化。
3. 区块时间窗口分层（早晚高峰对比而不暴露单用户）。
4. 单元测试/CI（包括轨迹生成、DP正确性、环验证）。
5. 网格替换为 H3 或 S2 分级空间编码。
6. API 访问控制（JWT + Rate Limiting）。
7. 数据清理策略与合规报告（隐私说明页）。

---
如需脚本自动化演示或测试集成、或希望提前接入真实环签名，请在 issue 中提出或继续对话。
