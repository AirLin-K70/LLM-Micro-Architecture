<template>
  <el-container class="layout-container">
    <el-aside width="240px" class="aside">
      <div class="logo-area">
        <div class="logo-icon">
          <el-icon><Monitor /></el-icon>
        </div>
        <span class="logo-text">LLM Arch</span>
      </div>
      
      <el-menu
        router
        :default-active="$route.path"
        class="el-menu-vertical-demo"
        background-color="transparent"
        text-color="#a1a1aa"
        active-text-color="#fff"
      >
        <el-menu-item index="/chat">
          <el-icon><ChatLineRound /></el-icon>
          <span>Chat Assistant</span>
        </el-menu-item>
        <el-menu-item index="/knowledge">
          <el-icon><Document /></el-icon>
          <span>Knowledge Base</span>
        </el-menu-item>
      </el-menu>

      <div class="user-area">
        <el-button class="logout-btn" @click="handleLogout">
          <el-icon><SwitchButton /></el-icon>
          <span>Sign Out</span>
        </el-button>
      </div>
    </el-aside>
    
    <el-container>
      <el-header class="header">
        <div class="header-content">
          <h3>{{ currentRouteName }}</h3>
          <div class="user-profile">
            <el-avatar :size="32" class="avatar">U</el-avatar>
            <span class="username">User</span>
          </div>
        </div>
      </el-header>
      
      <el-main class="main-content">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { ChatLineRound, Document, SwitchButton, Monitor } from '@element-plus/icons-vue';
import { useAuthStore } from '../stores/auth';
import { useRouter, useRoute } from 'vue-router';

const authStore = useAuthStore();
const router = useRouter();
const route = useRoute();

const currentRouteName = computed(() => {
  return route.name?.toString() || 'Dashboard';
});

const handleLogout = () => {
  authStore.logout();
  router.push('/login');
};
</script>

<style scoped>
.layout-container {
  height: 100vh;
  background-color: var(--bg-color);
}

.aside {
  background-color: var(--sidebar-bg);
  border-right: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
}

.logo-area {
  height: 64px;
  display: flex;
  align-items: center;
  padding: 0 20px;
  gap: 12px;
  border-bottom: 1px solid var(--border-color);
}

.logo-icon {
  width: 32px;
  height: 32px;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.logo-text {
  font-weight: 700;
  font-size: 1.1rem;
  color: var(--text-primary);
}

.el-menu-vertical-demo {
  border-right: none;
  margin-top: 1rem;
  flex: 1;
}

:deep(.el-menu-item) {
  margin: 4px 12px;
  border-radius: 8px;
  height: 48px;
}

:deep(.el-menu-item.is-active) {
  background-color: var(--accent-color) !important;
  font-weight: 600;
}

:deep(.el-menu-item:hover) {
  background-color: rgba(255, 255, 255, 0.05) !important;
}

.user-area {
  padding: 20px;
  border-top: 1px solid var(--border-color);
}

.logout-btn {
  width: 100%;
  background-color: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--border-color);
  color: var(--text-secondary);
  justify-content: flex-start;
}

.logout-btn:hover {
  background-color: rgba(239, 68, 68, 0.1);
  color: var(--danger-color);
  border-color: rgba(239, 68, 68, 0.2);
}

.header {
  height: 64px;
  border-bottom: 1px solid var(--border-color);
  padding: 0 32px;
  background-color: rgba(26, 27, 30, 0.8);
  backdrop-filter: blur(10px);
}

.header-content {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.header-content h3 {
  margin: 0;
  font-weight: 600;
}

.user-profile {
  display: flex;
  align-items: center;
  gap: 12px;
}

.avatar {
  background-color: var(--accent-color);
  color: white;
  font-weight: 600;
}

.username {
  font-weight: 500;
  font-size: 0.9rem;
}

.main-content {
  padding: 0;
  overflow: hidden; /* Handle scrolling in child components */
}

/* Transitions */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
