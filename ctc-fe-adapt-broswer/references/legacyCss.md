# legacyCssCompat 实验方案与风险说明

## 状态

`legacyCssCompat` 是针对特定项目产物的实验性 Vite/PostCSS 方案，不是 Tailwind CSS 4 的通用旧浏览器兼容层。禁止未经过项目级测试就复制到其他仓库，也禁止仅凭产物字符串扫描宣称兼容完成。

## 为什么不能做通用机械转换

| 转换 | 主要风险 | 必须验证 |
| --- | --- | --- |
| 展开 CSS nesting | 插件语义和原生 nesting 版本差异 | 复杂选择器、伪类、媒体查询 |
| 逻辑属性转物理属性 | 动态 RTL、writing-mode 信息丢失 | 中英文方向切换、纵向书写 |
| 删除 `@layer` | layered 与 unlayered 规则的优先级及 layer 声明顺序改变 | Reset、组件库覆盖、utility 优先级 |
| `@property` 转 `:root` | 丢失 `syntax`、`inherits` 和动画插值语义 | 主题变量、transform、动画 |
| 去除 `:where()` | specificity 从零提升为参数选择器的 specificity | hover、组件库覆盖、组合选择器 |
| 合并独立 transform | 独立属性采用固定组合顺序，直接拼接可能改变矩阵结果 | translate、rotate、scale 与已有 transform 组合 |
| gap 转子元素 margin | wrap、reverse、RTL、Grid、隐藏元素和原有 margin 行为不同 | 横纵布局、换行、嵌套容器 |
| 删除 `crossorigin` | 掩盖部署端响应头错误并改变跨域请求语义 | 同源/跨域 CDN、SRI、缓存和正式服务器响应头 |

## 允许采用实验转换的条件

必须同时满足：

1. 已在明确版本的目标浏览器复现问题。
2. 无法通过避免该特性或局部渐进增强解决。
3. 转换范围可以限定到已知文件、layer 或选择器，而非无差别修改全部产物。
4. 产品和设计接受记录在案的降级差异。
5. 具备自动 fixture、截图回归、关键流程测试及真实设备验收。

## 推荐实现方式

- 使用 PostCSS selector/value parser 等结构化解析器，禁止用字符串切分处理逗号选择器、嵌套函数或复杂 CSS 值。
- 每个转换独立成插件并提供开关，默认全部关闭；项目只能启用已验证的转换。
- 保留 source map，并在转换失败时终止构建，不静默输出部分转换产物。
- 输出转换统计和产物体积变化，便于升级构建工具时发现漂移。
- 不在 CSS 兼容插件中处理压缩、删除 console 或部署服务器 CORS 等其他职责。

## 最小 fixture 集合

```text
fixtures/
├── layer-order/
├── where-specificity/
├── property-inheritance/
├── transform-order/
├── flex-gap-row-column/
├── flex-gap-wrap-reverse-rtl/
└── complex-selectors/
```

每个 fixture 至少保存输入 CSS、预期输出 CSS 和最小 HTML。涉及布局或层叠语义时必须增加截图基线，不能只断言字符串被删除。

## 验收记录

每次项目启用实验转换，应记录：

- 浏览器产品、版本、内核、操作系统。
- Vite、Tailwind、PostCSS 和转换插件版本。
- 启用的转换及明确作用范围。
- 自动化测试、截图对比和真实设备 smoke test 结果。
- 已知差异、回退开关、维护人和复审日期。
