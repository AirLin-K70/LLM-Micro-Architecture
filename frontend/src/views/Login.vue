<template>
  <div class="auth-container">
    <div class="auth-box">
      <div class="auth-header">
        <h1>LLM Architecture</h1>
        <p>Micro-service based LLM Platform</p>
      </div>
      
      <el-card class="auth-card">
        <h2>{{ isLogin ? 'Welcome Back' : 'Create Account' }}</h2>
        <p class="subtitle">{{ isLogin ? 'Enter your details to access your account' : 'Sign up to get started' }}</p>
        
        <el-form :model="form" label-position="top" size="large">
          <el-form-item label="Username">
            <el-input 
              v-model="form.username" 
              placeholder="Enter your username"
              :prefix-icon="User"
            />
          </el-form-item>
          <el-form-item label="Password">
            <el-input 
              v-model="form.password" 
              type="password" 
              placeholder="Enter your password"
              :prefix-icon="Lock"
              show-password
            />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" class="full-width-btn" @click="handleSubmit" :loading="loading">
              {{ isLogin ? 'Sign In' : 'Sign Up' }}
            </el-button>
          </el-form-item>
        </el-form>
        
        <div class="auth-footer">
          <el-button link @click="isLogin = !isLogin">
            {{ isLogin ? "Don't have an account? Sign up" : 'Already have an account? Sign in' }}
          </el-button>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue';
import { useAuthStore } from '../stores/auth';
import { useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import { User, Lock } from '@element-plus/icons-vue';

const authStore = useAuthStore();
const router = useRouter();
const isLogin = ref(true);
const loading = ref(false);

const form = reactive({
  username: '',
  password: '',
});

const handleSubmit = async () => {
  if (!form.username || !form.password) {
    ElMessage.warning('Please fill in all fields');
    return;
  }

  loading.value = true;
  try {
    if (isLogin.value) {
      await authStore.login(form.username, form.password);
      ElMessage.success('Login successful');
    } else {
      await authStore.register(form.username, form.password);
      ElMessage.success('Registration successful');
    }
    router.push('/');
  } catch (error: any) {
    const message = error.response?.data?.detail || 'Authentication failed';
    ElMessage.error(message);
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
.auth-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  width: 100vw;
  background: linear-gradient(135deg, #1a1b1e 0%, #2c2e33 100%);
  position: relative;
  overflow: hidden;
}

/* Background Abstract Shapes */
.auth-container::before {
  content: '';
  position: absolute;
  top: -10%;
  right: -10%;
  width: 50%;
  height: 50%;
  background: radial-gradient(circle, rgba(99, 102, 241, 0.1) 0%, rgba(0, 0, 0, 0) 70%);
  border-radius: 50%;
  z-index: 0;
}

.auth-container::after {
  content: '';
  position: absolute;
  bottom: -10%;
  left: -10%;
  width: 50%;
  height: 50%;
  background: radial-gradient(circle, rgba(16, 185, 129, 0.1) 0%, rgba(0, 0, 0, 0) 70%);
  border-radius: 50%;
  z-index: 0;
}

.auth-box {
  z-index: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2rem;
}

.auth-header {
  text-align: center;
}

.auth-header h1 {
  font-size: 2.5rem;
  font-weight: 700;
  background: linear-gradient(to right, #6366f1, #a855f7);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  margin: 0;
}

.auth-header p {
  font-size: 1.1rem;
  color: var(--text-secondary);
  margin-top: 0.5rem;
}

.auth-card {
  width: 400px;
  background-color: rgba(44, 46, 51, 0.8) !important;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.1) !important;
  border-radius: 16px !important;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2) !important;
}

h2 {
  text-align: center;
  margin-top: 0;
  color: var(--text-primary);
}

.subtitle {
  text-align: center;
  margin-bottom: 2rem;
  font-size: 0.9rem;
}

.full-width-btn {
  width: 100%;
  font-weight: 600;
  padding: 1.2rem;
  background: linear-gradient(to right, #6366f1, #4f46e5);
  border: none;
}

.full-width-btn:hover {
  background: linear-gradient(to right, #4f46e5, #4338ca);
  transform: translateY(-1px);
}

.auth-footer {
  text-align: center;
  margin-top: 1rem;
}

/* Element Plus Overrides for Dark Mode */
:deep(.el-input__wrapper) {
  background-color: rgba(0, 0, 0, 0.2) !important;
  box-shadow: none !important;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

:deep(.el-input__wrapper:hover), :deep(.el-input__wrapper.is-focus) {
  border-color: var(--accent-color) !important;
}

:deep(.el-input__inner) {
  color: var(--text-primary) !important;
}

:deep(.el-form-item__label) {
  color: var(--text-secondary) !important;
}
</style>
