import { NextResponse } from "next/server";
import fs from "fs";
import path from "path";

const QUEUE_FILE = path.join(process.cwd(), "cv-telegram-queue.json");

interface QueuedCV {
  id: string;
  jobTitle: string;
  company: string;
  pdfPath: string;
  status: "pending" | "sent" | "failed";
  createdAt: string;
  error?: string;
}

function readQueue(): QueuedCV[] {
  try {
    if (fs.existsSync(QUEUE_FILE)) {
      return JSON.parse(fs.readFileSync(QUEUE_FILE, "utf-8"));
    }
  } catch {}
  return [];
}

function writeQueue(queue: QueuedCV[]) {
  fs.writeFileSync(QUEUE_FILE, JSON.stringify(queue, null, 2));
}

export const dynamic = "force-dynamic";

// Queue CV for Telegram
export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { jobTitle, company, pdfPath } = body;

    if (!jobTitle || !company || !pdfPath) {
      return NextResponse.json({ error: "jobTitle, company, and pdfPath required" }, { status: 400 });
    }

    const queue = readQueue();
    const id = `cv-${Date.now()}`;
    
    queue.unshift({
      id,
      jobTitle,
      company,
      pdfPath,
      status: "pending",
      createdAt: new Date().toISOString()
    });
    
    writeQueue(queue);

    return NextResponse.json({
      success: true,
      id,
      message: "CV queued for Telegram",
      queueLength: queue.length
    });
  } catch (error) {
    return NextResponse.json({ error: "Failed to queue CV" }, { status: 500 });
  }
}

// Get queue status
export async function GET() {
  try {
    const queue = readQueue();
    const pending = queue.filter(q => q.status === "pending");
    
    return NextResponse.json({
      queue,
      pendingCount: pending.length,
      readyToSend: pending.length > 0
    });
  } catch (error) {
    return NextResponse.json({ error: "Failed to get queue" }, { status: 500 });
  }
}

// Mark as sent (called after manual/cron trigger)
export async function PATCH(request: Request) {
  try {
    const body = await request.json();
    const { id, status, error } = body;

    const queue = readQueue();
    const item = queue.find(q => q.id === id);
    
    if (item) {
      item.status = status || "sent";
      if (error) item.error = error;
      writeQueue(queue);
    }

    return NextResponse.json({ success: true });
  } catch (error) {
    return NextResponse.json({ error: "Failed to update" }, { status: 500 });
  }
}

// Clear queue
export async function DELETE(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const clearAll = searchParams.get("all") === "true";
    
    if (clearAll) {
      writeQueue([]);
      return NextResponse.json({ success: true, message: "Queue cleared" });
    }
    
    return NextResponse.json({ error: "Use ?all=true to clear" }, { status: 400 });
  } catch (error) {
    return NextResponse.json({ error: "Failed to clear" }, { status: 500 });
  }
}
