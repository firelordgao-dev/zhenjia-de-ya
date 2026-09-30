const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const pageDir = path.join(__dirname, "..", "miniprogram/pages/result");
const wxml = fs.readFileSync(path.join(pageDir, "result.wxml"), "utf8");
const js = fs.readFileSync(path.join(pageDir, "result.js"), "utf8");
const wxss = fs.readFileSync(path.join(pageDir, "result.wxss"), "utf8");

function mustAppearBefore(first, second) {
  const firstIndex = wxml.indexOf(first);
  const secondIndex = wxml.indexOf(second);
  assert.notEqual(firstIndex, -1, `${first} should exist`);
  assert.notEqual(secondIndex, -1, `${second} should exist`);
  assert.ok(firstIndex < secondIndex, `${first} should appear before ${second}`);
}

assert.ok(wxml.includes('class="result-hero risk-{{analysis.risk_level}}"'), "result should start with a focused hero");
assert.ok(wxml.includes("现在先做这三件"), "result should prioritize immediate actions");
assert.ok(wxml.includes('class="result-main-actions"'), "result should expose primary actions near the top");
assert.ok(wxml.includes("复制给家人"), "copy-to-family should be a primary action");
assert.ok(wxml.includes("再判断一次"), "retry should be a primary action");
assert.ok(wxml.includes('wx:if="{{isSafeFallback}}"'), "safe fallback state should have a dedicated panel");
assert.ok(wxml.includes("只用文字再试"), "safe fallback should offer text-only retry");
assert.ok(wxml.includes("重新上传截图"), "safe fallback should offer image retry");

mustAppearBefore("现在先做这三件", "保护自己");
mustAppearBefore("复制给家人", "detail-toggle");
mustAppearBefore("只用文字再试", "detail-toggle");

assert.ok(js.includes("isSafeFallback"), "result page should derive safe fallback state");
assert.ok(js.includes("retryText"), "result page should keep retry text");
assert.ok(js.includes("retryWithText()"), "result page should support text-only retry");
assert.ok(js.includes("retryWithImage()"), "result page should support image retry");
assert.match(wxss, /\.bottom-actions\s*\{[^}]*grid-template-columns:\s*1fr;/s, "single bottom action should occupy the full row");

console.log("result page layout tests passed");
