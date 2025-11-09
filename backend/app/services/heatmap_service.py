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
            # 构造以北京近似坐标为中心的 10x10 区块演示数据，使用相对小坐标避免过大索引导致前端映射异常
            base_lat_idx = int(39.9042 / 0.001)
            base_lng_idx = int(116.4074 / 0.001)
            demo = []
            size = 10
            for dx in range(size):
                for dy in range(size):
                    dist_center = abs(dx - size//2) + abs(dy - size//2)
                    weight = max(0, 12 - dist_center * 2) + ((dx*dy) % 4)
                    if weight <= 0:
                        continue
                    demo.append({
                        'x': base_lng_idx + dx,
                        'y': base_lat_idx + dy,
                        'weight': float(weight)
                    })
            return demo
        return heatmap_data
