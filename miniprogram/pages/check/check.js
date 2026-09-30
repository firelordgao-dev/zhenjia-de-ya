const riskCopy = {
  low: "低风险",
  medium: "中风险",
  high: "高风险",
  emergency: "紧急风险"
};

const scenarioOptions = [
  { value: "chat", label: "微信/短信" },
  { value: "phone", label: "电话" },
  { value: "payment", label: "转账/退款" },
  { value: "link", label: "链接/App" },
  { value: "investment", label: "投资/刷单" },
  { value: "other", label: "说不清" }
];

const stateOptions = [
  { value: "transferred", label: "已经转账或充值" },
  { value: "leakedCode", label: "给过验证码" },
  { value: "screenSharing", label: "正在屏幕共享" },
  { value: "installedApp", label: "下载了陌生 App" },
  { value: "clickedLink", label: "点过陌生链接" },
  { value: "gaveIdCard", label: "给过身份证或银行卡" }
];

const emergencyGuides = {
  general: {
    title: "先停止操作",
    summary: "转账、给码、共享屏幕都先停。先保住钱和账号。",
    steps: ["不要继续转账、充值、下载 App 或屏幕共享。", "保存聊天记录、电话、链接、二维码和转账凭证。", "马上联系家人；已经扣款或泄露验证码时，拨打 110。"]
  },
  screenSharing: {
    title: "马上结束屏幕共享",
    summary: "不要再打开银行、支付、短信、相册和通讯录。",
    steps: ["马上停止屏幕共享或远程控制。", "不要打开银行、支付、短信、相册和通讯录。", "换一台设备联系家人；如果对方催付款，直接拨打 110。"]
  },
  transferred: {
    title: "不要再付第二笔钱",
    summary: "马上保存证据，并联系银行或支付平台尝试止付。",
    steps: ["不要继续转账、充值或交保证金。", "保存聊天记录、收款账户、订单号和转账凭证。", "马上拨打 110，并联系银行或支付平台尝试止付。"]
  },
  leakedCode: {
    title: "不要再给验证码",
    summary: "验证码可能已经被用来登录、绑卡或确认转账。",
    steps: ["不要再给任何验证码、密码或人脸识别。", "尽快联系银行、支付平台或官方客服冻结账户。", "保存聊天记录和电话；如果已经扣款，立刻拨打 110。"]
  },
  installedApp: {
    title: "停止使用陌生 App",
    summary: "不要在陌生 App 里输入银行卡、密码或验证码。",
    steps: ["停止使用陌生 App，不要登录银行卡或支付账户。", "检查是否开过屏幕共享、远程控制或通讯录权限。", "找家人帮忙卸载并修改重要账户密码。"]
  },
  gaveIdCard: {
    title: "不要继续做人脸识别",
    summary: "身份证、银行卡和人脸信息都先别再补充。",
    steps: ["不要继续提供身份证、银行卡、密码或人脸识别。", "联系银行和相关官方平台确认账户安全。", "保存对方账号、聊天记录、链接和你提交过的资料截图。"]
  },
  clickedLink: {
    title: "退出陌生链接",
    summary: "不要在页面里填银行卡、密码或验证码。",
    steps: ["不要继续点链接、扫码或下载页面里的 App。", "如果填过银行卡或验证码，按已泄露处理并联系银行。", "保存链接、二维码和页面截图，必要时拨打 110。"]
  }
};

const emergencyPriority = ["screenSharing", "transferred", "leakedCode", "installedApp", "gaveIdCard", "clickedLink"];

const sampleText =
  "我是平台客服，你的快递丢失可以理赔 300 元。请马上点击这个链接填写银行卡号和验证码，逾期就不能退款。";

