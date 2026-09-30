# 真的假的鸭

面向普通群众和老年人的微信小程序反诈助手。用户可以粘贴短信、微信聊天、电话话术、可疑链接，或上传截图；系统会先用本地规则做风险分级，文字判断走 DeepSeek V4 Flash，截图只用 MiniMax M3 做 OCR 和文字提取。

当前仓库包含两部分：

- `miniprogram/`：正式主线，微信小程序前端。
- `cloudfunctions/`：小程序云函数，包含 DeepSeek V4 Flash 文字判断、MiniMax M3 截图 OCR 和规则兜底。
- `public/` + `server/`：早期网页原型，保留用于本地演示。

## 微信小程序开发

1. 用微信开发者工具导入项目根目录。
2. 在项目配置中确认：
   - `miniprogramRoot`: `miniprogram/`
   - `cloudfunctionRoot`: `cloudfunctions/`
3. 开通微信云开发。
4. 上传并部署云函数：
   - `analyzeCase`
   - `ocrImage`
5. 给云函数配置环境变量。

### `analyzeCase` 环境变量

- `MINIMAX_API_KEY`：MiniMax API Key，仅用于截图 OCR 和提取文字，必须放云函数环境变量，不能放小程序前端。
- `MINIMAX_API_BASE`：默认 `https://api.minimaxi.com/v1`，与虾小龙 M3 视觉链路保持一致；如果你的 key 来自国际站控制台，可改为 `https://api.minimax.io/v1`。
- `MINIMAX_CHAT_PATH`：默认 `/chat/completions`
- `MINIMAX_MODEL`：默认 `MiniMax-M3`
- `MINIMAX_GROUP_ID`：可选，仅在 MiniMax 控制台或工作区明确要求时配置。
- `MINIMAX_ENABLE_THINKING`：可选，设为 `false` 时会发送 `thinking: { "type": "disabled" }`。
- `MINIMAX_INLINE_IMAGE_MAX_BYTES`：可选，默认 `8388608`；截图会先转为 `data:image/...;base64,...` 再交给 M3 提取文字。
- `MODEL_API_TIMEOUT_MS`：可选，默认 `40000`；图片识别较慢时用于避免云函数提前中断。
- `DEEPSEEK_API_KEY`：DeepSeek API Key，文字判断主通道，必须放云函数环境变量，不能放小程序前端。
- `DEEPSEEK_API_BASE`：默认 `https://api.deepseek.com`
- `DEEPSEEK_FLASH_MODEL`：默认 `deepseek-v4-flash`

### `ocrImage` 环境变量

- `OCR_SERVICE_ID`：微信服务市场中已开通 OCR 服务的服务 ID。
- `OCR_SERVICE_API`：默认 `OcrAllInOne`，按实际 OCR 服务文档调整。
- `OCR_TYPE`：按实际 OCR 服务文档调整；不同服务的通用文字识别类型可能不同。
- `OCR_DATA_TYPE`：默认 `3`，表示通过图片 URL 识别，按实际服务文档调整。

## 网页原型

网页原型仍可本地运行，用于快速演示和调试：

```powershell
npm run dev
```

打开 `http://localhost:5177`。

## 当前能力

