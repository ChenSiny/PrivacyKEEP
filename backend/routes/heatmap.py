from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import HeatmapDataCreate, HeatmapDataResponse
from app.services.heatmap_service import HeatmapService

# 创建热力图相关的API路由
router = APIRouter()

@router.post("/data", response_model=dict)
async def upload_heatmap_data(
    data: HeatmapDataCreate,
    db: Session = Depends(get_db)
):
    """
    上传差分隐私处理后的热力图数据
    
    - 前端已经完成位置坐标到区块编号的映射
    - 前端已经添加拉普拉斯噪声实现差分隐私
    - 后端直接存储处理后的区块数据和权重
    
    Args:
        data: 包含匿名ID和区块数据的请求体
        db: 数据库会话依赖注入
        
    Returns:
        dict: 上传结果消息
    """
    try:
        # 调用服务层存储热力图数据
        HeatmapService.store_heatmap_data(db, data.anonymous_id, data.data)
        return {
            "message": "热力图数据上传成功", 
            "status": "success",
            "description": "数据已通过差分隐私保护并存储"
        }
    except Exception as e:
        # 记录错误并返回用户友好的错误信息
        raise HTTPException(
            status_code=500, 
            detail=f"数据上传失败: {str(e)}"
        )

@router.get("/", response_model=dict)
async def get_heatmap(db: Session = Depends(get_db)):
    """
    获取全局热力图数据
    
    返回所有用户贡献的聚合热力图数据
    - x, y: 区块编号（非具体GPS坐标）
    - weight: 聚合后的权重值（已包含差分隐私保护）
    
    Args:
        db: 数据库会话依赖注入
        
    Returns:
        dict: 包含热力图数据的响应
    """
    try:
        heatmap_data = HeatmapService.get_global_heatmap(db)
        return {
            "heatmap": heatmap_data,
            "description": "全局热力图数据，已通过差分隐私保护"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"获取热力图数据失败: {str(e)}"
        )