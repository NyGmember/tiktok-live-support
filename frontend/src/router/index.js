import { createRouter, createWebHistory } from 'vue-router'
import AdminView from '../views/AdminView.vue'
import OverlayView from '../views/OverlayView.vue'
import QuestionView from '../views/QuestionView.vue'
import SessionView from '../views/SessionView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'admin',
      component: AdminView,
      meta: { title: 'Admin Control' }
    },
    {
      path: '/overlay',
      name: 'overlay',
      component: OverlayView,
      meta: { title: 'Leaderboard Overlay' }
    },
    {
      path: '/question',
      name: 'question',
      component: QuestionView,
      meta: { title: 'Question Overlay' }
    },
    {
      path: '/sessions',
      name: 'sessions',
      component: SessionView,
      meta: { title: 'Session Review' }
    }
  ]
})

router.beforeEach((to, from, next) => {
  document.title = to.meta.title || 'TikTok Live Support'
  next()
})

export default router
