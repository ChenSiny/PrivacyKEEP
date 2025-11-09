<template>
  <div class="user-settings-card">
    <h3>👤 用户设置</h3>
    <div class="user-settings">
      <div class="setting-item">
        <label>匿名ID</label>
        <input
          :value="anonymousId"
          @input="$emit('update:anonymousId', $event.target.value)"
          type="text"
          class="setting-input"
          placeholder="user_xxx"
        />
      </div>
      <div class="setting-item">
        <label>当前运动水平</label>
        <select
          :value="userLevel"
          @change="$emit('update:userLevel', $event.target.value)"
          class="setting-select"
        >
          <option value="beginner">初级</option>
          <option value="medium">中级</option>
          <option value="advanced">高级</option>
        </select>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'UserSettingsCard',
  props: {
    anonymousId: { type: String, default: '' },
    userLevel: { type: String, default: 'medium' }
  }
}
</script>

<style scoped>
.user-settings-card {
  background: white;
  border-radius: 10px;
  padding: 1rem 1.25rem;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.08);
  width: 100%;
}
.user-settings-card h3 {
  margin: 0 0 0.75rem;
  color: #2c3e50;
  font-size: 1rem;
}
.user-settings {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.75rem 1rem;
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
</style>
