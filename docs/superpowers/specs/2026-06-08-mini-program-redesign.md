# Mini Program Redesign Spec

## Goal

Turn the current single long assistant page into a clearer mini program flow:

1. Home chooses the user's intent.
2. Check page collects text, screenshot, and incident state.
3. Result page focuses on immediate actions.
4. Activity page remains a separate challenge flow.

The backend LLM/cloud-function behavior stays unchanged.

## Problems In The Current UI

- The home page tries to be an emergency guide, mode selector, input form, OCR tool, state checklist, result page, and detail report at once.
- The result is below a long form, so users may not notice it after analysis.
- OCR appears as the screenshot path's main action even though MiniMax M3 can analyze screenshots directly.
- The visual style uses many heavy cards and large headings, creating a crowded page on iPhone-sized screens.
- The activity challenge has a distinct event purpose but currently shares too much visual weight with the emergency assistant.

## Product Shape

### Home

Home is a calm routing surface. It shows:

- Brand and direct emergency call actions.
- Primary action: "马上判断".
- Secondary action: "活动闯关".
- Emergency action: "已经出事".

Home should not contain a textarea, OCR controls, or result details.

### Check Page

Check page owns case intake:

- Scenario chips.
- Text input.
- Screenshot upload.
- Incident-state checklist.
- Inline urgent guide when a high-risk state is selected.
- One primary analyze button.

OCR remains available only as a helper after a screenshot is selected, but the copy should make clear that direct screenshot analysis works.

### Result Page

Result page owns action:

- Risk level and short summary at the top.
- Three immediate actions with checkable progress.
- 110/96110/copy-to-family/share actions.
- Privacy and official verification reminders.
- Detailed reasoning collapsed lower on the page.

Result data is passed through local storage after `analyzeCase` returns. This avoids URL-size limits and keeps the cloud function contract unchanged.

### Activity Page

Activity page remains `pages/activity/activity`. It should stay visually warmer and more playful than the check flow, using landing-kit cues: progress, score, stamp reward, and replay/share.

## Visual Direction

- Use a WeUI-like hierarchy: fewer cards, clearer spacing, predictable button surfaces.
- Keep "真的假的鸭" warm and friendly, but reserve red for urgent actions.
- Use teal for safe/primary actions, red for emergency, gold for activity/reward.
- Avoid nested cards and unnecessary decorative strips.
- Keep text legible for older users: no cramped three-column action rows on mobile.

## External References

- WeUI / WeChat-native structure for familiar controls.
- TDesign MiniProgram for step/result/component hierarchy ideas, without adding the dependency in this pass.
- Vant Weapp as a later option if the project needs a component library.
- Quiz mini program examples for independent answer/result flow.
- Anti-scam detector products that use a simple intake -> analysis -> verdict flow.

## Non-Goals

- Do not change cloud function provider routing.
- Do not add login, history, database, or user accounts.
- Do not add a component library in this pass.
- Do not redesign the mascot or generated landing-kit assets.
