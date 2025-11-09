from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine
from app import models
from app.routers import heatmap, leaderboard
from app.routers import user as user_router
from sqlalchemy import text

# 创建数据库表（如果不存在）
models.Base.metadata.create_all(bind=engine)

def run_sqlite_migrations():
    """在应用启动时执行轻量级SQLite迁移，补齐新增字段。"""
    try:
        with engine.connect() as conn:
            # users 表：group_name 字段
            cols = conn.execute(text("PRAGMA table_info(users);")).fetchall()
            col_names = {c[1] for c in cols}
            if 'group_name' not in col_names:
                conn.execute(text("ALTER TABLE users ADD COLUMN group_name VARCHAR(100);"))

            # group_scores 表：group_name、user_anonymous_id 字段
            cols = conn.execute(text("PRAGMA table_info(group_scores);")).fetchall()
            col_names = {c[1] for c in cols}
            if 'group_name' not in col_names:
                conn.execute(text("ALTER TABLE group_scores ADD COLUMN group_name VARCHAR(100);"))
            if 'user_anonymous_id' not in col_names:
                conn.execute(text("ALTER TABLE group_scores ADD COLUMN user_anonymous_id VARCHAR(100);"))
    except Exception as e:
        # 迁移失败不应阻断服务，但记录日志
        print(f"[WARN] SQLite migrations failed: {e}")

run_sqlite_migrations()

app = FastAPI(
    title="运动隐私保护系统 API",
    description="""
    ## 运动隐私保护演示系统后端API

    - 前端差分隐私：GPS→区块 + 拉普拉斯加噪
    - 热力图：只存储匿名区块加权
    - 环签名：模拟匿名成绩验证
    - 数据最小化：不接收原始轨迹
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(heatmap.router, prefix="/api/heatmap", tags=["热力图"])
app.include_router(leaderboard.router, prefix="/api/leaderboard", tags=["排行榜"])
app.include_router(user_router.router, prefix="/api/user", tags=["用户"])

@app.get("/")
async def root():
    return {
        "message": "运动隐私保护系统后端服务正常运行",
        "docs": "/docs",
        "endpoints": {
            "heatmap": {
                "GET /api/heatmap/": "获取热力图数据",
                "POST /api/heatmap/data": "上传热力图数据"
            },
            "leaderboard": {
                "POST /api/leaderboard/request-ring": "请求匿名环",
                "POST /api/leaderboard/submit-score": "提交环签名成绩",
                "GET /api/leaderboard/": "获取群体排行榜"
            },
            "user": {
                "POST /api/user/login": "用户登录（首次分配固定队伍）"
            }
        }
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "sports-privacy-backend"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
