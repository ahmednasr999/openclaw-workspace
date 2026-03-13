"use client";

import { useState } from "react";
import { Shell } from "@/components/shell";
import { CardSkeleton } from "@/components/skeleton";

interface Job {
  id: string;
  company: string;
  role: string;
  location: string;
  appliedDate: string;
  stage: "CV Ready" | "Applied" | "Interview" | "Offer" | "Rejected";
  atsScore?: number;
  statusIndicator: string;
}

const stageConfig = {
  "CV Ready": {
    label: "CV Ready",
    icon: "📋",
    color: "text-purple-400 border-b-purple-700",
    bgColor: "bg-purple-900/5",
    badgeColor: "bg-purple-900/30 text-purple-300 border border-purple-800/40",
  },
  "Applied": {
    label: "Applied",
    icon: "✅",
    color: "text-emerald-400 border-b-emerald-700",
    bgColor: "bg-emerald-900/5",
    badgeColor: "bg-emerald-900/30 text-emerald-300 border border-emerald-800/40",
  },
  "Interview": {
    label: "Interview",
    icon: "📞",
    color: "text-blue-400 border-b-blue-700",
    bgColor: "bg-blue-900/5",
    badgeColor: "bg-blue-900/30 text-blue-300 border border-blue-800/40",
  },
  "Offer": {
    label: "Offer",
    icon: "🎉",
    color: "text-amber-400 border-b-amber-700",
    bgColor: "bg-amber-900/5",
    badgeColor: "bg-amber-900/30 text-amber-300 border border-amber-800/40",
  },
  "Rejected": {
    label: "Rejected",
    icon: "❌",
    color: "text-red-400 border-b-red-700",
    bgColor: "bg-red-900/5",
    badgeColor: "bg-red-900/30 text-red-300 border border-red-800/40",
  },
};

const stageOrder: (keyof typeof stageConfig)[] = [
  "CV Ready",
  "Applied",
  "Interview",
  "Offer",
  "Rejected",
];

