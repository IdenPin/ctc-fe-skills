<template>
	<router-view v-if="isLoaded" />
	<div v-else class="app-loading-placeholder">
		<!-- 骨架屏或 Loading 动画 -->
	</div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useFrameworkAuth } from '@/common/composables/useFrameworkAuth'
import { useUserStore } from '@/stores/user' // 示例 Pinia Store

const isLoaded = ref(false)
const userStore = useUserStore()

// 使用 Vue 3 Composable 监听基座 Token
const { token } = useFrameworkAuth({
	onTokenChange: newToken => {
		if (newToken) {
			userStore.setToken(newToken)
		}
	}
})

onMounted(async () => {
	try {
		// 如果有初始 Token 且需要获取用户信息
		if (token.value) {
			await userStore.fetchUserInfo?.()
		}
	} catch (error) {
		console.warn('[App] 初始化用户信息异常:', error)
	} finally {
		// 无论成功还是过期，确保 isLoaded 置为 true，杜绝白屏死锁
		isLoaded.value = true
	}
})
</script>
