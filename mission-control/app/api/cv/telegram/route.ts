import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { jobTitle, company, downloadUrl } = body;

    if (!jobTitle || !company || !downloadUrl) {
      return NextResponse.json({ error: "jobTitle, company, and downloadUrl required" }, { status: 400 });
    }

    // Message to send
    const message = `📄 *New CV Ready*

*Position:* ${jobTitle}
*Company:* ${company}

✅ QA Approved - Ready for submission
📎 Download: ${downloadUrl}

Best of luck with your application! 🍀`;

    // Send via OpenClaw message tool (this routes to configured channels)
    const telegramRes = await fetch("http://localhost:3001/api/message/send", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message,
        channel: "telegram",
      }),
    });

    if (telegramRes.ok) {
      return NextResponse.json({
        success: true,
        message: "CV sent via Telegram",
        jobTitle,
        company,
      });
    } else {
      // Fallback: just log it
      console.log("Telegram send failed, CV ready:", { jobTitle, company, downloadUrl });
      return NextResponse.json({
        success: true,
        message: "CV generated (Telegram not configured)",
        jobTitle,
        company,
        downloadUrl,
      });
    }
  } catch (error) {
    console.error("Telegram send error:", error);
    return NextResponse.json({ error: "Failed to send CV" }, { status: 500 });
  }
}