function parseJobsFromMarkdown(): Job[] {
  const jobs: Job[] = [
    {
      id: "1",
      company: "Delphi Consulting",
      role: "Senior AI PM",
      location: "UAE",
      appliedDate: "2026-02-21",
      stage: "Interview",
      atsScore: 91,
      statusIndicator: "📞",
    },
    {
      id: "2",
      company: "Talabat",
      role: "CPTO",
      location: "Dubai, UAE",
      appliedDate: "2026-02-24",
      stage: "Applied",
      atsScore: 87,
      statusIndicator: "✅",
    },
    {
      id: "3",
      company: "AIQU",
      role: "Director of AI",
      location: "Dubai, UAE",
      appliedDate: "2026-02-24",
      stage: "Applied",
      atsScore: 82,
      statusIndicator: "✅",
    },
    {
      id: "4",
      company: "Nexus Consulting",
      role: "CEO",
      location: "Saudi Arabia",
      appliedDate: "2026-02-24",
      stage: "Applied",
      atsScore: 78,
      statusIndicator: "✅",
    },
    {
      id: "5",
      company: "eMagine Solutions",
      role: "VP Digital Projects",
      location: "Abu Dhabi, UAE",
      appliedDate: "2026-02-25",
      stage: "Applied",
      atsScore: 88,
      statusIndicator: "✅",
    },
    {
      id: "6",
      company: "Confidential",
      role: "Group IT Director",
      location: "Bahrain",
      appliedDate: "2026-02-26",
      stage: "Applied",
      atsScore: 92,
      statusIndicator: "✅",
    },
    {
      id: "7",
      company: "Buro Happold",
      role: "Director Program Advisory",
      location: "Riyadh, KSA",
      appliedDate: "2026-02-27",
      stage: "Applied",
      atsScore: 88,
      statusIndicator: "✅",
    },
    {
      id: "8",
      company: "Inception (G42)",
      role: "Director Delivery",
      location: "Abu Dhabi, UAE",
      appliedDate: "2026-02-27",
      stage: "Applied",
      atsScore: 91,
      statusIndicator: "✅",
    },
    {
      id: "9",
      company: "Dubai Holding",
      role: "Director DT & IT",
      location: "Dubai, UAE",
      appliedDate: "2026-02-27",
      stage: "Applied",
      atsScore: 92,
      statusIndicator: "✅",
    },
    {
      id: "10",
      company: "FAB",
      role: "VP Technology & Data",
      location: "Abu Dhabi, UAE",
      appliedDate: "2026-02-27",
      stage: "Applied",
      atsScore: 87,
      statusIndicator: "✅",
    },
    {
      id: "11",
      company: "Al-Gihaz Holdings",
      role: "Chief Operating Officer",
      location: "Dammam, KSA",
      appliedDate: "2026-02-27",
      stage: "Applied",
      atsScore: 91,
      statusIndicator: "✅",
    },
    {
      id: "12",
      company: "Confidential",
      role: "Head of Artificial Intelligence",
      location: "Dubai, UAE",
      appliedDate: "2026-02-27",
      stage: "Applied",
      atsScore: 91,
      statusIndicator: "✅",
    },
    {
      id: "13",
      company: "Apex Group Ltd",
      role: "Head of AI Innovation",
      location: "Abu Dhabi, UAE",
      appliedDate: "2026-02-27",
      stage: "Applied",
      atsScore: 88,
      statusIndicator: "✅",
    },
    {
      id: "14",
      company: "du",
      role: "Director IT Strategy",
      location: "UAE",
      appliedDate: "2026-02-27",
      stage: "Applied",
      atsScore: 88,
      statusIndicator: "✅",
    },
    {
      id: "15",
      company: "Windmills Group",
      role: "CTO",
      location: "Dubai, UAE",
      appliedDate: "2026-02-27",
      stage: "Applied",
      atsScore: 91,
      statusIndicator: "✅",
    },
    {
      id: "16",
      company: "Hays (client)",
      role: "Head of AI",
      location: "Dubai, UAE",
      appliedDate: "2026-02-27",
      stage: "Applied",
      atsScore: 91,
      statusIndicator: "✅",
    },
    {
      id: "17",
      company: "SmartChoice GCC",
      role: "Head of Tech & Transformation",
      location: "Abu Dhabi, UAE",
      appliedDate: "2026-02-27",
      stage: "Applied",
      atsScore: 91,
      statusIndicator: "✅",
    },
    {
      id: "18",
      company: "Codesearch AI",
      role: "Head of Data Science & AI",
      location: "Dubai, UAE",
      appliedDate: "2026-02-27",
      stage: "Applied",
      atsScore: 87,
      statusIndicator: "✅",
    },
    {
      id: "19",
      company: "Halian (Federal)",
      role: "Director PMO, Federal Tech",
      location: "Abu Dhabi, UAE",
      appliedDate: "2026-02-27",
      stage: "Applied",
      atsScore: 91,
      statusIndicator: "✅",
    },
    {
      id: "20",
      company: "Confidential (AI Co.)",
      role: "COO",
      location: "Dammam, KSA",
      appliedDate: "2026-02-27",
      stage: "Applied",
      atsScore: undefined,
      statusIndicator: "✅",
    },
    {
      id: "21",
      company: "Confidential Careers",
      role: "CEO, Giga-Projects KSA",
      location: "Riyadh, KSA",
      appliedDate: "2026-02-27",
      stage: "Applied",
      atsScore: 89,
      statusIndicator: "✅",
    },
    {
      id: "22",
      company: "Proximie",
      role: "Transformation Lead UAE",
      location: "Dubai, UAE",
      appliedDate: "2026-02-27",
      stage: "Applied",
      atsScore: 88,
      statusIndicator: "✅",
    },
    {
      id: "23",
      company: "Renard International",
      role: "Director Tech & Innovation",
      location: "Doha, Qatar",
      appliedDate: "2026-02-27",
      stage: "Applied",
      atsScore: 88,
      statusIndicator: "✅",
    },
    {
      id: "24",
      company: "Confidential",
      role: "Director Enterprise PMO",
      location: "Dubai, UAE",
      appliedDate: "2026-02-27",
      stage: "Applied",
      atsScore: 88,
      statusIndicator: "✅",
    },
    {
      id: "25",
      company: "NXS Tech",
      role: "Director of AI",
      location: "Dubai, UAE",
      appliedDate: "2026-02-27",
      stage: "Applied",
      atsScore: 91,
      statusIndicator: "✅",
    },
    {
      id: "26",
      company: "Auxo Talent",
      role: "VP of Artificial Intelligence",
      location: "Dubai, UAE",
      appliedDate: "2026-02-27",
      stage: "Applied",
      atsScore: 91,
      statusIndicator: "✅",
    },
    {
      id: "27",
      company: "UnlockLand",
      role: "VP Global Operations",
      location: "Saudi Arabia",
      appliedDate: "2026-02-27",
      stage: "Applied",
      atsScore: 91,
      statusIndicator: "✅",
    },
    {
      id: "28",
      company: "Cooper Fitch",
      role: "Executive Director, Strategic Initiatives",
      location: "Riyadh, KSA",
      appliedDate: "2026-02-27",
      stage: "Applied",
      atsScore: 91,
      statusIndicator: "✅",
    },
    {
      id: "29",
      company: "One Executive",
      role: "Director, Organisational Development",
      location: "Dubai, UAE",
      appliedDate: "2026-02-27",
      stage: "Applied",
      atsScore: 88,
      statusIndicator: "✅",
    },
    {
      id: "30",
      company: "Sky News Arabia",
      role: "Head of AI Transformation & Innovation",
      location: "Abu Dhabi, UAE",
      appliedDate: "2026-02-27",
      stage: "Applied",
      atsScore: 87,
      statusIndicator: "✅",
    },
    {
      id: "31",
      company: "Dubai Health",
      role: "Head of Technology Transfer Office",
      location: "Dubai, UAE",
      appliedDate: "2026-02-27",
      stage: "Applied",
      atsScore: 70,
      statusIndicator: "✅",
    },
    {
      id: "32",
      company: "Cygnify",
      role: "Principal, Digital Delivery & Transformation",
      location: "Dubai, UAE",
      appliedDate: "2026-02-27",
      stage: "Applied",
      atsScore: 89,
      statusIndicator: "✅",
    },
    {
      id: "33",
      company: "Leru Partners",
      role: "Head of Solutions & Delivery (AI)",
      location: "Dubai, UAE",
      appliedDate: "2026-02-28",
      stage: "Applied",
      atsScore: 89,
      statusIndicator: "✅",
    },
    {
      id: "34",
      company: "Oracle",
      role: "Director Client Engagement / Digital Transformation",
      location: "Riyadh, KSA",
      appliedDate: "2026-02-28",
      stage: "Applied",
      atsScore: 67,
      statusIndicator: "✅",
    },
    {
      id: "35",
      company: "Teleperformance (TP)",
      role: "VP AI Delivery",
      location: "Cairo, Egypt",
      appliedDate: "2026-02-28",
      stage: "Applied",
      atsScore: 75,
      statusIndicator: "✅",
    },
    {
      id: "36",
      company: "King Salman International Airport",
      role: "VP Strategy and Performance Management",
      location: "Riyadh, KSA",
      appliedDate: "2026-02-28",
      stage: "Applied",
      atsScore: 88,
      statusIndicator: "✅",
    },
    {
      id: "37",
      company: "Faithful Executive (Client)",
      role: "AI Strategy & Readiness Expert",
      location: "GCC (KSA/UAE)",
      appliedDate: "2026-03-01",
      stage: "Applied",
      atsScore: 91,
      statusIndicator: "✅",
    },
    {
      id: "38",
      company: "Dubai Holding",
      role: "Senior Manager, Strategy & Execution (B2B)",
      location: "Dubai, UAE",
      appliedDate: "2026-03-01",
      stage: "Applied",
      atsScore: 89,
      statusIndicator: "✅",
    },
    {
      id: "39",
      company: "Legend Holding Group",
      role: "IT Director",
      location: "Dubai, UAE",
      appliedDate: "2026-03-01",
      stage: "Applied",
      atsScore: 85,
      statusIndicator: "✅",
    },
    {
      id: "40",
      company: "EATX",
      role: "Head of IT",
      location: "Dubai, UAE",
      appliedDate: "2026-03-01",
      stage: "Applied",
      atsScore: 88,
      statusIndicator: "✅",
    },
    {
      id: "41",
      company: "Starlink Qatar",
      role: "Products Portfolio Lead",
      location: "Doha, Qatar",
      appliedDate: "2026-03-01",
      stage: "Applied",
      atsScore: 90,
      statusIndicator: "✅",
    },
    {
      id: "42",
      company: "Agay Barho (Saudi Foundation)",
      role: "Strategy Director",
      location: "Riyadh, KSA",
      appliedDate: "2026-03-01",
      stage: "Applied",
      atsScore: 87,
      statusIndicator: "✅",
    },
    {
      id: "43",
      company: "RapidData Technologies",
      role: "Strategy & KPI Expert",
      location: "Dubai, UAE",
      appliedDate: "2026-03-01",
      stage: "Applied",
      atsScore: 88,
      statusIndicator: "✅",
    },
    {
      id: "44",
      company: "Salt",
      role: "Senior Program Manager",
      location: "Abu Dhabi, UAE",
      appliedDate: "2026-03-01",
      stage: "Applied",
      atsScore: 91,
      statusIndicator: "✅",
    },
    {
      id: "45",
      company: "Confidential (Michael Page)",
      role: "VP, AI & Technology",
      location: "International / UAE",
      appliedDate: "2026-03-02",
      stage: "Applied",
      atsScore: 88,
      statusIndicator: "✅",
    },
    {
      id: "46",
      company: "RAKBANK",
      role: "Vice President, AI Platform Owner",
      location: "Dubai, UAE",
      appliedDate: "2026-03-03",
      stage: "Applied",
      atsScore: 89,
      statusIndicator: "✅",
    },
  ];

  return jobs;
}

