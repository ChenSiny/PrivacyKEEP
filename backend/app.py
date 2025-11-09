from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine
from app import models
from app.routers import heatmap, leaderboard

# 创建数据库表（如果不存在）
# 在实际生产环境中，应该使用Alembic进行数据库迁移
models.Base.metadata.create_all(bind=engine)

# 创建FastAPI应用实例
app = FastAPI(
    title="运动隐私保护系统 API",
    description="""
    ## 运动隐私保护演示系统后端API
    
    ### 系统特色：
    - 前端隐私处理：所有敏感数据（位置坐标）在前端完成隐私处理
    - 差分隐私热力图：使用拉普拉斯机制保护位置隐私
    - 环签名排行榜：使用环签名技术实现可验证的匿名竞争
    - 数据最小化：后端只接收处理后的匿名数据
    
    ### 数据流程：
    1. 热力图数据：前端完成 位置→区块映射 + 差分隐私加噪 → 后端只接收区块编号和权重
    2. 排行榜数据：前端使用环签名 → 后端验证签名真实性 → 存储群体匿名成绩
    
    ### 技术栈：
    - 后端框架：FastAPI
    - 数据库：SQLite + SQLAlchemy ORM
    - 密码学：coincurve（椭圆曲线密码学）
    """,
    version="1.0.0",
    docs_url="/docs",  # Swagger UI文档地址
    redoc_url="/redoc"  # ReDoc文档地址
)

# 配置CORS中间件，允许前端应用访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # 前端开发服务器
        "http://127.0.0.1:3000",
        # 生产环境可以添加实际域名
    ],
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有HTTP方法
    allow_headers=["*"],  # 允许所有HTTP头
)

# 注册API路由
app.include_router(heatmap.router, prefix="/api/heatmap", tags=["热力图"])
app.include_router(leaderboard.router, prefix="/api/leaderboard", tags=["排行榜"])

@app.get("/")
async def root():
    """
    根路径，返回API基本信息
    """
    return {
        "message": "运动隐私保护系统后端服务正常运行",
        "docs": "访问 /docs 查看完整API文档",
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
    """
    健康检查端点，用于监控服务状态
    """
    return {
        "status": "healthy", 
        "service": "sports-privacy-backend",
        "timestamp": "2024-01-01T00:00:00Z"  # 应该使用实际时间戳
    }

# 直接运行脚本时的入口点
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",  # 应用导入路径
        host="0.0.0.0",  # 监听所有网络接口
        port=8000,       # 服务端口
        reload=True      # 开发模式：代码变更时自动重启
    )