const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

function loadMiniProgramModule(relativePath) {
  const filename = path.join(__dirname, "..", relativePath);
  const module = { exports: {} };
  const code = fs.readFileSync(filename, "utf8");
  vm.runInNewContext(code, { module, exports: module.exports }, { filename });
  return module.exports;
}

const challenge = loadMiniProgramModule("miniprogram/lib/activityChallenge.js");

function testQuestionSet() {
  assert.equal(challenge.questions.length, 5);
  assert.equal(challenge.questions[0].id, "verify-code");
  assert.equal(challenge.questions[0].correctOption, "fake");
  assert.ok(challenge.questions.every((question) => question.options.length === 2));
}

function testScoreAndProgress() {
  assert.equal(challenge.getScore(["fake", "true", "fake", "fake", "true"]), 5);
  assert.equal(challenge.getScore(["true", "true", "fake", "", "true"]), 3);
  assert.deepEqual(JSON.parse(JSON.stringify(challenge.getProgress(["fake", "", "fake"]))), [
    { index: 1, done: true, correct: true },
    { index: 2, done: false, correct: false },
    { index: 3, done: true, correct: true },
    { index: 4, done: false, correct: false },
    { index: 5, done: false, correct: false }
  ]);
}

function testLevels() {
  assert.equal(challenge.getLevel(0).label, "反诈小白");
  assert.equal(challenge.getLevel(3).label, "反诈新手");
  assert.equal(challenge.getLevel(4).label, "反诈达人");
  assert.equal(challenge.getLevel(5).label, "反诈守护官");
}

function testShareText() {
  const text = challenge.buildShareText(5);
  assert.match(text, /真的假的鸭/);
  assert.match(text, /5\/5/);
  assert.match(text, /反诈守护官/);
}

testQuestionSet();
testScoreAndProgress();
testLevels();
testShareText();

console.log("activityChallenge tests passed");
