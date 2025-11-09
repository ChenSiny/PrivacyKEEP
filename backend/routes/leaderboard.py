from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.schemas import RingRequest, RingResponse, ScoreSubmit, LeaderboardResponse
from app.services.ring_service import RingService
from app.services.crypto_service import CryptoService
from app.models import Ring, GroupScore, User

# 创建排行榜相关的API路由
router = APIRouter()

@router.post("/request-ring", response_model=RingResponse)
async def request_ring(
    request: RingRequest,
    db: Session = Depends(get_db)
):
    """
    请求加入一个匿名环
    
    为用户分配一个匿名竞赛组，用于环签名：
    - 根据用户水平匹配相似用户
    - 生成包含用户公钥的环
    - 返回环信息和群组名称
    
    Args:
        request: 环请求数据
        db: 数据库会话依赖注入
        
    Returns:
        RingResponse: 环信息响应
    """
    try:
        # 检查用户是否存在，不存在则创建新用户
        user = db.query(User).filter(User.anonymous_id == request.anonymous_id).first()
        if not user:
            user = User(
                anonymous_id=request.anonymous_id,
                public_key=request.public_key,
                user_level=request.user_level
            )
            db.add(user)
            db.commit()
        
        # 生成环（包含用户公钥和其他相似用户的公钥）
        ring_info = RingService.generate_ring(db, request.public_key, request.user_level)
        
        return RingResponse(**ring_info)
        
    except Exception as e:
        db.rollback()  # 发生错误时回滚数据库事务
        raise HTTPException(
            status_code=500, 
            detail=f"环生成失败: {str(e)}"
        )

@router.post("/submit-score", response_model=dict)
async def submit_score(
    score_data: ScoreSubmit,
    db: Session = Depends(get_db)
):
    """
    提交带有环签名的运动成绩
    
    验证环签名并存储群体成绩：
    - 验证签名确保数据真实性和完整性
    - 存储成绩到对应环的群体数据中
    - 保护用户匿名性的同时保证成绩真实
    
    Args:
        score_data: 成绩提交数据（包含环签名）
        db: 数据库会话依赖注入
        
    Returns:
        dict: 提交结果消息
    """
    try:
        # 1. 获取环信息
        ring = RingService.get_ring_by_id(db, score_data.ring_id)
        if not ring:
            raise HTTPException(status_code=404, detail="环不存在")
        
        # 2. 验证环签名
        message = f"{score_data.ring_id}{score_data.total_distance}{score_data.average_pace}"
        is_valid = CryptoService.verify_ring_signature(
            message, 
            score_data.signature, 
            ring.public_keys
        )
        
        if not is_valid:
            raise HTTPException(status_code=400, detail="环签名验证失败")
        
        # 3. 存储群体成绩（不关联具体用户，只关联环）
        group_score = GroupScore(
            ring_id=score_data.ring_id,
            total_distance=score_data.total_distance,
            average_pace=score_data.average_pace,
            signature=score_data.signature
        )
        db.add(group_score)
        db.commit()
        
        return {
            "message": "成绩上传成功", 
            "status": "success",
            "description": "成绩已通过环签名验证并匿名存储"
        }
        
    except HTTPException:
        # 重新抛出已知的HTTP异常
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, 
            detail=f"成绩提交失败: {str(e)}"
        )

@router.get("/", response_model=LeaderboardResponse)
async def get_leaderboard(db: Session = Depends(get_db)):
    """
    获取群体排行榜
    
    显示各匿名群组的平均成绩：
    - 不暴露任何个体用户信息
    - 按群组平均成绩排序
    - 保护用户隐私的同时提供竞争乐趣
    
    Args:
        db: 数据库会话依赖注入
        
    Returns:
        LeaderboardResponse: 排行榜数据
    """
    try:
        # 1. 计算每个环的平均成绩（子查询）
        subquery = db.query(
            GroupScore.ring_id,
            func.avg(GroupScore.total_distance).label('avg_distance'),
            func.avg(GroupScore.average_pace).label('avg_pace'),
            func.count(GroupScore.id).label('score_count')
        ).group_by(GroupScore.ring_id).subquery()
        
        # 2. 关联环表获取群组名称和其他信息
        leaderboard_data = db.query(
            Ring.group_name,
            subquery.c.avg_distance,
            subquery.c.avg_pace,
            subquery.c.score_count
        ).join(
            subquery, Ring.ring_id == subquery.c.ring_id
        ).all()
        
        # 3. 构建响应数据
        leaderboard = []
        for row in leaderboard_data:
            leaderboard.append({
                "group_name": row.group_name,
                "average_distance": float(row.avg_distance) if row.avg_distance else 0,
                "average_pace": float(row.avg_pace) if row.avg_pace else 0,
                "member_count": min(row.score_count, 5)  # 假设每个环最多5人
            })
        
        # 4. 按平均距离降序排列
        leaderboard.sort(key=lambda x: x["average_distance"], reverse=True)
        
        return LeaderboardResponse(leaderboard=leaderboard)
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"获取排行榜失败: {str(e)}"
        )