// Free Fire UID Info API
// Credit: @sakib01994

export default async function handler(req, res) {
  res.setHeader("Content-Type", "application/json; charset=UTF-8");

  const uid = (req.query.uid || "").trim();

  if (!uid) {
    return res.status(400).json({
      success: false,
      message: "Missing uid parameter",
      example: "/api/ff?uid=123456789",
    });
  }

  try {
    // Build payload
    const payload = {
      uid: uid,
      ts: Date.now(),
    };

    // Base64 encode
    const data = Buffer.from(JSON.stringify(payload)).toString("base64");

    const url = `https://1.indian-plays.site/getnickname.php?data=${encodeURIComponent(data)}`;

    const response = await fetch(url, {
      headers: {
        "User-Agent":
          "Mozilla/5.0 (Linux; Android 14) Instagram 412.0.0.35.87 Android",
        "X-Requested-With": "com.instagram.android",
      },
    });

    const js = await response.json();

    if (js.error) {
      return res.status(404).json({
        success: false,
        message: "Invalid UID or not found",
      });
    }

    // Clean nickname (remove hidden unicode)
    const nickname = js.nickname
      ? js.nickname.replace(/[\u3164\uf8ff]/g, "")
      : "Unknown";

    return res.status(200).json({
      success: true,
      credit: "@sakib01994",
      UID: js.accountid,
      Name: nickname,
      Level: js.level,
      Region: js.region,
    });
  } catch (e) {
    return res.status(500).json({
      success: false,
      message: "Server error",
    });
  }
}
