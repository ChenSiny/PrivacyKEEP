from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models import HeatmapData

class HeatmapService:
    """
    热力图数据服务类
    处理热力图数据的存储和查询
    注意：所有差分隐私处理已在前端完成，后端直接存储处理后的数据
    """

    @staticmethod
    def store_heatmap_data(db: Session, anonymous_id: str, data: list):
        """
        存储热力图数据到数据库
        
        Args:
            db: 数据库会话
            anonymous_id: 用户匿名标识
            data: 热力图数据列表，已在前端完成区块化和差分隐私处理
        """
        for item in data:
            # 直接存储前端处理后的数据
            # 前端已完成：1. GPS坐标→区块编号映射 2. 拉普拉斯噪声添加
            heatmap_item = HeatmapData(
                anonymous_id=anonymous_id,
                x=item.x,      # 区块横坐标编号
                y=item.y,      # 区块纵坐标编号  
                weight=item.weight  # 加噪后的权重值
            )
            db.add(heatmap_item)
        
        db.commit()
    
    @staticmethod
    def get_global_heatmap(db: Session):
        """
        获取全局热力图聚合数据
        
        Args:
            db: 数据库会话
            
        Returns:
            list: 聚合后的热力图数据
        """
        # 对相同区块的权重进行求和，生成全局热力图
        result = db.query(
            HeatmapData.x,
            HeatmapData.y,
            func.sum(HeatmapData.weight).label('total_weight')
        ).group_by(
            HeatmapData.x, 
            HeatmapData.y
        ).all()
        
        # 转换为前端需要的格式
        heatmap_data = []
        for row in result:
            heatmap_data.append({
                'x': row.x,
                'y': row.y, 
                'weight': float(row.total_weight)
            })
        
        return heatmap_data