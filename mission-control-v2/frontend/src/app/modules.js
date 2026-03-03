import { appRoutes } from './routes.js';
import {
  createTask,
  fetchActivity,
  fetchBoardData,
  fetchCalendarCronView,
  fetchDocsRepository,
  fetchMemoriesLongTerm,
  fetchMemoriesTimeline,
  fetchProjectLinksExpanded,
  fetchProjectProgress,
  fetchProjects,
  fetchTeamOverview,
  fetchHandoffQualityGate,
  fetchJobRadarSummary,
  fetchLinkedinDrafts,
  fetchLinkedinStatus,
  fetchContentFactorySummary,
  generateLinkedinDraft,
  parsePayload,
  patchTask,
  searchMemories,
  transitionTask
} from './api-stubs.js';
import { BOARD_COLUMNS, createActivityRows, createActivityFilterControls, createTaskBoard, escapeHtml, getActivityContextTypes, inlineActivitySection } from './components.js';
import { renderCalendarCronDashboard } from './calendar-cron.js';
import { renderProjectsModule } from '../modules/projects/index.js';
import { renderMemoriesModule } from '../modules/memories/index.js';
import { renderDocsModule } from '../modules/docs/index.js';
import { renderTeamModule } from '../modules/team/index.js';
import { renderOfficeModule } from '../modules/office/index.js';
import { renderHandoffGateModule } from '../modules/handoff-gate/index.js';
import { renderJobRadarModule } from '../modules/job-radar/index.js';
import { renderLinkedinGeneratorModule } from '../modules/linkedin-generator/index.js';
import { renderContentFactoryModule } from '../modules/content-factory/index.js';

const WIP_LIMITS = {
  backlog: 6,
  in_progress: 4,
  review: 3
};

function loadPanelState() {
  try {
    const saved = localStorage.getItem('mission-control-panel-state');
    if (saved) {
      return JSON.parse(saved);
    }
  } catch (e) {
    console.error('[state] failed to load panel state:', e);
  }
  const isMobile = typeof window !== 'undefined' && window.innerWidth < 768;
  return {
    leftCollapsed: false,
    rightCollapsed: false,
    leftCollapsedMobile: isMobile,
    rightCollapsedMobile: isMobile
  };
}

function savePanelState(panelState) {
  try {
    localStorage.setItem('mission-control-panel-state', JSON.stringify(panelState));
  } catch (e) {
    console.error('[state] failed to save panel state:', e);
  }
}

const initialPanelState = loadPanelState();

const appState = {
  tasks: [],
  activity: [],
  owners: [],
  source: 'api',
  saving: false,
  errorMessage: '',
  noticeMessage: '',
  noticeTone: 'info',
  calendarCron: {
    summary: {},
    jobs: [],
    traces: []
  },
  calendarFilters: {
    status: '',
    owner: '',
    source: ''
  },
  projects: [],
  projectProgress: null,
  projectLinks: null,
  memoriesTimeline: [],
  memoriesLongTerm: [],
  memoriesSearchResults: [],
  memoriesSearchQuery: '',
  docsRepository: { docs: [], categories: {} },
  docsQuery: '',
  docsCategory: '',
  teamOverview: { mission: null, agents: [], roles: [], delegation_routes: [] },
  handoffQualityGate: { metrics: {}, latest_failed_items: [], trend_last_7_days: [] },
  handoffPreflight: {
    urlInput: '',
    checked: false,
    valid: false,
    reason: 'Validate a direct role URL before promoting.'
  },
  jobRadarSummary: { latest_runs: [], qualified_roles: [], dropped_reasons: [], handoff_queue: [] },
  linkedinDrafts: [],
  linkedinStatus: {},
  contentFactorySummary: { lane_summary: [] },
  activityFilterMode: 'all',
  activitySearchQuery: '',
  activitySearchOpen: false,
  globalFailure: '',
  lastPathname: '/task-board',
  pollingMs: 5000,
  lastFetchAt: 0,
  latencyHistory: [],
  heartbeatHistory: [],
  navOpen: false,
  navPinned: false,
  commandOpen: false,
  toasts: [],
  criticalAlert: false,
  backendReachable: true,
  generatingDraftId: '',
  panelState: initialPanelState
};

let liveRefreshTimer = null;
let countdownTimer = null;

function activeModuleFromPath(pathname) {
  const match = appRoutes.find((route) => route.path === pathname);
  return match ? match.module : 'task-board';
}

function titleCaseLabel(moduleName = '') {
  return moduleName
    .split('-')
    .map((chunk) => chunk.charAt(0).toUpperCase() + chunk.slice(1))
    .join(' ');
}

function activeRouteMeta(activeModule) {
  const route = appRoutes.find((entry) => entry.module === activeModule);
  return {
    label: route?.label || titleCaseLabel(activeModule),
    path: route?.path || '/'
  };
}

function navTemplate(activeModule) {
  const groups = [
    { label: 'Workspace', routes: ['task-board', 'calendar-cron', 'projects', 'job-radar'] },
    { label: 'Knowledge', routes: ['memories', 'docs', 'team', 'linkedin-generator'] },
    { label: 'Operations', routes: ['office', 'handoff-gate', 'content-factory'] }
  ];

  const iconByModule = {
    'task-board': 'TB',
    'calendar-cron': 'CL',
    projects: 'PJ',
    memories: 'ME',
    docs: 'DC',
    team: 'TM',
    office: 'OF',
    'handoff-gate': 'HG',
    'job-radar': 'JR',
    'linkedin-generator': 'LI',
    'content-factory': 'CF'
  };

  return groups
    .map((group) => {
      const items = group.routes
        .map((moduleName) => appRoutes.find((route) => route.module === moduleName))
        .filter(Boolean)
        .map((route) => {
          const active = activeModule === route.module ? 'active' : '';
          const label = route.label || titleCaseLabel(route.module);
          const icon = iconByModule[route.module] || 'NA';
          return `<a class="nav-item ${active}" href="${route.path}" data-route="${route.path}" ${active ? 'aria-current="page"' : ''}><span class="nav-dot" aria-hidden="true"></span><span class="nav-icon" aria-hidden="true">${icon}</span><span class="nav-label">${label}</span></a>`;
        })
        .join('');

      return `<section class="nav-group"><h3 class="nav-group-title">${group.label}</h3>${items}</section>`;
    })
    .join('');
}

