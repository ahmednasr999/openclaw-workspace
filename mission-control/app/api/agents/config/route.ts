import { NextResponse } from "next/server";
import { readFileSync, writeFileSync } from "fs";
import { join } from "path";

const CONFIG_PATH = join(process.cwd(), "config", "agents.json");

export async function GET() {
  try {
    const raw = readFileSync(CONFIG_PATH, "utf-8");
    const agents = JSON.parse(raw);
    return NextResponse.json(agents);
  } catch (error) {
    console.error("Error reading agents config:", error);
    return NextResponse.json({ error: "Failed to read agents config" }, { status: 500 });
  }
}

export async function PUT(request: Request) {
  try {
    const body = await request.json();
    writeFileSync(CONFIG_PATH, JSON.stringify(body, null, 2), "utf-8");
    return NextResponse.json({ success: true });
  } catch (error) {
    console.error("Error writing agents config:", error);
    return NextResponse.json({ error: "Failed to write agents config" }, { status: 500 });
  }
}
