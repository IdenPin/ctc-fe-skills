import { ref, onMounted, onBeforeUnmount } from 'vue'
import { frameworkAuth } from '@/common/utils/frameworkAuth'

export interface UseFrameworkAuthOptions {
	/**
	 * 当 Token 发生变化时的回调（如同步 Pinia / Vuex 状态）
	 */
	onTokenChange?: (token: string | null) => void
	/**
	 * 是否自动在组件挂载时从 URL (t__ / token) 解析 Token
	 */
	syncFromUrl?: boolean
}

/**
 * Vue 3 专属组合式 API (Composable)
 * 用于在组件或 App.vue 中快捷监听基座 Token 更新
 */
export function useFrameworkAuth(options: UseFrameworkAuthOptions = {}) {
	const { onTokenChange, syncFromUrl = true } = options
	const token = ref<string | null>(frameworkAuth.getAccessToken())
	let unsubscribe: (() => void) | null = null

	const syncToken = (newToken: string | null) => {
		token.value = newToken
		onTokenChange?.(newToken)
	}

	onMounted(() => {
		// 1. 同步初始 Token
		if (syncFromUrl) {
			const urlParams = new URLSearchParams(window.location.search)
			const urlToken = urlParams.get('t__') || urlParams.get('token')
			if (urlToken) {
				frameworkAuth.onTokenRefreshed(urlToken)
				syncToken(urlToken)
			}
		}

		const currentToken = frameworkAuth.getAccessToken()
		if (currentToken && currentToken !== token.value) {
			syncToken(currentToken)
		}

		// 2. 订阅基座续租 / 更新事件
		unsubscribe = frameworkAuth.subscribe(session => {
			const freshToken = session?.accessToken || null
			syncToken(freshToken)
		})
	})

	onBeforeUnmount(() => {
		unsubscribe?.()
	})

	return {
		token,
		frameworkAuth,
		getAccessToken: () => frameworkAuth.getAccessToken(),
		notifyExpired: (reason?: string) => frameworkAuth.notifyExpired(reason)
	}
}
