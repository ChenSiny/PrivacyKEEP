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
      <div class="setting-item">
        <label>所在队伍</label>
        <div class="group-display" :class="{ placeholder: !groupName }">
          {{ groupName || '未加入' }}
        </div>
        
      </div>
      <div class="setting-item">
      <div class="group-actions">
          <button class="btn-assign" @click="$emit('assign-group')">群组分配</button>
          <button class="btn-login" @click="$emit('login')">登录</button>
        </div>
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
    margin: 0 0 0rem;
    color: #2c3e50;
    height: 50px;
    align-self: center; /* 使 h3 垂直居中 */
    font-family: 'Arial', sans-serif; /* 添加字体 */
  }
  
  .user-settings {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0rem 1rem;
    margin-left: 10%;
  }
  
  .setting-item {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
    align-items: flex-start; /* 对齐到左侧 */
  }
  
  .setting-item label {
    font-size: 0.8rem;
    color: #7f8c8d;
    font-weight: 500;
    font-family: 'Arial', sans-serif; /* 添加字体 */
  }
  
  .setting-input, .setting-select {
    padding: 0.5rem;
    border: 2px solid #ecf0f1;
    border-radius: 6px;
    font-size: 0.9rem;
    width: 100%; /* 使输入框宽度占满整个容器 */
    font-family: 'Arial', sans-serif; /* 添加字体 */
  }
  
  .setting-input:focus, .setting-select:focus {
    outline: none;
    border-color: #3498db;
    box-shadow: 0 0 5px rgba(52, 152, 219, 0.3); /* 添加聚焦时的阴影效果 */
  }
  
  .group-display {
    padding: 0.5rem;
    border: 2px dashed #ecf0f1;
    border-radius: 6px;
    font-size: 0.9rem;
    background: #fafafa;
    color: #2c3e50;
    width: 100%; /* 使展示区域宽度占满整个容器 */
  }
  
  .group-display.placeholder {
    color: #9ca3af;
    font-style: italic;
  }
  
  .group-actions {
    display: flex;
    gap: 0.5rem;
    margin-top: 1.75rem;
  }
  
  .btn-assign,
  .btn-login {
    padding: 0.4rem 0.6rem;
    border: none;
    background-color: rgba(239, 252, 252, 0.993); /* 白底 */
    color: #3498db; /* 蓝字 */
    border-radius: 6px;
    font-size: 0.8rem;
    cursor: pointer;
    transition: background-color 0.3s; /* 添加过渡效果 */
  }
  .btn-assign:hover,
  .btn-login:hover {
    background-color: #ecf0f1; /* 鼠标悬停时的浅灰色背景 */
  }
  
  </style>
