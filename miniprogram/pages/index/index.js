Page({
  goCheck() {
    wx.navigateTo({
      url: "/pages/check/check"
    });
  },

  goEmergencyCheck() {
    wx.navigateTo({
      url: "/pages/check/check?emergency=1"
    });
  },

  goActivityChallenge() {
    wx.navigateTo({
      url: "/pages/activity/activity"
    });
  },

  callPolice() {
    wx.makePhoneCall({ phoneNumber: "110" });
  },

  callAntiFraud() {
    wx.makePhoneCall({ phoneNumber: "96110" });
  },

  onShareAppMessage() {
    return {
      title: "真的假的鸭：转账之前，先问一问",
      path: "/pages/index/index",
      imageUrl: "/assets/activity-guide-duck.jpg"
    };
  }
});