function statusKey(status = '') {
  const normalized = status.toLowerCase();
  if (normalized === 'todo') {
    return 'backlog';
  }
  if (normalized === 'in-progress') {
    return 'in_progress';
  }
  return normalized;
}

function toActivityView(event) {
  const payload = parsePayload(event.payload_json);
  const summary = payload.summary || payload.message || event.event_type;
  const actor = event.actor_agent_id || 'system';
  const module = event.module || 'task-board';
  const context = payload.context || event.event_type || 'general';
  return {
    text: `${summary}`,
    meta: `${new Date(event.created_at).toLocaleTimeString()} · ${module} · ${actor}`,
    context: context,
    timestamp: event.created_at,
    module: module,
    actor: actor,
    eventType: event.event_type
  };
}

function filterActivityByContext(activities, currentModule, filterMode = 'all') {
  if (filterMode === 'all') return activities;
  
  const contextTypes = getActivityContextTypes(currentModule);
  return activities.filter(activity => contextTypes.includes(activity.context) || activity.module === currentModule);
}

function searchActivity(activities, query = '') {
  if (!query.trim()) return activities;
  const q = query.toLowerCase();
  return activities.filter(activity => 
    activity.text.toLowerCase().includes(q) || 
    activity.context.toLowerCase().includes(q) ||
    activity.actor.toLowerCase().includes(q)
  );
}

