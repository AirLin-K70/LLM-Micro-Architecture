<template>
  <div class="knowledge-container">
    <!-- Header Section with Gradient Text -->
    <div class="header-section">
      <h1 class="gradient-text">Knowledge Base</h1>
      <p class="subtitle">Manage your RAG context documents with ease</p>
    </div>

    <!-- Main Content Grid -->
    <div class="content-grid">
      <!-- Upload Card -->
      <div class="glass-card upload-card">
        <div class="card-header">
          <div class="header-title">
            <el-icon class="icon-pulse"><Upload /></el-icon>
            <span>Upload Documents</span>
          </div>
        </div>
        
        <el-upload
          class="upload-area"
          drag
          action="#"
          :http-request="uploadFile"
          :on-success="handleSuccess"
          :on-error="handleError"
          multiple
          :show-file-list="true"
        >
          <el-icon class="el-icon--upload"><upload-filled /></el-icon>
          <div class="el-upload__text">
            Drop files here or <em>click to upload</em>
          </div>
          <template #tip>
            <div class="el-upload__tip">
              <el-tag effect="dark" round size="small" class="tag-gradient">PDF</el-tag>
              <el-tag effect="dark" round size="small" class="tag-gradient">TXT</el-tag>
              <span class="limit-text">Max size: 10MB</span>
            </div>
          </template>
        </el-upload>
      </div>

      <!-- Recent Documents Section -->
      <div class="glass-card recent-uploads">
        <div class="section-title">
          <el-icon><Document /></el-icon>
          <h3>Recent Documents</h3>
        </div>
        
        <div class="documents-list">
          <el-empty 
            description="No documents uploaded yet" 
            :image-size="120"
            class="custom-empty"
          >
            <template #description>
              <p class="empty-text">Upload documents to start building your knowledge base</p>
            </template>
          </el-empty>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { UploadFilled, Upload, Document } from '@element-plus/icons-vue';
import { ElMessage } from 'element-plus';
import type { UploadRequestOptions } from 'element-plus';
import api from '../api/client';

const uploadFile = async (options: UploadRequestOptions) => {
    const { file, onSuccess, onError } = options;
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        await api.post('/knowledge/upload', formData, {
            headers: {
                'Content-Type': 'multipart/form-data'
            }
        });
        onSuccess(file);
    } catch (err) {
        onError(err as any);
    }
};

const handleSuccess = () => {
    ElMessage.success({
        message: 'File uploaded successfully',
        type: 'success',
        plain: true,
    });
};

const handleError = () => {
    ElMessage.error({
        message: 'File upload failed',
        type: 'error',
        plain: true,
    });
};
</script>

<style scoped>
.knowledge-container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 40px 20px;
    min-height: 100vh;
}

.header-section {
  text-align: center;
  margin-bottom: 4rem;
  animation: fadeInDown 0.8s ease-out;
}

.gradient-text {
  font-size: 3.5rem;
  font-weight: 800;
  background: linear-gradient(135deg, #6366f1 0%, #a855f7 50%, #ec4899 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  margin-bottom: 1rem;
  letter-spacing: -1px;
}

.subtitle {
  color: var(--text-secondary);
  font-size: 1.2rem;
  font-weight: 300;
}

.content-grid {
  display: grid;
  gap: 2rem;
  animation: fadeInUp 0.8s ease-out 0.2s backwards;
}

.glass-card {
  background: rgba(30, 41, 59, 0.7);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 24px;
  padding: 2rem;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.glass-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 12px 40px rgba(99, 102, 241, 0.15);
  border-color: rgba(99, 102, 241, 0.3);
}

.card-header {
  margin-bottom: 1.5rem;
}

.header-title {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--text-primary);
}

.icon-pulse {
  color: #6366f1;
  animation: pulse 2s infinite;
}

/* Upload Area Styling */
.upload-area {
  width: 100%;
}

:deep(.el-upload-dragger) {
  background-color: rgba(15, 23, 42, 0.6) !important;
  border: 2px dashed rgba(99, 102, 241, 0.3) !important;
  border-radius: 16px !important;
  padding: 40px 0 !important;
  transition: all 0.3s ease !important;
}

:deep(.el-upload-dragger:hover) {
  border-color: #6366f1 !important;
  background-color: rgba(99, 102, 241, 0.1) !important;
  transform: scale(1.01);
}

.el-upload__text {
  color: var(--text-secondary);
  margin-top: 1rem;
  font-size: 1.1rem;
}

.el-upload__text em {
  color: #818cf8;
  font-weight: 600;
  transition: color 0.3s;
}

.el-icon--upload {
  color: #6366f1 !important;
  font-size: 4rem !important;
  margin-bottom: 1rem;
  transition: transform 0.3s;
}

:deep(.el-upload-dragger:hover .el-icon--upload) {
  transform: translateY(-5px);
}

.el-upload__tip {
  margin-top: 1.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
}

.tag-gradient {
  background: linear-gradient(135deg, #4f46e5, #7c3aed);
  border: none;
  font-weight: 600;
}

.limit-text {
  font-size: 0.9rem;
  color: var(--text-secondary);
  opacity: 0.8;
}

/* Recent Uploads Section */
.section-title {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 2rem;
  color: var(--text-primary);
}

.section-title h3 {
  font-size: 1.5rem;
  font-weight: 600;
}

.section-title .el-icon {
  font-size: 1.5rem;
  color: #a855f7;
}

.custom-empty {
  padding: 40px 0;
}

.empty-text {
  color: var(--text-secondary);
  font-size: 1.1rem;
}

/* Animations */
@keyframes fadeInDown {
  from {
    opacity: 0;
    transform: translateY(-20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes pulse {
  0% {
    transform: scale(1);
    opacity: 1;
  }
  50% {
    transform: scale(1.1);
    opacity: 0.8;
  }
  100% {
    transform: scale(1);
    opacity: 1;
  }
}

/* Responsive */
@media (max-width: 768px) {
  .gradient-text {
    font-size: 2.5rem;
  }
  
  .glass-card {
    padding: 1.5rem;
  }
}
</style>