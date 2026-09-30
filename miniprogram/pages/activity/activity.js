const challenge = require("../../lib/activityChallenge");

Page({
  data: {
    questions: challenge.questions,
    currentIndex: 0,
    currentQuestion: challenge.questions[0],
    answers: [],
    selectedValue: "",
    answeredCurrent: false,
    currentCorrect: false,
    progress: challenge.getProgress([]),
    isFinished: false,
    score: 0,
    level: challenge.getLevel(0),
    shareText: ""
  },

  onLoad(options = {}) {
    if (options.reset === "1") {
      this.replay();
    }
  },

  chooseOption(event) {
    if (this.data.answeredCurrent) return;

    const selectedValue = event.currentTarget.dataset.value;
    const answers = this.data.answers.slice();
    answers[this.data.currentIndex] = selectedValue;

    const currentQuestion = this.data.currentQuestion;
    const currentCorrect = selectedValue === currentQuestion.correctOption;

    this.setData({
      answers,
      selectedValue,
      answeredCurrent: true,
      currentCorrect,
      progress: challenge.getProgress(answers)
    });
  },

  nextQuestion() {
    if (!this.data.answeredCurrent) {
      wx.showToast({
        title: "先选真假",
        icon: "none"
      });
      return;
    }

    const nextIndex = this.data.currentIndex + 1;
    if (nextIndex >= challenge.questions.length) {
      this.finishChallenge();
      return;
    }

    this.setData({
      currentIndex: nextIndex,
      currentQuestion: challenge.questions[nextIndex],
      selectedValue: this.data.answers[nextIndex] || "",
      answeredCurrent: Boolean(this.data.answers[nextIndex]),
      currentCorrect: this.data.answers[nextIndex] === challenge.questions[nextIndex].correctOption
    });
  },

  finishChallenge() {
    const score = challenge.getScore(this.data.answers);
    const level = challenge.getLevel(score);
    this.setData({
      isFinished: true,
      score,
      level,
      shareText: challenge.buildShareText(score),
      progress: challenge.getProgress(this.data.answers)
    });
  },

  replay() {
    this.setData({
      currentIndex: 0,
      currentQuestion: challenge.questions[0],
      answers: [],
      selectedValue: "",
      answeredCurrent: false,
      currentCorrect: false,
      progress: challenge.getProgress([]),
      isFinished: false,
      score: 0,
      level: challenge.getLevel(0),
      shareText: ""
    });
  },

  copyShareText() {
    const text = this.data.shareText || challenge.buildShareText(this.data.score);
    wx.setClipboardData({
      data: text,
      success: () => {
        wx.showToast({
          title: "已复制",
          icon: "success"
        });
      }
    });
  },

  goAssistant() {
    wx.reLaunch({
      url: "/pages/index/index"
    });
  },

  onShareAppMessage() {
    return {
      title: this.data.isFinished ? `${this.data.level.label}：我完成了反诈公益小测` : "真的假的鸭：反诈公益小测",
      path: "/pages/activity/activity",
      imageUrl: "/assets/activity-guide-duck.jpg"
    };
  }
});
