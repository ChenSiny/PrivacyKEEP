from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine
from app import models
from app.routers import heatmap, leaderboard

# 创建数据库表（如果不存在）
models.Base.metadata.create_all(bind=engine)

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
