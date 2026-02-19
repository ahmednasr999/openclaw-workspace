"use client";

import { useState, useEffect, useCallback, useMemo } from "react";
import { Icon } from "./Icon";

interface AgentDef {
  id: string;
  name: string;
  role: string;
  description: string;
  icon: string;
  type: "core" | "specialist";
  model: string;
  persistent: boolean;
  capabilities: string[];
  qaChecks?: string[];
}

interface AgentRun {
  sessionKey: string;
  label?: string;
  status: string;
  updatedAt: string;
  task?: string;
}

interface TeamStats {
  totalRuns: number;
  activeNow: number;
  todayRuns: number;
}

const AGENT_DEFINITIONS: AgentDef[] = [
  {
    id: "nasr",
    name: "NASR",
    role: "Orchestrator & Chief of Staff",
    description: "Routes all tasks, coordinates agents, daily briefs, strategic synthesis. The brain of the operation.",
    icon: "🎯",
    type: "core",
    model: "MiniMax-M2.1 (default) / Opus (complex)",
    persistent: true,
    capabilities: ["Task routing", "Agent coordination", "Daily briefings", "Strategic analysis", "Memory management"],
  },
  {
    id: "qa",
    name: "QA Agent",
    role: "Quality Assurance",
    description: "Verifies all agent outputs before delivery. Checks ATS compliance for CVs, tone for content, accuracy for research. Max 2 retries.",
    icon: "🛡️",
    type: "core",
    model: "Sonnet 4",
    persistent: true,
    capabilities: ["Output validation", "ATS compliance check", "Tone analysis", "Fact checking", "Retry management"],
    qaChecks: ["CV: ATS rules, no fabricated data, keyword match", "Content: tone, CTA, length, formatting", "Research: sources cited, relevance, completeness", "Code: builds without errors, matches requirements"],
  },
  {
    id: "scheduler",
    name: "Scheduler",
    role: "Automation & Scheduling",
    description: "Manages cron jobs, reminders, follow-ups, and proactive monitoring. Runs 24/7.",
    icon: "⏰",
    type: "core",
    model: "MiniMax-M2.1",
    persistent: true,
    capabilities: ["Cron management", "Reminders", "Email monitoring", "Git backups", "Usage alerts"],
  },
  {
    id: "researcher",
    name: "Research Agent",
    role: "Intelligence & Analysis",
    description: "Web research, company analysis, market intel, competitive research. Spawns per task, terminates when done.",
    icon: "🔍",
    type: "specialist",
    model: "MiniMax-M2.1",
    persistent: false,
    capabilities: ["Web search", "Company research", "News analysis", "Market intelligence", "Competitive analysis"],
  },
  {
    id: "writer",
    name: "Writer Agent",
    role: "Content & Copy",
    description: "LinkedIn posts, emails, thought leadership, marketing copy. Follows brand voice guidelines.",
    icon: "✍️",
    type: "specialist",
    model: "Sonnet 4",
    persistent: false,
    capabilities: ["LinkedIn posts", "Email drafting", "Thought leadership", "Marketing copy", "Brand voice"],
  },
  {
    id: "cv-specialist",
    name: "CV Specialist",
    role: "CV & Applications",
    description: "Tailored CVs, cover letters, ATS optimization. Uses master CV data. Follows strict ATS rules.",
    icon: "📄",
    type: "specialist",
    model: "Opus 4.5",
    persistent: false,
    capabilities: ["Tailored CVs", "ATS optimization", "Cover letters", "Keyword matching", "Format compliance"],
  },
  {
    id: "coder",
    name: "Coder Agent",
    role: "Development & Automation",
    description: "Mission Control features, automation scripts, integrations, bug fixes.",
    icon: "💻",
    type: "specialist",
    model: "Sonnet 4",
    persistent: false,
    capabilities: ["Feature development", "Bug fixes", "API integrations", "Automation scripts", "Code review"],
  },
];