function JobCard({ job }: { job: Job }) {
  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
  };

  return (
    <div className="glass rounded-[10px] p-4 space-y-3 min-w-[280px] hover:bg-opacity-100 transition-all">
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          <p className="text-xs text-[#4B6A9B] font-medium uppercase tracking-wider">
            {job.location}
          </p>
          <h3 className="font-semibold text-sm text-[#e2e8f0] mt-1 truncate">
            {job.company}
          </h3>
          <p className="text-xs text-[#6B8AAE] mt-1 line-clamp-2">
            {job.role}
          </p>
        </div>
        {job.atsScore && (
          <div className="flex flex-col items-center bg-blue-900/20 rounded px-2 py-1 border border-blue-800/40">
            <span className="text-xs font-bold text-blue-300">{job.atsScore}%</span>
            <span className="text-[10px] text-blue-400">ATS</span>
          </div>
        )}
      </div>

      <div className="flex items-center justify-between pt-2 border-t border-[#1E2D45]">
        <div className="flex items-center gap-2">
          <span className="text-xs bg-blue-900/20 text-blue-300 px-2 py-1 rounded border border-blue-800/40">
            {formatDate(job.appliedDate)}
          </span>
        </div>
      </div>
    </div>
  );
}

function KanbanColumn({
  stage,
  jobs,
  loading,
}: {
  stage: keyof typeof stageConfig;
  jobs: Job[];
  loading: boolean;
}) {
  const config = stageConfig[stage];
  const stageJobs = jobs.filter((job) => job.stage === stage);

  return (
    <div className={`flex-none w-full md:w-[350px] ${config.bgColor} rounded-lg p-4`}>
      <div
        className={`pb-3 mb-4 border-b-2 ${config.color} flex items-center justify-between`}
      >
        <div className="flex items-center gap-2">
          <span className="text-lg">{config.icon}</span>
          <h2 className="font-semibold text-sm">{config.label}</h2>
        </div>
        <span className={`text-xs font-semibold px-2 py-1 rounded ${config.badgeColor}`}>
          {stageJobs.length}
        </span>
      </div>

      {loading ? (
        <div className="space-y-3">
          {Array.from({ length: 2 }).map((_, i) => (
            <CardSkeleton key={i} />
          ))}
        </div>
      ) : stageJobs.length === 0 ? (
        <p className="text-sm text-[#4B6A9B] text-center py-8">
          No jobs in this stage
        </p>
      ) : (
        <div className="space-y-3">
          {stageJobs.map((job) => (
            <JobCard key={job.id} job={job} />
          ))}
        </div>
      )}
    </div>
  );
}