function exportActivity(activities) {
  const csv = [
    ['Timestamp', 'Module', 'Actor', 'Context', 'Text'].join(','),
    ...activities.map(a => [
      new Date(a.timestamp).toISOString(),
      a.module,
      a.actor,
      a.context,
      `"${(a.text || '').replace(/"/g, '""')}"`
    ].join(','))
  ].join('\n');
  
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
  const link = document.createElement('a');
  const url = URL.createObjectURL(blob);
  link.setAttribute('href', url);
  link.setAttribute('download', `activity-export-${Date.now()}.csv`);
  link.style.visibility = 'hidden';
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

function buildBoardView() {
  const ownerMap = new Map(appState.owners.map((owner) => [owner.id, owner.display_name || owner.id]));
  const columns = BOARD_COLUMNS.map((column) => {
    const wipLimit = WIP_LIMITS[column.key];
    return {
      ...column,
      items: [],
      wipLimit: Number.isFinite(Number(wipLimit)) ? Number(wipLimit) : null,
      isOverLimit: false
    };
  });

  appState.tasks.forEach((task) => {
    const key = statusKey(task.status);
    const column = columns.find((entry) => entry.key === key) || columns[1];
    column.items.push({
      ...task,
      status: key,
      owner_name: ownerMap.get(task.owner_agent_id) || task.owner_agent_id
    });
  });

  columns.forEach((column) => {
    column.isOverLimit = Number.isFinite(Number(column.wipLimit)) && column.items.length > Number(column.wipLimit);
  });

  const stats = [
    { label: 'Total Tasks', value: String(appState.tasks.length) },
    { label: 'Backlog', value: String(columns.find((c) => c.key === 'backlog')?.items.length || 0) },
    { label: 'In Progress', value: String(columns.find((c) => c.key === 'in_progress')?.items.length || 0) },
    { label: 'Review', value: String(columns.find((c) => c.key === 'review')?.items.length || 0) }
  ];

  return { stats, columns };
}

async function loadBoardData() {
  const started = performance.now();
  const data = await fetchBoardData();
  const latencyMs = Math.round(performance.now() - started);
  appState.tasks = data.tasks || [];
  appState.activity = data.activity || [];
  appState.owners = data.agents || [];
  appState.source = data.source || 'api';
  appState.backendReachable = appState.source === 'api';
  appState.lastFetchAt = Date.now();
  appState.latencyHistory = [...appState.latencyHistory.slice(-11), latencyMs];
  appState.heartbeatHistory = [...appState.heartbeatHistory.slice(-11), 1];
  appState.criticalAlert = latencyMs > 1000;
}

async function loadCalendarCronData() {
  if (appState.owners.length === 0) {
    const data = await fetchBoardData();
    appState.owners = data.agents || [];
  }
  appState.calendarCron = await fetchCalendarCronView(appState.calendarFilters);
}

async function loadProjectsData() {
  appState.projects = await fetchProjects();
  const first = appState.projects[0];
  if (!first) {
    appState.projectProgress = null;
    appState.projectLinks = null;
    return;
  }
  [appState.projectProgress, appState.projectLinks] = await Promise.all([
    fetchProjectProgress(first.id),
    fetchProjectLinksExpanded(first.id)
  ]);
}

async function loadMemoriesData() {
  const [timeline, longTerm, searchResults] = await Promise.all([
    fetchMemoriesTimeline(),
    fetchMemoriesLongTerm(),
    searchMemories(appState.memoriesSearchQuery || '')
  ]);
  appState.memoriesTimeline = timeline;
  appState.memoriesLongTerm = longTerm;
  appState.memoriesSearchResults = searchResults;
}

async function loadDocsData() {
  appState.docsRepository = await fetchDocsRepository(appState.docsQuery, appState.docsCategory);
}

async function loadTeamData() {
  appState.teamOverview = await fetchTeamOverview();
}

async function loadHandoffGateData() {
  appState.handoffQualityGate = await fetchHandoffQualityGate();
}

async function loadJobRadarData() {
  appState.jobRadarSummary = await fetchJobRadarSummary();
}

async function loadLinkedinGeneratorData() {
  const [drafts, status] = await Promise.all([
    fetchLinkedinDrafts(),
    fetchLinkedinStatus()
  ]);
  appState.linkedinDrafts = drafts;
  appState.linkedinStatus = status;
}

async function loadContentFactoryData() {
  appState.contentFactorySummary = await fetchContentFactorySummary();
}

function renderPlaceholder(moduleName) {
  return `
    <section class="content-card">
      <header class="module-header">
        <h2 class="module-title">${escapeHtml(moduleName)}</h2>
        <p class="module-subtitle">Phase 6 vertical slice is active for task-board and live activity.</p>
      </header>
    </section>
  `;
}

function appendLocalActivity(text) {
  appState.activity.unshift({
    id: `local-${Date.now()}`,
    event_type: 'ui_optimistic',
    module: 'task-board',
    actor_agent_id: 'agent-nasr',
    payload_json: JSON.stringify({ summary: text }),
    created_at: new Date().toISOString()
  });
}

function pushToast(message, tone = 'info') {
  if (!message) {
    return;
  }
  const id = `toast-${Date.now()}-${Math.random().toString(16).slice(2, 6)}`;
  appState.toasts = [...appState.toasts.slice(-3), { id, message, tone }];
  setTimeout(() => {
    appState.toasts = appState.toasts.filter((toast) => toast.id !== id);
  }, 3200);
}

function setNotice(message, tone = 'info') {
  appState.noticeMessage = message;
  appState.noticeTone = tone;
  if (message && tone !== 'info') {
    pushToast(message, tone);
  }
}

function telemetryView() {
  const now = Date.now();
  const heartbeatActive = appState.lastFetchAt > 0 && now - appState.lastFetchAt <= appState.pollingMs * 1.6;
  const backlog = appState.tasks.filter((task) => statusKey(task.status) === 'backlog').length;
  const inProgress = appState.tasks.filter((task) => statusKey(task.status) === 'in_progress').length;
  const completed = appState.tasks.filter((task) => statusKey(task.status) === 'done').length;
  const total = Math.max(appState.tasks.length, 1);
  const progressPercent = Math.round((completed / total) * 100);
  const healthLabel = appState.criticalAlert ? 'Critical' : backlog > inProgress * 2 + 2 ? 'Degraded' : 'Stable';
  const latencyMs = appState.latencyHistory.at(-1) || 0;

  return {
    healthLabel,
    progressPercent,
    latencyMs,
    heartbeatLabel: heartbeatActive ? 'Pulse active' : 'Pulse stale',
    heartbeatActive,
    healthTrend: appState.latencyHistory.slice(-7).map((ms) => Math.max(10, 100 - Math.round(ms / 8))),
    progressTrend: appState.heartbeatHistory.slice(-7).map((value, index) => Math.min(100, progressPercent - (6 - index) * 3 + value * 2)),
    latencyTrend: appState.latencyHistory.slice(-7),
    heartbeatTrend: appState.heartbeatHistory.slice(-7),
    pollingMs: appState.pollingMs,
    lastFetchLabel: appState.lastFetchAt ? new Date(appState.lastFetchAt).toLocaleTimeString() : 'Not available',
    critical: appState.criticalAlert
  };
}

async function runOptimistic(mutator, remoteCall, rollbackSnapshot, successMessage = 'Saved') {
  appState.errorMessage = '';
  appState.saving = true;
  setNotice('Saving changes...', 'info');
  mutator();

  try {
    await remoteCall();
    setNotice(successMessage, 'success');
  } catch (error) {
    appState.tasks = rollbackSnapshot;
    appState.errorMessage = error.message || 'We could not save that change. Board was restored to the last stable state.';
    setNotice('', 'info');
  } finally {
    appState.saving = false;
  }
}

function launchConfetti(root) {
  const host = root.querySelector('[data-confetti-layer]');
  if (!host) return;
  host.innerHTML = Array.from({ length: 22 }).map((_, i) => `<span class="confetti-piece" style="--x:${(i * 19) % 100}%;--d:${300 + i * 35}ms"></span>`).join('');
  setTimeout(() => { host.innerHTML = ''; }, 1400);
}

async function moveTaskToStatus(root, taskId, nextStatus) {
  const rollback = [...appState.tasks];
  await runOptimistic(
    () => {
      appState.tasks = appState.tasks.map((task) =>
        task.id === taskId ? { ...task, status: nextStatus, updated_at: new Date().toISOString() } : task
      );
      appendLocalActivity(`Task moved to ${nextStatus}`);
      if (nextStatus === 'done') launchConfetti(root);
    },
    async () => {
      await transitionTask(taskId, nextStatus, 'Moved from board column');
    },
    rollback,
    `Moved to ${nextStatus}`
  );
  renderApp(root, '/task-board');
}

function bindBoardHandlers(root) {
  const createForm = root.querySelector('[data-action="create-task"]');
  if (createForm) {
    createForm.addEventListener('submit', async (event) => {
      event.preventDefault();
      const formData = new FormData(createForm);
      const draftId = `draft-${Date.now()}`;
      const rollback = [...appState.tasks];
      const draft = {
        id: draftId,
        title: String(formData.get('title') || '').trim(),
        description: '',
        status: String(formData.get('status') || 'backlog'),
        owner_agent_id: String(formData.get('owner_agent_id') || ''),
        priority: String(formData.get('priority') || 'medium'),
        requires_handoff_gate: 0,
        updated_at: new Date().toISOString()
      };

      if (!draft.title) {
        return;
      }

      await runOptimistic(
        () => {
          appState.tasks = [draft, ...appState.tasks];
          appendLocalActivity(`Task created: ${draft.title}`);
        },
        async () => {
          const created = await createTask(draft);
          appState.tasks = appState.tasks.map((task) => (task.id === draftId ? created : task));
        },
        rollback,
        `Task created: ${draft.title}`
      );

      createForm.reset();
      renderApp(root, '/task-board');
    });
  }

  root.querySelectorAll('[data-action="assign-owner"]').forEach((input) => {
    input.addEventListener('change', async () => {
      const taskId = input.getAttribute('data-task-id');
      const ownerAgentId = input.value;
      const rollback = [...appState.tasks];

      await runOptimistic(
        () => {
          appState.tasks = appState.tasks.map((task) =>
            task.id === taskId ? { ...task, owner_agent_id: ownerAgentId, updated_at: new Date().toISOString() } : task
          );
          appendLocalActivity(`Owner assigned for ${taskId}`);
        },
        async () => {
          await patchTask(taskId, { owner_agent_id: ownerAgentId });
        },
        rollback,
        'Owner updated'
      );

      renderApp(root, '/task-board');
    });
  });

  root.querySelectorAll('[data-action="move-status"]').forEach((input) => {
    input.addEventListener('change', async () => {
      const taskId = input.getAttribute('data-task-id');
      const nextStatus = input.value;
      await moveTaskToStatus(root, taskId, nextStatus);
    });
  });

  root.querySelectorAll('[data-action="edit-task"]').forEach((form) => {
    form.addEventListener('submit', async (event) => {
      event.preventDefault();
      const taskId = form.getAttribute('data-task-id');
      const formData = new FormData(form);
      const rollback = [...appState.tasks];
      const patch = {
        title: String(formData.get('title') || '').trim(),
        description: String(formData.get('description') || '').trim(),
        priority: String(formData.get('priority') || 'medium'),
        requires_handoff_gate: Boolean(formData.get('requires_handoff_gate'))
      };

      await runOptimistic(
        () => {
          appState.tasks = appState.tasks.map((task) =>
            task.id === taskId ? { ...task, ...patch, updated_at: new Date().toISOString() } : task
          );
          appendLocalActivity(`Task updated: ${taskId}`);
        },
        async () => {
          await patchTask(taskId, patch);
        },
        rollback,
        'Task saved'
      );

      renderApp(root, '/task-board');
    });
  });

  root.querySelectorAll('.task-card[draggable="true"]').forEach((card) => {
    card.addEventListener('dragstart', (event) => {
      event.dataTransfer?.setData('text/task-id', card.getAttribute('data-task-id') || '');
      card.classList.add('dragging');
    });
    card.addEventListener('dragend', () => card.classList.remove('dragging'));
  });

  root.querySelectorAll('[data-drop-status]').forEach((zone) => {
    zone.addEventListener('dragover', (event) => { event.preventDefault(); zone.classList.add('drag-over'); });
    zone.addEventListener('dragleave', () => zone.classList.remove('drag-over'));
    zone.addEventListener('drop', async (event) => {
      zone.classList.remove('drag-over');
      event.preventDefault();
      const taskId = event.dataTransfer?.getData('text/task-id');
      const nextStatus = zone.getAttribute('data-drop-status');
      if (!taskId || !nextStatus) return;
      await moveTaskToStatus(root, taskId, nextStatus);
    });
  });
}

function bindCalendarCronHandlers(root) {
  const form = root.querySelector('[data-action="calendar-filters"]');
  if (form) {
    const applyFilters = async () => {
      const formData = new FormData(form);
      appState.calendarFilters = {
        status: String(formData.get('status') || ''),
        owner: String(formData.get('owner') || ''),
        source: String(formData.get('source') || '')
      };
      await renderApp(root, '/calendar-cron');
    };

    form.addEventListener('submit', async (event) => {
      event.preventDefault();
      await applyFilters();
    });
  }

  const countdown = root.querySelector('.next-run-countdown');
  const card = root.querySelector('.countdown-card');
  if (countdown && card) {
    const target = card.getAttribute('data-next-run-at');
    if (countdownTimer) clearInterval(countdownTimer);
    countdownTimer = setInterval(() => {
      if (!target) {
        countdown.textContent = 'No upcoming run scheduled';
        return;
      }
      const delta = new Date(target).getTime() - Date.now();
      if (delta <= 0) {
        countdown.textContent = 'Overdue';
        return;
      }
      const sec = Math.floor(delta / 1000);
      const h = Math.floor(sec / 3600);
      const m = Math.floor((sec % 3600) / 60);
      const s = sec % 60;
      countdown.textContent = `Due in ${h}h ${m}m ${s}s`;
    }, 1000);
  }
}

function bindMemoriesHandlers(root) {
  const form = root.querySelector('[data-action="search-memories"]');
  if (!form) return;
  const input = form.querySelector('input[name="query"]');
  let timer;
  const apply = async () => {
    const formData = new FormData(form);
    appState.memoriesSearchQuery = String(formData.get('query') || '');
    await renderApp(root, '/memories');
  };
  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    await apply();
  });
  input?.addEventListener('input', () => {
    clearTimeout(timer);
    timer = setTimeout(() => { apply(); }, 220);
  });
}