const TASK_FLOW = [
  { step: 1, label: "Task Created", column: "Inbox", description: "You or NASR creates a task" },
  { step: 2, label: "Assigned", column: "In Progress", description: "NASR routes to the right agent" },
  { step: 3, label: "QA Check", column: "QA", description: "QA Agent verifies output quality" },
  { step: 4, label: "Your Review", column: "Review", description: "Content/CVs need your approval" },
  { step: 5, label: "Done", column: "Completed", description: "Routine tasks auto-complete after QA" },
];

export function TeamBoard() {
  const [agents, setAgents] = useState<AgentDef[]>(AGENT_DEFINITIONS);
  const [selectedAgent, setSelectedAgent] = useState<AgentDef | null>(null);
  const [activeRuns, setActiveRuns] = useState<AgentRun[]>([]);
  const [viewMode, setViewMode] = useState<"org" | "flow">("org");
  const [loading, setLoading] = useState(false);

  const fetchAgentConfig = useCallback(async () => {
    try {
      const res = await fetch("/api/agents/config");
      if (res.ok) {
        const data = await res.json();
        if (Array.isArray(data) && data.length > 0) setAgents(data);
      }
    } catch {
      // Fall back to hardcoded definitions
    }
  }, []);

  const fetchActiveRuns = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch("/api/agents/status");
      if (res.ok) {
        const data = await res.json();
        setActiveRuns(data.runs || []);
      }
    } catch {
      // API may not exist yet
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAgentConfig();
    fetchActiveRuns();
    const interval = setInterval(fetchActiveRuns, 15000);
    return () => clearInterval(interval);
  }, [fetchAgentConfig, fetchActiveRuns]);

  const coreAgents = agents.filter((a) => a.type === "core");
  const specialists = agents.filter((a) => a.type === "specialist");

  const stats: TeamStats = useMemo(() => ({
    totalRuns: activeRuns.length,
    activeNow: activeRuns.filter((r) => r.status === "running").length,
    todayRuns: activeRuns.length,
  }), [activeRuns]);

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-[rgba(255,255,255,0.06)]">
        <div>
          <h1 className="text-xl font-bold text-white">Agent Team</h1>
          <p className="text-xs text-gray-500 mt-1">
            {coreAgents.length} core agents - {specialists.length} specialists - {stats.activeNow > 0 ? <span className="text-green-400">{stats.activeNow} active now</span> : "All idle"}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex gap-1 bg-[rgba(255,255,255,0.03)] rounded-lg p-1 border border-[rgba(255,255,255,0.08)]">
            <button
              onClick={() => setViewMode("org")}
              className={`px-3 py-1.5 rounded text-xs font-medium transition-all ${viewMode === "org" ? "bg-[rgba(124,92,252,0.15)] text-[#a78bfa]" : "text-gray-500 hover:text-white"}`}
            >
              Org Chart
            </button>
            <button
              onClick={() => setViewMode("flow")}
              className={`px-3 py-1.5 rounded text-xs font-medium transition-all ${viewMode === "flow" ? "bg-[rgba(124,92,252,0.15)] text-[#a78bfa]" : "text-gray-500 hover:text-white"}`}
            >
              Task Flow
            </button>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto p-6">
        {viewMode === "org" ? (
          <OrgChartView
            coreAgents={coreAgents}
            specialists={specialists}
            activeRuns={activeRuns}
            onSelectAgent={setSelectedAgent}
          />
        ) : (
          <TaskFlowView />
        )}
      </div>

      {/* Agent Detail Modal */}
      {selectedAgent && (
        <AgentDetailModal
          agent={selectedAgent}
          runs={activeRuns.filter((r) => r.label?.toLowerCase().includes(selectedAgent.id))}
          onClose={() => setSelectedAgent(null)}
        />
      )}
    </div>
  );
}

