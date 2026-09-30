const assert = require("node:assert/strict");
const { EventEmitter } = require("node:events");
const https = require("node:https");
const Module = require("node:module");

const originalRequest = https.request;
const originalModuleLoad = Module._load;
const originalEnv = { ...process.env };

const analyzePath = require.resolve("../cloudfunctions/analyzeCase/index.js");

function restore() {
  https.request = originalRequest;
  Module._load = originalModuleLoad;
  process.env = { ...originalEnv };
  delete require.cache[analyzePath];
}

function loadAnalyzeCase() {
  delete require.cache[analyzePath];
  return require(analyzePath);
}

function installHttpsMock(responses) {
  const calls = [];

  https.request = (url, options, callback) => {
    const request = new EventEmitter();
    const chunks = [];

    request.write = (chunk) => {
      chunks.push(Buffer.isBuffer(chunk) ? chunk : Buffer.from(String(chunk)));
    };

    request.end = () => {
      const response = responses.shift();
      if (!response) throw new Error("Unexpected HTTPS request");

      const bodyText = Buffer.concat(chunks).toString("utf8");
      calls.push({
        url: String(url),
        options,
        body: bodyText ? JSON.parse(bodyText) : null
      });

      const res = new EventEmitter();
      res.statusCode = response.statusCode;
      res.setEncoding = () => {};
      callback(res);

      queueMicrotask(() => {
        if (response.body !== undefined) {
          res.emit("data", typeof response.body === "string" ? response.body : JSON.stringify(response.body));
        }
        res.emit("end");
      });
    };

    request.destroy = (error) => request.emit("error", error);
    request.setTimeout = () => {};
    return request;
  };

  return calls;
}

function installWxServerSdkMock(options = {}) {
  const fileContent = options.fileContent || Buffer.from([0xff, 0xd8, 0xff, 0xe0]);
  const tempFileURL = options.tempFileURL || "https://example.com/temp-image.jpg";

  Module._load = (request, parent, isMain) => {
    if (request === "wx-server-sdk") {
      return {
        DYNAMIC_CURRENT_ENV: "mock-env",
        init() {},
        async downloadFile() {
          return { fileContent };
        },
        async getTempFileURL({ fileList }) {
          return {
            fileList: fileList.map((fileID) => ({ fileID, tempFileURL }))
          };
        },
        async deleteFile() {
          return {};
        }
      };
    }
    return originalModuleLoad.call(Module, request, parent, isMain);
  };
}

function modelResponse(overrides = {}) {
  return {
    choices: [
      {
        message: {
          content: JSON.stringify({
            risk_level: "high",
            is_likely_scam: true,
            confidence: 0.88,
            summary: "这很像冒充客服退款诈骗，先不要点链接。",
            case_stage: "suspicious_request",
            case_stage_label: "对方正在要求危险操作",
            judgement_basis: ["要求点击陌生链接", "要求填写银行卡和验证码"],
            red_flags: ["陌生链接", "银行卡和验证码"],
            recommended_actions: ["先停止操作", "走官方渠道核实"],
            scam_type: "customer_service_refund",
            scam_type_label: "冒充客服退款/理赔诈骗",
            sop_steps: ["不要点链接", "不要填银行卡或验证码", "从官方 App 核实"],
            official_verification_steps: ["只从官方 App 或官方客服电话核实"],
            privacy_risks: ["验证码可能被盗用"],
            privacy_safety_steps: ["不要再提供验证码"],
            privacy_notice: "先保护验证码、银行卡和密码。",
            police_notice: "如果已经转账或泄露验证码，请立即拨打 110。",
            should_contact_police: false,
            evidence_to_keep: ["聊天记录", "链接截图"],
            family_message: "我遇到可疑退款链接，请帮我一起核实。",
            ...overrides
          })
        }
      }
    ],
    model: overrides.model || "mock-model"
  };
}

