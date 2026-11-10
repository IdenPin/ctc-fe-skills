<!--
 * @Description: App.vue 生命周期与 Token 双向同步示例
-->
<script>
import { mapActions } from 'vuex'
import { getQueryString } from '@/common/utils/tools'
import { frameworkAuth } from '@/common/utils/frameworkAuth'

export default {
	name: 'App',
	data() {
		return {
			unsubscribeAuth: null,
			isLoaded: false
		}
	},
	created() {
		// 1. 同步基座已存 Token（从对应 storageKey 中提取）
		this.syncFrameworkToken()

		// 2. 订阅基座续租/更新事件，保证 Vuex 状态与基座时刻一致
		this.unsubscribeAuth = frameworkAuth.subscribe(session => {
			if (session?.accessToken) {
				this.setToken(session.accessToken)
			}
		})

		// 3. 处理 URL 入参 Token（如有）并安全拉取初始业务数据
		this.initSession()
	},
	beforeDestroy() {
		// 销毁监听
		this.unsubscribeAuth && this.unsubscribeAuth()
	},
	methods: {
		...mapActions({
			setToken: 'auth/setToken',
			fetchUserInfo: 'auth/fetchUserInfo' // 根据实际项目 Vuex Action 调整
		}),
		syncFrameworkToken() {
			const token = frameworkAuth.getAccessToken()
			if (token) {
				this.setToken(token)
			}
		},
		async initSession() {
			const token = getQueryString('t__') || getQueryString('token')
			if (token) {
				this.setToken(token)
				// 回写到 frameworkAuth 会话中
				frameworkAuth.onTokenRefreshed(token)
			}

			const currentToken =
				(this.$store && this.$store.getters['auth/token']) ||
				frameworkAuth.getAccessToken()

			// 关键点：初始请求必须使用 try/catch/finally 包裹，避免 Token 已失效导致页面永久白屏
			try {
				if (currentToken && this.fetchUserInfo) {
					await this.fetchUserInfo()
				}
			} catch (error) {
				console.warn('[App] 初始化用户信息失败:', error)
			} finally {
				this.isLoaded = true
			}
		}
	}
}
</script>
