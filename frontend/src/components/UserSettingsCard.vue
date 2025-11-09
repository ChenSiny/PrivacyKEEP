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
        <label>所在队伍</label>
        <div class="group-display" :class="{ placeholder: !groupName }">
          {{ groupName || '未加入' }}
        </div>
        <div class="group-actions">
          <button class="btn-assign" @click="$emit('assign-group')">群组分配</button>
          <button class="btn-login" @click="$emit('login')">登录</button>
        </div>
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
    userLevel: { type: String, default: 'medium' },
    groupName: { type: String, default: '' }
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
  /*font-size: 1rem; */
  position: relative;
  height: 50px;
  top: 70px
}
.user-settings {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.75rem 1rem;
  margin-left: 10%;
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
.group-display {
  padding: 0.5rem;
  border: 2px dashed #ecf0f1;
  border-radius: 6px;
  font-size: 0.9rem;
  background: #fafafa;
  color: #2c3e50;
}
.group-display.placeholder {
  color: #9ca3af;
  font-style: italic;
}
.group-actions { display: flex; gap: 0.5rem; margin-top: 0.5rem; }
.btn-assign {
  margin-top: 0.5rem;
  padding: 0.4rem 0.6rem;
  border: 1px solid #3498db;
  background: #ecf5ff;
  color: #3498db;
  border-radius: 6px;
  font-size: 0.8rem;
  cursor: pointer;
}
.btn-assign:hover { background: #d9ecff; }
.btn-login {
  padding: 0.4rem 0.6rem;
  border: 1px solid #2ecc71;
  background: #eafff1;
  color: #2ecc71;
  border-radius: 6px;
  font-size: 0.8rem;
  cursor: pointer;
}
.btn-login:hover { background: #defbe6; }
</style>
