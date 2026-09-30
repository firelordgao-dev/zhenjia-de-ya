const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const appJson = JSON.parse(
  fs.readFileSync(path.join(__dirname, "..", "miniprogram", "app.json"), "utf8")
);

assert.deepEqual(appJson.pages, [
  "pages/index/index",
  "pages/check/check",
  "pages/result/result",
  "pages/activity/activity"
]);

for (const route of appJson.pages) {
  const pageRoot = path.join(__dirname, "..", "miniprogram", route);
  for (const ext of [".js", ".wxml", ".wxss", ".json"]) {
    assert.ok(fs.existsSync(`${pageRoot}${ext}`), `${route}${ext} should exist`);
  }
}

console.log("appRoutes tests passed");
