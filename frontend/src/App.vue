<template>
  <div id="app">
    <header class="app-header">
      <h1>🏃 运动隐私保护演示系统</h1>
      <p>体验差分隐私和环签名技术如何保护您的运动数据</p>
    </header>
    <main>
      <DemoView />
    </main>
    <footer class="app-footer">
      <p>课程设计演示系统 - 基于差分隐私与环签名技术</p>
    </footer>
  </div>
</template>

<script>
import DemoView from './views/DemoView.vue'

export default {
  name: 'App',
  components: {
    DemoView
  }
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  min-height: 100vh;
}

#app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.app-header {
  background: rgba(255, 255, 255, 0.95);
  padding: 1rem 2rem;
  text-align: center;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.app-header h1 {
  color: #2c3e50;
  margin-bottom: 0.5rem;
}

.app-header p {
  color: #7f8c8d;
  font-size: 1.1rem;
}

.app-footer {
  z-index: -1;
  background: rgba(44, 62, 80, 0.9);
  color: white;
  text-align: center;
  padding: 1rem;
  margin-top: auto;
}

main {
  flex: 1;
  padding: 1rem;
}
</style>