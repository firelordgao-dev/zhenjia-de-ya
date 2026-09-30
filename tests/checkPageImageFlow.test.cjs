const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

function loadCheckPage(wxMock) {
  const filename = path.join(__dirname, "..", "miniprogram/pages/check/check.js");
  const code = fs.readFileSync(filename, "utf8");
  let pageConfig = null;

  vm.runInNewContext(
    code,
    {
      Page(config) {
        pageConfig = config;
      },
      wx: wxMock
    },
    { filename }
  );

  const page = {
    ...pageConfig,
    data: JSON.parse(JSON.stringify(pageConfig.data)),
    setData(update) {
      this.data = { ...this.data, ...update };
    }
  };
  return page;
}

async function testAnalyzeSkipsImageUploadAfterOcrTextExtraction() {
  const calls = {
    uploadCount: 0,
    functionCalls: []
  };

  const wxMock = {
    cloud: {
      uploadFile({ success }) {
        calls.uploadCount += 1;
        success({ fileID: `cloud://mock/image-${calls.uploadCount}.jpg` });
      },
      async callFunction(payload) {
        calls.functionCalls.push(payload);
        if (payload.data?.ocrOnly) {
          return { result: { text: "请点击链接退款，并填写验证码。" } };
        }
        return { result: { analysis: { risk_level: "high", summary: "测试结果" } } };
      },
      deleteFile() {}
    },
    showToast() {},
    setStorageSync() {},
    navigateTo() {}
  };

  const page = loadCheckPage(wxMock);
  page.setData({
    imagePaths: ["tmp/screenshot.jpg"],
    imageNames: ["screenshot.jpg"]
  });

  await page.recognizeImage();
  assert.equal(page.data.imageTextExtracted, true);
  assert.match(page.data.caseText, /填写验证码/);

  const uploadsAfterOcr = calls.uploadCount;
  await page.analyze();

  assert.equal(calls.uploadCount, uploadsAfterOcr);
  const analyzeCall = calls.functionCalls.find((call) => !call.data?.ocrOnly);
  assert.ok(analyzeCall);
  assert.deepEqual(Array.from(analyzeCall.data.imageFileIDs), []);
  assert.deepEqual(Array.from(analyzeCall.data.imageNotes), []);
}

async function testAnalyzeFailureStoresSafeFallbackForRetry() {
  let storedPayload = null;
  const wxMock = {
    cloud: {
      uploadFile({ success }) {
        success({ fileID: "cloud://mock/image.jpg" });
      },
      async callFunction() {
        throw new Error("Model API timeout");
      },
      deleteFile() {}
    },
    showToast() {},
    setStorageSync(key, value) {
      if (key === "latestAnalysisResult") storedPayload = value;
    },
    navigateTo() {}
  };

  const page = loadCheckPage(wxMock);
  page.setData({
    caseText: "对方让我点链接退款，还要填写验证码。",
    imagePaths: ["tmp/screenshot.jpg"],
    imageNames: ["screenshot.jpg"]
  });

  await page.analyze();

  assert.ok(storedPayload, "analysis result should be stored");
  assert.equal(storedPayload.retryText, "对方让我点链接退款，还要填写验证码。");
  assert.equal(storedPayload.hadImages, true);
  assert.equal(storedPayload.analysis.is_safe_fallback, true);
  assert.match(storedPayload.analysis.summary, /网络|超时|先按可疑情况处理/);
  assert.ok(storedPayload.analysis.sop_steps.some((item) => /不要继续|先停止|不转账/.test(item)));
}

async function run() {
  await testAnalyzeSkipsImageUploadAfterOcrTextExtraction();
  await testAnalyzeFailureStoresSafeFallbackForRetry();
  console.log("check page image flow tests passed");
}

run().catch((error) => {
  console.error(error);
  process.exit(1);
});
