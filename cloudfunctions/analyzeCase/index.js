const https = require("https");

const KEYWORD_RULES = [
  {
    label: "验证码或动态密码",
    weight: 32,
    patterns: [/验证码/, /动态密码/, /短信码/, /校验码/, /不要告诉别人/, /安全码/],
    reason: "对方提到验证码或动态密码，诈骗中常用来盗号、转账或绑定支付。"
  },
  {
    label: "转账或垫付",
    weight: 34,
    patterns: [/转账/, /汇款/, /打款/, /垫付/, /保证金/, /手续费/, /解冻金/, /认证金/, /刷流水/, /充值/],
    reason: "对方要求先付钱或刷流水，这是高频诈骗动作。"
  },
  {
    label: "冒充客服或平台",
    weight: 22,
    patterns: [/客服/, /官方客服/, /退款/, /理赔/, /订单异常/, /快递丢失/, /账户异常/, /会员到期/, /自动扣费/],
    reason: "冒充客服退款、理赔或取消扣费，是常见诈骗开场。"
  },
  {
    label: "冒充公检法或监管",
    weight: 42,
    patterns: [/公安/, /警官/, /检察院/, /法院/, /通缉/, /洗钱/, /涉案/, /安全账户/, /资金清查/, /保密/],
    reason: "公检法不会通过聊天软件要求转账，也不会让群众把钱转到所谓安全账户。"
  },
  {
    label: "投资理财或高收益",
    weight: 30,
    patterns: [/稳赚/, /内幕/, /导师/, /带单/, /高收益/, /虚拟币/, /股票群/, /投资平台/, /返利/, /收益率/],
    reason: "承诺高收益、导师带单、稳赚不赔，通常有较强诈骗风险。"
  },
  {
    label: "刷单返利",
    weight: 36,
    patterns: [/刷单/, /做任务/, /返佣/, /点赞赚钱/, /兼职/, /接单/, /先小额返利/, /任务单/],
    reason: "刷单返利类骗局通常先给小额甜头，再诱导大额垫付。"
  },
  {
    label: "陌生链接或下载 App",
    weight: 28,
    patterns: [/http:\/\//, /https:\/\//, /点击链接/, /下载.*app/i, /安装.*app/i, /屏幕共享/, /远程控制/, /会议软件/],
    reason: "陌生链接、陌生 App、屏幕共享或远程控制可能暴露银行卡和验证码。"
  },
  {
    label: "制造紧迫感",
    weight: 18,
    patterns: [/马上/, /立即/, /限时/, /逾期/, /冻结/, /关闭账户/, /影响征信/, /最后一次/, /不要挂电话/],
    reason: "骗子常用催促和恐吓让人来不及核实。"
  },
  {
    label: "索要隐私信息",
    weight: 26,
    patterns: [/身份证/, /银行卡/, /密码/, /人脸识别/, /银行卡号/, /手机号/, /支付密码/, /登录密码/],
    reason: "对方索要身份证、银行卡、密码或人脸识别信息，风险很高。"
  }
];

const EMERGENCY_STATE_WEIGHTS = {
  transferred: 45,
  leakedCode: 45,
  screenSharing: 42,
  installedApp: 28,
  gaveIdCard: 24,
  clickedLink: 18
};

const SCAM_TYPE_RULES = [
  {
    type: "police_impersonation",
    label: "冒充公检法诈骗",
    weight: 48,
    patterns: [/公安/, /警官/, /检察院/, /法院/, /通缉/, /洗钱/, /涉案/, /安全账户/, /资金清查/, /保密/],
    sop: [
      "马上挂断电话或停止聊天，不要继续听对方指挥。",
      "不要转到所谓“安全账户”，公检法不会让群众转账自证清白。",
      "保存电话号码、聊天记录和转账凭证，立即拨打 110。"
    ]
  },
  {
    type: "customer_service_refund",
    label: "冒充客服退款/理赔诈骗",
    weight: 38,
    patterns: [/客服/, /退款/, /理赔/, /快递丢失/, /订单异常/, /会员到期/, /自动扣费/, /取消会员/],
    sop: [
      "不要点对方发来的链接，也不要下载对方要求的 App。",
      "不要填写银行卡、验证码、支付密码或身份证信息。",
      "从官方 App 或官方客服电话核实，不要用对方提供的电话。"
    ]
  },
  {
    type: "task_rebate",
    label: "刷单返利/做任务诈骗",
    weight: 40,
    patterns: [/刷单/, /做任务/, /返佣/, /点赞赚钱/, /兼职/, /接单/, /任务单/, /垫付/],
    sop: [
      "立刻停止继续做任务，不要为了提现再垫钱。",
      "保存群聊、任务单、收款账户和转账记录。",
      "如果已经转账，马上拨打 110，并联系银行或支付平台尝试止付。"
    ]
  },
  {
    type: "investment",
    label: "投资理财诈骗",
    weight: 36,
    patterns: [/投资/, /理财/, /稳赚/, /内幕/, /导师/, /带单/, /高收益/, /虚拟币/, /股票群/, /收益率/],
    sop: [
      "不要继续充值、加仓或跟着“导师”操作。",
      "不要相信稳赚、内幕消息或快速回本承诺。",
      "保存投资平台网址、App 名称、聊天记录和转账凭证。"
    ]
  },
  {
    type: "remote_control",
    label: "屏幕共享/远程控制诈骗",
    weight: 42,
    patterns: [/屏幕共享/, /远程控制/, /会议软件/, /下载.*app/i, /安装.*app/i, /共享屏幕/, /远程协助/],
    sop: [
      "马上停止屏幕共享或远程控制。",
      "不要打开银行、支付、短信或验证码页面。",
      "尽快修改支付密码，并联系银行检查账户安全。"
    ]
  },
  {
    type: "phishing_link",
    label: "陌生链接/钓鱼页面风险",
    weight: 30,
    patterns: [/http:\/\//, /https:\/\//, /点击链接/, /二维码/, /填写资料/, /银行卡号/, /验证码/],
    sop: [
      "先不要继续点链接，也不要扫码。",
      "如果填过银行卡或验证码，马上联系银行和支付平台。",
      "把链接、二维码和页面截图保存下来，必要时拨打 110。"
    ]
  }
];

const PRIVACY_RULES = [
  {
    label: "验证码或动态密码",
    patterns: [/验证码/, /动态密码/, /短信码/, /校验码/, /安全码/],
    risk: "验证码可能被用来登录账号、绑定支付或确认转账。",
    step: "不要再给验证码；如果已经给过，马上联系银行、微信/支付宝或相关平台检查账户。"
  },
  {
    label: "银行卡或支付信息",
    patterns: [/银行卡/, /银行卡号/, /支付密码/, /取款密码/, /开户地址/, /收款账户/],
    risk: "银行卡号、支付密码和收款账户可能导致资金被转走或继续被套取。",
    step: "不要继续填写银行卡和支付密码；如果填过，马上联系银行冻结或改密。"
  },
  {
    label: "身份证或人脸识别",
    patterns: [/身份证/, /身份证号/, /人脸识别/, /刷脸/, /手持身份证/, /实名/],
    risk: "身份证和人脸识别可能被用来注册账号、借贷或冒用身份。",
    step: "不要继续做人脸识别；保存提交页面截图，并联系相关平台核查实名和借贷记录。"
  },
  {
    label: "账号密码",
    patterns: [/登录密码/, /密码/, /账号/, /账户异常/, /修改密码/],
    risk: "账号密码泄露后，对方可能登录微信、支付、网银或购物平台。",
    step: "尽快修改重要账号密码；不要在对方发来的页面里改密码。"
  },
  {
    label: "通讯录、相册或屏幕内容",
    patterns: [/通讯录/, /相册/, /屏幕共享/, /远程控制/, /远程协助/, /会议软件/, /共享屏幕/],
    risk: "屏幕共享、通讯录和相册权限可能暴露短信、验证码、亲友信息和银行卡页面。",
    step: "马上停止屏幕共享或远程控制，关闭陌生 App 权限，不要打开银行和支付页面。"
  }
];

const SYSTEM_PROMPT = `你是“真的假的鸭”的反诈分析 agent，服务对象是普通群众和老年人。
你的任务：根据用户提供的短信、聊天、电话话术、链接或事件描述，判断诈骗风险并给出清晰行动建议。

重要边界：
- 你不是警方、律师或银行，不能说“已经确定是诈骗分子”，只能做风险判断。
- 如果已经转账、泄露验证码/银行卡/身份证/密码、正在屏幕共享、下载了陌生 App、或对方继续催付款，必须提醒用户立即拨打 110 报警并保留证据。
- 96110 是反诈预警劝阻和咨询专线，接到来电应及时接听；紧急报案优先 110。
- 不要输出 Markdown，不要输出代码块，只返回 JSON。
- 用大白话，句子短，适合老人理解。
- 你必须判断最接近的诈骗类型；不确定时用 "unknown"，但仍要给可执行止损步骤。
- sop_steps 要比 recommended_actions 更具体，按诈骗类型说明“马上做什么、不要做什么、保存什么证据”。
- 必须提醒保护个人隐私信息，尤其是验证码、银行卡、身份证、人脸识别、密码、屏幕共享、通讯录和相册权限。
- official_verification_steps 只能建议用户走官方 App、官方客服电话、银行柜台、派出所或 110/96110；不要让用户点击对方提供的链接或拨打对方提供的号码。

返回 JSON，字段必须完整：
{
  "risk_level": "low | medium | high | emergency",
  "is_likely_scam": true,
  "confidence": 0.0,
  "summary": "一句话结论",
  "case_stage": "early_check | suspicious_request | privacy_exposed | money_lost | remote_control",
  "case_stage_label": "当前处在哪一步",
  "judgement_basis": ["判断依据1", "判断依据2"],
  "red_flags": ["危险点1", "危险点2"],
  "recommended_actions": ["下一步1", "下一步2"],
  "scam_type": "police_impersonation | customer_service_refund | task_rebate | investment | remote_control | phishing_link | unknown",
  "scam_type_label": "诈骗类型中文名",
  "sop_steps": ["该类型止损步骤1", "该类型止损步骤2"],
  "official_verification_steps": ["官方核实步骤1", "官方核实步骤2"],
  "privacy_risks": ["隐私风险1", "隐私风险2"],
  "privacy_safety_steps": ["隐私保护步骤1", "隐私保护步骤2"],
  "privacy_notice": "一句话隐私提醒",
  "police_notice": "报警或反诈专线提醒",
  "should_contact_police": false,
  "evidence_to_keep": ["证据1", "证据2"],
  "family_message": "可转发给家人的一句话"
}`;

exports.main = async (event = {}) => {
  const normalized = normalizeInput(event);
  const rules = analyzeWithRules(normalized);
  const scamProfile = detectScamType(normalized, rules);
  const privacyProfile = detectPrivacyRisks(normalized);
  const caseStage = detectCaseStage(normalized, rules, privacyProfile);
  const fallback = buildRuleFallback(normalized, rules, scamProfile, privacyProfile, caseStage);

  if (!process.env.DEEPSEEK_API_KEY) {
    return {
      analysis: fallback,
      meta: buildMeta({ rules, scamProfile, privacyProfile, caseStage, mode: "rules_only", usedModels: [], warning: "DEEPSEEK_API_KEY 未配置" })
    };
  }

  const usedModels = [];
  try {
    const flashModel = process.env.DEEPSEEK_FLASH_MODEL || "deepseek-v4-flash";
    const proModel = process.env.DEEPSEEK_PRO_MODEL || "deepseek-v4-pro";

    const flash = await runModelAnalysis(flashModel, normalized, rules, scamProfile, privacyProfile, caseStage, null);
    usedModels.push(flashModel);
    let analysis = sanitizeAnalysis(flash, fallback);

    const shouldUsePro =
      rules.shouldEscalateToPro ||
      ["high", "emergency"].includes(analysis.risk_level) ||
      analysis.confidence < 0.62;

    if (shouldUsePro) {
      const pro = await runModelAnalysis(proModel, normalized, rules, scamProfile, privacyProfile, caseStage, analysis);
      usedModels.push(proModel);
      analysis = sanitizeAnalysis(pro, analysis);
    }

    analysis = enforceSafetyFloor(analysis, rules, scamProfile, privacyProfile, caseStage);
    return {
      analysis,
      meta: buildMeta({ rules, scamProfile, privacyProfile, caseStage, mode: "deepseek", usedModels })
    };
  } catch (error) {
    return {
      analysis: {
        ...fallback,
        model_note: "大模型调用失败，已使用本地规则引擎给出保底判断。"
      },
      meta: buildMeta({ rules, scamProfile, privacyProfile, caseStage, mode: "rules_fallback", usedModels, warning: error.message })
    };
  }
};

function normalizeInput(input) {
  return {
    text: String(input.text || "").slice(0, 9000).trim(),
    scenario: String(input.scenario || "unknown").slice(0, 80),
    userStates: Array.isArray(input.userStates) ? input.userStates.slice(0, 12) : [],
    imageNotes: Array.isArray(input.imageNotes)
      ? input.imageNotes.map((item) => String(item).slice(0, 120)).slice(0, 5)
      : []
  };
}

function analyzeWithRules({ text = "", userStates = [] }) {
  const hits = [];
  let score = 0;

  for (const rule of KEYWORD_RULES) {
    if (rule.patterns.some((pattern) => pattern.test(text))) {
      score += rule.weight;
      hits.push({
        label: rule.label,
        reason: rule.reason,
        weight: rule.weight
      });
    }
  }

  for (const state of userStates) {
    score += EMERGENCY_STATE_WEIGHTS[state] || 0;
  }

  score = Math.min(score, 100);
  const hasEmergencyState = userStates.some((state) =>
    ["transferred", "leakedCode", "screenSharing"].includes(state)
  );
  const hasEmergencyText =
    /(已经|已|刚刚|给过|发过|泄露|透露|告诉过|告诉了|转了|转过|汇了|付了|充值了|正在).{0,14}(转账|汇款|打款|付款|充值|验证码|动态密码|银行卡|密码|屏幕共享|远程控制|下载|安装)/.test(text) ||
    /(验证码|动态密码|银行卡|密码|身份证).{0,10}(发给|告诉|泄露|透露|填了|输入了|给了)/.test(text) ||
    /(钱|款|金额).{0,10}(转了|转过|汇了|付了|打了|充值了)/.test(text);

  let riskLevel = "low";
  if (hasEmergencyState || hasEmergencyText) riskLevel = "emergency";
  else if (score >= 58) riskLevel = "high";
  else if (score >= 28) riskLevel = "medium";

  return {
    score,
    riskLevel,
    hits,
    hasEmergencyState: hasEmergencyState || hasEmergencyText,
    shouldEscalateToPro: riskLevel === "high" || riskLevel === "emergency" || text.length > 900
  };
}

function detectScamType({ text = "", userStates = [] }, rules) {
  const ranked = SCAM_TYPE_RULES.map((rule) => {
    let score = 0;
    const matched = [];
    for (const pattern of rule.patterns) {
      if (pattern.test(text)) {
        score += rule.weight;
        matched.push(pattern.toString());
      }
    }
    return { ...rule, score, matched };
  }).sort((a, b) => b.score - a.score);

  let best = ranked[0];
  if (userStates.includes("screenSharing")) {
    best = ranked.find((item) => item.type === "remote_control") || best;
  }
  if (!best || best.score === 0) {
    best = {
      type: "unknown",
      label: "暂未明确类型",
      score: 0,
      sop: defaultSop(rules.riskLevel),
      matched: []
    };
  }

  return {
    type: best.type,
    label: best.label,
    score: best.score,
    sop: best.sop,
    matched: best.matched,
    candidates: ranked
      .filter((item) => item.score > 0)
      .slice(0, 3)
      .map((item) => ({
        type: item.type,
        label: item.label,
        score: item.score
      }))
  };
}

function detectPrivacyRisks({ text = "", userStates = [] }) {
  const hits = PRIVACY_RULES.filter((rule) => rule.patterns.some((pattern) => pattern.test(text)));
  const forced = [];

  if (userStates.includes("leakedCode") && !hits.some((item) => item.label === "验证码或动态密码")) {
    forced.push(PRIVACY_RULES[0]);
  }
  if (userStates.includes("gaveIdCard") && !hits.some((item) => item.label === "身份证或人脸识别")) {
    forced.push(PRIVACY_RULES[2]);
  }
  if (userStates.includes("screenSharing") && !hits.some((item) => item.label === "通讯录、相册或屏幕内容")) {
    forced.push(PRIVACY_RULES[4]);
  }

  const combined = [...hits, ...forced];
  const privacyRisks = combined.map((item) => `${item.label}：${item.risk}`).slice(0, 5);
  const safetySteps = combined.map((item) => item.step).slice(0, 5);

  return {
    labels: combined.map((item) => item.label),
    risks: privacyRisks.length ? privacyRisks : ["暂未看到明确隐私泄露，但验证码、银行卡、身份证、密码和人脸识别都不要发给陌生人。"],
    steps: safetySteps.length
      ? safetySteps
      : ["不要把验证码、银行卡、身份证、密码或人脸识别发给对方。", "不要在对方发来的链接里填写个人信息。", "涉及账户安全时，只走官方 App、官方客服电话或银行柜台。"],
    notice:
      combined.length > 0
        ? "这段内容涉及个人隐私或账户安全，先停止提供信息。"
        : "先保护好个人隐私：验证码、银行卡、身份证、密码和人脸识别不要给陌生人。"
  };
}

function detectCaseStage({ text = "", userStates = [] }, rules, privacyProfile) {
  if (userStates.includes("screenSharing") || /正在.{0,8}(屏幕共享|远程控制|远程协助)/.test(text)) {
    return {
      key: "remote_control",
      label: "正在被远程指挥",
      advice: "先断开共享或远程控制，再处理钱和账号。"
    };
  }
  if (userStates.includes("transferred") || /(已经|已|刚刚|转了|转过|汇了|付了|充值了).{0,12}(钱|款|转账|付款|充值|保证金)/.test(text)) {
    return {
      key: "money_lost",
      label: "已经发生资金风险",
      advice: "先停止继续付款，保存证据并报警。"
    };
  }
  if (
    userStates.includes("leakedCode") ||
    userStates.includes("gaveIdCard") ||
    /(验证码|动态密码|银行卡|身份证|密码|人脸识别).{0,10}(发给|告诉|泄露|透露|填了|输入了|给了)/.test(text) ||
    /(已经|已|刚刚|填了|输入了|给了|发了|告诉了).{0,14}(验证码|动态密码|银行卡|身份证|密码|人脸识别)/.test(text)
  ) {
    return {
      key: "privacy_exposed",
      label: "个人信息可能已泄露",
      advice: "先联系银行或平台冻结、改密、核查登录记录。"
    };
  }
  if (rules.score >= 28 || privacyProfile.labels.length > 0) {
    return {
      key: "suspicious_request",
      label: "对方正在要求危险操作",
      advice: "先暂停，不要继续按对方说的做。"
    };
  }
  return {
    key: "early_check",
    label: "还在早期核实",
    advice: "继续保持谨慎，涉及钱和隐私先找官方渠道核实。"
  };
}

function buildRuleFallback(input, rules, scamProfile, privacyProfile, caseStage) {
  const redFlags = rules.hits.map((hit) => hit.reason);
  const actions = {
    low: ["暂时不要提供验证码、密码、银行卡或身份证信息。", "涉及钱款时，先通过官方 App 或官方电话核实。"],
    medium: ["先暂停操作，不要点击陌生链接。", "把这段内容发给家人或官方客服核实。", "不要下载对方发来的 App。"],
    high: ["立即停止转账、充值或继续聊天。", "不要点击链接，不要提供验证码。", "用官方渠道联系平台、银行或家人核实。"],
    emergency: ["立刻停止转账和屏幕共享。", "保存证据，并马上拨打 110 报警。", "尽快联系银行冻结相关银行卡或账户。"]
  };

  return {
    risk_level: rules.riskLevel,
    is_likely_scam: ["medium", "high", "emergency"].includes(rules.riskLevel),
    confidence: Math.max(0.35, Math.min(0.92, rules.score / 100)),
    summary: makeSummary(rules),
    red_flags: redFlags.length ? redFlags : ["暂未发现明显诈骗关键词，但涉及钱款和隐私仍需谨慎。"],
    recommended_actions: actions[rules.riskLevel],
    scam_type: scamProfile.type,
    scam_type_label: scamProfile.label,
    sop_steps: scamProfile.sop,
    police_notice: policeNotice(rules.riskLevel),
    should_contact_police: rules.riskLevel === "emergency",
    evidence_to_keep: ["聊天记录或短信截图", "对方电话号码、微信号、网址或 App 名称", "转账记录、订单号、收款账户", "快递单、合同、二维码或下载链接"],
    case_stage: caseStage.key,
    case_stage_label: caseStage.label,
    judgement_basis: makeJudgementBasis(rules, scamProfile, privacyProfile, caseStage),
    official_verification_steps: officialVerificationSteps(scamProfile.type),
    privacy_risks: privacyProfile.risks,
    privacy_safety_steps: privacyProfile.steps,
    privacy_notice: privacyProfile.notice,
    family_message: makeFamilyMessage(rules.riskLevel),
    model_note: "当前结果来自本地规则引擎。配置 DEEPSEEK_API_KEY 后会启用大模型复核。"
  };
}

function makeJudgementBasis(rules, scamProfile, privacyProfile, caseStage) {
  const basis = [];
  basis.push(`当前阶段：${caseStage.label}。${caseStage.advice}`);
  if (scamProfile.type !== "unknown") basis.push(`话术接近“${scamProfile.label}”。`);
  for (const hit of rules.hits.slice(0, 4)) {
    basis.push(hit.reason);
  }
  for (const risk of privacyProfile.risks.slice(0, 2)) {
    basis.push(risk);
  }
  return uniqueList(basis).slice(0, 6);
}

function officialVerificationSteps(type) {
  const common = ["不要点对方发来的链接，不要拨打对方提供的电话。", "只从官方 App、官方小程序、官方客服电话或线下柜台核实。"];
  const byType = {
    police_impersonation: ["挂断后可拨打 110，或到就近派出所当面核实。", "公检法不会让你转到所谓安全账户，也不会要求屏幕共享。"],
    customer_service_refund: ["打开购物、快递或支付平台的官方 App，在订单页查看售后和退款。", "需要客服电话时，自己从官方 App 或官网查，不用对方发来的号码。"],
    task_rebate: ["刷单、点赞返利、垫付做任务本身就高风险，不要为了提现继续交钱。", "保存群聊和收款账户后，找家人或警方核实。"],
    investment: ["投资平台先查是否为正规金融机构，不要相信群里的导师和客服。", "不要继续充值、加仓或缴纳解冻费、保证金。"],
    remote_control: ["先断开屏幕共享或远程控制，再打开银行和支付 App。", "检查手机是否安装了陌生会议、远程控制或投资理财 App。"],
    phishing_link: ["把链接关掉，不在页面里填银行卡、验证码、身份证或密码。", "如已填写，马上联系银行和相关平台处理账户安全。"]
  };
  return [...(byType[type] || []), ...common].slice(0, 4);
}

function makeSummary(rules) {
  if (rules.riskLevel === "emergency") return "这件事已经出现紧急风险，先别继续操作，优先报警和止损。";
  if (rules.riskLevel === "high") return `这段内容很像诈骗，命中了 ${rules.hits.length} 个高风险信号。`;
  if (rules.riskLevel === "medium") return "这段内容有可疑点，建议暂停操作并找官方渠道核实。";
  return "暂时没有发现明显诈骗信号，但涉及钱款、验证码或陌生链接时仍要谨慎。";
}

function makeFamilyMessage(riskLevel) {
  if (riskLevel === "emergency") return "我可能遇到诈骗了，已经涉及转账、验证码或屏幕共享，请马上帮我一起报警和联系银行。";
  if (riskLevel === "high") return "我收到一段很像诈骗的信息，先不操作了，你帮我一起看看是真是假。";
  if (riskLevel === "medium") return "这段信息有点可疑，我先发给你确认一下。";
  return "我收到一段信息，工具暂时没发现明显诈骗，但我想再确认一下。";
}

function defaultSop(riskLevel) {
  if (riskLevel === "emergency" || riskLevel === "high") {
    return ["先停止转账、聊天、下载 App 或屏幕共享。", "保存聊天记录、电话、链接、二维码和转账凭证。", "已经转账或给过验证码时，立即拨打 110。"];
  }
  if (riskLevel === "medium") {
    return ["先暂停操作，不要急着回复对方。", "换官方渠道核实，比如官方 App、官方客服电话或家人。", "不要提供验证码、银行卡、密码或身份证信息。"];
  }
  return ["暂时不要提供验证码、密码或银行卡。", "涉及钱款时先找家人或官方渠道核实。", "如果对方开始催你转账或下载 App，立刻停止。"];
}

function policeNotice(riskLevel) {
  if (riskLevel === "emergency" || riskLevel === "high") {
    return "如果已经转账、泄露验证码/银行卡/身份证信息，或对方正在催你继续付款，请立即拨打 110 报警，并保存聊天记录、转账凭证、电话号码、链接和收款账户。96110 是反诈预警劝阻和咨询专线，接到 96110 来电请及时接听。";
  }
  return "如果后续出现转账、验证码、屏幕共享、陌生 App 或继续催付款，请先停止操作；一旦已经造成损失或泄露重要信息，请立即拨打 110 报警。";
}

async function runModelAnalysis(model, normalized, rules, scamProfile, privacyProfile, caseStage, previous) {
  const response = await deepSeekChat({
    model,
    messages: [
      { role: "system", content: SYSTEM_PROMPT },
      {
        role: "user",
        content: JSON.stringify(
          {
            case_text: normalized.text,
            scenario: normalized.scenario,
            user_states: normalized.userStates,
            uploaded_image_notes: normalized.imageNotes,
            rule_engine: {
              score: rules.score,
              risk_level: rules.riskLevel,
              hits: rules.hits.map((hit) => hit.label),
              has_emergency_state: rules.hasEmergencyState
            },
            scam_type_candidate: {
              type: scamProfile.type,
              label: scamProfile.label,
              candidates: scamProfile.candidates,
              suggested_sop: scamProfile.sop
            },
            case_stage_candidate: caseStage,
            privacy_candidate: {
              risks: privacyProfile.risks,
              safety_steps: privacyProfile.steps,
              notice: privacyProfile.notice
            },
            previous_analysis: previous
          },
          null,
          2
        )
      }
    ]
  });

  return parseModelJson(response);
}

function deepSeekChat(payload) {
  const apiBase = process.env.DEEPSEEK_API_BASE || "https://api.deepseek.com";
  const url = new URL("/chat/completions", apiBase);
  const body = JSON.stringify({
    ...payload,
    temperature: 0.2,
    max_tokens: 1600,
    response_format: { type: "json_object" }
  });

  return requestJson(url, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${process.env.DEEPSEEK_API_KEY}`,
      "Content-Type": "application/json",
      "Content-Length": Buffer.byteLength(body)
    },
    body
  }).then((data) => {
    const content = data?.choices?.[0]?.message?.content;
    if (!content) throw new Error("DeepSeek API returned empty content");
    return content;
  });
}

function requestJson(url, options) {
  return new Promise((resolve, reject) => {
    const req = https.request(
      url,
      {
        method: options.method,
        headers: options.headers,
        timeout: 25000
      },
      (res) => {
        let raw = "";
        res.setEncoding("utf8");
        res.on("data", (chunk) => {
          raw += chunk;
        });
        res.on("end", () => {
          if (res.statusCode < 200 || res.statusCode >= 300) {
            reject(new Error(`DeepSeek API ${res.statusCode}: ${raw.slice(0, 300)}`));
            return;
          }
          try {
            resolve(JSON.parse(raw));
          } catch (error) {
            reject(error);
          }
        });
      }
    );

    req.on("error", reject);
    req.on("timeout", () => {
      req.destroy(new Error("DeepSeek API timeout"));
    });
    req.write(options.body);
    req.end();
  });
}

function parseModelJson(content) {
  const text = String(content || "").trim();
  try {
    return JSON.parse(text);
  } catch {
    const start = text.indexOf("{");
    const end = text.lastIndexOf("}");
    if (start >= 0 && end > start) return JSON.parse(text.slice(start, end + 1));
    throw new Error("Model response was not valid JSON");
  }
}

function sanitizeAnalysis(candidate, fallback) {
  const allowed = new Set(["low", "medium", "high", "emergency"]);
  const riskLevel = allowed.has(candidate?.risk_level) ? candidate.risk_level : fallback.risk_level;
  const confidence = Number(candidate?.confidence);

  return {
    risk_level: riskLevel,
    is_likely_scam:
      typeof candidate?.is_likely_scam === "boolean"
        ? candidate.is_likely_scam
        : ["medium", "high", "emergency"].includes(riskLevel),
    confidence: Number.isFinite(confidence) ? Math.max(0, Math.min(1, confidence)) : fallback.confidence,
    summary: shortText(candidate?.summary, fallback.summary),
    case_stage: shortText(candidate?.case_stage, fallback.case_stage),
    case_stage_label: shortText(candidate?.case_stage_label, fallback.case_stage_label),
    judgement_basis: list(candidate?.judgement_basis, fallback.judgement_basis),
    red_flags: list(candidate?.red_flags, fallback.red_flags),
    recommended_actions: list(candidate?.recommended_actions, fallback.recommended_actions),
    scam_type: shortText(candidate?.scam_type, fallback.scam_type),
    scam_type_label: shortText(candidate?.scam_type_label, fallback.scam_type_label),
    sop_steps: list(candidate?.sop_steps, fallback.sop_steps),
    official_verification_steps: list(candidate?.official_verification_steps, fallback.official_verification_steps),
    privacy_risks: list(candidate?.privacy_risks, fallback.privacy_risks),
    privacy_safety_steps: list(candidate?.privacy_safety_steps, fallback.privacy_safety_steps),
    privacy_notice: shortText(candidate?.privacy_notice, fallback.privacy_notice),
    police_notice: shortText(candidate?.police_notice, fallback.police_notice),
    should_contact_police:
      typeof candidate?.should_contact_police === "boolean"
        ? candidate.should_contact_police
        : fallback.should_contact_police,
    evidence_to_keep: list(candidate?.evidence_to_keep, fallback.evidence_to_keep),
    family_message: shortText(candidate?.family_message, fallback.family_message)
  };
}

function enforceSafetyFloor(analysis, rules, scamProfile, privacyProfile, caseStage) {
  const rank = { low: 0, medium: 1, high: 2, emergency: 3 };
  let riskLevel = analysis.risk_level;
  if (rank[riskLevel] < rank[rules.riskLevel]) riskLevel = rules.riskLevel;

  const emergency = riskLevel === "emergency" || rules.hasEmergencyState;
  return {
    ...analysis,
    risk_level: emergency ? "emergency" : riskLevel,
    scam_type: analysis.scam_type && analysis.scam_type !== "unknown" ? analysis.scam_type : scamProfile.type,
    scam_type_label:
      analysis.scam_type_label && analysis.scam_type_label !== "暂未明确类型"
        ? analysis.scam_type_label
        : scamProfile.label,
    sop_steps: Array.isArray(analysis.sop_steps) && analysis.sop_steps.length ? analysis.sop_steps : scamProfile.sop,
    case_stage: analysis.case_stage || caseStage.key,
    case_stage_label: analysis.case_stage_label || caseStage.label,
    judgement_basis:
      Array.isArray(analysis.judgement_basis) && analysis.judgement_basis.length
        ? analysis.judgement_basis
        : makeJudgementBasis(rules, scamProfile, privacyProfile, caseStage),
    official_verification_steps:
      Array.isArray(analysis.official_verification_steps) && analysis.official_verification_steps.length
        ? analysis.official_verification_steps
        : officialVerificationSteps(scamProfile.type),
    privacy_risks:
      Array.isArray(analysis.privacy_risks) && analysis.privacy_risks.length ? analysis.privacy_risks : privacyProfile.risks,
    privacy_safety_steps:
      Array.isArray(analysis.privacy_safety_steps) && analysis.privacy_safety_steps.length
        ? analysis.privacy_safety_steps
        : privacyProfile.steps,
    privacy_notice: analysis.privacy_notice || privacyProfile.notice,
    is_likely_scam: analysis.is_likely_scam || ["medium", "high", "emergency"].includes(riskLevel),
    should_contact_police: analysis.should_contact_police || emergency,
    police_notice: emergency || riskLevel === "high" ? policeNotice("high") : analysis.police_notice
  };
}

function shortText(value, fallback) {
  const text = String(value || "").trim();
  return text ? text.slice(0, 500) : fallback;
}

function list(value, fallback) {
  if (!Array.isArray(value)) return fallback;
  const cleaned = uniqueList(value.map((item) => String(item || "").trim()).filter(Boolean)).slice(0, 8);
  return cleaned.length ? cleaned : fallback;
}

function uniqueList(items) {
  return [...new Set(items.filter(Boolean))];
}

function buildMeta({ rules, scamProfile, privacyProfile, caseStage, mode, usedModels, warning }) {
  return {
    mode,
    used_models: usedModels,
    rule_score: rules.score,
    rule_level: rules.riskLevel,
    rule_hits: rules.hits.map((hit) => hit.label),
    scam_type: scamProfile.type,
    scam_type_label: scamProfile.label,
    case_stage: caseStage.key,
    case_stage_label: caseStage.label,
    privacy_hits: privacyProfile.labels,
    warning,
    created_at: new Date().toISOString()
  };
}
