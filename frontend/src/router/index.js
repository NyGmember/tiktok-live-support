import { createRouter, createWebHistory } from 'vue-router'
import AdminView from '../views/AdminView.vue'
import OverlayView from '../views/OverlayView.vue'

const router = createRouter({
    history: createWebHistory(import.meta.env.BASE_URL),
    routes: [
        {
            path: '/admin',
            name: 'admin',
            component: AdminView
        },
        {
            path: '/overlay',
            name: 'overlay',
            component: OverlayView
        },
        {
            path: '/',
            redirect: '/admin'
        }
    ]
})

export default router
