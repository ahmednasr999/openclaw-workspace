import { NextResponse } from "next/server";

// This endpoint is called by the DB layer when tasks move to Review
// It writes a flag file that OpenClaw's cron can pick up
import { writeFileSync } from "fs";
import path from "path";

export async function POST(request: Request) {
  try {
    const { taskId, taskTitle, from, to } = await request.json();
    
    // Write notification to a queue file for OpenClaw to pick up
    const notifyPath = path.join(process.cwd(), "notifications.jsonl");
    const entry = JSON.stringify({ 
      taskId, taskTitle, from, to, 
      timestamp: new Date().toISOString() 
    }) + "\n";
    
    writeFileSync(notifyPath, entry, { flag: "a" });
    
    return NextResponse.json({ success: true });
  } catch (error) {
    return NextResponse.json({ error: "Failed to queue notification" }, { status: 500 });
  }
}
