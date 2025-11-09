<template>
  <div class="data-cards">
    <div class="card">
      <div class="card-header">
        <h4>📊 实时数据</h4>
      </div>
      <div class="card-content">
        <div class="data-item">
          <span class="label">运动时长:</span>
          <span class="value">{{ formatTime(stats.duration) }}</span>
        </div>
        <div class="data-item">
          <span class="label">已跑距离:</span>
          <span class="value">{{ stats.totalDistance }} km</span>
        </div>
        <div class="data-item">
          <span class="label">平均配速:</span>
          <span class="value">{{ stats.averagePace }} min/km</span>
        </div>
      </div>
    </div>

    <div class="card">
      <div class="card-header">
        <h4>🔄 处理队列</h4>
      </div>
      <div class="process-steps">
        <div v-for="(step, index) in processSteps" 
             :key="index" 
             :class="['step', step.status]">
          <span class="step-icon">{{ step.icon }}</span>
          <span class="step-text">{{ step.text }}</span>
          <span v-if="step.detail" class="step-detail">{{ step.detail }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'DataCards',
  props: {
    stats: {
      type: Object,
      default: () => ({
        duration: 0,
        totalDistance: 0,
        averagePace: 0
      })
    },
    processState: {
      type: String,
      default: 'idle' // idle, recording, processing, completed
    },
    processDetails: {
      type: Object,
      default: () => ({})
    }
  },
  computed: {
    processSteps() {
      const steps = [
        {
          icon: '📍',
          text: '原始GPS点采集',
          status: this.processState === 'idle' ? 'pending' : 
                 this.processState === 'recording' ? 'active' : 'completed'
        },
        {
          icon: '🔲',
          text: '区块化处理',
          status: this.processState === 'processing' ? 'active' : 
                 this.processState === 'completed' ? 'completed' : 'pending',
          detail: this.processDetails.gridCount
        },
        {
          icon: '🎭',
          text: '差分隐私加噪',
          status: this.processState === 'processing' ? 'active' : 
                 this.processState === 'completed' ? 'completed' : 'pending',
          detail: this.processDetails.dpInfo
        },
        {
          icon: '📨',
          text: '数据上传',
          status: this.processState === 'completed' ? 'completed' : 'pending',
          detail: this.processDetails.uploadInfo
        }
      ];
      return steps;
    }
  },
  methods: {
    formatTime(seconds) {
      const mins = Math.floor(seconds / 60);
      const secs = seconds % 60;
      return `${mins}:${secs.toString().padStart(2, '0')}`;
    }
  }
}
</script>

<style scoped>
.data-cards {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.card {
  background: white;
  border-radius: 10px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.card-header {
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
  padding: 0.75rem 1rem;
}

.card-header h4 {
  margin: 0;
  font-size: 1rem;
}

.card-content {
  padding: 1rem;
}

.data-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem 0;
  border-bottom: 1px solid #f0f0f0;
}

.data-item:last-child {
  border-bottom: none;
}

.data-item .label {
  color: #666;
}

.data-item .value {
  font-weight: 600;
  color: #2c3e50;
  font-size: 1.1rem;
}

.process-steps {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.step {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.step.pending {
  background: #f8f9fa;
  color: #6c757d;
}

.step.active {
  background: #e3f2fd;
  color: #1565c0;
  border-left: 4px solid #2196f3;
}

.step.completed {
  background: #e8f5e8;
  color: #2e7d32;
  border-left: 4px solid #4caf50;
}

.step-icon {
  font-size: 1.2rem;
}

.step-text {
  flex: 1;
  font-weight: 500;
}

.step-detail {
  font-size: 0.8rem;
  background: rgba(0, 0, 0, 0.1);
  padding: 0.2rem 0.5rem;
  border-radius: 12px;
}
</style>