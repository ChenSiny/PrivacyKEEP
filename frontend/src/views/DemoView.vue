      
<template>
  <div class="demo-view">
    <transition name="toast-fade">
      <div v-if="lastMessage" :class="['toast', lastMessage.type]">
        {{ lastMessage.text }}
        <button class="toast-close" @click="lastMessage=null">×</button>
      </div>
    </transition>
    <!-- 顶部状态区：隐私状态 + 用户设置 并列展示 -->
    <div class="status-row">
      <PrivacyStatus 
        :is-recording="isRecording" 
        :data-uploaded="dataUploaded" 
        class="status-item"
      />
      <UserSettingsCard 
        :anonymous-id="currentAnonymousId"
        :user-level="userLevel"
        :group-name="currentRing?.group_name || ''"
        @update:anonymousId="val => currentAnonymousId = val"
        @update:userLevel="val => userLevel = val"
        @assign-group="handleAssignGroup"
        @login="handleLogin"
        class="status-item"
      />
    </div>
    
    <div class="demo-layout">
      <!-- 左侧：控制面板 -->
      <div class="left-panel">
        <ControlPanel 
          :is-recording="isRecording"
          :current-view="currentView"
          @start-workout="handleStartWorkout"
          @end-workout="handleEndWorkout"
          @reset-demo="handleResetDemo"
          @switch-view="handleSwitchView"
        />
        <!-- 保留运动实时数据在左侧下方 -->
        <DataCards 
          :stats="workoutStats"
          :process-state="processState"
          :process-details="processDetails"
          class="data-cards"
        />
      </div>
      
      <!-- 右侧：主内容区（地图始终存在，排行榜浮层切换） -->
      <div class="right-panel">
        <div class="map-view">
          <MapComponent
            :current-view="currentView"
            :personal-trajectory="personalTrajectory"
            :heatmap-data="globalHeatmapData"
            :is-recording="isRecording"
            :show-placeholder="!loggedIn && !dataUploaded"
            ref="mapRef"
          />
          <div v-if="currentView==='leaderboard'" class="leaderboard-inline">
            <div class="leaderboard-container">
              <h2>👥 群体排行榜</h2>
              <p class="leaderboard-description">
                基于环签名技术的匿名群体竞争 - 保护个人隐私的同时享受竞技乐趣
              </p>

              <div v-if="leaderboardData.length === 0" class="empty-state">
                <div class="empty-icon">📊</div>
                <p>暂无排行榜数据</p>
                <p class="empty-hint">完成一次运动后即可查看群体排名</p>
              </div>

              <div v-else class="leaderboard-list">
                <div v-for="(group, index) in leaderboardData"
                    :key="group.group_name"
                    :class="['leaderboard-item', { podium: index < 3 }]">

                  <div class="rank">
                    <span v-if="index < 3" class="podium-icon">
                      {{ ['🥇', '🥈', '🥉'][index] }}
                    </span>
                    <span v-else class="rank-number">#{{ index + 1 }}</span>
                  </div>
                  <div class="group-info">
                    <div class="group-name">{{ group.group_name }}</div>
                    <div class="group-stats">
                      <span class="stat">{{ format2(group.average_distance) }} km</span>
                      <span class="stat">{{ format2(group.average_pace) }} min/km</span>
                      <span class="stat">{{ group.member_count }} 人</span>
                    </div>
                  </div>
                  <div class="group-score">
                    <div class="score-value">{{ format2(group.average_distance) }}</div>
                    <div class="score-label">平均距离</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import PrivacyStatus from '../components/PrivacyStatus.vue'
import ControlPanel from '../components/ControlPanel.vue'
import DataCards from '../components/DataCards.vue'
import MapComponent from '../components/MapComponent.vue'
import UserSettingsCard from '../components/UserSettingsCard.vue'
import { calculateWorkoutStatsReal } from '../utils/gps.js'
import { processTrajectoryWithDP } from '../utils/dp.js'
import { generateKeyPair, ringSign, prepareSignatureMessage, generateGroupSignature } from '../utils/crypto.js'
import { uploadHeatmapData, getGlobalHeatmap, requestRing, submitScore, submitScoreRing, getLeaderboard, loginUser } from '../utils/api.js'

