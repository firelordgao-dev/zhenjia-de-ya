# Activity Challenge Mode Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a C-zone activity challenge mode inside the existing mini program while keeping the anti-scam assistant as the default home.

**Architecture:** The mini program stays single-app and gains a second route: `pages/activity/activity`. A reusable `miniprogram/lib/activityChallenge.js` module owns static quiz questions, scoring, level labels, and share text so the page can stay focused on UI state. The existing `pages/index/index` keeps the emergency assistant flow and only adds a small entry card to the activity mode.

**Tech Stack:** WeChat Mini Program WXML/WXSS/JS, CommonJS helper module, Node-based focused tests.

---

### Task 1: Activity Challenge Logic

**Files:**
- Create: `miniprogram/lib/activityChallenge.js`
- Create: `tests/activityChallenge.test.cjs`
- Modify: `package.json`

- [x] **Step 1: Write failing tests**

```js
const assert = require("node:assert/strict");
const challenge = require("../miniprogram/lib/activityChallenge.js");

assert.equal(challenge.questions.length, 5);
assert.equal(challenge.getScore([true, false, true, false, true]), 3);
assert.equal(challenge.getLevel(5).label, "反诈守护官");
assert.match(challenge.buildShareText(5), /5\/5/);
```

- [x] **Step 2: Run test and confirm it fails**

Run: `node tests/activityChallenge.test.cjs`
Expected: FAIL because `miniprogram/lib/activityChallenge.js` does not exist yet.

- [x] **Step 3: Implement minimal logic module**

Create a five-question module with `questions`, `getScore`, `getLevel`, `getProgress`, and `buildShareText`.

- [x] **Step 4: Run test and confirm it passes**

Run: `node tests/activityChallenge.test.cjs`
Expected: PASS with `activityChallenge tests passed`.

### Task 2: Mini Program Activity Route

**Files:**
- Create: `miniprogram/pages/activity/activity.js`
- Create: `miniprogram/pages/activity/activity.wxml`
- Create: `miniprogram/pages/activity/activity.wxss`
- Create: `miniprogram/pages/activity/activity.json`
- Modify: `miniprogram/app.json`
- Modify: `miniprogram/pages/index/index.js`
- Modify: `miniprogram/pages/index/index.wxml`
- Modify: `miniprogram/pages/index/index.wxss`

- [x] **Step 1: Register `pages/activity/activity` after the default home page**

Keep `pages/index/index` first in `app.json`.

- [x] **Step 2: Add activity entry from home**

Add a quick-start card labeled `活动闯关` that calls `goActivityChallenge`.

- [x] **Step 3: Build activity page**

Use the challenge module for question state, answer selection, result level, progress dots, stamp reward, replay, and share text.

### Task 3: Docs And Verification

**Files:**
- Modify: `README.md`
- Modify: `docs/PROJECT_CHECKPOINT.md`

- [x] **Step 1: Document product split**

State that the mini program has a default anti-scam assistant and an activity challenge mode.

- [x] **Step 2: Verify**

Run:

```powershell
node tests/activityChallenge.test.cjs
node tests/analyzeCaseProviders.test.cjs
node --check miniprogram/pages/activity/activity.js
node --check miniprogram/pages/index/index.js
node -e "JSON.parse(require('fs').readFileSync('miniprogram/app.json','utf8'))"
```

Expected: all commands exit 0.
