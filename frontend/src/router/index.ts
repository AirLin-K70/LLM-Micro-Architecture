import { createRouter, createWebHistory } from 'vue-router';
import Login from '../views/Login.vue';
import MainLayout from '../layouts/MainLayout.vue';
import Chat from '../views/Chat.vue';
import Knowledge from '../views/Knowledge.vue';
import { useAuthStore } from '../stores/auth';

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: Login,
  },
  {
    path: '/',
    component: MainLayout,
    children: [
      {
        path: '',
        redirect: '/chat',
      },
      {
        path: 'chat',
        name: 'Chat',
        component: Chat,
      },
      {
        path: 'knowledge',
        name: 'Knowledge',
        component: Knowledge,
      },
    ],
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

router.beforeEach((to, _from, next) => {
  const authStore = useAuthStore();
  if (to.name !== 'Login' && !authStore.token) {
    next({ name: 'Login' });
  } else {
    next();
  }
});

export default router;
