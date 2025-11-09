from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.schemas import RingRequest, RingResponse, ScoreSubmit, LeaderboardResponse, ScoreSubmitRing
from app.services.ring_service import RingService
from app.services.crypto_service import CryptoService
from app.models import Ring, GroupScore, User, Group
from sqlalchemy import func
import json

# 创建排行榜相关的API路由
router = APIRouter()

def seed_leaderboard(db: Session, target_groups: int = 6, target_members: int = 5):
    """确保演示排行榜至少有 target_groups 个群组，每组至少 target_members 位成员。
    若已有部分数据，则按需补齐，不重复插入相同 seed 用户。
    """
    import hashlib, random
    # 预设候选组名
    candidate_groups = [
        "闪电跑者", "旋风小队", "晨曦战士", "夜猫子联盟",
        "周末勇士", "马拉松训练营", "健康生活家", "城市探索者",
        "节奏大师", "耐力王者", "速度之星", "坚持到底队"
    ]
    random.shuffle(candidate_groups)
    use_groups = candidate_groups[:target_groups]

    # 统计现有每组的 distinct 成员数
    existing_counts = {row[0]: row[1] for row in db.query(
        GroupScore.group_name, func.count(func.distinct(GroupScore.user_anonymous_id))
    ).group_by(GroupScore.group_name).all()}

    for gname in use_groups:
        current = int(existing_counts.get(gname, 0) or 0)
        need = max(0, target_members - current)
        if need == 0:
            continue
        # 准备一个 seed ring（或复用同一个 ring_id）
        ring_id = f"seed_{hashlib.md5(gname.encode()).hexdigest()[:8]}"
        ring = db.query(Ring).filter(Ring.ring_id == ring_id).first()
        if not ring:
            pubkeys = [hashlib.md5((gname+str(i)).encode()).hexdigest() for i in range(7)]
            ring = Ring(ring_id=ring_id, public_keys=pubkeys, group_name=gname, user_level="medium")
            db.add(ring); db.commit(); db.refresh(ring)
        # 生成需要的成员成绩，保证 user_anonymous_id 唯一
        base_idx = current
        for k in range(need):
            idx = base_idx + k
            user_id = f"seed_user_{hashlib.md5((gname+str(idx)).encode()).hexdigest()[:10]}"
            # 合理的距离/配速随机（不同组可稍微偏置）
            # 距离 3~12km，配速 5.0~7.0 分/公里之间
            dist = round(random.uniform(3.0, 12.0), 1)
            pace = round(random.uniform(5.0, 7.0), 1)
            sig = hashlib.sha256(f"{ring_id}{user_id}{dist}{pace}".encode()).hexdigest()
            gs = GroupScore(
                ring_id=ring.ring_id,
                group_name=gname,
                user_anonymous_id=user_id,
                total_distance=dist,
                average_pace=pace,
                signature=sig
            )
            db.add(gs)
        db.commit()

@router.post("/request-ring", response_model=RingResponse)
async def request_ring(
    request: RingRequest,
    db: Session = Depends(get_db)
):
    """请求加入一个匿名环。"""
    try:
        user = db.query(User).filter(User.anonymous_id == request.anonymous_id).first()
        if not user:
            # 旧逻辑：无用户时直接创建，但不再在此分配随机组；组在登录时分配。
            # 为兼容旧前端，若前端未调用 /user/login，这里兜底分配一次。
            group_name = RingService.pick_group_for_user()
            user = User(
                anonymous_id=request.anonymous_id,
                public_key=request.public_key,
                user_level=request.user_level,
                group_name=group_name
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        else:
            # 更新公钥（如果变更）
            if user.public_key != request.public_key:
                user.public_key = request.public_key
                db.add(user)
                db.commit()
                db.refresh(user)

        ring_info = RingService.generate_ring(db, request.public_key, request.user_level, group_name=user.group_name)
        return RingResponse(**ring_info)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"环生成失败: {str(e)}")

