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
    imagePath: "",
    imageName: "",
    uploadedFileID: "",
    ocrStatus: "可以点“识别截图文字”，识别后文字会自动放进输入框。",
    ocrLoading: false,
    loading: false,
    statusText: "待分析",
    riskText: "风险提醒",
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

    this.setData({
      selectedStates,
      selectedStatesMap,
      urgentHint: this.makeUrgentHint(selectedStates)
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

  makeUrgentHint(selectedStates) {
    if (selectedStates.includes("transferred")) {
      return "你已经转账了。先别继续付款，马上保存证据，并拨打 110。";
    }
    if (selectedStates.includes("leakedCode")) {
      return "你已经给过验证码。先别继续操作，马上联系银行或平台，并视情况拨打 110。";
    }
    if (selectedStates.includes("screenSharing")) {
      return "你正在屏幕共享。请立刻停止共享，不要打开银行或支付 App。";
    }
    return "";
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
        summary: "暂时没有分析成功，先按可疑情况处理。",
        red_flags: [error.message || "分析服务暂时不可用"],
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
      analysis,
      riskText,
      statusText: riskText
    });
  },

  showInlineError(message) {
    this.renderResult({
      risk_level: "medium",
      summary: message,
      red_flags: ["现在还没有足够内容可以判断。"],
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

    return [
      "我用“真的假的鸭”检查了一段可疑信息，请帮我一起确认。",
      "",
      `风险等级：${riskCopy[analysis.risk_level] || "有风险"}`,
      `结论：${analysis.summary || "建议暂停操作并核实。"}`,
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