export default {
  name: 'DemoView',
  components: {
    PrivacyStatus,
    ControlPanel,
    DataCards,
    MapComponent,
    UserSettingsCard
  },
  data() {
    return {
      // 运动状态
      isRecording: false,
      dataUploaded: false,
      currentView: 'trajectory',
      
      // 运动数据
      personalTrajectory: [],
      workoutStats: {
        duration: 0,
        totalDistance: 0,
        averagePace: 0
      },
      
      // 处理状态
      processState: 'idle', // idle, recording, processing, completed
      processDetails: {},
      
      // 全局数据
      globalHeatmapData: [],
      leaderboardData: [],
      
      // 用户信息
      userKeyPair: null,
      currentAnonymousId: '',
  currentRing: null,
      // 新增：用户等级单独保存，匿名ID也可编辑
      userLevel: 'medium',
  // 目标配速（分钟/公里），用于计算“虚拟用时”，保持演示数据合理
  targetPaceMinPerKm: 6.0,
  // 虚拟用时（秒）：不等于真实秒，而是按每步距离×目标配速累计
  virtualElapsedSeconds: 0,
      
      // 模拟运动计时器
      workoutTimer: null,
      workoutStartTime: null,
      loggedIn: false
      ,
      lastMessage: null
      ,currentHeading: null
    }
  },
  async mounted() {
    this.userKeyPair = generateKeyPair();
    await this.handleLogin();
    await this.loadGlobalHeatmap();
    await this.loadLeaderboard();
  },
  methods: {
    async handleLogin() {
      try {
        this.currentAnonymousId = this.currentAnonymousId || ('user_' + Math.random().toString(36).slice(2,8));
        const login = await loginUser(this.currentAnonymousId, this.userKeyPair.publicKey, this.userLevel);
        this.currentRing = { group_name: login.group_name, group_key: login.group_key };
        this.loggedIn = true;
        this.$nextTick(() => {
          const center = this.personalTrajectory[0] || { lat: 39.9042, lng: 116.4074 };
          if (this.$refs.mapRef && this.$refs.mapRef.fitToGridWindow) {
            this.$refs.mapRef.fitToGridWindow(center, 10);
          }
        });
        this._showToast('success', `登录成功，已分配至 ${login.group_name}`);
      } catch (e) {
        console.warn('登录失败', e);
        this._showToast('error', '登录失败，请重试');
      }
    },
    async handleAssignGroup() {
      // 简单调用请求环以确保分配队伍（若已有则忽略）
      if (this.currentRing && this.currentRing.group_name) return;
      try {
        const ringInfo = await requestRing(this.currentAnonymousId, this.userKeyPair.publicKey, this.userLevel);
        this.currentRing = ringInfo;
        this._showToast('success', `已加入群组 ${ringInfo.group_name}`);
      } catch(e) { console.warn('群组分配失败', e); }
    },
    async handleStartWorkout(settings) {
      console.log('开始运动:', settings);
      
      this.isRecording = true;
      this.dataUploaded = false;
      this.processState = 'recording';
      // 若用户在顶部卡片编辑了匿名ID，则优先用顶部值；否则使用控制面板传来的；再兜底生成一个
  this.currentAnonymousId = this.currentAnonymousId || ('user_' + Math.random().toString(36).slice(2,8));
      this.currentView = 'trajectory';
      
      // 清空之前的轨迹
      this.personalTrajectory = [];
  // 重置虚拟用时
  this.virtualElapsedSeconds = 0;
      
      // 开始“按真实时间流速”的模拟运动（1Hz，每秒前进5-8米）
      this.startRandomWalkRealtime();
    },
    
    startRandomWalkRealtime() {
      this.workoutStartTime = Date.now();
      const center = { lat: 39.9042, lng: 116.4074 };
      if (this.personalTrajectory.length === 0) this.personalTrajectory.push(center);
      // 以起点为中心缩放到 10x10 视窗
      this.$nextTick(() => {
        if (this.$refs.mapRef && this.$refs.mapRef.fitToGridWindow) {
          this.$refs.mapRef.fitToGridWindow(center, 10);
        }
      });
      // 初始化方向（度）并限制后续转向幅度
      if (this.currentHeading == null) this.currentHeading = Math.random()*360;
      const TURN_MAX = 30; // 最大转向幅度（度）
      const MAX_RADIUS_METERS = 1500; // 距离起点最大半径，超出则缓慢向中心偏转
      const tick = () => {
        if (!this.isRecording) return;
        const last = this.personalTrajectory[this.personalTrajectory.length - 1];
        // 平滑方向：在当前 heading 基础上小幅调整
        let delta = (Math.random()*2 - 1) * TURN_MAX; // -TURN_MAX..TURN_MAX
        this.currentHeading = (this.currentHeading + delta + 360) % 360;
        const meters = 5 + Math.random() * 3; // 步长
        // 越界纠偏：计算与起点距离，若超半径则朝起点方向微调
        const start = this.personalTrajectory[0];
        const distFromStart = this._haversineMeters(start, last);
        if (distFromStart > MAX_RADIUS_METERS) {
          // 方向指向起点
          const dx = start.lng - last.lng;
            const dy = start.lat - last.lat;
          const angleToStart = (Math.atan2(dy, dx)*180/Math.PI + 360)%360;
          // 将当前 heading 往 angleToStart 靠近
          const diff = ((angleToStart - this.currentHeading + 540)%360)-180;
          this.currentHeading = (this.currentHeading + diff*0.2 + 360)%360; // 只纠偏 20%
        }
        const next = this._moveMeters(last, meters, this.currentHeading);
        if (Number.isFinite(next.lat) && Number.isFinite(next.lng)) {
          this.personalTrajectory.push(next);
        }
        const elapsed = Math.floor((Date.now() - this.workoutStartTime) / 1000);
        this.workoutStats = calculateWorkoutStatsReal(this.personalTrajectory, elapsed);
        this.workoutTimer = setTimeout(tick, 1000);
      };
      tick();
    },
    
    async handleEndWorkout() {
      console.log('结束运动');
      this.isRecording = false;
      this.processState = 'processing';
      
      // 更新处理详情
      this.processDetails = {
        gridCount: `已划分 ${this.personalTrajectory.length} 个位置点`,
        dpInfo: '应用拉普拉斯噪声 (ε=1.0)'
      };
      
      try {
        // 1. 处理热力图数据（差分隐私）
        const processedHeatmapData = processTrajectoryWithDP(this.personalTrajectory);
        this.processDetails.dpInfo = `生成 ${processedHeatmapData.length} 个加噪区块`;
        
        // 2. 上传热力图数据
        await uploadHeatmapData(this.currentAnonymousId, processedHeatmapData);
        this.processDetails.uploadInfo = '热力图数据上传成功';
        
        // 3. 请求环信息（若尚未获取）并生成真正环签名（当前前端为占位，后端会验证失败直到实现）
        if (!this.currentRing?.ring_id) {
          const ringInfo = await requestRing(
            this.currentAnonymousId,
            this.userKeyPair.publicKey,
            this.userLevel
          );
          this.currentRing = { ...this.currentRing, ...ringInfo };
        }
        const ringMsg = prepareSignatureMessage(
          this.currentRing.ring_id,
          this.workoutStats.totalDistance,
          this.workoutStats.averagePace
        );
        const ringSignature = await ringSign(
          ringMsg,
          this.userKeyPair.privateKey,
          this.currentRing.ring_public_keys || []
        );
        try {
          await submitScoreRing(
            this.currentRing.ring_id,
            this.workoutStats.totalDistance,
            this.workoutStats.averagePace,
            ringSignature
          );
        } catch (e) {
          console.warn('环签名提交失败，回退到群密钥HMAC流程', e);
          // 回退：使用群密钥 HMAC
          const grp = this.currentRing;
          if (grp?.group_key && grp?.group_name) {
            const groupSignature = await generateGroupSignature(
              grp.group_key,
              grp.group_name,
              this.workoutStats.totalDistance,
              this.workoutStats.averagePace
            );
            await submitScore(
              grp.group_name,
              this.workoutStats.totalDistance,
              this.workoutStats.averagePace,
              groupSignature
            );
          }
        }
        
        // 5. 更新全局数据
        await this.loadGlobalHeatmap();
        await this.loadLeaderboard();
        
        // 6. 完成处理
        this.processState = 'completed';
        this.dataUploaded = true;
        
        // 显示成功消息
        this.$emit('show-message', {
          type: 'success',
          text: `运动数据上传成功！您已加入 ${grp.group_name}`
        });
        this._showToast('success', `运动数据上传成功！您已加入 ${grp.group_name}`);
        
      } catch (error) {
        console.error('运动数据处理失败:', error);
        this.processState = 'idle';
        
        this.$emit('show-message', {
          type: 'error',
          text: '数据处理失败，请重试'
        });
        this._showToast('error', '数据处理失败，请重试');
      }
    },
    
    handleResetDemo() {
      console.log('重置演示');
      
      // 重置所有状态
      this.isRecording = false;
      this.dataUploaded = false;
      this.processState = 'idle';
      this.currentView = 'trajectory';
      
      // 清空数据
      this.personalTrajectory = [];
      this.workoutStats = { duration: 0, totalDistance: 0, averagePace: 0 };
      this.processDetails = {};
      
      // 清除计时器
      if (this.workoutTimer) {
        clearTimeout(this.workoutTimer);
        this.workoutTimer = null;
      }
      
      // 重新加载全局数据
      this.loadGlobalHeatmap();
      this.loadLeaderboard();
    },
    _showToast(type, text) {
      this.lastMessage = { type, text };
      clearTimeout(this._toastTimer);
      this._toastTimer = setTimeout(() => { this.lastMessage = null; }, 4000);
    },
    
    handleSwitchView(view) {
      this.currentView = view;
    },
    format2(value) {
      const n = Number(value);
      if (!Number.isFinite(n)) return '0.00';
      return n.toFixed(2);
    },
    
    async loadGlobalHeatmap() {
      try {
        const response = await getGlobalHeatmap();
        this.globalHeatmapData = response.heatmap || [];
      } catch (error) {
        console.error('加载热力图数据失败:', error);
      }
    },
    
    async loadLeaderboard() {
      try {
        const response = await getLeaderboard();
        this.leaderboardData = response.leaderboard || [];
      } catch (error) {
        console.error('加载排行榜数据失败:', error);
      }
    },
    // 计算两点间大圆距离（米）
    _haversineMeters(p1, p2) {
      if (!p1 || !p2) return 0;
      const R = 6371000;
      const toRad = v => v * Math.PI / 180;
      const dLat = toRad(p2.lat - p1.lat);
      const dLon = toRad(p2.lng - p1.lng);
      const a = Math.sin(dLat/2)**2 + Math.cos(toRad(p1.lat)) * Math.cos(toRad(p2.lat)) * Math.sin(dLon/2)**2;
      return 2 * R * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    }
    ,
    // 从上一点按给定方位和距离（米）生成下一点
    _moveMeters(origin, meters, headingDeg) {
      const R = 6371000; // 地球半径
      const lat1 = origin.lat * Math.PI/180;
      const lon1 = origin.lng * Math.PI/180;
      const brng = headingDeg * Math.PI/180;
      const dr = meters / R;
      const lat2 = Math.asin( Math.sin(lat1)*Math.cos(dr) + Math.cos(lat1)*Math.sin(dr)*Math.cos(brng) );
      const lon2 = lon1 + Math.atan2(Math.sin(brng)*Math.sin(dr)*Math.cos(lat1), Math.cos(dr)-Math.sin(lat1)*Math.sin(lat2));
      return { lat: +(lat2*180/Math.PI).toFixed(6), lng: +(((lon2*180/Math.PI)+540)%360-180).toFixed(6) };
    }
  }
}
</script>

