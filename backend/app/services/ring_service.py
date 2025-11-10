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
    def pick_group_for_user() -> str:
        """为用户选择一个稳定的群组名称（简单随机，可扩展为按负载均衡）。"""
        import random
        return random.choice(RingService.GROUP_NAMES)

    @staticmethod
    def ensure_seed_users(db: Session, user_level: str = "medium", min_count: int = 6) -> None:
        """确保指定水平的用户数至少为 min_count（用于凑环）。
        会自动插入若干 seed 用户（anonymous_id 前缀为 seed_），其公钥使用 CryptoService.generate_keypair
        生成有效的 secp256k1 压缩公钥。在 coincurve 不可用时，若安装了 ecdsa 也可生成有效公钥。
        """
        existing = db.query(User).filter(User.user_level == user_level).count()
        to_add = max(0, min_count - int(existing or 0))
        if to_add <= 0:
            return
        import hashlib, time
        for i in range(to_add):
            kp = CryptoService.generate_keypair()
            # 生成稳定匿名ID，避免重复
            stamp = f"{time.time_ns()}_{i}"
            anon = f"seed_{hashlib.md5(stamp.encode()).hexdigest()[:12]}"
            user = User(
                anonymous_id=anon,
                public_key=kp['public_key'],
                user_level=user_level,
                group_name=None
            )
            db.add(user)
        db.commit()

    @staticmethod
    def _is_valid_secp256k1_compressed_hex(pk_hex: str) -> bool:
        """纯 Python 校验压缩公钥是否位于 secp256k1 曲线上（无需 coincurve）。
        压缩公钥：33字节，前缀 0x02/0x03 + 32字节 x。
        p ≡ 3 (mod 4) 可用平方根简化：y = rhs^((p+1)//4) mod p。
        """
        if not isinstance(pk_hex, str):
            return False
        if pk_hex.startswith('0x') or pk_hex.startswith('0X'):
            pk_hex = pk_hex[2:]
        if len(pk_hex) != 66:
            return False
        try:
            prefix = int(pk_hex[:2], 16)
            if prefix not in (2, 3):
                return False
            x = int(pk_hex[2:], 16)
            # secp256k1 参数
            p = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
            # 曲线 y^2 = x^3 + 7 mod p
            rhs = (pow(x, 3, p) + 7) % p
            # 判断是否有平方根（勒让德符号判断）：rhs^((p-1)//2) == 1 则为二次剩余
            ls = pow(rhs, (p - 1) // 2, p)
            if ls != 1:
                return False
            y = pow(rhs, (p + 1) // 4, p)
            if (y * y) % p != rhs:
                return False
            # 奇偶性与前缀匹配
            if (y & 1) != (prefix & 1):
                # 另一根为 p - y
                y_alt = (p - y) % p
                if (y_alt & 1) != (prefix & 1):
                    return False
            return True
        except Exception:
            return False

    @staticmethod
    def generate_ring(db: Session, user_public_key: str, user_level: str = "medium", group_name: str = None, ring_size: int = 5) -> dict:
        # 确保同水平下至少有 ring_size 用户可供选取
        RingService.ensure_seed_users(db, user_level=user_level, min_count=ring_size)
        other_users = db.query(User).filter(
            User.user_level == user_level,
            User.public_key != user_public_key
        ).limit(ring_size - 1).all()
        # 累积有效压缩公钥
        public_keys = []
        # 先放入请求者公钥（若有效）
        if RingService._is_valid_secp256k1_compressed_hex(user_public_key):
            public_keys.append(user_public_key)
        # 加入其他用户的有效公钥
        for u in other_users:
            pk = u.public_key
            if RingService._is_valid_secp256k1_compressed_hex(pk):
                public_keys.append(pk)
            if len(public_keys) >= ring_size:
                break
        # 不足则持续生成直至达到 ring_size
        safety = 0
        while len(public_keys) < ring_size and safety < 50:
            mock = CryptoService.generate_keypair()
            if RingService._is_valid_secp256k1_compressed_hex(mock['public_key']):
                public_keys.append(mock['public_key'])
            safety += 1

        random.shuffle(public_keys)
        ring_id = CryptoService.generate_ring_id()
        # 若传入 group_name 则使用，否则随机（兼容旧逻辑）
        group_name = group_name or random.choice(RingService.GROUP_NAMES)

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
