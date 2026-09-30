const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const root = path.join(__dirname, "..");
const activityAsset = path.join(root, "miniprogram", "assets", "activity-guide-duck.jpg");

function readMiniProgramFile(relativePath) {
  return fs.readFileSync(path.join(root, "miniprogram", relativePath), "utf8");
}

assert.ok(fs.existsSync(activityAsset), "compressed activity guide asset should exist in miniprogram/assets");

const activityAssetSize = fs.statSync(activityAsset).size;
assert.ok(activityAssetSize > 20_000, "activity guide asset should not be an empty placeholder");
assert.ok(activityAssetSize < 420_000, "activity guide asset should stay small enough for the mini program package");

const indexWxml = readMiniProgramFile("pages/index/index.wxml");
const indexWxss = readMiniProgramFile("pages/index/index.wxss");
const checkWxml = readMiniProgramFile("pages/check/check.wxml");
const checkWxss = readMiniProgramFile("pages/check/check.wxss");
const resultWxml = readMiniProgramFile("pages/result/result.wxml");
const resultWxss = readMiniProgramFile("pages/result/result.wxss");
const activityWxml = readMiniProgramFile("pages/activity/activity.wxml");

assert.ok(indexWxml.includes("/assets/activity-guide-duck.jpg"), "home page should use the activity key visual");
assert.ok(activityWxml.includes("/assets/activity-guide-duck.jpg"), "activity page should use the activity key visual");
assert.ok(checkWxml.includes('class="activity-ribbon"'), "check page should carry the activity ribbon motif");
assert.ok(resultWxml.includes('class="result-stamp"'), "result page should carry the stamp motif");

assert.match(indexWxss, /\.hero-ribbon\b/, "home page should style the activity ribbon");
assert.match(checkWxss, /\.activity-ribbon\b/, "check page should style the activity ribbon");
assert.match(resultWxss, /\.result-stamp\b/, "result page should style the result stamp");

console.log("activity visual style tests passed");