function bindDocsHandlers(root) {
  const form = root.querySelector('[data-action="search-docs"]');
  if (!form) return;
  const input = form.querySelector('input[name="query"]');
  let timer;
  const apply = async () => {
    const formData = new FormData(form);
    appState.docsQuery = String(formData.get('query') || '');
    appState.docsCategory = String(formData.get('category') || '');
    await renderApp(root, '/docs');
  };
  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    await apply();
  });
  input?.addEventListener('input', () => {
    clearTimeout(timer);
    timer = setTimeout(() => { apply(); }, 220);
  });
}

function validatePreflightUrl(rawUrl = '') {
  const trimmed = String(rawUrl || '').trim();
  if (!trimmed) {
    return { checked: true, valid: false, reason: 'Enter a URL to validate.' };
  }

  let parsed;
  try {
    parsed = new URL(trimmed);
  } catch {
    return { checked: true, valid: false, reason: 'Invalid URL format.' };
  }

  if (!['http:', 'https:'].includes(parsed.protocol)) {
    return { checked: true, valid: false, reason: 'Only http and https URLs are allowed.' };
  }

  const host = parsed.hostname.toLowerCase();
  const path = parsed.pathname.toLowerCase();
  const full = `${host}${path}${parsed.search.toLowerCase()}`;

  const linkedinDirect = host.includes('linkedin.com')
    && (path.startsWith('/jobs/view/') || path === '/jobs/view' || parsed.searchParams.has('currentjobid'));

  if (linkedinDirect) {
    return { checked: true, valid: true, reason: 'Valid LinkedIn direct job URL.' };
  }

  const employerHost = !host.includes('linkedin.com')
    && !host.includes('indeed.')
    && !host.includes('glassdoor.')
    && !host.includes('bayt.')
    && !host.includes('naukri.')
    && !host.includes('ziprecruiter.')
    && !host.includes('google.');
  const employerPath = /(career|careers|job|jobs|vacanc|position|opportunit)/.test(path);
  const roleSlugSignal = /[a-z0-9-]{8,}/.test(path) || /jobid|gh_jid|lever-source/.test(full);

  if (employerHost && employerPath && roleSlugSignal) {
    return { checked: true, valid: true, reason: 'Valid direct employer job posting URL.' };
  }

  return {
    checked: true,
    valid: false,
    reason: 'URL must be a LinkedIn /jobs/view link or a direct employer job posting page.'
  };
}

