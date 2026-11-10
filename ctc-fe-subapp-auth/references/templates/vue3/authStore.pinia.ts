import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useUserStore = defineStore('user', () => {
	const token = ref<string | null>(null)
	const userInfo = ref<Record<string, unknown> | null>(null)

	const isAuthenticated = computed(() => Boolean(token.value))

	function setToken(newToken: string | null) {
		token.value = newToken
	}

	async function fetchUserInfo() {
		if (!token.value) return null
		// 实际业务调用 API
		// const res = await apiGetUserInfo()
		// userInfo.value = res.data
		// return res.data
	}

	function clearSession() {
		token.value = null
		userInfo.value = null
	}

	return {
		token,
		userInfo,
		isAuthenticated,
		setToken,
		fetchUserInfo,
		clearSession
	}
})
