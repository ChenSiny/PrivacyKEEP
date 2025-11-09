from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import UserLoginResponse, UserLoginRequest
from app.models import User, Group
from app.services.ring_service import RingService
import os, secrets

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
            # 生成/获取群密钥
            group = db.query(Group).filter(Group.name==user.group_name).first()
            if not group:
                secret = secrets.token_hex(32)
                group = Group(name=user.group_name, secret=secret)
                db.add(group); db.commit(); db.refresh(group)
            return UserLoginResponse(
                anonymous_id=user.anonymous_id,
                public_key=user.public_key,
                user_level=user.user_level,
                group_name=user.group_name,
                group_key=group.secret
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
        # 生成群密钥
        grp = db.query(Group).filter(Group.name==user.group_name).first()
        if not grp:
            secret = secrets.token_hex(32)
            grp = Group(name=user.group_name, secret=secret)
            db.add(grp); db.commit(); db.refresh(grp)

        return UserLoginResponse(
            anonymous_id=user.anonymous_id,
            public_key=user.public_key,
            user_level=user.user_level,
            group_name=user.group_name,
            group_key=grp.secret
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"登录失败: {str(e)}")
