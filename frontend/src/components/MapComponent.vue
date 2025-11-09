<template>
  <div class="map-container">
    <div id="map" ref="mapElement"></div>
    <div class="map-overlay">
      <div class="view-indicator">
        <span class="indicator-dot" :class="currentView"></span>
        <span class="indicator-text">{{ viewLabels[currentView] }}</span>
      </div>
    </div>
  </div>
</template>

<script>
import L from 'leaflet';

// 删除默认 icon 覆盖（保留使用 divIcon 的做法），避免依赖外部 CDN 图像
// delete L.Icon.Default.prototype._getIconUrl;
// L.Icon.Default.mergeOptions({ ... });

export default {
  name: 'MapComponent',
  props: {
    currentView: { type: String, default: 'trajectory' },
    personalTrajectory: { type: Array, default: () => [] },
    heatmapData: { type: Array, default: () => [] },
    isRecording: { type: Boolean, default: false },
    showPlaceholder: { type: Boolean, default: false },

    // 新增配置项
    showTiles: { type: Boolean, default: false },        // 是否加载真实瓦片（演示时可设 false）
    tileUrl: { type: String, default: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png' },
    gridSizeDeg: { type: Number, default: 0.001 },      // 网格度量（用于 x/y->lat/lng 映射）
    gridOrigin: { type: Object, default: () => ({ lat: 39.9042, lng: 116.4074 }) }, // 可被父组件覆盖
    redrawDebounceMs: { type: Number, default: 150 }
  },
  data() {
    return {
      map: null,
      trajectoryLayer: null,
      heatmapLayer: null,
      currentPosition: null,
      polyline: null,          // 复用 polyline
      viewLabels: {
        trajectory: '实时轨迹视图',
        heatmap: '差分隐私热力图',
        leaderboard: '群体排行榜'
      },
      _redrawTimer: null
    };
  },
  mounted() {
    this.initMap();
    // 初始若需要占位网格，则自动缩放到 10x10 视窗
    if (this.showPlaceholder) {
      const c = this.estimateCenter() || [this.gridOrigin.lat, this.gridOrigin.lng];
      const center = { lat: Array.isArray(c) ? c[0] : c.lat, lng: Array.isArray(c) ? c[1] : c.lng };
      this.$nextTick(() => this.fitToGridWindow(center, 10));
    }
  },
  beforeUnmount() {
    // 必须销毁地图以释放 DOM 事件和内存
    if (this.map) {
      this.map.remove();
      this.map = null;
    }
    if (this._redrawTimer) {
      clearTimeout(this._redrawTimer);
      this._redrawTimer = null;
    }
  },
  methods: {
    initMap() {
      // 以 data-driven 的方式确定初始中心：优先 personalTrajectory，再 fallback grid origin
      const center = this.estimateCenter() || [this.gridOrigin.lat, this.gridOrigin.lng];
      this.map = L.map(this.$refs.mapElement, { preferCanvas: true }).setView(center, 14);

      if (this.showTiles) {
        L.tileLayer(this.tileUrl, {
          attribution: '© OpenStreetMap contributors'
        }).addTo(this.map);
      } else {
        // 若不展示瓦片，添加一个简单的空白 tile layer（可选）或保持空白背景
      }

      // 初始化图层组并保留对象以便复用
      this.trajectoryLayer = L.layerGroup().addTo(this.map);
      this.heatmapLayer = L.layerGroup().addTo(this.map);
      this.polyline = L.polyline([], { color: '#3498db', weight: 4, opacity: 0.7, lineJoin: 'round' }).addTo(this.trajectoryLayer);

      // 初次渲染
      this.renderForView(this.currentView);
    },

    estimateCenter() {
      // 根据 personalTrajectory 计算 bbox 中心，兼容 [{lat,lng}] 或 [[lat,lng]]
      const pts = this.personalTrajectory || [];
      if (!pts.length) return null;
      let minLat = Infinity, maxLat = -Infinity, minLng = Infinity, maxLng = -Infinity;
      for (const p of pts) {
        const { lat, lng } = this._normalizePoint(p);
        if (lat == null || lng == null) continue;
        minLat = Math.min(minLat, lat); maxLat = Math.max(maxLat, lat);
        minLng = Math.min(minLng, lng); maxLng = Math.max(maxLng, lng);
      }
      if (!isFinite(minLat)) return null;
      return [(minLat + maxLat) / 2, (minLng + maxLng) / 2];
    },

    _normalizePoint(p) {
      // 支持 {lat,lng}、{latitude,longitude}、[lat,lng]、{0:lat,1:lng}
      if (!p) return { lat: null, lng: null };
      if (Array.isArray(p)) return { lat: Number(p[0]), lng: Number(p[1]) };
      if (p.lat != null && p.lng != null) return { lat: Number(p.lat), lng: Number(p.lng) };
      if (p.latitude != null && p.longitude != null) return { lat: Number(p.latitude), lng: Number(p.longitude) };
      if (p[0] != null && p[1] != null) return { lat: Number(p[0]), lng: Number(p[1]) };
      return { lat: null, lng: null };
    },

    // 节流重绘入口：用于避免高频更新导致重绘抖动
    scheduleRedraw(view = this.currentView) {
      if (this._redrawTimer) clearTimeout(this._redrawTimer);
      this._redrawTimer = setTimeout(() => {
        this.renderForView(view);
        this._redrawTimer = null;
      }, this.redrawDebounceMs);
    },

    renderForView(view) {
      // 我们希望无论是否在轨迹视图都保持热力图背景
      this.clearHeatmap();
      this.drawHeatmap(this.heatmapData);

      // 只有在轨迹视图或正在录制时才渲染轨迹层
      if (view === 'trajectory' || this.isRecording) {
        this.clearTrajectory();
        this.drawPersonalTrajectory(this.personalTrajectory);
      } else {
        // 非轨迹视图且未录制时隐藏轨迹层内容
        this.clearTrajectory();
      }
    },

    clearTrajectory() {
      // 只清除点图层，保留 polyline 对象以便复用
      if (this.trajectoryLayer) {
        this.trajectoryLayer.clearLayers();
        // 将 polyline 重新 add 到 trajectoryLayer
        if (this.polyline && !this.trajectoryLayer.hasLayer(this.polyline)) {
          this.polyline.addTo(this.trajectoryLayer);
        }
      }
    },

    clearHeatmap() {
      // 不销毁图层，只清空其内部对象
      if (this.heatmapLayer) this.heatmapLayer.clearLayers();
    },

    drawPersonalTrajectory(trajectory) {
      if (!this.map || !trajectory) return;
      const latlngs = trajectory
        .map(pt => {
          const { lat, lng } = this._normalizePoint(pt);
          return [Number(lat), Number(lng)];
        })
        .filter(x => Number.isFinite(x[0]) && Number.isFinite(x[1]));
      if (!latlngs.length) return; // 无有效点直接退出避免 fitBounds NaN

      // 复用 polyline，避免销毁重建
      if (this.polyline) {
        this.polyline.setLatLngs(latlngs);
      } else {
        this.polyline = L.polyline(latlngs, { color: '#3498db', weight: 4, opacity: 0.7 }).addTo(this.trajectoryLayer);
      }

      // 绘制点（轻量级）：若点过多可考虑下采样或 canvas 渲染插件
      latlngs.forEach((ll, i) => {
        L.circleMarker(ll, {
          radius: 3,
          fillColor: '#2980b9',
          color: '#fff',
          weight: 1,
          opacity: 1,
          fillOpacity: 0.8
        }).addTo(this.trajectoryLayer);
      });

      if (latlngs.length >= 2) {
        try {
          const bounds = this.polyline.getBounds();
          // 刚开始录制时避免过渡缩放，保持登录/开始时的网格窗口
          const EARLY_POINTS = 10;
          if (this.isRecording && latlngs.length <= EARLY_POINTS) {
            // 不进行任何 fit 操作，直接保持现有视图
            return;
          }
          // 其余情况：fit，但保证可视网格数不小于3，且不使用动画
          const center = bounds.getCenter();
          const sw = bounds.getSouthWest();
          const ne = bounds.getNorthEast();
          const latRange = Math.max(1e-9, ne.lat - sw.lat);
          const lngRange = Math.max(1e-9, ne.lng - sw.lng);
          const minCells = 3;
          const cell = this.gridSizeDeg;
          let targetSouth = sw.lat, targetNorth = ne.lat, targetWest = sw.lng, targetEast = ne.lng;
          // 纵向不足3格则扩展
          if (latRange / cell < minCells) {
            const need = minCells * cell;
            targetSouth = center.lat - need/2;
            targetNorth = center.lat + need/2;
          }
          // 横向不足3格则扩展
          if (lngRange / cell < minCells) {
            const need = minCells * cell;
            targetWest = center.lng - need/2;
            targetEast = center.lng + need/2;
          }
          this.map.fitBounds([[targetSouth, targetWest],[targetNorth, targetEast]], { padding: [20,20], animate: false });
        } catch (e) { /* ignore */ }
      }
    },

    drawHeatmap(heatmapData) {
      if (!this.map || !heatmapData) return;
      // 强制占位：显示初始 10x10 方格（不依赖后端返回）
      if (this.showPlaceholder) {
        // 以起点或 gridOrigin 为中心生成 10x10 占位，严格对齐网格，避免偏移重叠
        const anchor = this.personalTrajectory && this.personalTrajectory.length ? this._normalizePoint(this.personalTrajectory[0]) : { lat: this.gridOrigin.lat, lng: this.gridOrigin.lng };
        const centerX = Math.floor(anchor.lng / this.gridSizeDeg);
        const centerY = Math.floor(anchor.lat / this.gridSizeDeg);
        const size = 10; const half = Math.floor(size/2);
        const placeholder = [];
        for (let dx=-half; dx<half; dx++) {
          for (let dy=-half; dy<half; dy++) {
            const x = centerX + dx;
            const y = centerY + dy;
            const lat = y * this.gridSizeDeg;
            const lng = x * this.gridSizeDeg;
            const dist = Math.abs(dx) + Math.abs(dy);
            const weight = Math.max(1, 10 - dist); // 中心更热
            placeholder.push({ lat, lng, weight });
          }
        }
        heatmapData = placeholder;
      } else if (!heatmapData.length) {
        // 无数据但未强制占位：保持空
        return;
      }
      // 限制真实数据到起点中心 10x10（若已有起点），保证初始视图一致
      if (!this.showPlaceholder && this.personalTrajectory.length) {
        const anchor = this._normalizePoint(this.personalTrajectory[0]);
        const centerX = Math.floor(anchor.lng / this.gridSizeDeg);
        const centerY = Math.floor(anchor.lat / this.gridSizeDeg);
        const size = 10; const half = Math.floor(size/2);
        heatmapData = heatmapData.filter(cell => {
          const cx = cell.x != null ? Number(cell.x) : Math.floor(cell.lng / this.gridSizeDeg);
          const cy = cell.y != null ? Number(cell.y) : Math.floor(cell.lat / this.gridSizeDeg);
          return (cx >= centerX - half && cx < centerX + half && cy >= centerY - half && cy < centerY + half);
        });
      }
      // heatmapData 可支持两种格式：
      // 1) { lat, lng, weight }
      // 2) { x, y, weight } 其中 x/y 为格编号，映射到 gridOrigin + x*gridSizeDeg
      // 调整经度增量以在像素上更接近正方：lngDelta = gridSizeDeg / cos(lat)
      // 使用一致的经纬度增量，避免横向放大导致重叠
      const latDelta = this.gridSizeDeg;
      const lngDelta = this.gridSizeDeg;
      for (const item of heatmapData) {
        let lat, lng;
        if (item.lat != null && item.lng != null) {
          // 已经是地理坐标
          lat = Number(item.lat); lng = Number(item.lng);
        } else if (item.y != null && item.x != null) {
          const baseLatIndex = Math.floor(this.gridOrigin.lat / this.gridSizeDeg);
          const baseLngIndex = Math.floor(this.gridOrigin.lng / this.gridSizeDeg);
          lat = this.gridOrigin.lat + (Number(item.y) - baseLatIndex) * this.gridSizeDeg;
          lng = this.gridOrigin.lng + (Number(item.x) - baseLngIndex) * this.gridSizeDeg;
        } else {
          continue;
        }
        const intensity = Math.min((item.weight || 0) / 10, 1);
        const color = this.getColorForIntensity(intensity);
        const opacity = 0.3 + (intensity * 0.5);
        const bounds = [
          [lat, lng],
          [lat + latDelta, lng + lngDelta]
        ];
        // 最小像素尺寸保护：避免过度缩放导致单元格 < 2px
        const p1 = this.map.latLngToLayerPoint(bounds[0]);
        const p2 = this.map.latLngToLayerPoint(bounds[1]);
        if (Math.abs(p2.x - p1.x) < 2 || Math.abs(p2.y - p1.y) < 2) {
          continue; // 跳过过小的格子
        }
        L.rectangle(bounds, {
          color, fillColor: color, fillOpacity: opacity, weight: 1
        }).addTo(this.heatmapLayer);
      }
    },

    refreshAllLayers() {
      // 提供给父组件在外部强制刷新：保持热力图 + 轨迹叠加
      this.renderForView(this.currentView);
    },

    getColorForIntensity(intensity) {
      const colors = ['#4575b4','#74add1','#abd9e9','#e0f3f8','#fee090','#fdae61','#f46d43','#d73027'];
      const index = Math.floor(intensity * (colors.length - 1));
      return colors[Math.max(0, Math.min(index, colors.length - 1))];
    },

    updateCurrentPosition(point) {
      if (!point) return;
      const { lat, lng } = this._normalizePoint(point);
      if (!Number.isFinite(lat) || !Number.isFinite(lng)) return;
      if (this.currentPosition) {
        this.map.removeLayer(this.currentPosition);
      }
      this.currentPosition = L.marker([lat, lng], {
        icon: L.divIcon({
          className: 'current-position-marker',
          html: '📍',
          iconSize: [24, 24],
          iconAnchor: [12, 12]
        })
      }).addTo(this.map);
    },

    // 使地图缩放到以某中心为基准的 10x10 网格范围
    fitToGridWindow(center=null, cells=10) {
      if (!this.map) return;
      const minCells = Math.max(3, Number(cells) || 10);
      const half = Math.floor(minCells/2);
      const c = center || this.map.getCenter();
      const latCell = this.gridSizeDeg;
      const lngCell = this.gridSizeDeg / Math.max(0.0001, Math.cos(c.lat * Math.PI/180));
      const south = c.lat - half * latCell;
      const north = c.lat + half * latCell;
      const west = c.lng - half * lngCell;
      const east = c.lng + half * lngCell;
      try {
        this.map.fitBounds([[south, west], [north, east]], { padding: [20,20], animate: false });
      } catch(_) {}
    }
  },
  watch: {
    personalTrajectory: {
      handler() { this.scheduleRedraw(this.currentView); },
      deep: true
    },
    heatmapData: {
      handler() { this.scheduleRedraw(this.currentView); },
      deep: true
    },
    currentView(newView) { this.renderForView(newView); },
    isRecording(val) { this.renderForView(this.currentView); }
  }
}
</script>

<style scoped>
.map-container {
  position: relative;
  width: 100%;
  height: 100%;
  border-radius: 10px;
  overflow: hidden;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
}

#map {
  width: 100%;
  height: 100%;
  min-height: 500px;
}

.map-overlay {
  position: absolute;
  top: 10px;
  left: 10px;
  z-index: 1000;
}

.view-indicator {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: rgba(255, 255, 255, 0.95);
  padding: 0.5rem 1rem;
  border-radius: 20px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
  font-size: 0.9rem;
  font-weight: 500;
}

.indicator-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.indicator-dot.trajectory {
  background: #3498db;
}

.indicator-dot.heatmap {
  background: #e74c3c;
}

.indicator-dot.leaderboard {
  background: #2ecc71;
}

.indicator-text {
  color: #2c3e50;
}

/* Leaflet标记自定义样式 */
:deep(.current-position-marker) {
  background: transparent !important;
  border: none !important;
}
</style>