from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

# 热力图数据基础模型
class HeatmapDataBase(BaseModel):
    """热力图区块数据基础模型"""
    x: int
    y: int
    weight: float

class HeatmapDataCreate(BaseModel):
    """热力图数据创建请求模型"""
    anonymous_id: str
    data: List[HeatmapDataBase]  # 区块数据列表

class HeatmapDataResponse(BaseModel):
    """热力图数据响应模型"""
    x: int
    y: int
    weight: float
    
    class Config:
        from_attributes = True  # 允许从ORM对象创建

# 环相关模型
class RingRequest(BaseModel):
    """环请求模型"""
    anonymous_id: str
    public_key: str
    user_level: str = "medium"

class RingResponse(BaseModel):
    """环响应模型"""
    ring_id: str
    ring_public_keys: List[str]
    group_name: str

# 排行榜相关模型
class ScoreSubmit(BaseModel):
    """成绩提交模型"""
    total_distance: float
    average_pace: float
    group_name: str
    group_signature: str

class RingSignature(BaseModel):
    """真正环签名（Schnorr 风格）"""
    c0: str                 # 32字节 hex（挑战初值）
    s: List[str]            # 每个环成员对应的 32字节 hex 标量数组（长度等于环大小）

class ScoreSubmitRing(BaseModel):
    """使用真正环签名提交成绩"""
    ring_id: str
    total_distance: float
    average_pace: float
    signature: RingSignature

class GroupScoreResponse(BaseModel):
    """群体成绩响应模型"""
    group_name: str
    average_distance: float
    average_pace: float
    member_count: int
    
    class Config:
        from_attributes = True

class LeaderboardResponse(BaseModel):
    """排行榜响应模型"""
    leaderboard: List[GroupScoreResponse]

# 用户登录相关模型
class UserLoginRequest(BaseModel):
    anonymous_id: str
    public_key: str
    user_level: str = "medium"

class UserLoginResponse(BaseModel):
    anonymous_id: str
    public_key: str
    user_level: str
    group_name: str
    group_key: str