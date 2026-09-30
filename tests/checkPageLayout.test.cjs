const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const pageDir = path.join(__dirname, "..", "miniprogram/pages/check");
const wxml = fs.readFileSync(path.join(pageDir, "check.wxml"), "utf8");
const js = fs.readFileSync(path.join(pageDir, "check.js"), "utf8");
const wxss = fs.readFileSync(path.join(pageDir, "check.wxss"), "utf8");

function mustAppearBefore(first, second) {
  const firstIndex = wxml.indexOf(first);
  const secondIndex = wxml.indexOf(second);
  assert.notEqual(firstIndex, -1, `${first} should exist`);
  assert.notEqual(secondIndex, -1, `${second} should exist`);
  assert.ok(firstIndex < secondIndex, `${first} should appear before ${second}`);
}

assert.ok(wxml.includes('class="panel primary-intake"'), "primary intake panel should be visually prioritized");
assert.ok(wxml.includes("第一步：放入可疑内容"), "page should lead with content intake");
assert.ok(wxml.includes("第二步：有没有做过危险操作？"), "incident states should remain as step two");
assert.ok(wxml.includes('class="more-options" wx:if="{{showMoreOptions}}"'), "secondary choices should be hidden behind more options");
assert.ok(wxml.includes("更多辅助信息"), "page should expose secondary choices without making them mandatory");

mustAppearBefore("第一步：放入可疑内容", "第二步：有没有做过危险操作？");
mustAppearBefore("第二步：有没有做过危险操作？", "更多辅助信息");

assert.ok(js.includes("showMoreOptions: false"), "secondary choices should be collapsed by default");
assert.ok(js.includes("toggleMoreOptions()"), "page should allow expanding secondary choices");

const ghostButtonRule = wxss.match(/\.ghost-button\s*\{[^}]*\}/s)?.[0] || "";
assert.ok(ghostButtonRule.includes("border-radius: 14rpx;"), "110 button should use a normal rounded rectangle");
assert.ok(ghostButtonRule.includes("padding: 0;"), "110 button should override mini program button padding");
assert.ok(!ghostButtonRule.includes("border-radius: 50%"), "110 button should not be styled as a stamp");
assert.ok(!ghostButtonRule.includes("transform:"), "110 button should not be rotated");

console.log("check page layout tests passed");
