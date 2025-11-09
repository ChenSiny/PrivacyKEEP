import random
from sqlalchemy.orm import Session
from app.models import User, Ring
from app.services.crypto_service import CryptoService

class RingService:
    """环管理服务：生成与查询。"""

    GROUP_NAMES = [
        "闪电跑者", "旋风小队", "晨曦战士", "夜猫子联盟",
        "周末勇士", "马拉松训练营", "健康生活家", "城市探索者",
        "节奏大师", "耐力王者", "速度之星", "坚持到底队"
    ]

    @staticmethod
    def generate_ring(db: Session, user_public_key: str, user_level: str = "medium", ring_size: int = 5) -> dict:
        other_users = db.query(User).filter(
            User.user_level == user_level,
            User.public_key != user_public_key
        ).limit(ring_size - 1).all()

        public_keys = [user_public_key]
        public_keys.extend([u.public_key for u in other_users])

        while len(public_keys) < ring_size:
            mock = CryptoService.generate_keypair()
            public_keys.append(mock['public_key'])

        random.shuffle(public_keys)
        ring_id = CryptoService.generate_ring_id()
        group_name = random.choice(RingService.GROUP_NAMES)

        ring = Ring(
            ring_id=ring_id,
            public_keys=public_keys,
            group_name=group_name,
            user_level=user_level
        )
        db.add(ring)
        db.commit()
        db.refresh(ring)

        return {"ring_id": ring_id, "ring_public_keys": public_keys, "group_name": group_name}

    @staticmethod
    def get_ring_by_id(db: Session, ring_id: str):
        return db.query(Ring).filter(Ring.ring_id == ring_id).first()
