const routes = [
    {
        name: 'home',
        path: '/',
        component: () => import('@/views/Extensions.vue'),
        title: 'Home',
        permissions: {
            isPublic: false,
        },
    },
]

export default routes
