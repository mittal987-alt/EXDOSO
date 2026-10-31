/**
 * EDXSO Influencer Outreach — Frontend Command Center Logic
 */

const API_BASE_URL = 'http://127.0.0.1:8000';

// Global Application State
const state = {
  influencers: [],
  drafts: [],
  logs: [],
  filteredInfluencers: [],
  filteredDrafts: [],
  currentTab: 'influencers-tab',
  influencerFilter: 'all',
  influencerSearch: '',
  outreachChannelFilter: 'all',
  outreachStatusFilter: 'all',
  viewMode: 'grid', // 'grid' or 'table'
  isBackendConnected: false,
};

// ============================================================================
// Initialization
// ============================================================================
document.addEventListener('DOMContentLoaded', () => {
  setupEventListeners();
  checkBackendHealth();
  refreshAllData();

  // Polling backend health every 15s
  setInterval(checkBackendHealth, 15000);
});

// ============================================================================
// Event Listeners Setup
// ============================================================================
function setupEventListeners() {
  // Tabs Navigation
  document.querySelectorAll('.tab-btn').forEach((btn) => {
    btn.addEventListener('click', () => switchTab(btn.dataset.tab));
  });

  // Export Dropdown
  const exportBtn = document.getElementById('export-dropdown-btn');
  const exportMenu = document.getElementById('export-dropdown-menu');
  exportBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    exportMenu.classList.toggle('hidden');
  });

  document.addEventListener('click', () => exportMenu.classList.add('hidden'));

  document.getElementById('export-influencers-btn').addEventListener('click', (e) => {
    e.preventDefault();
    triggerExport('influencers.csv');
  });
  document.getElementById('export-drafts-btn').addEventListener('click', (e) => {
    e.preventDefault();
    triggerExport('outreach-messages.csv');
  });
  document.getElementById('export-logs-btn').addEventListener('click', (e) => {
    e.preventDefault();
    triggerExport('delivery-logs.csv');
  });

  // Pipeline Actions
  document.getElementById('pipeline-discover-btn').addEventListener('click', openDiscoveryModal);
  document.getElementById('open-discovery-modal-btn').addEventListener('click', openDiscoveryModal);
  document.getElementById('close-discovery-modal-btn').addEventListener('click', closeDiscoveryModal);
  document.getElementById('cancel-discovery-btn').addEventListener('click', closeDiscoveryModal);
  document.getElementById('execute-discovery-btn').addEventListener('click', executeDiscovery);

  document.getElementById('pipeline-enrich-btn').addEventListener('click', executeEnrichment);
  document.getElementById('pipeline-qualify-btn').addEventListener('click', executeQualification);
  document.getElementById('pipeline-generate-btn').addEventListener('click', executeGenerateOutreach);
  document.getElementById('pipeline-send-btn').addEventListener('click', executeSendPending);
  document.getElementById('send-pending-studio-btn').addEventListener('click', executeSendPending);
  document.getElementById('refresh-logs-btn').addEventListener('click', fetchDeliveryLogs);

  // Search & Filters for Influencers
  document.getElementById('influencer-search-input').addEventListener('input', (e) => {
    state.influencerSearch = e.target.value.toLowerCase().trim();
    filterAndRenderInfluencers();
  });

  document.querySelectorAll('#influencer-status-filters .filter-pill').forEach((pill) => {
    pill.addEventListener('click', () => {
      document.querySelectorAll('#influencer-status-filters .filter-pill').forEach((p) => p.classList.remove('active'));
      pill.classList.add('active');
      state.influencerFilter = pill.dataset.filter;
      filterAndRenderInfluencers();
    });
  });

  // View Mode (Grid vs Table)
  document.getElementById('view-mode-grid').addEventListener('click', () => {
    state.viewMode = 'grid';
    document.getElementById('view-mode-grid').classList.add('active');
    document.getElementById('view-mode-table').classList.remove('active');
    document.getElementById('influencer-cards-grid').classList.remove('hidden');
    document.getElementById('influencer-table-container').classList.add('hidden');
  });

  document.getElementById('view-mode-table').addEventListener('click', () => {
    state.viewMode = 'table';
    document.getElementById('view-mode-table').classList.add('active');
    document.getElementById('view-mode-grid').classList.remove('active');
    document.getElementById('influencer-cards-grid').classList.add('hidden');
    document.getElementById('influencer-table-container').classList.remove('hidden');
  });

  // Outreach Studio Filters
  document.querySelectorAll('#outreach-channel-filters .filter-pill').forEach((pill) => {
    pill.addEventListener('click', () => {
      document.querySelectorAll('#outreach-channel-filters .filter-pill').forEach((p) => p.classList.remove('active'));
      pill.classList.add('active');
      state.outreachChannelFilter = pill.dataset.channel;
      filterAndRenderDrafts();
    });
  });

  document.querySelectorAll('#outreach-status-filters .filter-pill').forEach((pill) => {
    pill.addEventListener('click', () => {
      document.querySelectorAll('#outreach-status-filters .filter-pill').forEach((p) => p.classList.remove('active'));
      pill.classList.add('active');
      state.outreachStatusFilter = pill.dataset.status;
      filterAndRenderDrafts();
    });
  });

  // Manual Add Form
  document.getElementById('add-influencer-form').addEventListener('submit', handleAddInfluencer);

  // Details Modal Close
  document.getElementById('close-details-modal-btn').addEventListener('click', () => {
    document.getElementById('details-modal').classList.add('hidden');
  });
}

