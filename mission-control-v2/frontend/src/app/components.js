export const BOARD_COLUMNS = [
  { key: 'recurring', label: 'Recurring' },
  { key: 'backlog', label: 'Backlog' },
  { key: 'in_progress', label: 'In Progress' },
  { key: 'review', label: 'Review' },
  { key: 'done', label: 'Done' }
];

export function escapeHtml(value = '') {
  return String(value)
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;');
}

export function createActivityRows(rows = [], filterMode = 'all') {
  if (!rows.length) {
    return '<div class="empty-state">No live activity yet. As agents start emitting traces, activity will show here automatically.</div>';
  }

  return `
    <div class="activity-list" data-activity-list>
      ${rows
        .map(
          (row, idx) => `
            <article class="activity-row" data-activity-index="${idx}" data-activity-context="${escapeHtml(row.context || 'general')}">
              <div>${escapeHtml(row.text)}</div>
              <div class="activity-meta">${escapeHtml(row.meta)}</div>
            </article>
          `
        )
        .join('')}
    </div>
  `;
}

export function createActivityFilterControls(currentModule, showFilterToggle = true) {
  if (!showFilterToggle) return '';

  const contextLabel = moduleContextLabel(currentModule);
  return `
    <div class="activity-filter-controls">
      <button class="btn filter-toggle active" data-filter-mode="all" title="Show all activity">All</button>
      <button class="btn filter-toggle" data-filter-mode="context" title="Show ${contextLabel}-only activity">${contextLabel}</button>
      <button class="btn filter-btn" type="button" data-action="search-activity" title="Search activity">Search</button>
      <button class="btn filter-btn" type="button" data-action="export-activity" title="Export activity">Export</button>
    </div>
  `;
}

export function inlineActivitySection(currentModule, activityRows, activitySearchOpen = false, activitySearchQuery = '') {
  return `
    <section class="content-card inline-activity-section">
      <header class="module-header">
        <h2 class="module-title">Live Activity</h2>
        <p class="module-subtitle">Real-time system events and agent traces.</p>
      </header>
      ${createActivityFilterControls(currentModule, true)}
      ${activitySearchOpen ? `
        <div class="activity-search-box">
          <input type="text" placeholder="Search activity..." value="${escapeHtml(activitySearchQuery)}" data-action="activity-search-input" autofocus />
        </div>
      ` : ''}
      <div data-live-activity>
        ${createActivityRows(activityRows)}
      </div>
    </section>
  `;
}

function moduleContextLabel(moduleName) {
  const labels = {
    'task-board': 'Board',
    'calendar-cron': 'Cron',
    'projects': 'Projects',
    'memories': 'Memory',
    'docs': 'Docs',
    'team': 'Team',
    'office': 'Office',
    'handoff-gate': 'Gate',
    'job-radar': 'Radar',
    'linkedin-generator': 'LinkedIn',
    'content-factory': 'Factory'
  };
  return labels[moduleName] || 'Page';
}

export function getActivityContextTypes(moduleName) {
  const contexts = {
    'task-board': ['task_created', 'task_updated', 'task_completed', 'task_moved', 'board_activity'],
    'calendar-cron': ['cron_scheduled', 'cron_triggered', 'cron_completed', 'job_pickup', 'next_run_update'],
    'projects': ['project_created', 'project_updated', 'task_linked', 'task_completed', 'progress_updated'],
    'memories': ['memory_captured', 'doc_updated', 'search_executed', 'doc_retrieved', 'knowledge_added'],
    'docs': ['doc_created', 'doc_updated', 'category_changed', 'doc_retrieved', 'search_performed'],
    'team': ['agent_handoff', 'delegation_created', 'availability_changed', 'agent_status_updated'],
    'office': ['agent_movement', 'agent_state_changed', 'status_updated', 'presence_changed'],
    'handoff-gate': ['handoff_quality_check', 'url_validated', 'radar_scan_completed', 'validation_result'],
    'job-radar': ['job_scan_completed', 'qualified_role_found', 'radar_event', 'role_discovery'],
    'linkedin-generator': ['draft_generated', 'draft_approved', 'post_published', 'approval_completed'],
    'content-factory': ['draft_created', 'draft_transitioned', 'sla_breach_warning', 'approval_given']
  };
  return contexts[moduleName] || ['general'];
}

function priorityOptions(selected = 'medium') {
  return ['low', 'medium', 'high']
    .map((priority) => `<option value="${priority}" ${priority === selected ? 'selected' : ''}>${priority[0].toUpperCase()}${priority.slice(1)}</option>`)
    .join('');
}

