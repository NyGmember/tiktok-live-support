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
      component: AdminView
    },
    {
      path: '/overlay',
      name: 'overlay',
      component: OverlayView
    },
    {
      path: '/question',
      name: 'question',
      component: QuestionView
    },
    {
      path: '/sessions',
      name: 'sessions',
      component: SessionView
    }
  ]
})

export default router
