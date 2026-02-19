import { NextResponse } from "next/server";
import { sqliteDb } from "@/lib/db";

// In-memory store for connected SSE clients
const clients = new Set<ReadableStreamDefaultController>();

// GET endpoint for SSE - clients subscribe to this
export async function GET() {
  const stream = new ReadableStream({
    start(controller) {
      clients.add(controller);
      
      const encoder = new TextEncoder();
      
      // Send initial connection message
      controller.enqueue(encoder.encode(`data: {"type":"connected"}\n\n`));
      
      // Keep connection alive with heartbeat
      const heartbeat = setInterval(() => {
        try {
          controller.enqueue(encoder.encode(`data: {"type":"heartbeat"}\n\n`));
        } catch {
          clearInterval(heartbeat);
          clients.delete(controller);
        }
      }, 25000);
    },
    cancel() {
      // Client disconnected - cleanup handled by the heartbeat try/catch
    },
  });

  return new NextResponse(stream, {
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache",
      "Connection": "keep-alive",
    },
  });
}

// Function to notify all connected clients
function notifyClients(eventType: string, data?: any) {
  const encoder = new TextEncoder();
  const message = `data: ${JSON.stringify({ type: eventType, ...data })}\n\n`;
  
  for (const client of clients) {
    try {
      client.enqueue(encoder.encode(message));
    } catch {
      clients.delete(client);
    }
  }
}

export { notifyClients };
