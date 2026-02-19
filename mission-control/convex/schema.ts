import { defineSchema, defineTable } from "convex/server";

export default defineSchema({
  tasks: defineTable({
    title: v.string(),
    description: v.optional(v.string()),
    assignee: v.string(), // "Ahmed", "OpenClaw", "Both"
    status: v.string(), // "Inbox", "My Tasks", "OpenClaw Tasks", "In Progress", "Completed"
    priority: v.string(), // "High", "Medium", "Low"
    category: v.string(), // "Job Search", "Content", "Networking", "Applications", "Interviews"
    dueDate: v.optional(v.string()),
    completedDate: v.optional(v.string()),
    relatedTo: v.optional(v.array(v.string())), // Links to jobs, contacts, content
    createdAt: v.string(),
  }),
});
