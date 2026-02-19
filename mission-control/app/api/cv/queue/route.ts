import { NextResponse } from "next/server";
import fs from "fs";
import path from "path";

const QUEUE_FILE = path.join(process.cwd(), "cv-generation-queue.json");

interface QueueItem {
  id: string;
  jobDescription: string;
  createdAt: string;
  status: "pending" | "completed";
  cvHtml?: string;
}

// Read queue
function readQueue(): QueueItem[] {
  try {
    if (fs.existsSync(QUEUE_FILE)) {
      return JSON.parse(fs.readFileSync(QUEUE_FILE, "utf-8"));
    }
  } catch {}
  return [];
}

// Write queue
function writeQueue(items: QueueItem[]) {
  fs.writeFileSync(QUEUE_FILE, JSON.stringify(items, null, 2));
}

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { jobDescription } = body;

    if (!jobDescription) {
      return NextResponse.json({ error: "jobDescription required" }, { status: 400 });
    }

    const queue = readQueue();
    const id = `cv-${Date.now()}`;
    
    queue.unshift({
      id,
      jobDescription,
      createdAt: new Date().toISOString(),
      status: "pending",
    });
    
    writeQueue(queue);

    return NextResponse.json({
      success: true,
      id,
      message: "Job added to queue. AI will process and generate CV.",
      queueLength: queue.length,
    });
  } catch (error) {
    return NextResponse.json({ error: "Failed to add to queue" }, { status: 500 });
  }
}

export async function GET() {
  try {
    const queue = readQueue();
    return NextResponse.json({ queue });
  } catch (error) {
    return NextResponse.json({ error: "Failed to read queue" }, { status: 500 });
  }
}

// Mark as completed (called by AI when CV is generated)
export async function PATCH(request: Request) {
  try {
    const body = await request.json();
    const { id, cvHtml } = body;

    const queue = readQueue();
    const item = queue.find((i) => i.id === id);
    
    if (item) {
      item.status = "completed";
      item.cvHtml = cvHtml;
      writeQueue(queue);
    }

    return NextResponse.json({ success: true });
  } catch (error) {
    return NextResponse.json({ error: "Failed to update" }, { status: 500 });
  }
}
