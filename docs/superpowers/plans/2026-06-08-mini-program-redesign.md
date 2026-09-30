# Mini Program Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Split the current one-page assistant into a clearer home -> check -> result flow while keeping the deployed cloud function contract unchanged.

**Architecture:** `pages/index/index` becomes a routing home. A new `pages/check/check` page owns intake and calls `analyzeCase`. A new `pages/result/result` page reads the latest analysis from local storage and displays action-first results. `pages/activity/activity` remains the event challenge mode.

**Tech Stack:** WeChat Mini Program WXML/WXSS/JS, `wx.cloud.callFunction`, local `wx.setStorageSync`, existing Node verification tests.

---

### Task 1: Route Structure

**Files:**
- Modify: `miniprogram/app.json`
- Modify: `miniprogram/pages/index/index.js`
- Modify: `miniprogram/pages/index/index.wxml`
- Modify: `miniprogram/pages/index/index.wxss`
- Create: `miniprogram/pages/check/check.js`
- Create: `miniprogram/pages/check/check.wxml`
- Create: `miniprogram/pages/check/check.wxss`
- Create: `miniprogram/pages/check/check.json`
- Create: `miniprogram/pages/result/result.js`
- Create: `miniprogram/pages/result/result.wxml`
- Create: `miniprogram/pages/result/result.wxss`
- Create: `miniprogram/pages/result/result.json`

- [x] **Step 1: Register routes**

Set app pages to:

```json
[
  "pages/index/index",
  "pages/check/check",
  "pages/result/result",
  "pages/activity/activity"
]
```

- [x] **Step 2: Convert home to routing page**

Home should only navigate to check, activity, or emergency check.

- [x] **Step 3: Create check page**

Move intake, screenshot upload, incident states, urgent guide, and cloud function call to `pages/check/check`.

- [x] **Step 4: Create result page**

Read `latestAnalysisResult` from storage, display risk/action sections, and support copy/share/call actions.

### Task 2: Visual System

**Files:**
- Modify: `miniprogram/pages/index/index.wxss`
- Create: `miniprogram/pages/check/check.wxss`
- Create: `miniprogram/pages/result/result.wxss`
- Modify: `miniprogram/pages/activity/activity.wxss`

- [x] **Step 1: Home visual hierarchy**

Use one brand hero, one emergency band, and three intent cards.

- [x] **Step 2: Check visual hierarchy**

Use a compact form flow with a sticky-feeling primary action at the bottom of the content.

- [x] **Step 3: Result visual hierarchy**

Use risk banner -> immediate checklist -> contact actions -> collapsible details.

- [x] **Step 4: Activity polish**

Keep the event challenge page separate and avoid cramped action rows.

### Task 3: Verification

**Files:**
- Modify: `tests/activityChallenge.test.cjs` if needed
- Create: `tests/appRoutes.test.cjs`
- Modify: `package.json`
- Modify: `README.md`
- Modify: `docs/PROJECT_CHECKPOINT.md`

- [x] **Step 1: Add route smoke test**

Assert `miniprogram/app.json` contains the new route order.

- [x] **Step 2: Run verification**

Run:

```powershell
node tests/appRoutes.test.cjs
node tests/activityChallenge.test.cjs
node tests/analyzeCaseProviders.test.cjs
node --check miniprogram/pages/index/index.js
node --check miniprogram/pages/check/check.js
node --check miniprogram/pages/result/result.js
node --check miniprogram/pages/activity/activity.js
node --check cloudfunctions/analyzeCase/index.js
```

Expected: all commands exit 0.
