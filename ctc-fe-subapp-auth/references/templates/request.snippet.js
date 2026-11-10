/**
 * @Description: Axios 挂载 @ctc-front/gf-framework-auth 示例片段
 */
import { frameworkAuth } from '@/common/utils/frameworkAuth'

// 1. 挂载认证与 401 队列重试拦截器（必须在业务响应拦截器之前）
frameworkAuth.attachAxios(service, {
	isUnauthorized: ({ status, data }) => {
		if ([401, 402, 403].includes(Number(status))) return true
		if (data && typeof data === 'object') {
			const code = Number(data.code)
			if (
				[401, 402, 403, 40108].includes(code) ||
				String(data.code) === '40108'
			) {
				return true
			}
			if ([401, 402, 403].includes(Number(data.status))) return true
		}
		return false
	}
})

// 2. 响应拦截器调整
service.interceptors.response.use(
	res => {
		// 防御已解包的业务数据对象再次进入拦截器（重发请求防重解包）
		if (res && res.code !== undefined && !res.request && !res.headers) {
			return res
		}

		// 处理文件流...
		if (
			res?.request?.responseType === 'blob' ||
			res?.request?.responseType === 'arraybuffer'
		) {
			return res
		}

		let data = res.data
		data.code = Number(data?.code)

		// 成功业务码判断
		if (['200', 200, 201, 202, 'SYS000', 1311].includes(data.code)) {
			return data
		} else if (data.code === 401 || data.code === 402 || data.code === 403) {
			// 超时未续租或最终失效时 reject，交由全局路由或错误处理器处理，不要在此强跳登录
			return Promise.reject(data)
		} else {
			Notification.warning({
				title: '失败',
				message: data.msg || 'Error'
			})
			return Promise.reject(data || new Error('Request error'))
		}
	},
	error => {
		const status = error.response?.status
		// 401/402/403 交由认证模块重试或静默拒绝，避免弹出网络超时提示
		if ([401, 402, 403].includes(status)) {
			return Promise.reject(error)
		}
		if (error.code === 'ECONNABORTED') {
			Notification.warning({
				title: '失败',
				message: '页面响应超时，请刷新后重试'
			})
		}
		return Promise.reject(error)
	}
)
