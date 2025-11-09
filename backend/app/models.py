from sqlalchemy import Column, Integer, String, Float, Text, JSON, DateTime
from sqlalchemy.sql import func
from .database import Base

class User(Base):
    """
    用户数据模型
    存储用户的匿名标识和公钥信息
    """
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    anonymous_id = Column(String(100), unique=True, index=True, nullable=False, 
                         comment="用户匿名标识，用于关联数据但不暴露真实身份")
    public_key = Column(Text, nullable=False, comment="用户的椭圆曲线公钥")
    group_name = Column(String(100), nullable=True, comment="用户所属的固定群组名称（登录时分配，一次性）")
    user_level = Column(String(50), default="medium", comment="用户运动水平，用于环匹配")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), 
                       comment="用户注册时间")

class Ring(Base):
    """
    环数据模型
    存储环签名所需的公钥组信息
    """
    __tablename__ = "rings"
    
    id = Column(Integer, primary_key=True, index=True)
    ring_id = Column(String(100), unique=True, index=True, nullable=False, 
                    comment="环的唯一标识符")
    public_keys = Column(JSON, nullable=False, comment="环成员的公钥列表，顺序随机以增强匿名性")
    group_name = Column(String(100), comment="自动生成的趣味群组名称")
    user_level = Column(String(50), comment="环的用户水平分类")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), 
                       comment="环创建时间")

class HeatmapData(Base):
    """
    热力图数据模型
    存储经过前端差分隐私处理的区块数据
    """
    __tablename__ = "heatmap_data"
    
    id = Column(Integer, primary_key=True, index=True)
    anonymous_id = Column(String(100), nullable=False, 
                         comment="上传数据的用户匿名标识")
    x = Column(Integer, nullable=False, comment="区块横坐标编号（非具体GPS坐标）")
    y = Column(Integer, nullable=False, comment="区块纵坐标编号（非具体GPS坐标）")
    weight = Column(Float, nullable=False, 
                   comment="区块权重值，已在前端添加拉普拉斯噪声实现差分隐私")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), 
                       comment="数据上传时间")

class GroupScore(Base):
    """
    群体成绩数据模型
    存储环签名验证后的运动成绩
    """
    __tablename__ = "group_scores"
    
    id = Column(Integer, primary_key=True, index=True)
    ring_id = Column(String(100), nullable=False, comment="所属环的ID")
    group_name = Column(String(100), nullable=True, comment="群组名称冗余存储便于统计")
    user_anonymous_id = Column(String(100), nullable=True, comment="提交者匿名ID，用于统计成员数")
    total_distance = Column(Float, nullable=False, comment="运动总距离（公里）")
    average_pace = Column(Float, nullable=False, comment="平均配速（分钟/公里）")
    signature = Column(Text, nullable=False, comment="环签名，用于验证成绩真实性")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), 
                       comment="成绩提交时间")

class Group(Base):
    """
    运动群组与群密钥（对称密钥，用于成员上传成绩时的 HMAC 验证）。
    注意：群密钥仅用于教学演示；生产建议采用真实环签名或群签名方案。
    """
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    secret = Column(Text, nullable=False, comment="群密钥（hex 编码）")
    created_at = Column(DateTime(timezone=True), server_default=func.now())