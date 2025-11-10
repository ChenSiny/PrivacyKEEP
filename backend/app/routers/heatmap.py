from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import HeatmapDataCreate
from app.services.heatmap_service import HeatmapService

# 创建热力图相关的API路由
router = APIRouter()

@router.post("/data", response_model=dict)
async def upload_heatmap_data(
    data: HeatmapDataCreate,
    db: Session = Depends(get_db)
):
    """上传经过差分隐私处理后的热力图数据。

    前端已经完成以下处理：
    1. GPS坐标 → 区块(x, y)映射
    2. 拉普拉斯噪声添加 (差分隐私)

    后端只存储匿名区块及其加噪权重，不包含任何原始坐标。

    Args:
    data: 上传的热力图数据请求体
        db: 数据库会话

    Returns:
        dict: 上传结果
    """
    try:
        HeatmapService.store_heatmap_data(db, data.anonymous_id, data.data)
        return {
            "message": "热力图数据上传成功",
            "status": "success",
            "description": "数据已通过差分隐私保护并存储"
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"热力图数据上传失败: {str(e)}")

@router.get("/", response_model=dict)
async def get_heatmap(db: Session = Depends(get_db), attenuate: bool = True, factor: float = 0.7, radius: int = 5):
    """获取全局聚合热力图。

    后端对同一区块的权重求和，不反推任何单个用户轨迹。

    Args:
        db: 数据库会话

    Returns:
        HeatmapResponse: 聚合热力图数据
    """
    try:
        aggregated = HeatmapService.get_global_heatmap(db)
        if attenuate:
            aggregated = HeatmapService.attenuate_center(aggregated, factor=factor, radius=radius)
        return {
            "heatmap": aggregated,
            "description": "全局热力图数据，已通过差分隐私保护" + ("（中心已衰减显示）" if attenuate else "")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取热力图失败: {str(e)}")
