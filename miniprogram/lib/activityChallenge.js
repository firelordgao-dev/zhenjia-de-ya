const questions = [
  {
    id: "verify-code",
    title: "对方要验证码，说不告诉别人就行，是真的假的？",
    scene: "客服说退款要先报短信验证码。",
    correctOption: "fake",
    options: [
      { value: "true", label: "真的" },
      { value: "fake", label: "假的" }
    ],
    explanation: "验证码就是账户钥匙。陌生人要验证码，先按高风险处理。"
  },
  {
    id: "official-app",
    title: "遇到退款、扣费、理赔，自己打开官方 App 核实，是真的假的？",
    scene: "不点对方链接，自己从官方入口查订单。",
    correctOption: "true",
    options: [
      { value: "true", label: "真的" },
      { value: "fake", label: "假的" }
    ],
    explanation: "核实要走官方 App、官方客服电话、银行柜台或 110/96110。"
  },
  {
    id: "safe-account",
    title: "警官让你转到安全账户配合调查，是真的假的？",
    scene: "对方说涉嫌洗钱，要把钱转走自证清白。",
    correctOption: "fake",
    options: [
      { value: "true", label: "真的" },
      { value: "fake", label: "假的" }
    ],
    explanation: "公检法不会让群众转账到安全账户，也不会要求屏幕共享。"
  },
  {
    id: "screen-share",
    title: "开屏幕共享时打开银行 App 没关系，是真的假的？",
    scene: "对方在会议软件里催你打开支付、银行或短信。",
    correctOption: "fake",
    options: [
      { value: "true", label: "真的" },
      { value: "fake", label: "假的" }
    ],
    explanation: "屏幕共享会暴露验证码、余额和操作页面，要马上关闭。"
  },
  {
    id: "keep-evidence",
    title: "可疑情况先截图留证，再找家人或 110，是真的假的？",
    scene: "聊天、链接、电话、二维码和转账凭证都先保存。",
    correctOption: "true",
    options: [
      { value: "true", label: "真的" },
      { value: "fake", label: "假的" }
    ],
    explanation: "留证据有助于家人判断，也有助于报警和联系银行止付。"
  }
];

const levels = [
  { minScore: 5, label: "反诈守护官", summary: "你已经很会停手、核实和留证。" },
  { minScore: 4, label: "反诈达人", summary: "大多数风险你能识别，继续记住验证码和转账红线。" },
  { minScore: 2, label: "反诈新手", summary: "已经会识别一些陷阱，遇到钱和验证码先找人核实。" },
  { minScore: 0, label: "反诈小白", summary: "先记住三件事：不转钱、不报码、不共享屏幕。" }
];

function getScore(answers) {
  return questions.reduce((score, question, index) => {
    return answers[index] === question.correctOption ? score + 1 : score;
  }, 0);
}

function getLevel(score) {
  return levels.find((level) => score >= level.minScore) || levels[levels.length - 1];
}

function getProgress(answers) {
  return questions.map((question, index) => ({
    index: index + 1,
    done: Boolean(answers[index]),
    correct: answers[index] === question.correctOption
  }));
}

function buildShareText(score) {
  const level = getLevel(score);
  return `我在“真的假的鸭”完成了反诈公益小测，得分 ${score}/${questions.length}，等级是“${level.label}”。转账、验证码、屏幕共享之前，先停下问一问。`;
}

module.exports = {
  questions,
  getScore,
  getLevel,
  getProgress,
  buildShareText
};
