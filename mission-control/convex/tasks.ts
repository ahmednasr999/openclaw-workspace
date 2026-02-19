import { query, mutation } from "./_generated";
import { v } from "convex/values";

export const getTasks = query({
  args: {},
  handler: async (ctx) => {
    const tasks = await ctx.db.query("tasks").collect();
    return tasks;
  },
});

export const addTask = mutation({
  args: {
    title: v.string(),
    description: v.optional(v.string()),
    assignee: v.string(),
    status: v.string(),
    priority: v.string(),
    category: v.string(),
    dueDate: v.optional(v.string()),
    relatedTo: v.optional(v.array(v.string())),
    createdAt: v.string(),
  },
  handler: async (ctx, args) => {
    const taskId = await ctx.db.insert("tasks", args);
    return taskId;
  },
});

export const updateTaskStatus = mutation({
  args: {
    id: v.id("tasks"),
    status: v.string(),
    completedDate: v.optional(v.string()),
  },
  handler: async (ctx, args) => {
    await ctx.db.patch(args.id, {
      status: args.status,
      completedDate: args.completedDate,
    });
  },
});

export const deleteTask = mutation({
  args: { id: v.id("tasks") },
  handler: async (ctx, args) => {
    await ctx.db.delete(args.id);
  },
});