// ============================================================================
// API Calls & Data Synchronization
// ============================================================================
async function checkBackendHealth() {
  const badge = document.getElementById('backend-status-badge');
  const text = document.getElementById('backend-status-text');

  try {
    const res = await fetch(`${API_BASE_URL}/health`);
    if (res.ok) {
      state.isBackendConnected = true;
      badge.className = 'status-pill status-online';
      text.textContent = 'Backend Online (127.0.0.1:8000)';
    } else {
      throw new Error();
    }
  } catch (err) {
    state.isBackendConnected = false;
    badge.className = 'status-pill status-offline';
    text.textContent = 'Backend Offline';
  }
}

async function refreshAllData() {
  await Promise.all([
    fetchInfluencers(),
    fetchOutreachDrafts(),
    fetchDeliveryLogs(),
  ]);
  updateStatsCounters();
}

async function fetchInfluencers() {
  try {
    const res = await fetch(`${API_BASE_URL}/api/influencers`);
    if (!res.ok) throw new Error('Failed to fetch influencers');
    state.influencers = await res.json();
    filterAndRenderInfluencers();
  } catch (err) {
    showToast(`Error fetching creators: ${err.message}`, 'error');
  }
}

async function fetchOutreachDrafts() {
  try {
    const res = await fetch(`${API_BASE_URL}/api/outreach/drafts`);
    if (!res.ok) throw new Error('Failed to fetch outreach drafts');
    const data = await res.json();
    state.drafts = data.drafts || [];
    filterAndRenderDrafts();
  } catch (err) {
    showToast(`Error fetching drafts: ${err.message}`, 'error');
  }
}

async function fetchDeliveryLogs() {
  try {
    const res = await fetch(`${API_BASE_URL}/api/outreach/delivery-logs`);
    if (!res.ok) throw new Error('Failed to fetch delivery logs');
    const data = await res.json();
    state.logs = data.logs || [];
    renderDeliveryLogs();
  } catch (err) {
    showToast(`Error fetching logs: ${err.message}`, 'error');
  }
}

// ============================================================================
// Pipeline Actions Execution
// ============================================================================
function openDiscoveryModal() {
  document.getElementById('discovery-modal').classList.remove('hidden');
}

function closeDiscoveryModal() {
  document.getElementById('discovery-modal').classList.add('hidden');
}

async function executeDiscovery() {
  const target = parseInt(document.getElementById('discovery-target-input').value, 10) || 10;
  closeDiscoveryModal();
  showToast(`Running YouTube creator discovery (target: ${target})...`, 'info');

  try {
    const res = await fetch(`${API_BASE_URL}/api/discovery/youtube?target=${target}`, {
      method: 'POST',
    });
    const data = await res.json();

    if (!res.ok) throw new Error(data.detail || 'Discovery failed');

    showToast(`Discovered ${data.discovered} creators! (${data.inserted} added, ${data.duplicates_skipped} duplicates skipped)`, 'success');
    await refreshAllData();
  } catch (err) {
    showToast(`Discovery error: ${err.message}`, 'error');
  }
}

