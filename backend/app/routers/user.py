from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import UserLoginResponse, UserLoginRequest
from app.models import User
from app.services.ring_service import RingService

router = APIRouter()

@router.post("/login", response_model=UserLoginResponse)
async def user_login(payload: UserLoginRequest, db: Session = Depends(get_db)):
    """用户登录/注册：首次登录分配固定队伍，后续保持不变。"""
    try:
        user = db.query(User).filter(User.anonymous_id == payload.anonymous_id).first()
        if user:
            # 若已有用户但未分配组（旧数据），为其补齐组名
            if not user.group_name:
                user.group_name = RingService.pick_group_for_user()
                db.add(user)
                db.commit()
                db.refresh(user)
            return UserLoginResponse(
                anonymous_id=user.anonymous_id,
                public_key=user.public_key,
                user_level=user.user_level,
                group_name=user.group_name
            )

        # 首次：创建并分配队伍
        group = RingService.pick_group_for_user()
        user = User(
            anonymous_id=payload.anonymous_id,
            public_key=payload.public_key,
            user_level=payload.user_level,
            group_name=group
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        return UserLoginResponse(
            anonymous_id=user.anonymous_id,
            public_key=user.public_key,
            user_level=user.user_level,
            group_name=user.group_name
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"登录失败: {str(e)}")
