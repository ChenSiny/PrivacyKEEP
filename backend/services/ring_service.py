import random
from typing import List
from sqlalchemy.orm import Session
from app.models import User, Ring
from app.services.crypto_service import CryptoService

class RingService:
    """
    环管理服务类
    负责环的生成、管理和查询
    """
    
    # 预定义的趣味群组名称，用于增强用户体验
    GROUP_NAMES = [
        "闪电跑者", "旋风小队", "晨曦战士", "夜猫子联盟", 
        "周末勇士", "马拉松训练营", "健康生活家", "城市探索者",
        "节奏大师", "耐力王者", "速度之星", "坚持到底队"
    ]
    
    @staticmethod
    def generate_ring(db: Session, user_public_key: str, user_level: str = "medium", ring_size: int = 5) -> dict:
        """
        生成一个新的匿名环
        
        Args:
            db: 数据库会话
            user_public_key: 请求用户的公钥
            user_level: 用户水平，用于匹配相似用户
            ring_size: 环的大小（成员数量）
            
        Returns:
            dict: 包含环信息的字典
        """
        # 1. 从数据库中查找相同水平的其他用户
        other_users = db.query(User).filter(
            User.user_level == user_level,
            User.public_key != user_public_key  # 排除自己
        ).limit(ring_size - 1).all()  # 需要ring_size-1个其他用户
        
        # 2. 构建公钥列表（包含请求用户自己）
        public_keys = [user_public_key]  # 首先添加请求者
        public_keys.extend([user.public_key for user in other_users])
        
        # 3. 如果用户数量不足，生成模拟公钥补足环大小
        while len(public_keys) < ring_size:
            mock_keypair = CryptoService.generate_keypair()
            public_keys.append(mock_keypair['public_key'])
        
        # 4. 随机打乱公钥顺序以增强匿名性
        random.shuffle(public_keys)
        
        # 5. 生成环ID和趣味群组名
        ring_id = CryptoService.generate_ring_id()
        group_name = random.choice(RingService.GROUP_NAMES)
        
        # 6. 保存环信息到数据库
        ring = Ring(
            ring_id=ring_id,
            public_keys=public_keys,
            group_name=group_name,
            user_level=user_level
        )
        db.add(ring)
        db.commit()
        db.refresh(ring)
        
        return {
            "ring_id": ring_id,
            "ring_public_keys": public_keys,
            "group_name": group_name
        }
    
    @staticmethod
    def get_ring_by_id(db: Session, ring_id: str) -> Ring:
        """
        根据环ID获取环信息
        
        Args:
            db: 数据库会话
            ring_id: 环ID
            
        Returns:
            Ring: 环对象，如果不存在则返回None
        """
        return db.query(Ring).filter(Ring.ring_id == ring_id).first()