async function executeEnrichment() {
  showToast('Enriching stored YouTube influencers with public metadata...', 'info');

  try {
    const res = await fetch(`${API_BASE_URL}/api/influencers/enrich`, {
      method: 'POST',
    });
    const data = await res.json();

    if (!res.ok) throw new Error(data.detail || 'Enrichment failed');

    showToast(`Enrichment complete! ${data.enriched} enriched, ${data.needs_review} flagged for review.`, 'success');
    await refreshAllData();
  } catch (err) {
    showToast(`Enrichment error: ${err.message}`, 'error');
  }
}

async function executeQualification() {
  showToast('Evaluating creators against subscriber & engagement rules...', 'info');

  try {
    const res = await fetch(`${API_BASE_URL}/api/influencers/qualify`, {
      method: 'POST',
    });
    const data = await res.json();

    if (!res.ok) throw new Error(data.detail || 'Qualification failed');

    showToast(`Qualification complete! ${data.qualified} qualified, ${data.rejected} rejected.`, 'success');
    await refreshAllData();
  } catch (err) {
    showToast(`Qualification error: ${err.message}`, 'error');
  }
}

async function executeGenerateOutreach() {
  showToast('Generating personalized multi-channel outreach drafts...', 'info');

  try {
    const res = await fetch(`${API_BASE_URL}/api/outreach/generate`, {
      method: 'POST',
    });
    const data = await res.json();

    if (!res.ok) throw new Error(data.detail || 'Outreach generation failed');

    showToast(`Generated ${data.drafts_generated} drafts across ${data.qualified_influencers} qualified creators! (${data.existing_drafts_skipped} skipped)`, 'success');
    await refreshAllData();
    switchTab('outreach-tab');
  } catch (err) {
    showToast(`Generation error: ${err.message}`, 'error');
  }
}

async function executeSendSingle(messageId) {
  try {
    const res = await fetch(`${API_BASE_URL}/api/outreach/send/${messageId}`, {
      method: 'POST',
    });
    const data = await res.json();

    if (!res.ok) throw new Error(data.detail || 'Send failed');

    showToast(`Simulated send succeeded for message #${messageId}!`, 'success');
    await refreshAllData();
  } catch (err) {
    showToast(`Send error: ${err.message}`, 'error');
  }
}

async function executeSendPending() {
  showToast('Simulating dispatch for all pending outreach messages...', 'info');

  try {
    const res = await fetch(`${API_BASE_URL}/api/outreach/send-pending`, {
      method: 'POST',
    });
    const data = await res.json();

    if (!res.ok) throw new Error(data.detail || 'Batch send failed');

    showToast(`Simulated send complete! ${data.sent} sent, ${data.failed} failed.`, 'success');
    await refreshAllData();
  } catch (err) {
    showToast(`Batch send error: ${err.message}`, 'error');
  }
}