function bindHandoffGateHandlers(root) {
  const form = root.querySelector('[data-action="handoff-url-preflight"]');
  if (!form) return;

  const input = form.querySelector('input[name="source_url"]');
  const validateButton = form.querySelector('[data-action="validate-preflight-url"]');

  validateButton?.addEventListener('click', async (event) => {
    event.preventDefault();
    appState.handoffPreflight = {
      ...appState.handoffPreflight,
      urlInput: String(input?.value || '').trim(),
      ...validatePreflightUrl(input?.value || '')
    };
    await renderApp(root, '/handoff-gate');
  });

  input?.addEventListener('input', () => {
    appState.handoffPreflight = {
      ...appState.handoffPreflight,
      urlInput: String(input.value || ''),
      checked: false,
      valid: false,
      reason: 'Validate a direct role URL before promoting.'
    };
  });
}

function bindLinkedinGeneratorHandlers(root) {
  root.querySelectorAll('[data-action="generate-draft"]').forEach((button) => {
    button.addEventListener('click', async () => {
      const draftId = button.getAttribute('data-draft-id');
      if (!draftId) return;
      appState.generatingDraftId = draftId;
      button.classList.add('is-loading');
      button.disabled = true;
      try {
        await generateLinkedinDraft(draftId);
        setNotice('Draft generated in safe mode, no posting executed.', 'success');
      } finally {
        appState.generatingDraftId = '';
      }
      await renderApp(root, '/linkedin-generator');
    });
  });
}

async function refreshLiveActivityIfVisible(root, activeModule) {
  if (activeModule !== 'task-board') {
    return;
  }

  try {
    const latest = await fetchActivity(100);
    appState.activity = latest;
    appState.lastFetchAt = Date.now();
    appState.heartbeatHistory = [...appState.heartbeatHistory.slice(-11), 1];
    const container = root.querySelector('[data-live-activity]');
    if (container) {
      container.innerHTML = createActivityRows(appState.activity.slice(0, 12).map(toActivityView));
    }
  } catch (error) {
    appState.heartbeatHistory = [...appState.heartbeatHistory.slice(-11), 0];
    pushToast('Live refresh missed one cycle', 'warn');
  }
}

