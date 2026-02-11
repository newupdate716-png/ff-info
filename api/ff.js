export default async function handler(req, res) {
  res.setHeader("Content-Type", "application/json; charset=UTF-8");

  const uid = (req.query.uid || "").trim();

  if (!uid) {
    return res.status(400).json({
      success: false,
      message: "Missing uid parameter",
    });
  }

  try {
    const payload = {
      uid: uid,
      ts: Date.now(),
    };

    const encoded = Buffer
      .from(JSON.stringify(payload))
      .toString("base64");

    const apiUrl =
      `https://1.indian-plays.site/getnickname.php?data=${encodeURIComponent(encoded)}`;

    const response = await fetch(apiUrl, {
      method: "GET",
      headers: {
        "User-Agent":
          "Mozilla/5.0 (Linux; Android 14; SM-G990E) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Mobile Safari/537.36",
        "Accept": "application/json",
        "X-Requested-With": "com.instagram.android",
        "Referer": "https://instagram.com/",
        "Origin": "https://instagram.com"
      }
    });

    const text = await response.text();

    if (!text) {
      return res.status(502).json({
        success: false,
        message: "Upstream empty response"
      });
    }

    const data = JSON.parse(text);

    if (data.error || !data.accountid) {
      return res.status(404).json({
        success: false,
        message: "Invalid UID or blocked by upstream"
      });
    }

    const nickname = data.nickname
      ? data.nickname.replace(/[\u3164\uf8ff]/g, "")
      : "Unknown";

    return res.status(200).json({
      success: true,
      credit: "@sakib01994",
      UID: data.accountid,
      Name: nickname,
      Level: data.level,
      Region: data.region,
    });

  } catch (err) {
    return res.status(500).json({
      success: false,
      message: "Server error"
    });
  }
} 
