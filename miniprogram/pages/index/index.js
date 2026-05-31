const riskCopy = {
  low: "低风险",
  medium: "中风险",
  high: "高风险",
  emergency: "紧急风险"
};

const scenarioOptions = [
  { value: "chat", label: "微信或短信" },
  { value: "phone", label: "电话里说的" },
  { value: "payment", label: "转账或退款" },
  { value: "link", label: "链接或 App" },
  { value: "investment", label: "投资或刷单" },
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
    title: "已经转账、给验证码或共享屏幕",
    summary: "先停止操作，先保住钱和账号。",
    steps: ["不要继续转账、充值、下载 App 或屏幕共享。", "保存聊天记录、电话、链接、二维码和转账凭证。", "马上联系家人；已经扣款或泄露验证码时，拨打 110。"]
  },
  screenSharing: {
    title: "正在屏幕共享",
    summary: "先结束共享，不要再打开银行、支付或短信。",
    steps: ["马上停止屏幕共享或远程控制。", "不要打开银行、支付、短信、相册和通讯录。", "换一台设备联系家人；如果对方催付款，直接拨打 110。"]
  },
  transferred: {
    title: "已经转账或充值",
    summary: "先别再付第二笔钱，马上保存证据并报警。",
    steps: ["不要继续转账、充值或交保证金。", "保存聊天记录、收款账户、订单号和转账凭证。", "马上拨打 110，并联系银行或支付平台尝试止付。"]
  },
  leakedCode: {
    title: "已经给过验证码",
    summary: "先别再给验证码，马上联系银行或平台改密码。",
    steps: ["不要再给任何验证码、密码或人脸识别。", "尽快联系银行、支付平台或官方客服冻结账户。", "保存聊天记录和电话；如果已经扣款，立刻拨打 110。"]
  },
  installedApp: {
    title: "下载了陌生 App",
    summary: "先别在这个 App 里输入银行卡、密码或验证码。",
    steps: ["停止使用陌生 App，不要登录银行卡或支付账户。", "检查是否开过屏幕共享、远程控制或通讯录权限。", "找家人帮忙卸载并修改重要账户密码。"]
  },
  gaveIdCard: {
    title: "给过身份证或银行卡",
    summary: "先别继续做人脸识别，也不要再补充更多资料。",
    steps: ["不要继续提供身份证、银行卡、密码或人脸识别。", "联系银行和相关官方平台确认账户安全。", "保存对方账号、聊天记录、链接和你提交过的资料截图。"]
  },
  clickedLink: {
    title: "点过陌生链接",
    summary: "先退出页面，不要填写银行卡、密码或验证码。",
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
    urgentHint: "",
    urgentGuide: null,
    imagePath: "",
    imageName: "",
    uploadedFileID: "",
    ocrStatus: "可以点“识别截图文字”，识别后文字会自动放进输入框。",
    ocrLoading: false,
    loading: false,
    statusText: "待分析",
    riskText: "风险提醒",
    detailExpanded: false,
    detailToggleText: "展开详细说明",
    analysis: null
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

  pasteFromClipboard() {
    wx.getClipboardData({
      success: (res) => {
        const text = String(res.data || "").trim();
        if (!text) {
          wx.showToast({
            title: "剪贴板没有文字",
            icon: "none"
          });
          return;
        }

        this.appendTextBlock(text, "微信复制内容");
        wx.showToast({
          title: "已粘贴",
          icon: "success"
        });
      },
      fail: () => {
        wx.showToast({
          title: "没有读取到剪贴板",
          icon: "none"
        });
      }
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
      urgentGuide,
      urgentHint: urgentGuide ? urgentGuide.summary : ""
    });
  },

  chooseScreenshot() {
    wx.chooseImage({
      count: 1,
      sizeType: ["compressed"],
      sourceType: ["album", "camera"],
      success: (res) => {
        const imagePath = res.tempFilePaths[0];
        this.setData({
          imagePath,
          imageName: imagePath.split("/").pop() || "已选择截图",
          uploadedFileID: "",
          ocrStatus: "可以点“识别截图文字”，识别后文字会自动放进输入框。"
        });
      }
    });
  },

  async recognizeImage() {
    if (!this.data.imagePath) return;
    if (!wx.cloud) {
      this.setData({ ocrStatus: "当前小程序没有开启云开发，暂时不能识别截图。" });
      return;
    }

    this.setData({
      ocrLoading: true,
      ocrStatus: "正在上传截图..."
    });

    try {
      const fileID = this.data.uploadedFileID || (await this.uploadImage());
      this.setData({ ocrStatus: "正在识别截图文字..." });

      const result = await wx.cloud.callFunction({
        name: "ocrImage",
        data: { fileID }
      });

      const text = result?.result?.text?.trim();
      if (!text) {
        this.setData({
          ocrStatus: result?.result?.error || "没有识别出清楚文字。可以简单打字说明。"
        });
        return;
      }

      this.appendRecognizedText(text);
      this.setData({
        ocrStatus: "已识别截图文字，并放进输入框。你可以检查一下再分析。"
      });
    } catch (error) {
      this.setData({
        ocrStatus: `截图识别失败：${error.message || "请稍后再试"}`
      });
    } finally {
      this.setData({ ocrLoading: false });
    }
  },

  uploadImage() {
    const cloudPath = `scam-screenshots/${Date.now()}-${Math.random().toString(16).slice(2)}.jpg`;
    return new Promise((resolve, reject) => {
      wx.cloud.uploadFile({
        cloudPath,
        filePath: this.data.imagePath,
        success: (res) => {
          this.setData({ uploadedFileID: res.fileID });
          resolve(res.fileID);
        },
        fail: reject
      });
    });
  },

  appendRecognizedText(text) {
    this.appendTextBlock(text, "截图识别文字");
  },

  appendTextBlock(text, title) {
    const current = this.data.caseText.trim();
    const block = `【${title}】\n${text.trim()}`;
    this.setData({
      caseText: current ? `${current}\n\n${block}` : block
    });
  },

  makeUrgentGuide(selectedStates) {
    const state = emergencyPriority.find((value) => selectedStates.includes(value));
    if (!state) return null;
    return emergencyGuides[state];
  },

  copyUrgentGuide() {
    const guide = this.data.urgentGuide;
    if (!guide) return;

    const steps = guide.steps.map((item, index) => `${index + 1}. ${item}`).join("\n");
    wx.setClipboardData({
      data: [
        "我在用“真的假的鸭”检查可疑情况，现在先按紧急止损处理。",
        "",
        `情况：${guide.title}`,
        `提醒：${guide.summary}`,
        "",
        "请帮我一起做：",
        steps
      ].join("\n"),
      success: () => {
        wx.showToast({
          title: "已复制给家人",
          icon: "success"
        });
      }
    });
  },

  showGeneralEmergencyGuide() {
    this.setData({
      urgentGuide: emergencyGuides.general,
      urgentHint: emergencyGuides.general.summary
    });

    if (wx.pageScrollTo) {
      wx.pageScrollTo({
        selector: ".urgent-guide",
        duration: 240
      });
    }
  },

  async analyze() {
    const text = this.data.caseText.trim();
    if (!text) {
      this.showInlineError(
        this.data.imagePath ? "请先点“识别截图文字”，或简单写下对方让你做什么。" : "请先写下对方让你做什么。"
      );
      return;
    }

    if (!wx.cloud) {
      this.showInlineError("当前小程序没有开启云开发，暂时不能分析。");
      return;
    }

    this.setData({
      loading: true,
      analysis: null,
      statusText: "分析中"
    });

    try {
      const result = await wx.cloud.callFunction({
        name: "analyzeCase",
        data: {
          text,
          scenario: this.data.scenario,
          userStates: this.data.selectedStates,
          imageNotes: this.data.imageName ? [this.data.imageName] : []
        }
      });

      this.renderResult(result.result.analysis);
    } catch (error) {
      this.renderResult({
        risk_level: "medium",
        scam_type: "unknown",
        scam_type_label: "暂未明确类型",
        case_stage: "suspicious_request",
        case_stage_label: "需要先暂停核实",
        summary: "暂时没有分析成功，先按可疑情况处理。",
        judgement_basis: ["分析服务暂时不可用，但涉及钱款、验证码、银行卡或陌生链接时都应先暂停。"],
        red_flags: [error.message || "分析服务暂时不可用"],
        sop_steps: ["先停止操作，不要继续回复对方。", "保存聊天记录、电话、链接和转账凭证。", "找家人或官方渠道一起核实。"],
        official_verification_steps: ["不要点对方发来的链接。", "只从官方 App、官方客服电话或线下柜台核实。"],
        privacy_risks: ["验证码、银行卡、身份证、密码和人脸识别都属于重要隐私。"],
        privacy_safety_steps: ["不要再提供验证码、密码、银行卡或身份证。", "如果已经填过信息，马上联系银行或官方平台处理账户安全。"],
        privacy_notice: "先保护好个人隐私，不要继续给对方任何验证码或账户信息。",
        recommended_actions: ["先不要转账。", "不要给验证码、密码、银行卡。", "找家人或官方客服一起核实。"],
        police_notice: "如果已经转账或泄露重要信息，请立即拨打 110 报警。",
        evidence_to_keep: ["聊天记录", "电话号码", "链接或二维码", "转账凭证"],
        family_message: "我遇到一段可疑信息，工具暂时没分析成功，请帮我一起看看。"
      });
    } finally {
      this.setData({ loading: false });
    }
  },

  renderResult(analysis) {
    const riskText = riskCopy[analysis.risk_level] || "风险提醒";
    this.setData({
      analysis: this.makeDisplayAnalysis(analysis),
      riskText,
      statusText: riskText,
      detailExpanded: false,
      detailToggleText: "展开详细说明"
    });
  },

  makeDisplayAnalysis(analysis) {
    return {
      ...analysis,
      display_sop_steps: this.takeList(analysis.sop_steps, 3),
      display_privacy_step: this.firstItem(analysis.privacy_safety_steps),
      display_verify_step: this.firstItem(analysis.official_verification_steps)
    };
  },

  takeList(value, count) {
    return Array.isArray(value) ? value.slice(0, count) : [];
  },

  firstItem(value) {
    return Array.isArray(value) && value.length ? value[0] : "";
  },

  toggleDetails() {
    const detailExpanded = !this.data.detailExpanded;
    this.setData({
      detailExpanded,
      detailToggleText: detailExpanded ? "收起详细说明" : "展开详细说明"
    });
  },

  showInlineError(message) {
    this.renderResult({
      risk_level: "medium",
      scam_type: "unknown",
      scam_type_label: "暂未明确类型",
      case_stage: "early_check",
      case_stage_label: "还在早期核实",
      summary: message,
      judgement_basis: ["现在信息还不够完整，但涉及钱、验证码、链接、App 和个人信息时要先停下。"],
      red_flags: ["现在还没有足够内容可以判断。"],
      sop_steps: ["先别继续操作。", "把对方让你做的事补充清楚。", "涉及钱、验证码、链接时先找家人核实。"],
      official_verification_steps: ["不要用对方提供的电话或链接。", "自己打开官方 App，或从官方渠道查客服电话。"],
      privacy_risks: ["暂未看到明确隐私泄露，但验证码、银行卡、身份证、密码和人脸识别都不能发给陌生人。"],
      privacy_safety_steps: ["不要在陌生链接里填写个人信息。", "不要开启屏幕共享或远程控制。"],
      privacy_notice: "先保护好个人隐私，不要把验证码、银行卡、身份证或密码发给对方。",
      recommended_actions: ["补充对方说了什么。", "补充对方让你做什么。", "如果涉及钱或验证码，先停下。"],
      police_notice: "如果已经转账、给过验证码或泄露银行卡信息，请立即拨打 110 报警。",
      evidence_to_keep: ["聊天记录", "电话号码", "链接或二维码"],
      family_message: "我有一段可疑信息还没弄清楚，请帮我一起看看。"
    });
  },

  callPolice() {
    wx.makePhoneCall({ phoneNumber: "110" });
  },

  callAntiFraud() {
    wx.makePhoneCall({ phoneNumber: "96110" });
  },

  copyFamilyMessage() {
    const text = this.buildShareText();
    wx.setClipboardData({
      data: text,
      success: () => {
        wx.showToast({
          title: "已复制给家人",
          icon: "success"
        });
      }
    });
  },

  buildShareText() {
    const analysis = this.data.analysis;
    if (!analysis) return "我遇到一段可疑信息，请帮我一起看看。";

    const actions = (analysis.recommended_actions || [])
      .map((item, index) => `${index + 1}. ${item}`)
      .join("\n");
    const sop = (analysis.sop_steps || [])
      .map((item, index) => `${index + 1}. ${item}`)
      .join("\n");
    const privacy = (analysis.privacy_safety_steps || [])
      .map((item, index) => `${index + 1}. ${item}`)
      .join("\n");

    return [
      "我用“真的假的鸭”检查了一段可疑信息，请帮我一起确认。",
      "",
      `风险等级：${riskCopy[analysis.risk_level] || "有风险"}`,
      `疑似类型：${analysis.scam_type_label || "暂未明确类型"}`,
      `当前阶段：${analysis.case_stage_label || "需要核实"}`,
      `结论：${analysis.summary || "建议暂停操作并核实。"}`,
      "",
      "这类情况先这样做：",
      sop || "先停止操作，保存证据，找家人或官方渠道核实。",
      "",
      "个人隐私先这样保护：",
      privacy || "不要再提供验证码、银行卡、身份证、密码或人脸识别。",
      "",
      "现在建议：",
      actions || "先停止操作，找家人或官方渠道核实。",
      "",
      analysis.police_notice || "如果已经转账或泄露重要信息，请立即拨打 110 报警。"
    ].join("\n");
  },

  onShareAppMessage() {
    const analysis = this.data.analysis;
    return {
      title: analysis ? `真的假的鸭提醒：${riskCopy[analysis.risk_level] || "有风险"}` : "真的假的鸭：转账之前，先问一问",
      path: "/pages/index/index",
      imageUrl: "/assets/logo-duck-minjin.png"
    };
  }
});