// Org Chart View
function OrgChartView({ coreAgents, specialists, activeRuns, onSelectAgent }: {
  coreAgents: AgentDef[];
  specialists: AgentDef[];
  activeRuns: AgentRun[];
  onSelectAgent: (a: AgentDef) => void;
}) {
  return (
    <div className="max-w-5xl mx-auto">
      {/* Ahmed at the top */}
      <div className="flex justify-center mb-2">
        <div className="px-6 py-4 rounded-xl bg-[rgba(124,92,252,0.08)] border border-indigo-500/20 text-center">
          <div className="text-2xl mb-1">👤</div>
          <div className="text-sm font-semibold text-white">Ahmed Nasr</div>
          <div className="text-[10px] text-indigo-400">Executive Director</div>
          <div className="text-[10px] text-gray-500 mt-1">Decisions - Approvals - Strategy</div>
        </div>
      </div>

      {/* Connector line */}
      <div className="flex justify-center mb-2">
        <div className="w-px h-8 bg-[rgba(255,255,255,0.1)]" />
      </div>

      {/* Core Agents */}
      <div className="mb-2">
        <div className="text-[10px] text-gray-500 uppercase tracking-wider mb-3 text-center">Core Team - Always Running</div>
        <div className="flex justify-center gap-4 flex-wrap">
          {coreAgents.map((agent) => (
            <AgentCard key={agent.id} agent={agent} isActive={false} onSelect={onSelectAgent} />
          ))}
        </div>
      </div>

      {/* Connector line */}
      <div className="flex justify-center mb-2">
        <div className="w-px h-8 bg-[rgba(255,255,255,0.06)]" />
      </div>

      {/* Specialists */}
      <div>
        <div className="text-[10px] text-gray-500 uppercase tracking-wider mb-3 text-center">Specialists - Spawn Per Task</div>
        <div className="flex justify-center gap-4 flex-wrap">
          {specialists.map((agent) => (
            <AgentCard key={agent.id} agent={agent} isActive={false} onSelect={onSelectAgent} />
          ))}
        </div>
      </div>

      {/* Rules summary */}
      <div className="mt-10 grid grid-cols-3 gap-4 max-w-3xl mx-auto">
        <RuleCard
          title="Routing"
          icon="🔀"
          rules={["NASR routes all tasks", "One responsibility per agent", "Max 2 retries on failure"]}
        />
        <RuleCard
          title="Quality"
          icon="🛡️"
          rules={["QA checks every output", "Content/CVs need Ahmed's review", "Routine auto-completes after QA"]}
        />
        <RuleCard
          title="Efficiency"
          icon="⚡"
          rules={["Specialists terminate when done", "Promote if 10+ tasks/day", "Cheapest model that works"]}
        />
      </div>
    </div>
  );
}

