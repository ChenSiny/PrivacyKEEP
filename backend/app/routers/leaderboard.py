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
    """请求加入一个匿名环。"""
    try:
        user = db.query(User).filter(User.anonymous_id == request.anonymous_id).first()
        if not user:
            user = User(
                anonymous_id=request.anonymous_id,
                public_key=request.public_key,
                user_level=request.user_level
            )
            db.add(user)
            db.commit()

        ring_info = RingService.generate_ring(db, request.public_key, request.user_level)
        return RingResponse(**ring_info)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"环生成失败: {str(e)}")

@router.post("/submit-score", response_model=dict)
async def submit_score(
    score_data: ScoreSubmit,
    db: Session = Depends(get_db)
):
    """提交带有环签名的运动成绩。"""
    try:
        ring = RingService.get_ring_by_id(db, score_data.ring_id)
        if not ring:
            raise HTTPException(status_code=404, detail="环不存在")

        message = f"{score_data.ring_id}{score_data.total_distance}{score_data.average_pace}"
        is_valid = CryptoService.verify_ring_signature(
            message,
            score_data.signature,
            ring.public_keys
        )

        if not is_valid:
            raise HTTPException(status_code=400, detail="环签名验证失败")

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
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"成绩提交失败: {str(e)}")

@router.get("/", response_model=LeaderboardResponse)
async def get_leaderboard(db: Session = Depends(get_db)):
    """获取群体排行榜。"""
    try:
        subquery = db.query(
            GroupScore.ring_id,
            func.avg(GroupScore.total_distance).label('avg_distance'),
            func.avg(GroupScore.average_pace).label('avg_pace'),
            func.count(GroupScore.id).label('score_count')
        ).group_by(GroupScore.ring_id).subquery()

        leaderboard_data = db.query(
            Ring.group_name,
            subquery.c.avg_distance,
            subquery.c.avg_pace,
            subquery.c.score_count
        ).join(subquery, Ring.ring_id == subquery.c.ring_id).all()

        leaderboard = []
        for row in leaderboard_data:
            leaderboard.append({
                "group_name": row.group_name,
                "average_distance": float(row.avg_distance) if row.avg_distance else 0,
                "average_pace": float(row.avg_pace) if row.avg_pace else 0,
                "member_count": min(row.score_count, 5)
            })

        leaderboard.sort(key=lambda x: x["average_distance"], reverse=True)
        return LeaderboardResponse(leaderboard=leaderboard)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取排行榜失败: {str(e)}")