function createSparkline(values = [], tone = 'active') {
  const clean = values.map((value) => Number(value) || 0);
  const points = clean.length > 1 ? clean : [0, 0];
  const min = Math.min(...points);
  const max = Math.max(...points);
  const range = max - min || 1;
  const coordinates = points
    .map((value, index) => {
      const x = (index / (points.length - 1)) * 100;
      const y = 26 - ((value - min) / range) * 22;
      return `${x.toFixed(2)},${y.toFixed(2)}`;
    })
    .join(' ');

  return `<svg class="sparkline ${tone}" viewBox="0 0 100 28" preserveAspectRatio="none" aria-hidden="true"><polyline points="${coordinates}" /></svg>`;
}

export function createTaskBoard({
  stats,
  columns,
  owners,
  errorMessage = '',
  saving = false,
  noticeMessage = '',
  noticeTone = 'info',
  telemetry = {},
  activityRows = []
}) {
  const ownerOptions = owners
    .map((owner) => `<option value="${escapeHtml(owner.id)}">${escapeHtml(owner.display_name || owner.id)}</option>`)
    .join('');

  const telemetryCards = [
    {
      label: 'Health',
      value: telemetry.healthLabel || 'Stable',
      trend: telemetry.healthTrend || [90, 91, 90, 92, 93, 94, 95],
      tone: telemetry.critical ? 'danger' : 'success'
    },
    {
      label: 'Progress',
      value: `${telemetry.progressPercent || 0}%`,
      trend: telemetry.progressTrend || [10, 15, 20, 25, 30, 35, 40],
      tone: 'active'
    },
    {
      label: 'Latency',
      value: `${telemetry.latencyMs || 0} ms`,
      trend: telemetry.latencyTrend || [320, 300, 290, 270, 250, 240, 220],
      tone: 'warn'
    },
    {
      label: 'Heartbeat',
      value: telemetry.heartbeatLabel || 'No pulse',
      trend: telemetry.heartbeatTrend || [0, 1, 0, 1, 1, 1, 1],
      tone: telemetry.heartbeatActive ? 'active' : 'warn',
      pulse: telemetry.heartbeatActive
    }
  ];

  return `
    <section class="telemetry-row">
      ${telemetryCards
        .map(
          (item) => `
            <article class="telemetry-card ${item.tone}">
              <div class="telemetry-head">
                <span class="telemetry-label">${escapeHtml(item.label)}</span>
                ${item.pulse ? '<span class="heartbeat-dot" aria-label="Live heartbeat"></span>' : ''}
              </div>
              <div class="telemetry-value">${escapeHtml(item.value)}</div>
              ${createSparkline(item.trend, item.tone)}
            </article>
          `
        )
        .join('')}
    </section>

    <section class="bento-grid" data-bento-grid>
      <article class="content-card bento-card" data-bento-card draggable="true">
        <header class="module-header bento-header">
          <h2 class="module-title">Core Overview</h2>
          <p class="module-subtitle">Create, assign, and update tasks with quick inline controls.</p>
          <button class="btn" type="button" data-action="toggle-card" data-target="core-board">Collapse</button>
        </header>

        <div class="bento-body" data-card-body="core-board">
          <form class="task-create-form" data-action="create-task">
            <input name="title" required maxlength="120" placeholder="New task title" autofocus />
            <select name="status">
              ${BOARD_COLUMNS.map((column) => `<option value="${column.key}" ${column.key === 'backlog' ? 'selected' : ''}>${column.label}</option>`).join('')}
            </select>
            <select name="owner_agent_id">
              ${ownerOptions}
            </select>
            <select name="priority">
              ${priorityOptions('medium')}
            </select>
            <button class="btn primary" type="submit" ${saving ? 'disabled' : ''}>${saving ? 'Saving...' : 'Create task'}</button>
          </form>
          <p class="form-hint">Tip: press Enter in title to create instantly, defaults are Backlog and Medium priority.</p>

          ${noticeMessage ? `<p class="notice-banner ${escapeHtml(noticeTone)}" role="status">${escapeHtml(noticeMessage)}</p>` : ''}
          ${errorMessage ? `<p class="error-banner" role="alert">${escapeHtml(errorMessage)}</p>` : ''}

          <section class="kanban-grid">
            ${columns
              .map(
                (column) => {
                  const limitLabel = Number.isFinite(Number(column.wipLimit))
                    ? `${column.items.length}/${Number(column.wipLimit)} WIP`
                    : `${column.items.length}`;
                  return `
                  <article class="column ${column.isOverLimit ? 'wip-warning' : ''}">
                    <header class="column-head">
                      <span>${escapeHtml(column.label)} (${column.items.length})</span>
                      ${Number.isFinite(Number(column.wipLimit)) ? `<span class="wip-pill ${column.isOverLimit ? 'warn' : 'ok'}">${escapeHtml(limitLabel)}</span>` : ''}
                    </header>
                    <div class="column-body" data-drop-status="${escapeHtml(column.key)}">
                      ${column.items.length === 0
                        ? `<div class="empty-state">No tasks in ${escapeHtml(column.label)} yet. Add a task above or move one here.</div>`
                        : column.items
                          .map(
                            (task) => `
                              <article class="task-card ${column.isOverLimit ? 'wip-warning' : ''}" draggable="true" data-task-id="${escapeHtml(task.id)}" data-task-status="${escapeHtml(task.status)}">
                                <h3 class="task-title">${escapeHtml(task.title)}</h3>
                                <p class="task-desc">${escapeHtml(task.description || 'No description yet')}</p>
                                <div class="task-meta">
                                  <span>${escapeHtml(task.owner_name || task.owner_agent_id || 'unassigned')}</span>
                                  <span>${escapeHtml(task.priority || 'medium')}</span>
                                </div>

                                <div class="task-controls">
                                  <select data-action="assign-owner" data-task-id="${escapeHtml(task.id)}" aria-label="Assign owner">
                                    ${owners
                                      .map(
                                        (owner) =>
                                          `<option value="${escapeHtml(owner.id)}" ${owner.id === task.owner_agent_id ? 'selected' : ''}>${escapeHtml(owner.display_name || owner.id)}</option>`
                                      )
                                      .join('')}
                                  </select>

                                  <select data-action="move-status" data-task-id="${escapeHtml(task.id)}" aria-label="Move status">
                                    ${BOARD_COLUMNS.map(
                                      (option) =>
                                        `<option value="${option.key}" ${option.key === task.status ? 'selected' : ''}>${option.label}</option>`
                                    ).join('')}
                                  </select>
                                </div>

                                <form class="task-edit-form" data-action="edit-task" data-task-id="${escapeHtml(task.id)}">
                                  <input name="title" value="${escapeHtml(task.title)}" maxlength="120" aria-label="Task title" />
                                  <input name="description" value="${escapeHtml(task.description || '')}" maxlength="200" placeholder="Description (optional)" aria-label="Task description" />
                                  <div class="task-edit-row">
                                    <select name="priority" aria-label="Task priority">
                                      ${priorityOptions(task.priority || 'medium')}
                                    </select>
                                    <label class="handoff-checkbox">
                                      <input type="checkbox" name="requires_handoff_gate" ${Number(task.requires_handoff_gate) === 1 ? 'checked' : ''} />
                                      Requires review gate
                                    </label>
                                    <button class="btn" type="submit" ${saving ? 'disabled' : ''}>Save</button>
                                  </div>
                                </form>
                              </article>
                            `
                          )
                          .join('')}
                    </div>
                  </article>
                `;
                })
              .join('')}
          </section>
        </div>
      </article>

      <article class="content-card bento-card" data-bento-card draggable="true">
        <header class="module-header bento-header">
          <h2 class="module-title">Real-time Controls</h2>
          <p class="module-subtitle">Adjust polling cadence and trigger immediate refresh.</p>
          <button class="btn" type="button" data-action="toggle-card" data-target="rt-controls">Collapse</button>
        </header>
        <div class="bento-body" data-card-body="rt-controls">
          <div class="actions-row cadence-row">
            <label class="cadence-label">Polling cadence
              <select data-action="polling-cadence">
                <option value="2000" ${Number(telemetry.pollingMs) === 2000 ? 'selected' : ''}>2s</option>
                <option value="5000" ${Number(telemetry.pollingMs) === 5000 ? 'selected' : ''}>5s</option>
                <option value="10000" ${Number(telemetry.pollingMs) === 10000 ? 'selected' : ''}>10s</option>
                <option value="15000" ${Number(telemetry.pollingMs) === 15000 ? 'selected' : ''}>15s</option>
              </select>
            </label>
            <button class="btn primary" type="button" data-action="refresh-now">Refresh now</button>
            <button class="btn" type="button" data-action="create-task-quick">Quick create task</button>
          </div>
          <p class="form-hint">Last successful fetch: ${escapeHtml(telemetry.lastFetchLabel || 'Not available')}</p>
        </div>
      </article>

      <article class="content-card bento-card" data-bento-card draggable="true">
        <header class="module-header bento-header">
          <h2 class="module-title">Deep Dive Logs</h2>
          <p class="module-subtitle">Progressive disclosure, inspect traces only when needed.</p>
          <button class="btn" type="button" data-action="toggle-card" data-target="deep-logs">Collapse</button>
        </header>
        <div class="bento-body" data-card-body="deep-logs">
          <details open>
            <summary>Latest activity stream (${activityRows.length})</summary>
            ${createActivityRows(activityRows)}
          </details>
          <details>
            <summary>Board summary</summary>
            <div class="stats-row">
              ${stats
                .map(
                  (item) => `
                    <article class="stat-card">
                      <div class="stat-label">${escapeHtml(item.label)}</div>
                      <div class="stat-value">${escapeHtml(item.value)}</div>
                    </article>
                  `
                )
                .join('')}
            </div>
          </details>
        </div>
      </article>
    </section>
  `;
}
