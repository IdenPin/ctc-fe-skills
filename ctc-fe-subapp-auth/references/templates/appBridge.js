/**
 * @Description: AppBridge 通信模块 - 统一管理微前端与基座通信
 */
import { initAppBridge } from '@ctc-front/bridge-next'
import Package from '../../../package.json'

const APP_ID = Package.name
const HOST_APP_ID = 'main-app'
const BRIDGE_CHANNEL = 'gf-bridge'
const EVENTS = Object.freeze({
	HEART: 'HEART',
	FROM_CHILD: 'FROM_SON_MESSAGE'
})
const noop = () => {}
const logoutHandlers = new Set()

/**
 * 当前基座兼容层使用 gf-bridge。
 * 待基座和所有子系统统一迁移后，再一起切换为 ctc-bridge。
 */
const AppBridge = initAppBridge({
	appId: APP_ID,
	hostAppId: HOST_APP_ID,
	channel: BRIDGE_CHANNEL,
	onLogout: payload => {
		logoutHandlers.forEach(handler => {
			try {
				handler(payload)
			} catch (error) {
				console.error('[appBridge] 处理基座登出通知失败', error)
			}
		})
	}
})

export function getBridge() {
	return AppBridge.enabled && AppBridge.bridge ? AppBridge.bridge : null
}

function sendToHost(event, payload) {
	const bridge = getBridge()
	if (!bridge) return false

	try {
		bridge.send(HOST_APP_ID, event, payload)
		return true
	} catch (error) {
		console.warn(`[appBridge] 发送 ${event} 失败`, error)
		return false
	}
}

/**
 * 注册基座登出后的业务清理逻辑，并返回解绑函数。
 */
export function registerLogoutHandler(handler) {
	if (typeof handler !== 'function') return noop
	logoutHandlers.add(handler)

	return () => {
		logoutHandlers.delete(handler)
	}
}

/**
 * 通知基座当前业务系统的鉴权已失效。
 */
export function notifyTokenExpired(payload = true) {
	try {
		return AppBridge.notifyTokenExpired(payload)
	} catch (error) {
		console.warn('[appBridge] 通知基座鉴权失效失败', error)
		return false
	}
}

/**
 * 兼容历史调用方，新的业务代码请使用 notifyTokenExpired。
 * @deprecated
 */
export function doLogout(payload = true) {
	return notifyTokenExpired(payload)
}

/**
 * 监听基座心跳消息
 */
export function onHeart(callback) {
	const bridge = getBridge()
	if (!bridge || typeof callback !== 'function') return noop
	return bridge.on(EVENTS.HEART, callback)
}

/**
 * 发送消息给基座
 */
export function sendMessage({ type, data } = {}) {
	if (!type) return false

	return sendToHost(EVENTS.FROM_CHILD, {
		appId: APP_ID,
		biz: {
			type,
			data
		}
	})
}

/**
 * 销毁桥接会话，供应用卸载或测试场景使用。
 */
export function destroy() {
	AppBridge.destroy()
}
