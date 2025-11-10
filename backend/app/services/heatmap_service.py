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

    @staticmethod
    def attenuate_center(heatmap_data: list, factor: float = 0.7, radius: int = 5) -> list:
        """对热力图中心区域做衰减（不修改数据库，仅在返回前调整）。

        计算加权质心作为“中心点”，将欧式距离不超过 radius 的格子权重乘以 factor。

        Args:
            heatmap_data: 形如 [{'x': int, 'y': int, 'weight': float}, ...]
            factor: 衰减系数，0~1
            radius: 作用半径，格子单位
        Returns:
            新列表（浅拷贝），不会修改入参对象。
        """
        if not heatmap_data:
            return []
        try:
            total_w = sum(max(0.0, float(item.get('weight', 0.0))) for item in heatmap_data)
            if total_w <= 0:
                return list(heatmap_data)
            cx = sum(item['x'] * float(item['weight']) for item in heatmap_data) / total_w
            cy = sum(item['y'] * float(item['weight']) for item in heatmap_data) / total_w
            r2 = float(radius) * float(radius)
            f = min(max(float(factor), 0.0), 1.0)
            out = []
            for item in heatmap_data:
                x, y, w = int(item['x']), int(item['y']), float(item['weight'])
                dx, dy = x - cx, y - cy
                if (dx*dx + dy*dy) <= r2:
                    w = w * f
                out.append({'x': x, 'y': y, 'weight': float(w)})
            return out
        except Exception:
            # 发生异常则不做衰减，原样返回
            return list(heatmap_data)