- 单小程序多入口：首页分流，`真假判断` 负责输入，`判断结果` 负责行动建议，活动二维码/首页卡片进入 5 题闯关模式
- 粘贴文本或链接进行诈骗风险分析
- 支持从微信剪贴板粘贴聊天内容
- 微信小程序上传截图后，`analyzeCase` 会先用 MiniMax M3 提取文字，再交给 DeepSeek V4 Flash 做文字判断
- 微信小程序上传截图后，可通过云函数 OCR 识别文字
- OCR 或文字判断完成后，云函数会尽量删除临时上传的截图
- 首页提供适老化分流入口：马上判断、已经出事、活动闯关
- 判断结果页加入“停 / 存 / 找”三格图示急救卡，减少慌张状态下的阅读负担
- 分析结果可一键分享/复制给家人
- 默认适老化界面：大字、大按钮、高对比、单线流程
- 小程序视觉加入克制的公益文化元素：深红、金线、书页、同心守护纹样
- 紧急场景优先提示停止操作、拨打 `110`、咨询 `96110`
- 选择“已转账 / 给过验证码 / 正在屏幕共享”等紧急状态后，立即展示止损步骤，不等待 AI 分析
- 活动闯关模式支持 5 题真假挑战、答题进度、反诈等级、盖章领奖提示、成绩复制和转发
- 判断页专注收集文字/截图/已发生状态，结果页将“现在只做这几件事”做成可勾选完成清单，帮助老人逐步确认已经做完的止损动作
- 本地规则引擎保底判断
- DeepSeek V4 Flash 负责文字判断；MiniMax M3 仅负责截图 OCR 和文字提取
- 识别常见诈骗类型：冒充公检法、客服退款/理赔、刷单返利、投资理财、屏幕共享/远程控制、钓鱼链接
- 判断当前阶段：早期核实、危险操作请求、隐私可能泄露、资金已风险、正在远程控制
- 按诈骗类型输出固定止损 SOP，并同步到结果页和可转发家属的话
- 输出个人隐私安全提醒：验证码、银行卡、身份证、人脸识别、密码、屏幕共享、通讯录和相册权限
- 输出风险等级、疑似诈骗类型、当前阶段、判断依据、固定止损 SOP、官方核实步骤、隐私保护步骤、报警提醒、证据清单和可转发家属的话

## 品牌资产

- `public/assets/logo-duck.png`：完整吉祥物，适合空状态、宣传页和结果页。
- `public/assets/icon-duck-512.png`：小程序头像、公众号头像、应用图标候选。
- `public/assets/icon-duck-192.png`：网页顶部品牌图标。
- `public/assets/favicon.png`：浏览器标签页图标。
- `miniprogram/assets/logo-duck-minjin.png`：小程序当前使用的公益文化气质主视觉。
- `miniprogram/assets/icon-duck-minjin-512.png`：小程序头像/图标候选。
- `miniprogram/assets/icon-duck-minjin-192.png`：小程序顶部品牌图标。
- `public/assets/logo-duck-minjin-bold.svg`：红金书页与公益徽章更突出的矢量探索稿。
- `public/assets/logo-duck-minjin-bold-preview.png`：上述探索稿的 PNG 预览图。
- `miniprogram/assets/design-iterations/`：本轮民进反诈公益鸭图标迭代稿归档。
- `miniprogram/assets/concept-boards/`：活动 IP、wildcard 方向板和总览图。
- `miniprogram/assets/landing-kit/`：C 区扫码闯关落地物料概念稿，包括展架、任务卡/印章、小程序成绩页和礼品延展。
- `output/pdf/zhenjiade-ya-wildcard-concepts-12.pdf`：12 张大胆方向板打包 PDF。
- `output/vendor-package/2026-06-07/`：广告公司交付包，包含 47 份 `pdf-print/` 核版 PDF、47 张 `png-preview/` 校对图、`contact-sheet.png` 总览图、`README_VENDOR.md` 制作说明、`production-spec.csv`/`production-spec.md` 下单规格表，以及 `handoff/` 活动物料交接手册、现场执行清单、最终信息回填、印前签核和完成度审计。
- `docs/VISUAL_DESIGN_ASSETS.md`：视觉探索约束、文件索引和推荐方向。

## 活动资料

- `docs/ACTIVITY_SOURCE_DIGEST.md`：2026-06-07 学习的 6 份活动资料摘要，覆盖 V5 执行手册、主持词、情景剧题库、各区 SOP、预算和 PPT 方案。

## 重要边界

本工具不能替代警方、银行或司法机关判断。若已经转账、泄露验证码/银行卡/身份证信息，或对方正在催促继续付款，应立即拨打 `110` 报警，并保存聊天记录、转账凭证、电话号码、链接和收款账户。`96110` 是反诈预警劝阻和咨询专线，接到来电请及时接听。

## 隐私策略草案

- 小程序前端不保存用户输入的聊天内容。
- MiniMax / DeepSeek API Key 只放在 `analyzeCase` 云函数环境变量中，不能放进小程序前端。
- 截图仅用于 OCR 和文字提取；`analyzeCase` 和 `ocrImage` 云函数处理完成或失败后都会尝试删除临时上传文件。
- 目前不主动落库保存分析记录。后续若要做家属守护、历史记录或反馈闭环，需要先增加明确授权和删除机制。
- 前端和分享文案会持续提醒：不要把验证码、银行卡、身份证、密码、人脸识别或屏幕共享交给陌生人。