@router.post("/submit-score", response_model=dict)
async def submit_score(
    score_data: ScoreSubmit,
    db: Session = Depends(get_db)
):
    """提交带有群密钥 HMAC 的运动成绩（教学版）。"""
    try:
        grp = db.query(Group).filter(Group.name==score_data.group_name).first()
        if not grp:
            raise HTTPException(status_code=404, detail="群组不存在")

        # 验证 HMAC（基于 group_key 的 SHA-512 HMAC）
        import hmac, hashlib
        msg = f"{score_data.group_name}|{score_data.total_distance}|{score_data.average_pace}".encode()
        key = bytes.fromhex(grp.secret)
        mac = hmac.new(key, msg, hashlib.sha512).hexdigest()
        if mac != score_data.group_signature:
            raise HTTPException(status_code=400, detail="群密钥验证失败")

        # 将成绩聚合进对应群组
        group_score = GroupScore(
            ring_id=f"group_{grp.id}",
            group_name=score_data.group_name,
            user_anonymous_id=None,
            total_distance=score_data.total_distance,
            average_pace=score_data.average_pace,
            signature=score_data.group_signature
        )
        db.add(group_score)
        db.commit()

        return {
            "message": "成绩上传成功",
            "status": "success",
            "description": "成绩已通过群密钥验证并匿名存储"
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"成绩提交失败: {str(e)}")

@router.post("/submit-score-ring", response_model=dict)
async def submit_score_ring(
    payload: ScoreSubmitRing,
    db: Session = Depends(get_db)
):
    """使用真正环签名提交成绩 (Schnorr-like 教学版)。"""
    try:
        # 获取环信息
        ring = db.query(Ring).filter(Ring.ring_id == payload.ring_id).first()
        if not ring:
            raise HTTPException(status_code=404, detail="环不存在")
        # 组装消息（与前端保持一致）
        msg = f"{payload.ring_id}|{payload.total_distance}|{payload.average_pace}".encode()
        c0 = payload.signature.c0
        s_list = payload.signature.s
        # 验证环签名
        if not CryptoService.ring_verify(msg, ring.public_keys, c0, s_list):
            raise HTTPException(status_code=400, detail="环签名验证失败")
        # 写入成绩；签名序列化保留
        sig_store = json.dumps({"c0": c0, "s": s_list})
        gs = GroupScore(
            ring_id=ring.ring_id,
            group_name=ring.group_name,
            user_anonymous_id=None,
            total_distance=payload.total_distance,
            average_pace=payload.average_pace,
            signature=sig_store
        )
        db.add(gs)
        db.commit()
        return {"message": "环签名成绩上传成功", "status": "success"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"环签名成绩提交失败: {str(e)}")

@router.get("/", response_model=LeaderboardResponse)
async def get_leaderboard(db: Session = Depends(get_db), seed: bool = True):
    """获取群体排行榜。"""
    try:
        if seed:
            seed_leaderboard(db)
        subquery = db.query(
            GroupScore.group_name.label('gname'),
            func.avg(GroupScore.total_distance).label('avg_distance'),
            func.avg(GroupScore.average_pace).label('avg_pace'),
            func.count(func.distinct(GroupScore.user_anonymous_id)).label('member_count')
        ).group_by(GroupScore.group_name).subquery()

        leaderboard_data = db.query(
            subquery.c.gname,
            subquery.c.avg_distance,
            subquery.c.avg_pace,
            subquery.c.member_count
        ).all()

        leaderboard = []
        for row in leaderboard_data:
            # 规格化为两位小数
            avg_dist = round(float(row.avg_distance), 2) if row.avg_distance is not None else 0.0
            avg_pace = round(float(row.avg_pace), 2) if row.avg_pace is not None else 0.0
            leaderboard.append({
                "group_name": row.gname or "未知组",
                "average_distance": avg_dist,
                "average_pace": avg_pace,
                "member_count": int(row.member_count) if row.member_count is not None else 0
            })

        leaderboard.sort(key=lambda x: x["average_distance"], reverse=True)
        return LeaderboardResponse(leaderboard=leaderboard)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取排行榜失败: {str(e)}")