<style scoped>
.demo-view {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  height: 100%;
}

/* 新增：顶部状态行并列布局 */
.status-row {
  display: flex;
  gap: 1rem;
  align-items: stretch;
  width: 100%;
}
.status-item {
  flex: 1;
  display: flex;
  height: 210px;
}
.data-cards { margin-top: 1rem; }

.demo-layout {
  display: grid;
  grid-template-columns: 300px 1fr; /* 略微缩小左侧宽度，为顶部并列腾空间 */
  gap: 1rem;
  height: calc(100vh - 220px); /* 顶部多一行卡片，略调高度 */
}

.left-panel {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.right-panel {
  display: flex;
  flex-direction: column;
}

.map-view {
  flex: 1;
  background: white;
  border-radius: 10px;
  overflow: hidden;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
  position: relative; /* 让内部面板可相对定位 */
}

.leaderboard-view { display: none; }
.leaderboard-inline {
  position: absolute;
  z-index: 1000;
  top: 0;
  right: 0;
  bottom: 0;
  width: 42%;
  min-width: 300px;
  max-width: 520px;
  background: rgba(255,255,255,0.96);
  box-shadow: -6px 0 12px rgba(0,0,0,0.08);
  border-left: 1px solid #f0f0f0;
  overflow-y: auto;
  padding: 1rem 1.25rem;
}

.leaderboard-container h2 {
  text-align: center;
  margin-bottom: 0.5rem;
  color: #2c3e50;
}

.leaderboard-description {
  text-align: center;
  color: #7f8c8d;
  margin-bottom: 2rem;
}

.empty-state {
  text-align: center;
  padding: 3rem 2rem;
  color: #bdc3c7;
}

.empty-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
}

