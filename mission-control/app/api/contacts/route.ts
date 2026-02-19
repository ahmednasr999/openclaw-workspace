import { NextResponse } from "next/server";
import { sqliteDb } from "@/lib/db";

export async function GET() {
  try {
    const contacts = sqliteDb.getAllContacts();
    // Parse tags JSON string back to array
    return NextResponse.json(contacts.map((c: any) => ({
      ...c,
      tags: c.tags ? JSON.parse(c.tags) : [],
    })));
  } catch (error) {
    return NextResponse.json({ error: "Failed to fetch contacts" }, { status: 500 });
  }
}

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const id = sqliteDb.addContact({
      name: body.name,
      role: body.role,
      company: body.company,
      email: body.email,
      phone: body.phone,
      linkedin: body.linkedin,
      category: body.category || "Networking",
      status: body.status || "Active",
      warmth: body.warmth || "Warm",
      notes: body.notes,
      lastContactDate: body.lastContactDate,
      nextFollowUp: body.nextFollowUp,
      source: body.source,
      tags: body.tags ? JSON.stringify(body.tags) : undefined,
      createdAt: new Date().toISOString(),
    });
    return NextResponse.json({ id, success: true });
  } catch (error) {
    return NextResponse.json({ error: "Failed to create contact" }, { status: 500 });
  }
}

export async function PATCH(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const id = parseInt(searchParams.get("id") || "");
    const body = await request.json();
    if (body.tags && Array.isArray(body.tags)) body.tags = JSON.stringify(body.tags);
    sqliteDb.updateContact(id, body);
    return NextResponse.json({ success: true });
  } catch (error) {
    return NextResponse.json({ error: "Failed to update contact" }, { status: 500 });
  }
}

export async function DELETE(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const id = parseInt(searchParams.get("id") || "");
    if (id) sqliteDb.deleteContact(id);
    return NextResponse.json({ success: true });
  } catch (error) {
    return NextResponse.json({ error: "Failed to delete contact" }, { status: 500 });
  }
}