function bindGlobalUiHandlers(root, activeModule) {
  const isMobile = typeof window !== 'undefined' && window.innerWidth < 768;
  const currentLeftState = isMobile ? appState.panelState.leftCollapsedMobile : appState.panelState.leftCollapsed;
  const currentRightState = isMobile ? appState.panelState.rightCollapsedMobile : appState.panelState.rightCollapsed;

  const leftToggleButton = root.querySelector('[data-action="toggle-left-panel"]');
  if (leftToggleButton) {
    leftToggleButton.addEventListener('click', () => {
      if (isMobile) {
        appState.panelState.leftCollapsedMobile = !appState.panelState.leftCollapsedMobile;
      } else {
        appState.panelState.leftCollapsed = !appState.panelState.leftCollapsed;
      }
      savePanelState(appState.panelState);
      root.querySelector('.app-shell')?.classList.toggle('left-panel-collapsed');
    });
  }

  /* Hamburger edge toggle for left panel */
  const leftEdgeToggle = root.querySelector('[data-action="toggle-left-panel-edge"]');
  if (leftEdgeToggle) {
    const toggleLeftPanel = () => {
      if (isMobile) {
        appState.panelState.leftCollapsedMobile = !appState.panelState.leftCollapsedMobile;
      } else {
        appState.panelState.leftCollapsed = !appState.panelState.leftCollapsed;
      }
      savePanelState(appState.panelState);
      const shell = root.querySelector('.app-shell');
      shell?.classList.toggle('left-panel-collapsed');
      leftEdgeToggle.classList.toggle('rotated');
    };
    
    leftEdgeToggle.addEventListener('click', toggleLeftPanel);
    
    /* Keyboard accessibility: Enter and Space to toggle */
    leftEdgeToggle.addEventListener('keydown', (event) => {
      if (event.key === 'Enter' || event.key === ' ') {
        event.preventDefault();
        toggleLeftPanel();
      }
    });
  }

  const menuButton = root.querySelector('[data-action="toggle-nav"]');
  if (menuButton) {
    menuButton.addEventListener('click', () => {
      if (!appState.navPinned) {
        appState.navOpen = !appState.navOpen;
        root.querySelector('.app-shell')?.classList.toggle('nav-open', appState.navOpen);
      }
    });
  }

  const pinButton = root.querySelector('[data-action="pin-nav"]');
  if (pinButton) {
    pinButton.addEventListener('click', () => {
      appState.navPinned = !appState.navPinned;
      const shell = root.querySelector('.app-shell');
      shell?.classList.toggle('nav-pinned', appState.navPinned);
      if (appState.navPinned) {
        appState.navOpen = true;
        shell?.classList.add('nav-open');
      }
    });
  }

  const createTaskBtn = root.querySelector('[data-action="create-task"]');
  if (createTaskBtn) {
    createTaskBtn.addEventListener('click', () => {
      const titleInput = root.querySelector('[data-action="create-task"] input[name="title"]');
      if (titleInput instanceof HTMLInputElement) {
        titleInput.focus();
      }
    });
  }

  const newDocBtn = root.querySelector('[data-action="new-doc"]');
  if (newDocBtn) {
    newDocBtn.addEventListener('click', () => {
      window.history.pushState({}, '', '/docs');
      renderApp(root, '/docs');
    });
  }

  const refreshBtn = root.querySelector('[data-action="refresh-data"]');
  if (refreshBtn) {
    refreshBtn.addEventListener('click', () => {
      fetchActivity().then((activity) => {
        appState.activity = activity;
        renderApp(root, appState.lastPathname);
      });
    });
  }

  root.querySelectorAll('[data-action="toggle-card"]').forEach((button) => {
    button.addEventListener('click', () => {
      const target = button.getAttribute('data-target');
      const body = target ? root.querySelector(`[data-card-body="${target}"]`) : null;
      if (!body) {
        return;
      }
      const collapsed = body.classList.toggle('is-collapsed');
      button.textContent = collapsed ? 'Expand' : 'Collapse';
    });
  });

  const cards = Array.from(root.querySelectorAll('[data-bento-card]'));
  cards.forEach((card) => {
    card.addEventListener('dragstart', () => {
      card.classList.add('dragging');
    });
    card.addEventListener('dragend', () => {
      card.classList.remove('dragging');
    });
  });

  const grid = root.querySelector('[data-bento-grid]');
  if (grid) {
    grid.addEventListener('dragover', (event) => {
      event.preventDefault();
      const dragging = grid.querySelector('.dragging');
      if (!dragging) {
        return;
      }
      const siblings = [...grid.querySelectorAll('[data-bento-card]:not(.dragging)')];
      const next = siblings.find((sibling) => event.clientY <= sibling.getBoundingClientRect().top + sibling.offsetHeight / 2);
      if (next) {
        grid.insertBefore(dragging, next);
      } else {
        grid.appendChild(dragging);
      }
    });
  }

  const cadenceSelect = root.querySelector('[data-action="polling-cadence"]');
  if (cadenceSelect) {
    cadenceSelect.addEventListener('change', () => {
      appState.pollingMs = Number(cadenceSelect.value) || 5000;
      pushToast(`Polling cadence set to ${Math.round(appState.pollingMs / 1000)}s`, 'info');
      renderApp(root, '/task-board');
    });
  }

  const refreshNowButton = root.querySelector('[data-action="refresh-now"]');
  if (refreshNowButton) {
    refreshNowButton.addEventListener('click', async () => {
      await loadBoardData();
      pushToast('Data refreshed', 'success');
      await renderApp(root, '/task-board');
    });
  }

  const quickCreateButton = root.querySelector('[data-action="create-task-quick"]');
  if (quickCreateButton) {
    quickCreateButton.addEventListener('click', async () => {
      const title = window.prompt('Quick task title');
      if (!title) {
        return;
      }
      const firstOwner = appState.owners[0]?.id || '';
      await createTask({
        title,
        status: 'backlog',
        owner_agent_id: firstOwner,
        priority: 'medium'
      });
      pushToast('Quick task created', 'success');
      await renderApp(root, '/task-board');
    });
  }

  const commandOverlay = root.querySelector('[data-command-palette]');
  const commandInput = root.querySelector('[data-command-input]');
  root.querySelectorAll('[data-action="open-command-palette"]').forEach((button) => {
    button.addEventListener('click', () => {
      appState.commandOpen = true;
      commandOverlay?.classList.add('open');
      commandInput?.focus();
    });
  });
  root.querySelectorAll('[data-action="close-command-palette"]').forEach((button) => {
    button.addEventListener('click', () => {
      appState.commandOpen = false;
      commandOverlay?.classList.remove('open');
    });
  });

  root.querySelectorAll('[data-command]').forEach((button) => {
    button.addEventListener('click', async () => {
      const action = button.getAttribute('data-command');
      if (action?.startsWith('route:')) {
        const nextPath = action.replace('route:', '');
        window.history.pushState({}, '', nextPath);
        await renderApp(root, nextPath);
      }
      if (action === 'refresh') {
        await renderApp(root, appState.lastPathname || '/task-board');
      }
      if (action === 'create-task') {
        const titleInput = root.querySelector('[data-action="create-task"] input[name="title"]');
        if (titleInput instanceof HTMLInputElement) {
          titleInput.focus();
        }
      }
      appState.commandOpen = false;
      commandOverlay?.classList.remove('open');
    });
  });

  if (!window.__MC2_COMMAND_KEYBOUND__) {
    window.__MC2_COMMAND_KEYBOUND__ = true;
    document.addEventListener('keydown', (event) => {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'k') {
        event.preventDefault();
        const palette = document.querySelector('[data-command-palette]');
        palette?.classList.add('open');
        const input = document.querySelector('[data-command-input]');
        if (input instanceof HTMLInputElement) {
          input.focus();
        }
      }
      if (event.key === 'Escape') {
        document.querySelector('[data-command-palette]')?.classList.remove('open');
      }
    });
  }

  root.querySelectorAll('[data-filter-mode]').forEach((button) => {
    button.addEventListener('click', () => {
      const mode = button.getAttribute('data-filter-mode');
      appState.activityFilterMode = mode;
      root.querySelectorAll('[data-filter-mode]').forEach((btn) => btn.classList.remove('active'));
      button.classList.add('active');
      renderApp(root, appState.lastPathname);
    });
  });

  const searchActivityButton = root.querySelector('[data-action="search-activity"]');
  if (searchActivityButton) {
    searchActivityButton.addEventListener('click', () => {
      appState.activitySearchOpen = !appState.activitySearchOpen;
      renderApp(root, appState.lastPathname);
    });
  }

  const activitySearchInput = root.querySelector('[data-action="activity-search-input"]');
  if (activitySearchInput) {
    activitySearchInput.addEventListener('input', (e) => {
      appState.activitySearchQuery = e.target.value;
      renderApp(root, appState.lastPathname);
    });
    activitySearchInput.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        appState.activitySearchOpen = false;
        renderApp(root, appState.lastPathname);
      }
    });
  }

  const exportActivityButton = root.querySelector('[data-action="export-activity"]');
  if (exportActivityButton) {
    exportActivityButton.addEventListener('click', () => {
      const allActivities = appState.activity.map(toActivityView);
      exportActivity(allActivities);
      pushToast('Activity exported to CSV', 'success');
    });
  }
}

