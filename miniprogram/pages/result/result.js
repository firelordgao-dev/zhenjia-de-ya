const riskCopy = {
  low: "低风险",
  medium: "中风险",
  high: "高风险",
  emergency: "紧急风险"
};

const panicSteps = [
  { icon: "停", title: "先停手", text: "不转钱" },
  { icon: "存", title: "留证据", text: "截图留好" },
  { icon: "找", title: "找人帮", text: "家人/110" }
];

Page({
  data: {
    analysis: null,
    riskText: "风险提醒",
    resultStampText: "停",
    visualSteps: panicSteps,
    actionSteps: [],
    privacyStep: "",
    verifyStep: "",
    isSafeFallback: false,
    retryText: "",
    hadImages: false,
    completedStepsMap: {},
    completedCount: 0,
    actionProgressPercent: 0,
    actionProgressText: "先按第 1 件做。",
    detailExpanded: false,
    detailToggleText: "展开详细说明"
  },

  onLoad() {
    this.loadLatestResult();
  },

  loadLatestResult() {
    const payload = wx.getStorageSync("latestAnalysisResult");
    const analysis = payload?.analysis;

    if (!analysis) {
      this.setData({
        analysis: null,
        riskText: "没有结果"
      });
      return;
    }

    const actionSteps = this.takeList(analysis.sop_steps, 3).map((item) => this.shortActionText(item));
    this.setData({
      analysis,
      riskText: payload.riskText || riskCopy[analysis.risk_level] || "风险提醒",
      resultStampText: analysis.risk_level === "low" ? "核" : "停",
      visualSteps: this.makeVisualSteps(analysis),
      actionSteps,
      privacyStep: this.shortSafetyText(this.firstItem(analysis.privacy_safety_steps)),
      verifyStep: this.shortSafetyText(this.firstItem(analysis.official_verification_steps)),
      isSafeFallback: analysis.is_safe_fallback === true,
      retryText: payload.retryText || "",
      hadImages: Boolean(payload.hadImages),
      completedStepsMap: {},
      completedCount: 0,
      actionProgressPercent: 0,
      actionProgressText: actionSteps.length ? "先按第 1 件做。" : "先停止操作，找人一起核实。",
      detailExpanded: false,
      detailToggleText: "展开详细说明"
    });
  },

  takeList(value, count) {
    return Array.isArray(value) ? value.slice(0, count) : [];
  },

  firstItem(value) {
    return Array.isArray(value) && value.length ? value[0] : "";
  },

  makeVisualSteps(analysis) {
    if (analysis.case_stage === "remote_control" || analysis.scam_type === "remote_control") {
      return [
        { icon: "断", title: "断开", text: "关共享" },
        { icon: "别", title: "别打开", text: "银行/短信" },
        { icon: "找", title: "换机求助", text: "家人/110" }
      ];
    }

    if (analysis.case_stage === "privacy_exposed") {
      return [
        { icon: "停", title: "别再给", text: "验证码/密码" },
        { icon: "改", title: "改密码", text: "官方 App" },
        { icon: "找", title: "找人帮", text: "银行/家人" }
      ];
    }

    if (analysis.risk_level === "emergency" || analysis.case_stage === "money_lost") {
      return [
        { icon: "停", title: "停止付款", text: "别付第二笔" },
        { icon: "存", title: "留证据", text: "截图/账号" },
        { icon: "报", title: "打 110", text: "马上报警" }
      ];
    }

    return panicSteps;
  },

  shortActionText(text) {
    const value = String(text || "");
    if (/屏幕共享|远程控制|远程协助|共享屏幕/.test(value)) return "关掉共享";
    if (/转账|充值|垫|保证金|付款|汇款|提现|交钱/.test(value)) return "别再转钱";
    if (/验证码|动态密码|短信码/.test(value)) return "别给验证码";
    if (/银行卡|身份证|密码|人脸识别|刷脸/.test(value)) return "别给隐私";
    if (/保存|截图|凭证|聊天记录|证据/.test(value)) return "留好截图";
    if (/110|报警|警方|派出所/.test(value)) return "打 110";
    if (/官方|客服|核实|银行|平台/.test(value)) return "走官方核实";
    if (/家人|亲友/.test(value)) return "找家人一起看";
    return value.length > 18 ? `${value.slice(0, 18)}...` : value;
  },

  shortSafetyText(text) {
    const value = String(text || "");
    if (/验证码|动态密码|短信码/.test(value)) return "验证码不要给。";
    if (/银行卡|支付密码|取款密码/.test(value)) return "银行卡、密码别填。";
    if (/身份证|人脸|刷脸/.test(value)) return "身份证、人脸先停。";
    if (/屏幕共享|远程控制|权限/.test(value)) return "关共享，关陌生权限。";
    if (/官方|链接|电话|客服/.test(value)) return "只走官方入口。";
    if (/银行|冻结|改密|账户/.test(value)) return "联系银行或平台。";
    return value.length > 20 ? `${value.slice(0, 20)}...` : value;
  },

  toggleActionStep(event) {
    const index = String(event.currentTarget.dataset.index);
    const completedStepsMap = {
      ...this.data.completedStepsMap,
      [index]: !this.data.completedStepsMap[index]
    };
    const completedCount = Object.keys(completedStepsMap).filter((key) => completedStepsMap[key]).length;
    const total = this.data.actionSteps.length;

    this.setData({
      completedStepsMap,
      completedCount,
      actionProgressPercent: total ? Math.round((completedCount / total) * 100) : 0,
      actionProgressText: this.makeProgressText(completedCount, total)
    });
  },

  makeProgressText(completed, total) {
    if (!total) return "先停止操作，找人一起核实。";
    if (completed === 0) return "先按第 1 件做。";
    if (completed < total) return `已完成 ${completed}/${total}。`;
    return "完成。留好证据，必要时打 110。";
  },

  toggleDetails() {
    const detailExpanded = !this.data.detailExpanded;
    this.setData({
      detailExpanded,
      detailToggleText: detailExpanded ? "收起详细说明" : "展开详细说明"
    });
  },

  goCheckAgain() {
    wx.navigateTo({
      url: "/pages/check/check"
    });
  },

  retryWithText() {
    if (this.data.retryText && wx.setStorageSync) {
      wx.setStorageSync("pendingRetryText", this.data.retryText);
    }
    wx.navigateTo({
      url: "/pages/check/check?retry=text"
    });
  },

  retryWithImage() {
    wx.navigateTo({
      url: "/pages/check/check"
    });
  },

  goHome() {
    wx.reLaunch({
      url: "/pages/index/index"
    });
  },

  callPolice() {
    wx.makePhoneCall({ phoneNumber: "110" });
  },

  callAntiFraud() {
    wx.makePhoneCall({ phoneNumber: "96110" });
  },

  copyFamilyMessage() {
    wx.setClipboardData({
      data: this.buildShareText(),
      success: () => {
        wx.showToast({ title: "已复制给家人", icon: "success" });
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
      imageUrl: "/assets/logo-duck-minjin.jpg"
    };
  }
});