async function testPureTextUsesDeepSeekFlashFirst() {
  process.env = {
    ...originalEnv,
    MINIMAX_API_KEY: "mini-key",
    MINIMAX_MODEL: "MiniMax-M3",
    DEEPSEEK_API_KEY: "deepseek-key"
  };
  const calls = installHttpsMock([{ statusCode: 200, body: modelResponse({ model: "deepseek-v4-flash" }) }]);

  const { main } = loadAnalyzeCase();
  const result = await main({
    text: "客服说快递丢了，让我点链接填写银行卡和验证码。",
    scenario: "payment"
  });

  assert.equal(calls.length, 1);
  assert.match(calls[0].url, /api\.deepseek\.com\/chat\/completions$/);
  assert.equal(calls[0].body.model, "deepseek-v4-flash");
  assert.equal(calls[0].body.max_tokens, 1600);
  assert.equal(calls[0].body.max_completion_tokens, undefined);
  assert.equal(typeof calls[0].body.messages[1].content, "string");
  assert.equal(result.meta.mode, "deepseek");
  assert.deepEqual(result.meta.used_models, ["deepseek-v4-flash"]);
}

async function testImageAnalysisUsesMiniMaxOcrThenDeepSeekTextAnalysis() {
  process.env = {
    ...originalEnv,
    MINIMAX_API_KEY: "mini-key",
    MINIMAX_MODEL: "MiniMax-M3",
    DEEPSEEK_API_KEY: "deepseek-key",
    DEEPSEEK_FLASH_MODEL: "deepseek-v4-flash"
  };
  installWxServerSdkMock();
  const calls = installHttpsMock([
    {
      statusCode: 200,
      body: {
        choices: [{ message: { content: "客服说快递理赔，需要点链接填写银行卡和验证码。" } }],
        base_resp: { status_code: 0, status_msg: "" }
      }
    },
    { statusCode: 200, body: modelResponse({ model: "deepseek-v4-flash" }) }
  ]);

  const { main } = loadAnalyzeCase();
  const result = await main({
    text: "",
    scenario: "payment",
    imageFileIDs: ["cloud://mock-env/scam-screenshots/a.jpg"]
  });

  assert.equal(calls.length, 2);
  assert.match(calls[0].url, /api\.minimaxi\.com\/v1\/chat\/completions$/);
  assert.equal(calls[0].body.model, "MiniMax-M3");
  assert.equal(Array.isArray(calls[0].body.messages[1].content), true);
  assert.match(calls[0].body.messages[1].content[1].image_url.url, /^data:image\/jpeg;base64,/);

  assert.match(calls[1].url, /api\.deepseek\.com\/chat\/completions$/);
  assert.equal(calls[1].body.model, "deepseek-v4-flash");
  assert.equal(typeof calls[1].body.messages[1].content, "string");
  assert.match(calls[1].body.messages[1].content, /截图提取文字/);
  assert.match(calls[1].body.messages[1].content, /银行卡和验证码/);
  assert.doesNotMatch(calls[1].body.messages[1].content, /image_url/);
  assert.equal(result.meta.mode, "deepseek_with_ocr");
  assert.deepEqual(result.meta.used_models, ["MiniMax-M3", "deepseek-v4-flash"]);
}

async function testOcrOnlyUsesDownloadedImageDataUrl() {
  process.env = {
    ...originalEnv,
    MINIMAX_API_KEY: "mini-key",
    MINIMAX_MODEL: "MiniMax-M3"
  };
  installWxServerSdkMock();
  const calls = installHttpsMock([
    {
      statusCode: 200,
      body: {
        choices: [{ message: { content: "截图里的文字" } }],
        base_resp: { status_code: 0, status_msg: "" }
      }
    }
  ]);

  const { main } = loadAnalyzeCase();
  const result = await main({
    ocrOnly: true,
    imageFileIDs: ["cloud://mock-env/scam-screenshots/a.jpg"]
  });

  assert.equal(result.text, "截图里的文字");
  assert.equal(calls.length, 1);
  const userContent = calls[0].body.messages[1].content;
  assert.match(userContent[1].image_url.url, /^data:image\/jpeg;base64,/);
  assert.doesNotMatch(userContent[1].image_url.url, /^https?:/);
}

