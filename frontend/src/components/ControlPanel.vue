<template>
  <div class="control-panel">
    <div class="panel-section">
      <h3>🎯 运动控制</h3>
      <div class="control-buttons">
        <button 
          @click="startWorkout" 
          :disabled="isRecording"
          class="btn btn-primary"
        >
          🏃 开始运动
        </button>
        <button 
          @click="endWorkout" 
          :disabled="!isRecording"
          class="btn btn-secondary"
        >
          ⏹️ 结束运动
        </button>
        <button 
          @click="resetDemo" 
          class="btn btn-outline"
        >
          🔄 重置演示
        </button>
      </div>
    </div>

    <div class="panel-section">
      <h3>🗺️ 轨迹模拟</h3>
      <select v-model="selectedTrajectory" class="trajectory-select">
        <option value="circle">环形轨迹</option>
        <option value="line">直线轨迹</option>
        <option value="random">随机轨迹</option>
      </select>
    </div>

    <div class="panel-section">
      <h3> 数据视图</h3>
      <div class="view-buttons">
        <button 
          @click="switchView('trajectory')"
          :class="['view-btn', { active: currentView === 'trajectory' }]"
        >
          实时轨迹
        </button>
        <button 
          @click="switchView('heatmap')"
          :class="['view-btn', { active: currentView === 'heatmap' }]"
        >
          热力图
        </button>
        <button 
          @click="switchView('leaderboard')"
          :class="['view-btn', { active: currentView === 'leaderboard' }]"
        >
          排行榜
        </button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ControlPanel',
  props: {
    isRecording: {
      type: Boolean,
      default: false
    },
    currentView: {
      type: String,
      default: 'trajectory'
    }
  },
  data() {
    return {
      selectedTrajectory: 'circle'
    };
  },
  methods: {
    startWorkout() {
      this.$emit('start-workout', {
        trajectoryType: this.selectedTrajectory
      });
    },
    endWorkout() {
      this.$emit('end-workout');
    },
    resetDemo() {
      this.$emit('reset-demo');
    },
    switchView(view) {
      this.$emit('switch-view', view);
    }
  }
}
</script>

<style scoped>
.control-panel {
  background: white;
  border-radius: 10px;
  padding: 1.5rem;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  height: fit-content;
}

.panel-section {
  margin-bottom: 1.5rem;
}

.panel-section:last-child {
  margin-bottom: 0;
}

.panel-section h3 {
  margin-bottom: 0.75rem;
  color: #2c3e50;
  font-size: 1rem;
}

.control-buttons {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.btn {
  padding: 0.75rem 1rem;
  border: none;
  border-radius: 8px;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  text-align: center;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-primary {
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
}

.btn-secondary {
  background: #e74c3c;
  color: white;
}

.btn-secondary:hover:not(:disabled) {
  background: #c0392b;
  transform: translateY(-2px);
}

.btn-outline {
  background: transparent;
  border: 2px solid #bdc3c7;
  color: #7f8c8d;
}

.btn-outline:hover {
  border-color: #95a5a6;
  color: #2c3e50;
}

.trajectory-select {
  width: 100%;
  padding: 0.5rem;
  border: 2px solid #ecf0f1;
  border-radius: 6px;
  font-size: 0.9rem;
  background: white;
}

.trajectory-select:focus {
  outline: none;
  border-color: #3498db;
}

.user-settings {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.setting-item {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.setting-item label {
  font-size: 0.8rem;
  color: #7f8c8d;
  font-weight: 500;
}

.setting-input, .setting-select {
  padding: 0.5rem;
  border: 2px solid #ecf0f1;
  border-radius: 6px;
  font-size: 0.9rem;
}

.setting-input:focus, .setting-select:focus {
  outline: none;
  border-color: #3498db;
}

.view-buttons {
  display: flex;
  gap: 0.5rem;
}

.view-btn {
  flex: 1;
  padding: 0.5rem;
  background: #f8f9fa;
  border: 2px solid #e9ecef;
  border-radius: 6px;
  font-size: 0.8rem;
  cursor: pointer;
  transition: all 0.3s ease;
}

.view-btn:hover {
  background: #e9ecef;
}

.view-btn.active {
  background: #3498db;
  color: white;
  border-color: #3498db;
}
</style>