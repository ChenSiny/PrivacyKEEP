# 运动隐私保护演示系统 (PrivacyKEEP)

一个包含前端 (Vue3 + Vite) 与后端 (FastAPI + SQLite + SQLAlchemy) 的教学/演示项目，展示在运动轨迹场景中应用差分隐私、匿名群组与“教学版”真实环签名（Schnorr-like）验证，实现匿名热力图与群组排行榜。当前版本重点在“数据最小化 + 前端差分隐私 + 教学版环签名 + 匿名成绩聚合”。

## 当前功能概览（基于当前实现）

| 模块 | 功能 | 要点 |
|------|------|------|
| 登录与群组 | `/api/user/login` 首次登录分配固定群组 | 稳定 group_name，不因后续请求变化 |
| 差分隐私热力图 | 前端网格化 + 拉普拉斯噪声后仅上传 `{x,y,weight}` | 后端无原始 GPS，纯聚合 |
| 匿名环成绩 | 教学版真实环签名（Schnorr-like） | 前后端同构：前端 secp256k1 生成签名，后端验证挑战闭合 |
| 群组排行榜 | 按群组聚合平均距离/配速 + 成员数 | 自动种子填充多群组、多成员 |
| 轨迹模拟 | 平滑随机游走（限制最大转向、越界回拉） | 接近自然运动路线，无硬调头 |
| 初始地图视图 | 以起点为中心的 10x10 网格占位 + 后续真实热力图窗口化 | 避免空白闪烁与过度暴露 |
| 数据格式化 | 排行榜距离/配速两位小数 (后端 round + 前端 format2) | 统一展示、防浮点噪点 |
| 提示反馈 | 轻量 Toast（登录 / 群组分配 / 上传成功 / 错误） | 无需额外库，易替换 |
| 数据种子 | 自动填充若空排行榜（可通过 `?seed=false` 禁用） | 演示更丰满，展示匿名聚合价值 |
| SQLite 迁移 | 启动时自动补齐新增列 (group_name / user_anonymous_id) | 无需手动删库，幂等 ALTER |


## 运行环境要求

- Python ≥ 3.10
- Node.js ≥ 16 (建议 18+)

## 后端快速启动（FastAPI）

```bash
cd backend
pip install -r requirements.txt  # 若 coincurve 安装失败仍可运行：它有降级逻辑
uvicorn main:app --reload --port 8000
# 访问: http://localhost:8000/docs 查看接口文档
```

## 前端快速启动（Vite + Vue3）

```bash
cd frontend
npm install
npm run dev
# 访问: http://localhost:3000
```

## 数据流程概览（端到端）

1. 运动中：客户端每秒生成当前位置点 → 本地数组（不上传）。
2. 结束：网格化 (gpsToGrid) + 差分隐私处理 (Laplace 噪声) → 净化区块列表。
3. 上传：POST `/api/heatmap/data`（仅 x,y,weight）。
4. 请求环：POST `/api/leaderboard/request-ring` → 返回 `ring_id` + `ring_public_keys` + `group_name`。
5. 真实环签名：前端以 `ring_id|total_distance|average_pace` 生成 `{c0,s[]}`（secp256k1）。
6. 提交成绩：POST `/api/leaderboard/submit-score-ring`，后端验证挑战闭合 → 入库。
7. 地图/排行榜：右侧浮层展示最新匿名群组排行榜。

## 真实环签名实现（教学版 Schnorr-like）

- 曲线：secp256k1（前端 `@noble/secp256k1`，后端 coincurve）。
- 消息：`ring_id|total_distance|average_pace`（UTF-8 字节串）。
- 生成：`ring_sign(message, priv, ring_pubkeys)` → `(c0, s[])`。
- 验证：`ring_verify(message, ring_pubkeys, c0, s[])` 闭合挑战链 `c`。
- 接口：`POST /api/leaderboard/submit-score-ring`（`ScoreSubmitRing`）。
- 入库：签名以 JSON `{c0,s}` 序列化保存于 `GroupScore.signature`。

差异与限制：未加入 key image、重放防护与抗侧信道；教学用途，勿用于生产安全判定。

## 真实运动统计逻辑（前端计算）

- 距离：采用 Haversine 公式累加相邻点距离。
- 配速：`(elapsed_seconds/60) / total_km`。
- 实时轨迹每秒推进，模拟自然运动节奏。

## 隐私与数据最小化要点（当前）

| 层面 | 已采取措施 | 说明 | 后续改进 |
|------|------------|------|----------|
| GPS 原始点 | 不上行 | 上传前网格化 + 加噪 | 可加 k-匿名格过滤 |
| 匿名标识 | `anonymous_id` 随机/可编辑 | 不含真实身份字段 | 增加模式校验防敏感输入 |
| 差分隐私 | Laplace 噪声 (ε=1.0) | 客户端预处理 | 引入隐私预算选择和会计 |
| 环签名 | 教学版 Schnorr-like | 弱于生产级 | 引入 key image / 防重放 / 更强方案 |
| 成绩展示 | 群组平均值 | 无单用户历史接口 | 加入异常值截尾、分箱 |
| 数据库结构 | 仅必要列 | 无地理原始轨迹 | 增加定期归档清理 |
| 初始地图 | 占位 10x10 | 降低空视图泄露 | 起点模糊/延迟显示 |
| 成员计数 | distinct 匿名ID | 避免重复用户放大统计 | 加重复检测与最小阈值 |
```
