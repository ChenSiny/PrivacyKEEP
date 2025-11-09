<template>
  <div class="privacy-status">
    <h3>🔒 隐私保护状态</h3>
    <div class="status-items">
      <div class="status-item" :class="status.class">
        <span class="status-icon">{{ status.icon }}</span>
        <span class="status-text">{{ status.text }}</span>
      </div>
      <div class="protection-details">
        <div class="detail-item">
          <span class="detail-label">轨迹处理:</span>
          <span class="detail-value">前端本地计算</span>
        </div>
        <div class="detail-item">
          <span class="detail-label">热力图保护:</span>
          <span class="detail-value">差分隐私 (ε=1.0)</span>
        </div>
        <div class="detail-item">
          <span class="detail-label">排行榜保护:</span>
          <span class="detail-value">环签名技术</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'PrivacyStatus',
  props: {
    isRecording: {
      type: Boolean,
      default: false
    },
    dataUploaded: {
      type: Boolean,
      default: false
    }
  },
  computed: {
    status() {
      if (this.isRecording) {
        return {
          icon: '🟢',
          text: '本地计算中 - 原始轨迹数据未离开您的设备',
          class: 'recording'
        };
      } else if (this.dataUploaded) {
        return {
          icon: '🔵',
          text: '匿名数据已上传 - 隐私保护处理完成',
          class: 'uploaded'
        };
      } else {
        return {
          icon: '⚪',
          text: '系统就绪 - 准备开始运动演示',
          class: 'ready'
        };
      }
    }
  }
}
</script>

<style scoped>
.privacy-status {
  background: white;
  border-radius: 10px;
  padding: 1rem;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  margin-bottom: 1rem;
}

.privacy-status h3 {
  margin-bottom: 0.5rem;
  color: #2c3e50;
}

.status-items {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-left: 10%;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem;
  border-radius: 5px;
  font-weight: 500;
}

.status-item.recording {
  background: #e8f5e8;
  color: #2e7d32;
}

.status-item.uploaded {
  background: #e3f2fd;
  color: #1565c0;
}

.status-item.ready {
  background: #f5f5f5;
  color: #666;
}

.status-icon {
  font-size: 1.2rem;
}

.protection-details {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  margin-top: 0.5rem;
  padding-top: 0.5rem;
  border-top: 1px solid #eee;
}

.detail-item {
  display: flex;
  justify-content: space-between;
  font-size: 0.9rem;
}

.detail-label {
  color: #666;
}

.detail-value {
  color: #2c3e50;
  font-weight: 500;
}
</style>