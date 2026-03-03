import { NextRequest, NextResponse } from "next/server";
import { loadModuleSnapshot } from "@/lib/module-store";

export const runtime = "nodejs";

const allowed = ["docs", "memory", "team", "office", "projects", "tasks"] as const;
type AllowedKey = (typeof allowed)[number];

function isAllowedKey(value: string): value is AllowedKey {
  return allowed.includes(value as AllowedKey);
}

export async function GET(request: NextRequest) {
  const snapshot = await loadModuleSnapshot();
  const moduleName = request.nextUrl.searchParams.get("module");

  if (!moduleName) {
    return NextResponse.json({ snapshot, fetchedAt: new Date().toISOString() });
  }

  if (!isAllowedKey(moduleName)) {
    return NextResponse.json({ error: "Invalid module query" }, { status: 400 });
  }

  return NextResponse.json({ data: snapshot[moduleName], fetchedAt: new Date().toISOString() });
}
