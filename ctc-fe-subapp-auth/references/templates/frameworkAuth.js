/**
 * @Description: GfFrameworkAuth 认证客户端初始化
 * 针对不同基座选择对应的 storageKey：
 * - 重点排污单位监控系统 (gf-monitor / zdjk-system / zdjk-cockpit): 'monitor-user-info'
 * - 生态环境移动执法/法治系统 (gf-law / shj-fxc-biz): 'law-user-info'
 */
import { createGfFrameworkAuth } from '@ctc-front/gf-framework-auth'
import { getAppBridgeSession } from '@ctc-front/bridge-next'
import { getBridge } from '@/common/utils/appBridge'

export const frameworkAuth = createGfFrameworkAuth({
	// 请根据所属基座二选一：
	storageKey: 'monitor-user-info', // gf-monitor 基座
	// storageKey: 'law-user-info', // gf-law 基座
	bridge: () => getAppBridgeSession() || getBridge()
})

export default frameworkAuth