Page({
  data: {
    scenarioOptions,
    stateOptions,
    scenario: "chat",
    caseText: "",
    selectedStates: [],
    selectedStatesMap: {},
    urgentGuide: null,
    imagePaths: [],
    imageNames: [],
    uploadedFileIDs: [],
    ocrStatus: "上传截图后，可以先识别文字，也可以直接判断。",
    imageTextExtracted: false,
    showMoreOptions: false,
    ocrLoading: false,
    loading: false
  },

  onLoad(options = {}) {
    if (options.emergency === "1") {
      this.setData({ urgentGuide: emergencyGuides.general });
    }
    if (options.retry === "text" && wx.getStorageSync) {
      const retryText = String(wx.getStorageSync("pendingRetryText") || "").trim();
      if (retryText) {
        this.setData({ caseText: retryText });
        if (wx.removeStorageSync) wx.removeStorageSync("pendingRetryText");
      }
    }
  },

  selectScenario(event) {
    this.setData({
      scenario: event.currentTarget.dataset.scenario
    });
  },

  loadSample() {
    this.setData({
      caseText: sampleText,
      scenario: "payment"
    });
  },

  onTextInput(event) {
    this.setData({
      caseText: event.detail.value
    });
  },

  toggleMoreOptions() {
    this.setData({
      showMoreOptions: !this.data.showMoreOptions
    });
  },

  pasteFromClipboard() {
    wx.getClipboardData({
      success: (res) => {
        const text = String(res.data || "").trim();
        if (!text) {
          wx.showToast({ title: "剪贴板没有文字", icon: "none" });
          return;
        }

        this.appendTextBlock(text, "微信复制内容");
        wx.showToast({ title: "已粘贴", icon: "success" });
      },
      fail: () => {
        wx.showToast({ title: "没有读取到剪贴板", icon: "none" });
      }
    });
  },

  chooseScreenshot() {
    const remaining = 9 - this.data.imagePaths.length;
    if (remaining <= 0) {
      wx.showToast({ title: "最多9张截图", icon: "none" });
      return;
    }
    wx.chooseImage({
      count: remaining,
      sizeType: ["compressed"],
      sourceType: ["album", "camera"],
      success: (res) => {
        const newPaths = res.tempFilePaths || [];
        const newNames = newPaths.map((p) => p.split("/").pop() || "截图");
        this.setData({
          imagePaths: [...this.data.imagePaths, ...newPaths],
          imageNames: [...this.data.imageNames, ...newNames],
          uploadedFileIDs: [],
          imageTextExtracted: false,
          ocrStatus: `已选 ${this.data.imagePaths.length + newPaths.length}/9 张截图。可以识别文字，也可以直接判断。`
        });
      }
    });
  },

  removeImage(event) {
    const index = Number(event.currentTarget.dataset.index);
    const imagePaths = this.data.imagePaths.filter((_, i) => i !== index);
    const imageNames = this.data.imageNames.filter((_, i) => i !== index);
    const uploadedFileIDs = this.data.uploadedFileIDs.filter((_, i) => i !== index);
    this.setData({
      imagePaths,
      imageNames,
      uploadedFileIDs,
      imageTextExtracted: false,
      ocrStatus: imagePaths.length
        ? `已选 ${imagePaths.length}/9 张截图。可以识别文字，也可以直接判断。`
        : "上传截图后，可以先识别文字，也可以直接判断。"
    });
  },

  onStateChange(event) {
    const selectedStates = event.detail.value;
    const selectedStatesMap = selectedStates.reduce((map, value) => {
      map[value] = true;
      return map;
    }, {});
    const urgentGuide = this.makeUrgentGuide(selectedStates);

    this.setData({
      selectedStates,
      selectedStatesMap,
      urgentGuide
    });
  },

  makeUrgentGuide(selectedStates) {
    const state = emergencyPriority.find((value) => selectedStates.includes(value));
    if (!state) return null;
    return emergencyGuides[state];
  },

  async recognizeImage() {
    if (!this.data.imagePaths.length || this.data.ocrLoading) return;
    if (!wx.cloud) {
      this.setData({ ocrStatus: "当前小程序没有开启云开发，暂时不能识别截图。" });
      return;
    }

    this.setData({ ocrLoading: true, ocrStatus: "正在上传截图..." });

    try {
      const fileID = await this.uploadSingleImage(this.data.imagePaths[0]);
      this.setData({ ocrStatus: "正在提取文字..." });

      const result = await wx.cloud.callFunction({
        name: "analyzeCase",
        data: {
          ocrOnly: true,
          imageFileIDs: [fileID]
        }
      });

      const text = result?.result?.text?.trim();
      if (!text) {
        this.setData({ ocrStatus: this.formatOcrStatus(result?.result?.error || "没有提取到文字，可以直接分析截图。") });
        return;
      }

      this.appendTextBlock(text, "截图提取文字");
      this.setData({
        imageTextExtracted: true,
        ocrStatus: "已提取文字。下面分析会优先用文字，不重复识图。"
      });
    } catch (error) {
      this.setData({ ocrStatus: this.formatOcrStatus(`提取文字失败：${error.message || "请稍后再试"}`) });
    } finally {
      this.setData({ ocrLoading: false });
    }
  },

  formatOcrStatus(message) {
    const text = String(message || "").replace(/\s+/g, " ").trim();
    if (/invalid api key|2049|认证未通过/i.test(text)) {
      return "截图识别暂时失败：图片通道认证未通过。可先直接分析截图。";
    }
    return text.length > 64 ? `${text.slice(0, 64)}...` : text;
  },

  uploadSingleImage(filePath) {
    const cloudPath = `scam-screenshots/${Date.now()}-${Math.random().toString(16).slice(2)}.jpg`;
    return new Promise((resolve, reject) => {
      wx.cloud.uploadFile({
        cloudPath,
        filePath,
        success: (res) => resolve(res.fileID),
        fail: reject
      });
    });
  },

  async uploadAllImages() {
    const { imagePaths } = this.data;
    if (!imagePaths.length) return [];
    const uploads = imagePaths.map((path) => this.uploadSingleImage(path));
    return Promise.all(uploads);
  },

  appendTextBlock(text, title) {
    const current = this.data.caseText.trim();
    const block = `【${title}】\n${text.trim()}`;
    this.setData({
      caseText: current ? `${current}\n\n${block}` : block
    });
  },

  async analyze() {
    if (this.data.loading) return;
    const text = this.data.caseText.trim();
    if (!text && !this.data.imagePaths.length) {
      wx.showToast({
        title: "先粘贴文字或上传截图",
        icon: "none"
      });
      return;
    }

    if (!wx.cloud) {
      wx.showToast({
        title: "当前没有开启云开发",
        icon: "none"
      });
      return;
    }

    this.setData({ loading: true });

    let imageFileIDs = [];
    try {
      const shouldSendImages = this.data.imagePaths.length && (!this.data.imageTextExtracted || !text);
      if (shouldSendImages) {
        this.setData({ ocrStatus: "正在上传截图并一起分析..." });
        imageFileIDs = await this.uploadAllImages();
      } else if (this.data.imagePaths.length && this.data.imageTextExtracted) {
        this.setData({ ocrStatus: "已用提取文字分析，不重复识图。" });
      }

      const result = await wx.cloud.callFunction({
        name: "analyzeCase",
        data: {
          text: text || "用户只上传了截图，请直接分析截图中的聊天、短信、链接、二维码、付款或验证码风险。",
          scenario: this.data.scenario,
          userStates: this.data.selectedStates,
          imageNotes: imageFileIDs.length ? this.data.imageNames : [],
          imageFileIDs: imageFileIDs
        }
      });

      if (imageFileIDs.length) {
        this.setData({
          uploadedFileIDs: imageFileIDs,
          ocrStatus: "截图已随分析处理，临时上传文件会由云函数清理。"
        });
      }

      this.openResult(result.result.analysis);
    } catch (error) {
      if (imageFileIDs.length && wx.cloud.deleteFile) {
        wx.cloud.deleteFile({ fileList: imageFileIDs });
      }
      this.setData({ uploadedFileIDs: [] });
      this.openResult(this.makeFallbackAnalysis(error), {
        retryText: text,
        hadImages: this.data.imagePaths.length > 0
      });
    } finally {
      this.setData({ loading: false });
    }
  },

  openResult(analysis, extra = {}) {
    wx.setStorageSync("latestAnalysisResult", {
      analysis,
      riskText: riskCopy[analysis.risk_level] || "风险提醒",
      createdAt: Date.now(),
      retryText: extra.retryText || "",
      hadImages: Boolean(extra.hadImages)
    });
    wx.navigateTo({
      url: "/pages/result/result"
    });
  },

  makeFallbackAnalysis(error) {
    const message = String(error?.message || "");
    const isNetworkSlow = /timeout|timed out|ETIMEDOUT|ECONNRESET|ENOTFOUND|network|socket/i.test(message);
    return {
      risk_level: "medium",
      is_safe_fallback: true,
      scam_type: "unknown",
      scam_type_label: "暂未完全判断",
      case_stage: "suspicious_request",
      case_stage_label: "网络慢，先暂停",
      summary: isNetworkSlow ? "网络慢或识别超时，先按可疑情况处理。" : "分析服务暂时不稳定，先按可疑情况处理。",
      judgement_basis: ["工具暂时没有完整分析成功，但涉及钱款、验证码、银行卡或陌生链接时都应先暂停。"],
      red_flags: [error.message || "分析服务暂时不可用"],
      sop_steps: ["先停止操作，不要继续回复或转账。", "不要提供验证码、银行卡、身份证、密码或人脸识别。", "保存聊天记录、电话、链接和转账凭证，找家人或官方渠道核实。"],
      official_verification_steps: ["不要点对方发来的链接。", "只从官方 App、官方客服电话或线下柜台核实。"],
      privacy_risks: ["验证码、银行卡、身份证、密码和人脸识别都属于重要隐私。"],
      privacy_safety_steps: ["不要再提供验证码、密码、银行卡或身份证。", "如果已经填过信息，马上联系银行或官方平台处理账户安全。"],
      privacy_notice: "先保护好个人隐私，不要继续给对方任何验证码或账户信息。",
      recommended_actions: ["只用文字再试一次。", "重新上传清晰截图。", "找家人或官方客服一起核实。"],
      police_notice: "如果已经转账或泄露重要信息，请立即拨打 110 报警。",
      evidence_to_keep: ["聊天记录", "电话号码", "链接或二维码", "转账凭证"],
      family_message: "我遇到一段可疑信息，工具暂时没分析成功，请帮我一起看看。"
    };
  },

  callPolice() {
    wx.makePhoneCall({ phoneNumber: "110" });
  },

  callAntiFraud() {
    wx.makePhoneCall({ phoneNumber: "96110" });
  },

  copyUrgentGuide() {
    const guide = this.data.urgentGuide;
    if (!guide) return;

    const steps = guide.steps.map((item, index) => `${index + 1}. ${item}`).join("\n");
    wx.setClipboardData({
      data: [`情况：${guide.title}`, `提醒：${guide.summary}`, "", steps].join("\n"),
      success: () => {
        wx.showToast({ title: "已复制", icon: "success" });
      }
    });
  }
});