async function testPlaceholderMiniMaxEnvFallsBackToDefaults() {
  process.env = {
    ...originalEnv,
    MINIMAX_API_KEY: "mini-key",
    MINIMAX_API_BASE: "${MINIMAX_API_BASE}",
    MINIMAX_CHAT_PATH: "${MINIMAX_CHAT_PATH}",
    MINIMAX_MODEL: "${MINIMAX_MODEL}"
  };
  installWxServerSdkMock();
  const calls = installHttpsMock([
    {
      statusCode: 200,
      body: {
        choices: [{ message: { content: "截图里的文字" } }],
        base_resp: { status_code: 0, status_msg: "" }
      }
    }
  ]);

  const { main } = loadAnalyzeCase();
  await main({ ocrOnly: true, imageFileIDs: ["cloud://mock-env/scam-screenshots/a.jpg"] });

  assert.equal(calls.length, 1);
  assert.match(calls[0].url, /api\.minimaxi\.com\/v1\/chat\/completions$/);
  assert.equal(calls[0].body.model, "MiniMax-M3");
}

async function testCommonMiniMaxDomainTypoFallsBackToCnEndpoint() {
  process.env = {
    ...originalEnv,
    MINIMAX_API_KEY: "mini-key",
    MINIMAX_API_BASE: "https://api.minimax.com/v1"
  };
  installWxServerSdkMock();
  const calls = installHttpsMock([
    {
      statusCode: 200,
      body: {
        choices: [{ message: { content: "截图里的文字" } }],
        base_resp: { status_code: 0, status_msg: "" }
      }
    }
  ]);

  const { main } = loadAnalyzeCase();
  await main({ ocrOnly: true, imageFileIDs: ["cloud://mock-env/scam-screenshots/a.jpg"] });

  assert.equal(calls.length, 1);
  assert.match(calls[0].url, /api\.minimaxi\.com\/v1\/chat\/completions$/);
}

async function testImageOcrFailureStillUsesDeepSeekForTextAnalysis() {
  process.env = {
    ...originalEnv,
    MINIMAX_API_KEY: "mini-key",
    DEEPSEEK_API_KEY: "deepseek-key",
    DEEPSEEK_FLASH_MODEL: "deepseek-v4-flash"
  };
  const calls = installHttpsMock([
    { statusCode: 500, body: { error: "minimax unavailable" } },
    { statusCode: 200, body: modelResponse({ model: "deepseek-v4-flash" }) }
  ]);

  const { main } = loadAnalyzeCase();
  const result = await main({
    text: "客服说快递丢了，让我点链接填写银行卡和验证码。",
    scenario: "payment",
    imageUrls: ["https://example.com/screenshot.jpg"]
  });

  assert.equal(calls.length, 2);
  assert.match(calls[0].url, /api\.minimaxi\.com/);
  assert.match(calls[1].url, /api\.deepseek\.com\/chat\/completions$/);
  assert.equal(calls[1].body.model, "deepseek-v4-flash");
  assert.equal(typeof calls[1].body.messages[1].content, "string");
  assert.equal(result.meta.mode, "deepseek_ocr_warning");
  assert.deepEqual(result.meta.used_models, ["MiniMax-M3", "deepseek-v4-flash"]);
}

async function testRulesOnlyWithoutProviderKeys() {
  process.env = { ...originalEnv };
  delete process.env.MINIMAX_API_KEY;
  delete process.env.DEEPSEEK_API_KEY;
  const calls = installHttpsMock([]);

  const { main } = loadAnalyzeCase();
  const result = await main({
    text: "客服让我点链接填银行卡和验证码。",
    scenario: "payment"
  });

  assert.equal(calls.length, 0);
  assert.equal(result.meta.mode, "rules_only");
  assert.match(result.meta.warning, /MINIMAX_API_KEY|DEEPSEEK_API_KEY/);
}

async function run() {
  try {
    await testPureTextUsesDeepSeekFlashFirst();
    restore();
    await testImageAnalysisUsesMiniMaxOcrThenDeepSeekTextAnalysis();
    restore();
    await testOcrOnlyUsesDownloadedImageDataUrl();
    restore();
    await testPlaceholderMiniMaxEnvFallsBackToDefaults();
    restore();
    await testCommonMiniMaxDomainTypoFallsBackToCnEndpoint();
    restore();
    await testImageOcrFailureStillUsesDeepSeekForTextAnalysis();
    restore();
    await testRulesOnlyWithoutProviderKeys();
    restore();
    console.log("analyzeCase provider tests passed");
  } catch (error) {
    restore();
    console.error(error);
    process.exit(1);
  }
}

run();
