# 真的假的鸭

面向普通群众和老年人的微信小程序反诈助手。用户可以粘贴短信、微信聊天、电话话术、可疑链接，或上传截图识别文字；系统会先用本地规则做风险分级，再调用 DeepSeek V4 Flash/Pro 做反诈分析和适老化行动提醒。

当前仓库包含两部分：

- `miniprogram/`：正式主线，微信小程序前端。
- `cloudfunctions/`：小程序云函数，包含 DeepSeek 分析和 OCR 适配。
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

- `DEEPSEEK_API_KEY`：DeepSeek API Key，必须放云函数环境变量，不能放小程序前端。
- `DEEPSEEK_API_BASE`：默认 `https://api.deepseek.com`
- `DEEPSEEK_FLASH_MODEL`：默认 `deepseek-v4-flash`
- `DEEPSEEK_PRO_MODEL`：默认 `deepseek-v4-pro`

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

- 粘贴文本或链接进行诈骗风险分析
- 支持从微信剪贴板粘贴聊天内容
- 微信小程序上传截图后，可通过云函数 OCR 识别文字
- OCR 识别完成后，云函数会尽量删除临时上传的截图
- 分析结果可一键分享/复制给家人
- 默认适老化界面：大字、大按钮、高对比、单线流程
- 小程序视觉加入克制的公益文化元素：深红、金线、书页、同心守护纹样
- 紧急场景优先提示停止操作、拨打 `110`、咨询 `96110`
- 选择“已转账 / 给过验证码 / 正在屏幕共享”等紧急状态
- 本地规则引擎保底判断
- DeepSeek Flash + Pro 双模型路由
- 输出风险等级、危险点、下一步行动、报警提醒、证据清单和可转发家属的话

## 品牌资产

- `public/assets/logo-duck.png`：完整吉祥物，适合空状态、宣传页和结果页。
- `public/assets/icon-duck-512.png`：小程序头像、公众号头像、应用图标候选。
- `public/assets/icon-duck-192.png`：网页顶部品牌图标。
- `public/assets/favicon.png`：浏览器标签页图标。
- `miniprogram/assets/logo-duck-minjin.png`：小程序当前使用的公益文化气质主视觉。
- `miniprogram/assets/icon-duck-minjin-512.png`：小程序头像/图标候选。
- `miniprogram/assets/icon-duck-minjin-192.png`：小程序顶部品牌图标。

## 重要边界

本工具不能替代警方、银行或司法机关判断。若已经转账、泄露验证码/银行卡/身份证信息，或对方正在催促继续付款，应立即拨打 `110` 报警，并保存聊天记录、转账凭证、电话号码、链接和收款账户。`96110` 是反诈预警劝阻和咨询专线，接到来电请及时接听。

## 隐私策略草案

- 小程序前端不保存用户输入的聊天内容。
- DeepSeek API Key 只放在 `analyzeCase` 云函数环境变量中，不能放进小程序前端。
- 截图仅用于 OCR 识别；`ocrImage` 云函数识别完成或失败后都会尝试删除临时上传文件。
- 目前不主动落库保存分析记录。后续若要做家属守护、历史记录或反馈闭环，需要先增加明确授权和删除机制。
