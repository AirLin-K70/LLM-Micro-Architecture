<template>
  <div class="chat-container">
    <!-- Messages Area -->
    <div class="messages" ref="messagesContainer">
      <div v-if="messages.length === 0" class="empty-state">
        <div class="empty-icon">
          <el-icon><ChatLineRound /></el-icon>
        </div>
        <h3>How can I help you today?</h3>
      </div>
      
      <div v-for="(msg, index) in messages" :key="index" :class="['message-wrapper', msg.role]">
        <div class="avatar">
          <el-avatar :size="36" :class="msg.role === 'user' ? 'user-avatar' : 'ai-avatar'">
            {{ msg.role === 'user' ? 'U' : 'AI' }}
          </el-avatar>
        </div>
        <div class="message-content">
            <div class="role-name">{{ msg.role === 'user' ? 'You' : 'Assistant' }}</div>
            <div class="bubble">
                <div v-if="msg.role === 'assistant'" v-html="renderMarkdown(msg.content)" class="markdown-body"></div>
                <div v-else>{{ msg.content }}</div>
            </div>
        </div>
      </div>
      
      <div v-if="loading" class="message-wrapper assistant">
        <div class="avatar">
          <el-avatar :size="36" class="ai-avatar">AI</el-avatar>
        </div>
        <div class="message-content">
            <div class="role-name">Assistant</div>
            <div class="bubble loading-bubble">
                <span class="dot"></span>
                <span class="dot"></span>
                <span class="dot"></span>
            </div>
        </div>
      </div>
    </div>

    <!-- Input Area -->
    <div class="input-container">
      <div class="input-box">
        <el-input
          v-model="input"
          placeholder="Type a message..."
          @keyup.enter="sendMessage"
          :disabled="loading"
          type="textarea"
          :autosize="{ minRows: 1, maxRows: 4 }"
          resize="none"
          class="chat-input"
        />
        <el-button 
            type="primary" 
            circle 
            @click="sendMessage" 
            :loading="loading" 
            :disabled="!input.trim()"
            class="send-btn"
        >
            <el-icon><Position /></el-icon>
        </el-button>
      </div>
      <div class="disclaimer">
        AI can make mistakes. Consider checking important information.
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick } from 'vue';
import api from '../api/client';
import MarkdownIt from 'markdown-it';
import hljs from 'highlight.js';
import 'highlight.js/styles/github-dark.css'; // Dark theme for code
import { ChatLineRound, Position } from '@element-plus/icons-vue';

const md: MarkdownIt = new MarkdownIt({
  html: true,
  linkify: true,
  typographer: true,
  highlight: function (str: string, lang: string): string {
    if (lang && hljs.getLanguage(lang)) {
      try {
        return `<pre class="hljs"><code>${hljs.highlight(str, { language: lang, ignoreIllegals: true }).value}</code></pre>`;
      } catch (__) {}
    }
    return ''; // use external default escaping
  }
});

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

const messages = ref<Message[]>([]);
const input = ref('');
const loading = ref(false);
const messagesContainer = ref<HTMLElement | null>(null);

const renderMarkdown = (text: string) => {
    return md.render(text);
}

const sendMessage = async () => {
  if (!input.value.trim() || loading.value) return;

  const userMsg = input.value;
  messages.value.push({ role: 'user', content: userMsg });
  input.value = '';
  loading.value = true;
  scrollToBottom();

  try {
    const response = await api.post('/chat', {
      query: userMsg,
      history: messages.value.slice(0, -1).map(m => ({ role: m.role, content: m.content })), 
      stream: false 
    });
    
    messages.value.push({ role: 'assistant', content: response.data.answer });
  } catch (error: any) {
    const errorMessage = error.response?.data?.detail || error.message || 'Error: Failed to get response.';
    messages.value.push({ role: 'assistant', content: `Error: ${errorMessage}` });
  } finally {
    loading.value = false;
    scrollToBottom();
  }
};

const scrollToBottom = async () => {
  await nextTick();
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight;
  }
};
</script>

<style scoped>
.chat-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  max-width: 900px;
  margin: 0 auto;
  position: relative;
}

.messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  padding-bottom: 120px; /* Space for input */
}

.empty-state {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary);
  opacity: 0.5;
}

.empty-icon {
  font-size: 4rem;
  margin-bottom: 1rem;
  color: var(--accent-color);
}

.message-wrapper {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
}

.message-wrapper.user {
  flex-direction: row-reverse;
}

.avatar {
  flex-shrink: 0;
  margin-top: 4px;
}

.user-avatar {
  background-color: var(--accent-color);
  color: white;
}

.ai-avatar {
  background-color: var(--success-color);
  color: white;
}

.message-content {
  display: flex;
  flex-direction: column;
  max-width: 80%;
}

.message-wrapper.user .message-content {
  align-items: flex-end;
}

.role-name {
  font-size: 0.8rem;
  color: var(--text-secondary);
  margin-bottom: 4px;
}

.bubble {
  padding: 12px 16px;
  border-radius: 12px;
  line-height: 1.6;
  font-size: 0.95rem;
}

.message-wrapper.user .bubble {
  background-color: var(--accent-color);
  color: white;
  border-bottom-right-radius: 4px;
}

.message-wrapper.assistant .bubble {
  background-color: var(--card-bg);
  border: 1px solid var(--border-color);
  border-bottom-left-radius: 4px;
}

.input-container {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 20px;
  background: linear-gradient(to top, var(--bg-color) 80%, transparent);
}

.input-box {
  background-color: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: 24px;
  padding: 8px 8px 8px 20px;
  display: flex;
  align-items: flex-end;
  gap: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transition: border-color 0.2s, box-shadow 0.2s;
}

.input-box:focus-within {
  border-color: var(--accent-color);
  box-shadow: 0 4px 20px rgba(99, 102, 241, 0.15);
}

.chat-input :deep(.el-textarea__inner) {
  background-color: transparent;
  box-shadow: none;
  border: none;
  padding: 8px 0;
  color: var(--text-primary);
  max-height: 150px;
}

.send-btn {
  margin-bottom: 4px;
  background-color: var(--accent-color);
  border: none;
}

.send-btn:disabled {
  background-color: var(--border-color);
}

.disclaimer {
  text-align: center;
  font-size: 0.75rem;
  color: var(--text-secondary);
  margin-top: 8px;
  opacity: 0.7;
}

/* Markdown Styles */
.markdown-body :deep(p) {
  margin-bottom: 1em;
}

.markdown-body :deep(p:last-child) {
  margin-bottom: 0;
}

.markdown-body :deep(pre) {
  background-color: #0d1117;
  padding: 12px;
  border-radius: 8px;
  overflow-x: auto;
  margin: 12px 0;
}

.markdown-body :deep(code) {
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  font-size: 0.9em;
}

/* Loading Animation */
.loading-bubble {
  display: flex;
  gap: 4px;
  align-items: center;
  padding: 16px !important;
}

.dot {
  width: 6px;
  height: 6px;
  background-color: var(--text-secondary);
  border-radius: 50%;
  animation: bounce 1.4s infinite ease-in-out both;
}

.dot:nth-child(1) { animation-delay: -0.32s; }
.dot:nth-child(2) { animation-delay: -0.16s; }

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}
</style>