export default function PipelinePage() {
  const jobs = parseJobsFromMarkdown();
  const loading = false;

  const metrics = {
    total: jobs.length,
    applied: jobs.filter((j) => j.stage === "Applied").length,
    interview: jobs.filter((j) => j.stage === "Interview").length,
    avgAts: Math.round(
      jobs
        .filter((j) => j.atsScore)
        .reduce((sum, j) => sum + (j.atsScore || 0), 0) /
        Math.max(jobs.filter((j) => j.atsScore).length, 1)
    ),
  };

  return (
    <Shell
      title="Pipeline"
      description="Job search kanban board with ATS scores and timeline tracking."
    >
      <div className="space-y-6">
        {/* Metrics */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div className="glass rounded-[10px] p-4">
            <p className="text-xs text-[#4B6A9B] font-medium uppercase">
              Total Jobs
            </p>
            <p className="text-2xl font-bold text-gradient-blue mt-1">
              {metrics.total}
            </p>
          </div>
          <div className="glass rounded-[10px] p-4">
            <p className="text-xs text-[#4B6A9B] font-medium uppercase">
              Applied
            </p>
            <p className="text-2xl font-bold text-emerald-400 mt-1">
              {metrics.applied}
            </p>
          </div>
          <div className="glass rounded-[10px] p-4">
            <p className="text-xs text-[#4B6A9B] font-medium uppercase">
              Interview
            </p>
            <p className="text-2xl font-bold text-blue-400 mt-1">
              {metrics.interview}
            </p>
          </div>
          <div className="glass rounded-[10px] p-4">
            <p className="text-xs text-[#4B6A9B] font-medium uppercase">
              Avg ATS
            </p>
            <p className="text-2xl font-bold text-blue-300 mt-1">
              {metrics.avgAts}%
            </p>
          </div>
        </div>

        {/* Kanban Board */}
        <div className="overflow-x-auto pb-4">
          <div className="flex gap-4 min-w-max md:min-w-0">
            {stageOrder.map((stage) => (
              <KanbanColumn
                key={stage}
                stage={stage}
                jobs={jobs}
                loading={loading}
              />
            ))}
          </div>
        </div>
      </div>
    </Shell>
  );
}