.empty-hint {
  font-size: 0.9rem;
  margin-top: 0.5rem;
}

.leaderboard-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.leaderboard-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  background: #f8f9fa;
  border-radius: 10px;
  transition: all 0.3s ease;
}

.leaderboard-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
}

.leaderboard-item.podium {
  background: linear-gradient(135deg, #ffeaa7, #fab1a0);
  border: 2px solid #e17055;
}

.rank {
  width: 40px;
  text-align: center;
}

.podium-icon {
  font-size: 1.5rem;
}

.rank-number {
  font-size: 1.1rem;
  font-weight: 600;
  color: #7f8c8d;
}

.group-info {
  flex: 1;
}

.group-name {
  font-size: 1.1rem;
  font-weight: 600;
  color: #2c3e50;
  margin-bottom: 0.25rem;
}

.group-stats {
  display: flex;
  gap: 1rem;
  font-size: 0.8rem;
}

.stat {
  background: rgba(255, 255, 255, 0.7);
  padding: 0.2rem 0.5rem;
  border-radius: 12px;
  color: #2c3e50;
}

.group-score {
  text-align: center;
  padding: 0.5rem 1rem;
  background: rgba(255, 255, 255, 0.9);
  border-radius: 8px;
}

.score-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: #2c3e50;
}

.score-label {
  font-size: 0.7rem;
  color: #7f8c8d;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
</style>