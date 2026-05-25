import { buildRuleFallback, analyzeWithRules, policeNotice } from "./riskRules.mjs";
import { chatCompletion, getDeepSeekConfig, parseModelJson } from "./deepseekClient.mjs";

const SYSTEM_PROMPT = `你是“真的假的鸭”的反诈分析 agent，服务对象是普通群众和老年人。
你的任务：根据用户提供的短信、聊天、电话话术、链接或事件描述，判断诈骗风险并给出清晰行动建议。

重要边界：
- 你不是警方、律师或银行，不能说“已经确定是诈骗分子”，只能做风险判断。
- 如果已经转账、泄露验证码/银行卡/身份证/密码、正在屏幕共享、下载了陌生 App、或对方继续催付款，必须提醒用户立即拨打 110 报警并保留证据。
- 96110 是反诈预警劝阻和咨询专线，接到来电应及时接听；紧急报案优先 110。
- 不要输出 Markdown，不要输出代码块，只返回 JSON。
- 用大白话，句子短，适合老人理解。

返回 JSON，字段必须完整：
{
  "risk_level": "low | medium | high | emergency",
  "is_likely_scam": true,
  "confidence": 0.0,
  "summary": "一句话结论",
  "red_flags": ["危险点1", "危险点2"],
  "recommended_actions": ["下一步1", "下一步2"],
  "police_notice": "报警或反诈专线提醒",
  "should_contact_police": false,
  "evidence_to_keep": ["证据1", "证据2"],
  "family_message": "可转发给家人的一句话"
}`;

export async function analyzeCase(input) {
  const normalized = normalizeInput(input);
  const rules = analyzeWithRules(normalized);
  const fallback = buildRuleFallback(normalized);
  const config = getDeepSeekConfig();
  const usedModels = [];

  if (!config.apiKey) {
    return {
      analysis: fallback,
      meta: buildMeta({ rules, usedModels, mode: "rules_only", warning: "DEEPSEEK_API_KEY 未配置" })
    };
  }

  try {
    const flashResult = await runModelAnalysis({
      model: config.flashModel,
      normalized,
      rules,
      previous: null
    });
    usedModels.push(config.flashModel);

    let analysis = sanitizeAnalysis(flashResult, fallback);

    const shouldUsePro =
      rules.shouldEscalateToPro ||
      ["high", "emergency"].includes(analysis.risk_level) ||
      analysis.confidence < 0.62;

    if (shouldUsePro) {
      const proResult = await runModelAnalysis({
        model: config.proModel,
        normalized,
        rules,
        previous: analysis
      });
      usedModels.push(config.proModel);
      analysis = sanitizeAnalysis(proResult, analysis);
    }

    analysis = enforceSafetyFloor(analysis, rules);

    return {
      analysis,
      meta: buildMeta({ rules, usedModels, mode: "deepseek" })
    };
  } catch (error) {
    return {
      analysis: {
        ...fallback,
        model_note: "大模型调用失败，已使用本地规则引擎给出保底判断。"
      },
      meta: buildMeta({
        rules,
        usedModels,
        mode: "rules_fallback",
        warning: error.message
      })
    };
  }
}

function normalizeInput(input = {}) {
  const text = String(input.text || "").slice(0, 9000).trim();
  const scenario = String(input.scenario || "unknown").slice(0, 80);
  const userStates = Array.isArray(input.userStates) ? input.userStates.slice(0, 12) : [];
  const imageNotes = Array.isArray(input.imageNotes)
    ? input.imageNotes.map((item) => String(item).slice(0, 120)).slice(0, 5)
    : [];

  return {
    text,
    scenario,
    userStates,
    imageNotes
  };
}

async function runModelAnalysis({ model, normalized, rules, previous }) {
  const messages = [
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
          previous_analysis: previous
        },
        null,
        2
      )
    }
  ];

  const response = await chatCompletion({ model, messages });
  return parseModelJson(response.content);
}

function sanitizeAnalysis(candidate, fallback) {
  const riskLevels = new Set(["low", "medium", "high", "emergency"]);
  const riskLevel = riskLevels.has(candidate?.risk_level) ? candidate.risk_level : fallback.risk_level;
  const confidence = Number(candidate?.confidence);

  return {
    risk_level: riskLevel,
    is_likely_scam:
      typeof candidate?.is_likely_scam === "boolean"
        ? candidate.is_likely_scam
        : ["medium", "high", "emergency"].includes(riskLevel),
    confidence: Number.isFinite(confidence)
      ? Math.max(0, Math.min(1, confidence))
      : fallback.confidence,
    summary: asShortText(candidate?.summary, fallback.summary),
    red_flags: asList(candidate?.red_flags, fallback.red_flags),
    recommended_actions: asList(candidate?.recommended_actions, fallback.recommended_actions),
    police_notice: asShortText(candidate?.police_notice, fallback.police_notice),
    should_contact_police:
      typeof candidate?.should_contact_police === "boolean"
        ? candidate.should_contact_police
        : fallback.should_contact_police,
    evidence_to_keep: asList(candidate?.evidence_to_keep, fallback.evidence_to_keep),
    family_message: asShortText(candidate?.family_message, fallback.family_message),
    model_note: candidate?.model_note ? asShortText(candidate.model_note, "") : undefined
  };
}

function enforceSafetyFloor(analysis, rules) {
  const levelRank = { low: 0, medium: 1, high: 2, emergency: 3 };
  const floor = rules.riskLevel;

  let riskLevel = analysis.risk_level;
  if (levelRank[riskLevel] < levelRank[floor]) {
    riskLevel = floor;
  }

  const emergency = riskLevel === "emergency" || rules.hasEmergencyState;
  return {
    ...analysis,
    risk_level: emergency ? "emergency" : riskLevel,
    is_likely_scam: analysis.is_likely_scam || ["medium", "high", "emergency"].includes(riskLevel),
    should_contact_police: analysis.should_contact_police || emergency,
    police_notice:
      emergency || riskLevel === "high"
        ? policeNotice("high")
        : analysis.police_notice || policeNotice(riskLevel)
  };
}

function asShortText(value, fallback) {
  const text = String(value || "").trim();
  return text ? text.slice(0, 500) : fallback;
}

function asList(value, fallback) {
  if (!Array.isArray(value)) return fallback;
  const list = value
    .map((item) => String(item || "").trim())
    .filter(Boolean)
    .map((item) => item.slice(0, 160))
    .slice(0, 8);
  return list.length ? list : fallback;
}

function buildMeta({ rules, usedModels, mode, warning }) {
  return {
    mode,
    used_models: usedModels,
    rule_score: rules.score,
    rule_level: rules.riskLevel,
    rule_hits: rules.hits.map((hit) => hit.label),
    warning,
    created_at: new Date().toISOString()
  };
}

