from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models import HeatmapData

class HeatmapService:
    """热力图数据服务：存储与聚合（前端已做差分隐私）。"""

    @staticmethod
    def store_heatmap_data(db: Session, anonymous_id: str, data: list):
        for item in data:
            heatmap_item = HeatmapData(
                anonymous_id=anonymous_id,
                x=item.x,
                y=item.y,
                weight=item.weight
            )
            db.add(heatmap_item)
        db.commit()

    @staticmethod
    def get_global_heatmap(db: Session):
        result = db.query(
            HeatmapData.x,
            HeatmapData.y,
            func.sum(HeatmapData.weight).label('total_weight')
        ).group_by(HeatmapData.x, HeatmapData.y).all()
        heatmap_data = []
        for row in result:
            heatmap_data.append({
                'x': row.x,
                'y': row.y,
                'weight': float(row.total_weight)
            })
        # 若尚无真实数据，返回一组预置演示点（不会覆盖已有数据）
        if not heatmap_data:
            demo = []
            # 构造 5x5 网格中若干热点区块
            for i in range(5):
                for j in range(5):
                    weight = max(0, 10 - (abs(2-i) + abs(2-j))*2) + (i*j)%3
                    if weight <= 0: continue
                    demo.append({ 'x': 100000 + i, 'y': 100000 + j, 'weight': weight })
            return demo
        return heatmap_data
