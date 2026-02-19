import { NextResponse } from "next/server";
import { sqliteDb } from "@/lib/db";

export async function GET() {
  try {
    const posts = sqliteDb.getAllPosts();
    return NextResponse.json(posts);
  } catch (error) {
    console.error("Error fetching posts:", error);
    return NextResponse.json({ error: "Failed to fetch posts" }, { status: 500 });
  }
}

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const postId = sqliteDb.addPost(body);
    return NextResponse.json({ id: postId, success: true });
  } catch (error) {
    console.error("Error adding post:", error);
    return NextResponse.json({ error: "Failed to add post" }, { status: 500 });
  }
}

export async function PATCH(request: Request) {
  try {
    const body = await request.json();
    const { id, ...fields } = body;
    sqliteDb.updatePost(Number(id), fields);
    return NextResponse.json({ success: true });
  } catch (error) {
    console.error("Error updating post:", error);
    return NextResponse.json({ error: "Failed to update post" }, { status: 500 });
  }
}

export async function DELETE(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const id = searchParams.get("id");
    if (id) sqliteDb.deletePost(Number(id));
    return NextResponse.json({ success: true });
  } catch (error) {
    console.error("Error deleting post:", error);
    return NextResponse.json({ error: "Failed to delete post" }, { status: 500 });
  }
}
