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

export function analyzeWithRules({ text = "", userStates = [] }) {
  const normalizedText = String(text).trim();
  const hits = [];
  let score = 0;

  for (const rule of KEYWORD_RULES) {
    if (rule.patterns.some((pattern) => pattern.test(normalizedText))) {
      score += rule.weight;
      hits.push({
        label: rule.label,
        reason: rule.reason,
        weight: rule.weight
      });
    }
  }

  const states = Array.isArray(userStates) ? userStates : [];
  for (const state of states) {
    const weight = EMERGENCY_STATE_WEIGHTS[state] || 0;
    if (weight > 0) {
      score += weight;
    }
  }

  score = Math.min(score, 100);

  const hasEmergencyState = states.some((state) =>
    ["transferred", "leakedCode", "screenSharing"].includes(state)
  );

  let riskLevel = "low";
  if (hasEmergencyState || score >= 85) {
    riskLevel = "emergency";
  } else if (score >= 58) {
    riskLevel = "high";
  } else if (score >= 28) {
    riskLevel = "medium";
  }

  return {
    score,
    riskLevel,
    hits,
    hasEmergencyState,
    shouldEscalateToPro: riskLevel === "high" || riskLevel === "emergency" || normalizedText.length > 900
  };
}

export function buildRuleFallback({ text = "", userStates = [] }) {
  const rules = analyzeWithRules({ text, userStates });
  const redFlags = rules.hits.map((hit) => hit.reason);

  const actionByLevel = {
    low: ["暂时不要提供验证码、密码、银行卡或身份证信息。", "涉及钱款时，先通过官方 App 或官方电话核实。"],
    medium: ["先暂停操作，不要点击陌生链接。", "把这段内容发给家人或官方客服核实。", "不要下载对方发来的 App。"],
    high: ["立即停止转账、充值或继续聊天。", "不要点击链接，不要提供验证码。", "用官方渠道联系平台、银行或家人核实。"],
    emergency: ["立刻停止转账和屏幕共享。", "保存证据，并马上拨打 110 报警。", "尽快联系银行冻结相关银行卡或账户。"]
  };

  return {
    risk_level: rules.riskLevel,
    is_likely_scam: ["medium", "high", "emergency"].includes(rules.riskLevel),
    confidence: Math.max(0.35, Math.min(0.92, rules.score / 100)),
    summary: makeSummary(rules.riskLevel, rules.hits),
    red_flags: redFlags.length ? redFlags : ["暂未发现明显诈骗关键词，但涉及钱款和隐私仍需谨慎。"],
    recommended_actions: actionByLevel[rules.riskLevel],
    police_notice: policeNotice(rules.riskLevel),
    should_contact_police: rules.riskLevel === "emergency",
    evidence_to_keep: [
      "聊天记录或短信截图",
      "对方电话号码、微信号、网址或 App 名称",
      "转账记录、订单号、收款账户",
      "快递单、合同、二维码或下载链接"
    ],
    family_message: makeFamilyMessage(rules.riskLevel),
    model_note: "当前结果来自本地规则引擎。配置 DEEPSEEK_API_KEY 后会启用大模型复核。"
  };
}

function makeSummary(riskLevel, hits) {
  if (riskLevel === "emergency") {
    return "这件事已经出现紧急风险，先别继续操作，优先报警和止损。";
  }
  if (riskLevel === "high") {
    return `这段内容很像诈骗，命中了 ${hits.length} 个高风险信号。`;
  }
  if (riskLevel === "medium") {
    return `这段内容有可疑点，建议暂停操作并找官方渠道核实。`;
  }
  return "暂时没有发现明显诈骗信号，但涉及钱款、验证码或陌生链接时仍要谨慎。";
}

function makeFamilyMessage(riskLevel) {
  if (riskLevel === "emergency") {
    return "我可能遇到诈骗了，已经涉及转账、验证码或屏幕共享，请马上帮我一起报警和联系银行。";
  }
  if (riskLevel === "high") {
    return "我收到一段很像诈骗的信息，先不操作了，你帮我一起看看是真是假。";
  }
  if (riskLevel === "medium") {
    return "这段信息有点可疑，我先发给你确认一下。";
  }
  return "我收到一段信息，工具暂时没发现明显诈骗，但我想再确认一下。";
}

export function policeNotice(riskLevel) {
  if (riskLevel === "emergency" || riskLevel === "high") {
    return "如果已经转账、泄露验证码/银行卡/身份证信息，或对方正在催你继续付款，请立即拨打 110 报警，并保存聊天记录、转账凭证、电话号码、链接和收款账户。96110 是反诈预警劝阻和咨询专线，接到 96110 来电请及时接听。";
  }
  return "如果后续出现转账、验证码、屏幕共享、陌生 App 或继续催付款，请先停止操作；一旦已经造成损失或泄露重要信息，请立即拨打 110 报警。";
}