async function handleAddInfluencer(e) {
  e.preventDefault();

  const payload = {
    name: document.getElementById('form-name').value.trim(),
    platform: document.getElementById('form-platform').value,
    profile_url: document.getElementById('form-profile-url').value.trim(),
    source_url: document.getElementById('form-source-url').value.trim() || null,
    follower_count: parseInt(document.getElementById('form-followers').value, 10) || null,
    engagement_rate: parseFloat(document.getElementById('form-engagement').value) || null,
    category: document.getElementById('form-category').value.trim() || null,
    geography: document.getElementById('form-geography').value.trim() || null,
    contact_email: document.getElementById('form-email').value.trim() || null,
    website: document.getElementById('form-website').value.trim() || null,
    content_themes: document.getElementById('form-themes').value.trim() || null,
  };

  try {
    const res = await fetch(`${API_BASE_URL}/api/influencers`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    const data = await res.json();

    if (!res.ok) throw new Error(data.detail || 'Failed to add influencer');

    showToast(`Influencer "${payload.name}" successfully created!`, 'success');
    document.getElementById('add-influencer-form').reset();
    await refreshAllData();
    switchTab('influencers-tab');
  } catch (err) {
    showToast(`Error creating influencer: ${err.message}`, 'error');
  }
}

function triggerExport(filename) {
  const url = `${API_BASE_URL}/api/exports/${filename}`;
  window.open(url, '_blank');
  showToast(`Downloading ${filename}...`, 'info');
}

// ============================================================================
// UI Rendering
// ============================================================================
function updateStatsCounters() {
  const total = state.influencers.length;
  const qualified = state.influencers.filter((i) => i.qualification_status === 'Qualified').length;
  const drafts = state.drafts.length;
  const sent = state.logs.filter((l) => l.status === 'Sent' || l.status === 'sent').length;

  document.getElementById('stat-total-val').textContent = total.toLocaleString();
  document.getElementById('stat-qualified-val').textContent = qualified.toLocaleString();
  const pct = total > 0 ? ((qualified / total) * 100).toFixed(1) : 0;
  document.getElementById('stat-qualified-pct').textContent = `${pct}% conversion rate`;

  document.getElementById('stat-drafts-val').textContent = drafts.toLocaleString();
  document.getElementById('stat-sent-val').textContent = sent.toLocaleString();

  document.getElementById('tab-influencers-count').textContent = total;
  document.getElementById('tab-outreach-count').textContent = drafts;
  document.getElementById('tab-logs-count').textContent = state.logs.length;
}

function filterAndRenderInfluencers() {
  state.filteredInfluencers = state.influencers.filter((inf) => {
    // Status filter
    if (state.influencerFilter !== 'all' && inf.qualification_status !== state.influencerFilter) {
      return false;
    }
    // Search query filter
    if (state.influencerSearch) {
      const q = state.influencerSearch;
      const name = (inf.name || '').toLowerCase();
      const cat = (inf.category || '').toLowerCase();
      const themes = (inf.content_themes || '').toLowerCase();
      return name.includes(q) || cat.includes(q) || themes.includes(q);
    }
    return true;
  });

  renderInfluencerCards();
  renderInfluencerTable();
}

function renderInfluencerCards() {
  const container = document.getElementById('influencer-cards-grid');

  if (state.filteredInfluencers.length === 0) {
    container.innerHTML = `
      <div class="empty-state">
        <p>No creators match the current filter or search criteria.</p>
      </div>
    `;
    return;
  }

  container.innerHTML = state.filteredInfluencers
    .map((inf) => {
      const initial = (inf.name || 'C')[0].toUpperCase();
      const statusClass = getStatusClass(inf.qualification_status);
      const followers = formatNumber(inf.follower_count);
      const engagement = inf.engagement_rate != null ? `${inf.engagement_rate}%` : 'N/A';
      const category = inf.category || 'General Fitness';

      // Parse themes into pills
      const themesHtml = (inf.content_themes || '')
        .split(',')
        .slice(0, 3)
        .map((t) => t.trim())
        .filter(Boolean)
        .map((t) => `<span class="theme-pill">${escapeHtml(t)}</span>`)
        .join('');

      return `
        <div class="creator-card" id="creator-card-${inf.id}">
          <div class="creator-card-header">
            <div class="creator-avatar">${initial}</div>
            <div class="creator-headline">
              <h4 class="creator-name" title="${escapeHtml(inf.name)}">${escapeHtml(inf.name)}</h4>
              <a href="${escapeHtml(inf.profile_url)}" target="_blank" rel="noopener noreferrer" class="creator-platform-link">
                ${inf.platform} Profile ↗
              </a>
            </div>
            <span class="status-tag ${statusClass}">${inf.qualification_status || 'Pending'}</span>
          </div>

          <div class="creator-metrics-row">
            <div class="metric-item">
              <span class="metric-name">Subscribers</span>
              <span class="metric-num">${followers}</span>
            </div>
            <div class="metric-item">
              <span class="metric-name">Engagement</span>
              <span class="metric-num">${engagement}</span>
            </div>
          </div>

          <div class="creator-themes-tags">
            <span class="theme-pill" style="border-color: rgba(99,102,241,0.3); color: #a5b4fc;">${escapeHtml(category)}</span>
            ${themesHtml}
          </div>

          <div class="creator-card-footer">
            <span style="font-size: 12px; color: var(--text-subtle);">
              ${inf.contact_email ? `✉️ ${escapeHtml(inf.contact_email)}` : 'No email found'}
            </span>
            <button class="btn btn-secondary btn-sm" onclick="window.viewInfluencerDetails(${inf.id})">
              Details
            </button>
          </div>
        </div>
      `;
    })
    .join('');
}

function renderInfluencerTable() {
  const tbody = document.getElementById('influencer-table-body');
  if (state.filteredInfluencers.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" class="text-center py-4">No creators found.</td></tr>`;
    return;
  }

  tbody.innerHTML = state.filteredInfluencers
    .map((inf) => {
      const statusClass = getStatusClass(inf.qualification_status);
      return `
        <tr>
          <td>
            <strong>${escapeHtml(inf.name)}</strong><br />
            <a href="${escapeHtml(inf.profile_url)}" target="_blank" style="font-size: 12px; color: var(--accent-cyan);">
              ${inf.platform}
            </a>
          </td>
          <td>${formatNumber(inf.follower_count)}</td>
          <td>${inf.engagement_rate != null ? `${inf.engagement_rate}%` : 'N/A'}</td>
          <td>${escapeHtml(inf.category || 'N/A')}</td>
          <td>${escapeHtml(inf.contact_email || 'Not Found')}</td>
          <td><span class="status-tag ${statusClass}">${inf.qualification_status || 'Pending'}</span></td>
          <td>
            <button class="btn btn-secondary btn-sm" onclick="window.viewInfluencerDetails(${inf.id})">
              Details
            </button>
          </td>
        </tr>
      `;
    })
    .join('');
}

function filterAndRenderDrafts() {
  state.filteredDrafts = state.drafts.filter((draft) => {
    if (state.outreachChannelFilter !== 'all' && draft.channel !== state.outreachChannelFilter) {
      return false;
    }
    if (state.outreachStatusFilter !== 'all' && draft.status !== state.outreachStatusFilter) {
      return false;
    }
    return true;
  });

  const container = document.getElementById('outreach-cards-grid');

  if (state.filteredDrafts.length === 0) {
    container.innerHTML = `
      <div class="empty-state">
        <p>No outreach drafts generated yet. Run Stage 4 in the pipeline to generate copies!</p>
      </div>
    `;
    return;
  }

  container.innerHTML = state.filteredDrafts
    .map((draft) => {
      const isEmail = draft.channel === 'Email';
      const channelClass = isEmail ? 'channel-email' : 'channel-instagram';
      const channelIcon = isEmail ? '✉️' : '💬';
      const isSent = draft.status === 'Sent';

      return `
        <div class="outreach-card" id="draft-card-${draft.id}">
          <div class="outreach-header">
            <span class="channel-badge ${channelClass}">${channelIcon} ${draft.channel}</span>
            <div style="display: flex; gap: 8px; align-items: center;">
              <span class="word-count-badge">${draft.word_count} words</span>
              <span class="status-tag ${isSent ? 'tag-qualified' : 'tag-pending'}">${draft.status}</span>
            </div>
          </div>

          ${draft.subject ? `<div class="outreach-subject">Subject: ${escapeHtml(draft.subject)}</div>` : ''}

          <div class="outreach-message-body">${escapeHtml(draft.message)}</div>

          <div class="outreach-footer">
            <span style="font-size: 12px; color: var(--text-subtle);">
              Influencer ID #${draft.influencer_id}
            </span>
            ${
              isSent
                ? `<button class="btn btn-secondary btn-sm" disabled>Sent ✓</button>`
                : `<button class="btn btn-primary btn-sm" onclick="window.sendSingleMessage(${draft.id})">
                    Simulate Send
                  </button>`
            }
          </div>
        </div>
      `;
    })
    .join('');
}

function renderDeliveryLogs() {
  const tbody = document.getElementById('logs-table-body');
  if (state.logs.length === 0) {
    tbody.innerHTML = `<tr><td colspan="6" class="text-center py-4">No delivery audit logs recorded yet.</td></tr>`;
    return;
  }

  tbody.innerHTML = state.logs
    .map((log) => {
      const dateStr = new Date(log.created_at).toLocaleString();
      return `
        <tr>
          <td>#${log.id}</td>
          <td>#${log.outreach_message_id}</td>
          <td><code>${escapeHtml(log.event)}</code></td>
          <td><span class="status-tag tag-qualified">${escapeHtml(log.status)}</span></td>
          <td style="max-width: 320px; font-size: 12.5px;">${escapeHtml(log.details || '')}</td>
          <td style="font-size: 12px; color: var(--text-subtle);">${dateStr}</td>
        </tr>
      `;
    })
    .join('');
}

// Window Exposed Handlers for inline onclicks
window.viewInfluencerDetails = function (influencerId) {
  const inf = state.influencers.find((i) => i.id === influencerId);
  if (!inf) return;

  const modalBody = document.getElementById('details-modal-body');
  document.getElementById('details-modal-name').textContent = `${inf.name} — Full Profile`;

  modalBody.innerHTML = `
    <div style="display: flex; flex-direction: column; gap: 16px;">
      <div style="display: flex; justify-content: space-between; align-items: center;">
        <span class="status-tag ${getStatusClass(inf.qualification_status)}">${inf.qualification_status || 'Pending'}</span>
        <a href="${escapeHtml(inf.profile_url)}" target="_blank" class="btn btn-outline-cyan btn-sm">
          Open YouTube Channel ↗
        </a>
      </div>

      <div class="creator-metrics-row">
        <div class="metric-item">
          <span class="metric-name">Subscribers</span>
          <span class="metric-num">${formatNumber(inf.follower_count)}</span>
        </div>
        <div class="metric-item">
          <span class="metric-name">Engagement Rate</span>
          <span class="metric-num">${inf.engagement_rate != null ? `${inf.engagement_rate}%` : 'N/A'}</span>
        </div>
      </div>

      <div style="background: rgba(13,18,31,0.6); padding: 14px; border-radius: var(--radius-md); border: 1px solid var(--border-color); font-size: 13.5px;">
        <p><strong>Category:</strong> ${escapeHtml(inf.category || 'N/A')}</p>
        <p class="mt-4"><strong>Geography:</strong> ${escapeHtml(inf.geography || 'N/A')}</p>
        <p class="mt-4"><strong>Contact Email:</strong> ${escapeHtml(inf.contact_email || 'Not Found')}</p>
        <p class="mt-4"><strong>Website / Socials:</strong> ${inf.website ? `<a href="${escapeHtml(inf.website)}" target="_blank" style="color: var(--accent-cyan);">${escapeHtml(inf.website)}</a>` : 'Not Found'}</p>
        <p class="mt-4"><strong>Detected Themes:</strong> ${escapeHtml(inf.content_themes || 'None')}</p>
        ${
          inf.rejection_reasons
            ? `<div class="mt-4" style="padding: 10px; background: rgba(244,63,94,0.1); border-left: 3px solid #f43f5e; color: #fecdd3; border-radius: 4px;">
                <strong>Rejection Reason:</strong> ${escapeHtml(inf.rejection_reasons)}
              </div>`
            : ''
        }
      </div>
    </div>
  `;

  document.getElementById('details-modal').classList.remove('hidden');
};

window.sendSingleMessage = function (messageId) {
  executeSendSingle(messageId);
};

// ============================================================================
// Utilities
// ============================================================================
function switchTab(tabId) {
  document.querySelectorAll('.app-tabs-nav .tab-btn').forEach((btn) => {
    btn.classList.toggle('active', btn.dataset.tab === tabId);
  });

  document.querySelectorAll('.tab-pane').forEach((pane) => {
    pane.classList.toggle('hidden', pane.id !== tabId);
    pane.classList.toggle('active', pane.id === tabId);
  });

  state.currentTab = tabId;
}

function getStatusClass(status) {
  if (status === 'Qualified') return 'tag-qualified';
  if (status === 'Rejected') return 'tag-rejected';
  return 'tag-pending';
}

function formatNumber(num) {
  if (num == null) return 'N/A';
  if (num >= 1_000_000) return `${(num / 1_000_000).toFixed(1)}M`;
  if (num >= 1_000) return `${(num / 1_000).toFixed(1)}K`;
  return num.toString();
}

function escapeHtml(str) {
  if (!str) return '';
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function showToast(message, type = 'info') {
  const container = document.getElementById('toast-container');
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;

  const icon = type === 'success' ? '✅' : type === 'error' ? '❌' : 'ℹ️';

  toast.innerHTML = `
    <span class="toast-icon">${icon}</span>
    <span class="toast-message">${escapeHtml(message)}</span>
  `;

  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(100%)';
    toast.style.transition = 'all 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}