function renderFailureShell(root, message) {
  root.innerHTML = `
    <div class="app-shell">
      <main class="main-area">
        <section class="content-card">
          <header class="module-header">
            <h2 class="module-title">Mission Control v2</h2>
            <p class="module-subtitle">A recoverable UI error happened. Retry should restore the page.</p>
          </header>
          <p class="error-banner" role="alert">${escapeHtml(message || 'Unknown UI error')}</p>
          <div class="actions-row">
            <button class="btn primary" data-action="retry-render">Retry render</button>
          </div>
        </section>
      </main>
    </div>
  `;

  const retryButton = root.querySelector('[data-action="retry-render"]');
  if (retryButton) {
    retryButton.addEventListener('click', () => {
      renderApp(root, appState.lastPathname || '/task-board');
    });
  }
}

export async function renderApp(root, pathname = window.location.pathname) {
  appState.lastPathname = pathname;

  try {
    const activeModule = activeModuleFromPath(pathname);

    if (liveRefreshTimer) {
      clearInterval(liveRefreshTimer);
      liveRefreshTimer = null;
    }
    if (countdownTimer) {
      clearInterval(countdownTimer);
      countdownTimer = null;
    }

    appState.globalFailure = '';

    if (activeModule === 'task-board') {
      await loadBoardData();
    } else {
      await fetchActivity(50).then((rows) => { appState.activity = rows; }).catch(() => {});
    }

    if (activeModule === 'calendar-cron') {
      await loadCalendarCronData();
    }
    if (activeModule === 'projects') {
      await loadProjectsData();
    }
    if (activeModule === 'memories') {
      await loadMemoriesData();
    }
    if (activeModule === 'docs') {
      await loadDocsData();
    }
    if (activeModule === 'team') {
      await loadTeamData();
    }
    if (activeModule === 'office') {
      await Promise.all([loadTeamData(), fetchActivity(40).then((rows) => { appState.activity = rows; })]);
    }
    if (activeModule === 'handoff-gate') {
      await loadHandoffGateData();
    }
    if (activeModule === 'job-radar') {
      await loadJobRadarData();
    }
    if (activeModule === 'linkedin-generator') {
      await loadLinkedinGeneratorData();
    }
    if (activeModule === 'content-factory') {
      await loadContentFactoryData();
    }

    const boardView = activeModule === 'task-board' ? buildBoardView() : null;
    
    // Initialize sideActivityRows before use
    let sideActivityRows = activeModule === 'calendar-cron'
      ? (appState.calendarCron.traces || []).slice(0, 12).map((trace) => ({
        text: trace.summary || trace.event_type,
        meta: `${new Date(trace.occurred_at || Date.now()).toLocaleTimeString()} · ${trace.source || 'calendar-cron'} · ${trace.owner_agent_id || 'system'}`,
        context: 'cron_event'
      }))
      : appState.activity.slice(0, 50).map(toActivityView);
    
    sideActivityRows = filterActivityByContext(sideActivityRows, activeModule, appState.activityFilterMode);
    if (appState.activitySearchQuery) {
      sideActivityRows = searchActivity(sideActivityRows, appState.activitySearchQuery);
    }
    sideActivityRows = sideActivityRows.slice(0, 12);
    
    let mainContent = renderPlaceholder(activeModule);

    if (activeModule === 'calendar-cron') {
      mainContent = renderCalendarCronDashboard({
        summary: appState.calendarCron.summary || {},
        jobs: appState.calendarCron.jobs || [],
        traces: appState.calendarCron.traces || [],
        filters: appState.calendarFilters,
        owners: appState.owners
      });
      mainContent += inlineActivitySection(activeModule, sideActivityRows, appState.activitySearchOpen, appState.activitySearchQuery);
    } else if (activeModule === 'projects') {
      mainContent = renderProjectsModule({
        projects: appState.projects,
        progress: appState.projectProgress,
        links: appState.projectLinks
      });
      mainContent += inlineActivitySection(activeModule, sideActivityRows, appState.activitySearchOpen, appState.activitySearchQuery);
    } else if (activeModule === 'memories') {
      mainContent = renderMemoriesModule({
        timeline: appState.memoriesTimeline,
        longTerm: appState.memoriesLongTerm,
        searchResults: appState.memoriesSearchResults,
        searchQuery: appState.memoriesSearchQuery
      });
      mainContent += inlineActivitySection(activeModule, sideActivityRows, appState.activitySearchOpen, appState.activitySearchQuery);
    } else if (activeModule === 'docs') {
      mainContent = renderDocsModule({
        repository: appState.docsRepository,
        query: appState.docsQuery,
        category: appState.docsCategory
      });
      mainContent += inlineActivitySection(activeModule, sideActivityRows, appState.activitySearchOpen, appState.activitySearchQuery);
    } else if (activeModule === 'team') {
      mainContent = renderTeamModule({ overview: appState.teamOverview });
      mainContent += inlineActivitySection(activeModule, sideActivityRows, appState.activitySearchOpen, appState.activitySearchQuery);
    } else if (activeModule === 'office') {
      mainContent = renderOfficeModule({
        overview: appState.teamOverview,
        activity: appState.activity.slice(0, 10).map(toActivityView)
      });
      mainContent += inlineActivitySection(activeModule, sideActivityRows, appState.activitySearchOpen, appState.activitySearchQuery);
    } else if (activeModule === 'handoff-gate') {
      mainContent = renderHandoffGateModule({
        qualityGate: appState.handoffQualityGate,
        preflight: appState.handoffPreflight
      });
      mainContent += inlineActivitySection(activeModule, sideActivityRows, appState.activitySearchOpen, appState.activitySearchQuery);
    } else if (activeModule === 'job-radar') {
      mainContent = renderJobRadarModule({ summary: appState.jobRadarSummary });
      mainContent += inlineActivitySection(activeModule, sideActivityRows, appState.activitySearchOpen, appState.activitySearchQuery);
    } else if (activeModule === 'linkedin-generator') {
      mainContent = renderLinkedinGeneratorModule({ drafts: appState.linkedinDrafts, status: appState.linkedinStatus });
      mainContent += inlineActivitySection(activeModule, sideActivityRows, appState.activitySearchOpen, appState.activitySearchQuery);
    } else if (activeModule === 'content-factory') {
      mainContent = renderContentFactoryModule({ summary: appState.contentFactorySummary });
      mainContent += inlineActivitySection(activeModule, sideActivityRows, appState.activitySearchOpen, appState.activitySearchQuery);
    }

    const currentRoute = activeRouteMeta(activeModule);

    const telemetry = telemetryView();
    const toastHtml = appState.toasts
      .map((toast) => `<article class="toast ${escapeHtml(toast.tone)}">${escapeHtml(toast.message)}</article>`)
      .join('');

    const isMobile = typeof window !== 'undefined' && window.innerWidth < 768;
    const leftCollapsed = isMobile ? appState.panelState.leftCollapsedMobile : appState.panelState.leftCollapsed;

    root.innerHTML = `
      <div class="app-shell ${appState.navOpen ? 'nav-open' : ''} ${appState.navPinned ? 'nav-pinned' : ''} ${appState.criticalAlert ? 'red-alert' : ''} ${leftCollapsed ? 'left-panel-collapsed' : ''}">
        <aside class="panel left-nav">
          <button 
            class="panel-edge-toggle left-panel-toggle ${leftCollapsed ? 'rotated' : ''}"
            type="button"
            data-action="toggle-left-panel-edge"
            title="Toggle left panel"
            aria-label="Toggle left menu panel"
          >
            <div class="hamburger-icon">
              <span class="hamburger-line"></span>
              <span class="hamburger-line"></span>
              <span class="hamburger-line"></span>
            </div>
          </button>
          <div class="menu-header">
            <div class="brand">
              <h1>Mission Control v2</h1>
              <p>${appState.source === 'api' ? 'Backend connected' : 'Fallback mode'}</p>
            </div>
            <div class="menu-actions">
              <button class="btn icon-btn" type="button" data-action="create-task" title="Create task">+</button>
              <button class="btn icon-btn" type="button" data-action="new-doc" title="New doc">D</button>
              <button class="btn icon-btn" type="button" data-action="refresh-data" title="Refresh">@</button>
            </div>
          </div>
          <nav class="nav-list">${navTemplate(activeModule)}</nav>
        </aside>

        <main class="main-area">
          <section class="page-context" aria-label="Current page context">
            <div class="nav-controls">
              <button class="btn panel-toggle left-toggle" type="button" data-action="toggle-left-panel" title="Toggle left panel" aria-label="Toggle left panel">${leftCollapsed ? '←' : '→'}</button>
              <button class="btn menu-toggle" type="button" data-action="toggle-nav" title="Toggle menu">☰</button>
              <button class="btn icon-btn pin-toggle" type="button" data-action="pin-nav" title="Pin menu">${appState.navPinned ? 'P' : 'p'}</button>
            </div>
            <div>
              <div class="page-context-label">Current page</div>
              <div class="page-context-title">${escapeHtml(currentRoute.label)}</div>
              <div class="page-context-path">${escapeHtml(currentRoute.path)}</div>
            </div>
            <div class="page-context-right-controls">
              <button class="btn" type="button" data-action="open-command-palette">Command</button>
            </div>
          </section>
          ${appState.globalFailure ? `<p class="error-banner" role="alert">${escapeHtml(appState.globalFailure)}</p>` : ''}
          ${activeModule === 'task-board'
            ? createTaskBoard({
              ...boardView,
              owners: appState.owners,
              errorMessage: appState.errorMessage,
              noticeMessage: appState.noticeMessage,
              noticeTone: appState.noticeTone,
              saving: appState.saving,
              telemetry,
              activityRows: sideActivityRows
            })
            : mainContent}
        </main>
      </div>

      <footer class="global-footer">
        <span class="footer-heartbeat ${appState.backendReachable ? 'ok' : 'down'}"></span>
        <span>${appState.backendReachable ? 'Backend and Tailscale reachable' : 'Backend or Tailscale unreachable'}</span>
      </footer>

      <div class="confetti-layer" data-confetti-layer aria-hidden="true"></div>
      <section class="toast-stack" aria-live="polite">${toastHtml}</section>

      <section class="command-palette ${appState.commandOpen ? 'open' : ''}" data-command-palette>
        <div class="command-panel">
          <div class="command-head">
            <strong>Command Palette</strong>
            <button class="btn" type="button" data-action="close-command-palette">Close</button>
          </div>
          <input data-command-input placeholder="Type an action, route, or keyword" />
          <div class="command-actions">
            <button class="btn" type="button" data-command="route:/">Go to Board</button>
            <button class="btn" type="button" data-command="route:/calendar-cron">Go to Calendar</button>
            <button class="btn" type="button" data-command="refresh">Refresh data</button>
            <button class="btn" type="button" data-command="create-task">Create task</button>
          </div>
          <p class="form-hint">Shortcut: Ctrl+K or Cmd+K</p>
        </div>
      </section>
    `;

    document.body.classList.toggle('red-alert', appState.criticalAlert || !appState.backendReachable);

    root.querySelectorAll('[data-route]').forEach((anchor) => {
      anchor.addEventListener('click', (event) => {
        event.preventDefault();
        const nextPath = anchor.getAttribute('data-route') || '/';
        window.history.pushState({}, '', nextPath);
        renderApp(root, nextPath);
      });
    });

    if (activeModule === 'task-board') {
      bindBoardHandlers(root);
      const titleInput = root.querySelector('[data-action="create-task"] input[name="title"]');
      if (titleInput instanceof HTMLInputElement && document.activeElement?.tagName !== 'INPUT') {
        titleInput.focus();
      }
      liveRefreshTimer = setInterval(() => {
        refreshLiveActivityIfVisible(root, activeModule);
      }, appState.pollingMs);
    }

    bindGlobalUiHandlers(root, activeModule);

    if (activeModule === 'calendar-cron') {
      bindCalendarCronHandlers(root);
    }
    if (activeModule === 'memories') {
      bindMemoriesHandlers(root);
    }
    if (activeModule === 'docs') {
      bindDocsHandlers(root);
    }
    if (activeModule === 'handoff-gate') {
      bindHandoffGateHandlers(root);
    }
    if (activeModule === 'linkedin-generator') {
      bindLinkedinGeneratorHandlers(root);
    }
  } catch (error) {
    appState.globalFailure = error.message || 'Render failed unexpectedly';
    console.error('[ui] render failed', error);
    renderFailureShell(root, appState.globalFailure);
  }
}
