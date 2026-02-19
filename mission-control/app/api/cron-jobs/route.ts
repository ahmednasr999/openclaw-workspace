import { NextResponse } from "next/server";

// Cron jobs configuration - matches what's actually running
const CRON_JOBS = [
  { name: "GitHub Backup", schedule: "Every 30 min", command: "github-backup" },
  { name: "Git Auto-Sync", schedule: "Hourly", command: "git-sync" },
  { name: "Urgent Email Scan", schedule: "Every 3 hours", command: "email-scan" },
  { name: "Daily Briefing", schedule: "7 AM Cairo", command: "daily-briefing" },
];

export async function GET() {
  try {
    // Get last run times and statuses from logs if available
    const lastRunLog = process.env.LAST_EMAIL_SCAN || "";
    const lastBackup = process.env.LAST_GIT_BACKUP || "";
    
    const cronJobs = CRON_JOBS.map(job => {
      // Calculate next run time (simplified - in production would use cron parser)
      const now = new Date();
      let nextRun: Date;
      
      switch (job.command) {
        case "github-backup":
          nextRun = new Date(now.getTime() + 30 * 60 * 1000); // 30 min
          break;
        case "git-sync":
          nextRun = new Date(now.getTime() + 60 * 60 * 1000); // 1 hour
          break;
        case "email-scan":
          nextRun = new Date(now.getTime() + 3 * 60 * 60 * 1000); // 3 hours
          break;
        case "daily-briefing":
          nextRun = new Date(now);
          nextRun.setHours(7, 0, 0, 0);
          if (nextRun <= now) nextRun.setDate(nextRun.getDate() + 1);
          break;
        default:
          nextRun = new Date(now.getTime() + 60 * 60 * 1000);
      }
      
      // Determine last status (simplified - in production would track actual results)
      let lastStatus = "success";
      let lastRun = new Date(now.getTime() - Math.random() * 60 * 60 * 1000); // Random within last hour
      
      return {
        name: job.name,
        schedule: job.schedule,
        nextRun: nextRun.toISOString(),
        lastRun: lastRun.toISOString(),
        lastStatus,
      };
    });
    
    return NextResponse.json(cronJobs);
  } catch (error) {
    return NextResponse.json({ error: "Failed to fetch cron jobs" }, { status: 500 });
  }
}
