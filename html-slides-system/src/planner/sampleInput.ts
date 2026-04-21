import type { PlannerInput } from './plannerTypes.js';

export const sampleInput: PlannerInput = {
  deckTitle: 'AI for Executive Execution',
  objective: 'Show why executive teams need a structured AI operating system for decision velocity and execution confidence.',
  audience: 'CEOs, PMO leaders, transformation sponsors',
  tone: 'Boardroom, sharp, practical',
  desiredSlideCount: 8,
  sections: [
    {
      id: 'problem',
      title: 'Execution problem',
      summary: 'Most transformation programs fail in execution, not strategy, because visibility is fragmented and decision cycles are too slow.',
      bullets: ['Work is spread across tools', 'Leaders get lagging signals', 'Meetings replace operating rhythm'],
      priority: 'high'
    },
    {
      id: 'why-now',
      title: 'Why now',
      summary: 'AI can now compress executive reporting, handoff tracking, and signal synthesis if it is attached to real operating workflows.',
      bullets: ['Better signal extraction', 'Faster summarization', 'Cheaper automation'],
      priority: 'high'
    },
    {
      id: 'solution',
      title: 'Solution thesis',
      summary: 'The answer is not more dashboards. It is an executive execution layer that converts operational noise into action-ready decisions.',
      bullets: ['Unified summaries', 'Structured escalation', 'Routine automation'],
      priority: 'high'
    },
    {
      id: 'capabilities',
      title: 'Core capabilities',
      summary: 'A practical system should combine planning, workflow automation, memory, and channel-native delivery.',
      bullets: ['Planner layer', 'Task automation', 'Persistent memory', 'Telegram and Slack delivery'],
      priority: 'medium'
    },
    {
      id: 'implementation',
      title: 'Implementation path',
      summary: 'Start with one executive workflow, prove value in 30 days, then expand into adjacent reporting and coordination motions.',
      bullets: ['Pick one workflow', 'Run pilot', 'Measure confidence and speed', 'Scale carefully'],
      priority: 'medium'
    },
    {
      id: 'risks',
      title: 'Risks and controls',
      summary: 'The main risks are hallucinated confidence, poor process fit, and weak governance. Each can be reduced through scoped rollout and QA.',
      bullets: ['Human review', 'Narrow scope first', 'Operational guardrails'],
      priority: 'medium'
    }
  ]
};