// Task Flow View
function TaskFlowView() {
  return (
    <div className="max-w-4xl mx-auto">
      <div className="text-center mb-8">
        <h2 className="text-base font-semibold text-white mb-2">How Tasks Flow Through the Team</h2>
        <p className="text-xs text-gray-500">Every task follows this pipeline. QA catches issues before they reach you.</p>
      </div>

      <div className="space-y-0">
        {TASK_FLOW.map((step, i) => (
          <div key={step.step} className="flex items-start gap-4">
            {/* Step number */}
            <div className="flex flex-col items-center">
              <div className={`w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold ${
                step.step === 3 ? "bg-amber-500/15 text-amber-400 border border-amber-500/30" :
                step.step === 5 ? "bg-green-500/15 text-green-400 border border-green-500/30" :
                "bg-[rgba(124,92,252,0.15)] text-indigo-400 border border-indigo-500/30"
              }`}>
                {step.step}
              </div>
              {i < TASK_FLOW.length - 1 && <div className="w-px h-12 bg-[rgba(255,255,255,0.06)]" />}
            </div>

            {/* Content */}
            <div className="flex-1 pb-8">
              <div className="flex items-center gap-3 mb-1">
                <span className="text-sm font-medium text-white">{step.label}</span>
                <span className="text-[10px] px-2 py-0.5 rounded bg-[rgba(255,255,255,0.05)] text-gray-500">
                  → {step.column}
                </span>
              </div>
              <p className="text-xs text-gray-500">{step.description}</p>

              {/* Special detail for QA step */}
              {step.step === 3 && (
                <div className="mt-3 p-3 rounded-lg bg-[rgba(245,158,11,0.05)] border border-amber-500/15">
                  <div className="text-[10px] text-amber-400 font-medium mb-2">QA Checks by Task Type:</div>
                  <div className="grid grid-cols-2 gap-2">
                    <div className="text-[10px] text-gray-400"><span className="text-amber-400">CV:</span> ATS rules, no fabricated data, keywords</div>
                    <div className="text-[10px] text-gray-400"><span className="text-amber-400">Content:</span> Tone, CTA, length, formatting</div>
                    <div className="text-[10px] text-gray-400"><span className="text-amber-400">Research:</span> Sources, relevance, completeness</div>
                    <div className="text-[10px] text-gray-400"><span className="text-amber-400">Code:</span> Builds, matches requirements</div>
                  </div>
                </div>
              )}

              {/* Auto-complete note */}
              {step.step === 4 && (
                <div className="mt-2 text-[10px] text-gray-600">
                  ⚡ Routine tasks (backups, syncs, research) skip this step and auto-complete after QA pass
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Failure handling */}
      <div className="mt-6 p-4 rounded-xl bg-[rgba(248,113,113,0.05)] border border-red-500/15">
        <div className="text-sm font-medium text-white mb-2">⚠️ When Things Fail</div>
        <div className="grid grid-cols-3 gap-4 text-[11px] text-gray-400">
          <div>
            <span className="text-red-400 font-medium">QA Fail →</span> Back to specialist with feedback (max 2 retries)
          </div>
          <div>
            <span className="text-red-400 font-medium">Agent Timeout →</span> Task flagged, NASR notifies Ahmed
          </div>
          <div>
            <span className="text-red-400 font-medium">2 Retries Exhausted →</span> Escalate to Ahmed for manual handling
          </div>
        </div>
      </div>
    </div>
  );
}

// Agent Card
function AgentCard({ agent, isActive, onSelect }: {
  agent: AgentDef;
  isActive: boolean;
  onSelect: (a: AgentDef) => void;
}) {
  return (
    <button
      onClick={() => onSelect(agent)}
      className={`w-52 p-4 rounded-xl border text-left transition-all hover:border-[rgba(255,255,255,0.15)] hover:bg-[rgba(255,255,255,0.04)] ${
        agent.type === "core"
          ? "bg-[rgba(255,255,255,0.02)] border-[rgba(255,255,255,0.08)]"
          : "bg-[rgba(255,255,255,0.01)] border-[rgba(255,255,255,0.05)]"
      }`}
    >
      <div className="flex items-center justify-between mb-2">
        <span className="text-2xl">{agent.icon}</span>
        <div className="flex items-center gap-1.5">
          {agent.persistent && (
            <span className="text-[8px] px-1.5 py-0.5 rounded bg-green-500/10 text-green-400 border border-green-500/20">ALWAYS ON</span>
          )}
          {isActive && (
            <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
          )}
        </div>
      </div>
      <div className="text-sm font-medium text-white mb-0.5">{agent.name}</div>
      <div className="text-[10px] text-indigo-400 mb-2">{agent.role}</div>
      <div className="text-[10px] text-gray-500 line-clamp-2 mb-3">{agent.description}</div>
      <div className="text-[9px] text-gray-600">
        Model: {agent.model}
      </div>
    </button>
  );
}

// Rule Card
function RuleCard({ title, icon, rules }: { title: string; icon: string; rules: string[] }) {
  return (
    <div className="p-4 rounded-xl bg-[rgba(255,255,255,0.02)] border border-[rgba(255,255,255,0.06)]">
      <div className="flex items-center gap-2 mb-3">
        <span className="text-lg">{icon}</span>
        <span className="text-xs font-semibold text-white">{title}</span>
      </div>
      <div className="space-y-2">
        {rules.map((rule, i) => (
          <div key={i} className="flex items-start gap-2">
            <div className="w-1 h-1 rounded-full bg-gray-600 mt-1.5 flex-shrink-0" />
            <span className="text-[10px] text-gray-400">{rule}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

// Agent Detail Modal
function AgentDetailModal({ agent, runs, onClose }: {
  agent: AgentDef;
  runs: AgentRun[];
  onClose: () => void;
}) {
  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4" onClick={onClose}>
      <div className="bg-[#12121a] border border-[rgba(255,255,255,0.1)] rounded-xl w-full max-w-lg max-h-[80vh] overflow-hidden flex flex-col" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="p-6 border-b border-[rgba(255,255,255,0.06)]">
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-4">
              <div className="w-14 h-14 rounded-xl bg-[rgba(124,92,252,0.1)] border border-indigo-500/20 flex items-center justify-center text-2xl">
                {agent.icon}
              </div>
              <div>
                <h2 className="text-lg font-semibold text-white">{agent.name}</h2>
                <div className="text-xs text-indigo-400">{agent.role}</div>
                <div className="flex items-center gap-2 mt-1">
                  <span className={`text-[9px] px-1.5 py-0.5 rounded ${
                    agent.persistent ? "bg-green-500/10 text-green-400 border border-green-500/20" : "bg-gray-500/10 text-gray-400 border border-gray-500/20"
                  }`}>
                    {agent.persistent ? "Persistent" : "Spawns per task"}
                  </span>
                  <span className="text-[9px] px-1.5 py-0.5 rounded bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                    {agent.type}
                  </span>
                </div>
              </div>
            </div>
            <button onClick={onClose} className="text-gray-500 hover:text-white">
              <Icon name="close" size={20} />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Description */}
          <div>
            <div className="text-[10px] text-gray-500 uppercase tracking-wider mb-2">About</div>
            <p className="text-sm text-gray-300">{agent.description}</p>
          </div>

          {/* Model */}
          <div>
            <div className="text-[10px] text-gray-500 uppercase tracking-wider mb-2">Model</div>
            <p className="text-sm text-gray-300">{agent.model}</p>
          </div>

          {/* Capabilities */}
          <div>
            <div className="text-[10px] text-gray-500 uppercase tracking-wider mb-2">Capabilities</div>
            <div className="flex flex-wrap gap-2">
              {agent.capabilities.map((cap) => (
                <span key={cap} className="text-[10px] px-2.5 py-1 rounded-lg bg-[rgba(124,92,252,0.08)] text-indigo-400 border border-indigo-500/15">
                  {cap}
                </span>
              ))}
            </div>
          </div>

          {/* QA Checks (for QA agent) */}
          {agent.qaChecks && (
            <div>
              <div className="text-[10px] text-gray-500 uppercase tracking-wider mb-2">Quality Checks</div>
              <div className="space-y-2">
                {agent.qaChecks.map((check, i) => (
                  <div key={i} className="flex items-start gap-2 text-xs text-gray-400">
                    <span className="text-amber-400 mt-0.5">✓</span>
                    <span>{check}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Recent runs */}
          <div>
            <div className="text-[10px] text-gray-500 uppercase tracking-wider mb-2">Recent Activity</div>
            {runs.length === 0 ? (
              <p className="text-xs text-gray-600">No recent runs</p>
            ) : (
              <div className="space-y-2">
                {runs.map((run) => (
                  <div key={run.sessionKey} className="flex items-center gap-3 p-2 rounded-lg bg-[rgba(255,255,255,0.02)] border border-[rgba(255,255,255,0.04)]">
                    <div className={`w-2 h-2 rounded-full ${run.status === "running" ? "bg-green-500 animate-pulse" : "bg-gray-500"}`} />
                    <span className="text-xs text-gray-300 flex-1 truncate">{run.task || run.label || run.sessionKey}</span>
                    <span className="text-[10px] text-gray-600">{new Date(run.updatedAt).toLocaleTimeString("en-US", { timeZone: "Africa/Cairo" })}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
