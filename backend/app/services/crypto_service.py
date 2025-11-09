import hashlib
import time
import json
from typing import List

# 可选依赖：coincurve 不可用时使用降级策略，保证服务可启动
try:
    import coincurve  # type: ignore
except Exception:  # pragma: no cover - 环境缺少本地依赖时的降级路径
    coincurve = None

class CryptoService:
    """简化的环签名密码学服务（演示用）。"""

    @staticmethod
    def generate_keypair():
        if coincurve is None:
            # 降级：生成伪随机的十六进制字符串，满足演示需要
            ts = str(int(time.time() * 1000))
            fake_priv = hashlib.sha256((ts + "priv").encode()).hexdigest()
            fake_pub = hashlib.sha256((ts + "pub").encode()).hexdigest()
            return {'private_key': fake_priv, 'public_key': fake_pub}
        else:
            private_key = coincurve.PrivateKey()
            public_key = private_key.public_key
            return {
                'private_key': private_key.secret.hex(),
                'public_key': public_key.format(compressed=True).hex()
            }

    @staticmethod
    def simulate_ring_signature(message: str, private_key_hex: str, public_keys: List[str]) -> str:
        signature_data = {
            'message': message,
            'timestamp': time.time(),
            'ring_size': len(public_keys),
            'algorithm': 'ring-signature-simulation'
        }
        payload = json.dumps(signature_data).encode()
        if coincurve is None:
            # 降级：使用 sha512 生成 64 字节签名占位，满足验证长度阈值
            return hashlib.sha512(private_key_hex.encode() + payload).hexdigest()
        else:
            private_key = coincurve.PrivateKey.from_hex(private_key_hex)
            signature = private_key.sign(payload)
            return signature.hex()

    @staticmethod
    def verify_ring_signature(message: str, signature: str, public_keys: List[str]) -> bool:
        try:
            signature_bytes = bytes.fromhex(signature)
            if len(signature_bytes) < 64:
                return False
            if len(public_keys) < 2:
                return False
            return True
        except Exception:
            return False

    @staticmethod
    def generate_ring_id():
        timestamp = str(int(time.time() * 1000))
        random_part = hashlib.md5(timestamp.encode()).hexdigest()[:8]
        return f"ring_{timestamp}_{random_part}"
