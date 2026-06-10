/**
 * Mélange — Enterprise Contract Intelligence Platform
 * Frontend Application Controller
 * Connects the premium UI to the Django REST API backend.
 */

'use strict';

// ============================================================
// CONFIGURATION
// ============================================================
const API_URL = 'http://localhost:8000/api';

// ============================================================
// STATE
// ============================================================
let allDocuments = [];
let chartRisk = null;
let chartClauses = null;
let chartStatus = null;
let currentDocId = null;

// ============================================================
// DOM HELPERS
// ============================================================
const $ = (id) => document.getElementById(id);
const show = (el) => el && el.classList.remove('hidden');
const hide = (el) => el && el.classList.add('hidden');

function showToast(message, type = 'success') {
    const container = $('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    const icon = type === 'success' ? 'fa-check-circle' : type === 'error' ? 'fa-times-circle' : 'fa-info-circle';
    toast.innerHTML = `<i class="fas ${icon}"></i> <span>${message}</span>`;
    container.appendChild(toast);
    setTimeout(() => toast.classList.add('visible'), 10);
    setTimeout(() => {
        toast.classList.remove('visible');
        setTimeout(() => toast.remove(), 400);
    }, 3500);
}

// ============================================================
// NAVIGATION
// ============================================================
function navigateTo(viewName) {
    // Update nav items
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.toggle('active', item.dataset.view === viewName);
    });

    // Show correct view
    document.querySelectorAll('.view').forEach(view => view.classList.remove('active'));
    const target = document.getElementById(`view-${viewName}`);
    if (target) target.classList.add('active');

    // Update topbar title
    const titles = {
        dashboard: 'Dashboard',
        documents: 'Documents',
        obligations: 'Obligations Tracker',
        search: 'Search Intelligence',
        compare: 'Compare Documents',
        settings: 'Settings',
        analysis: 'Document Analysis',
    };
    $('topbar-title').textContent = titles[viewName] || viewName;

    // Trigger data loading for the view
    if (viewName === 'dashboard') loadDashboard();
    if (viewName === 'documents') loadDocuments();
    if (viewName === 'obligations') loadObligations();
    if (viewName === 'compare') loadCompare();
}

// Attach nav clicks
document.querySelectorAll('.nav-item[data-view]').forEach(item => {
    item.addEventListener('click', (e) => {
        e.preventDefault();
        navigateTo(item.dataset.view);
    });
});

// "View All" links on dashboard
document.querySelectorAll('[data-view-link]').forEach(el => {
    el.addEventListener('click', (e) => {
        e.preventDefault();
        navigateTo(el.dataset.viewLink);
    });
});

// ============================================================
// DASHBOARD
// ============================================================
async function loadDashboard() {
    try {
        const res = await fetch(`${API_URL}/dashboard/`);
        if (!res.ok) throw new Error('Dashboard API error');
        const data = await res.json();

        // KPIs
        $('kpi-total-docs').textContent = data.kpis.total_documents;
        $('kpi-high-risks').textContent = data.kpis.high_risks;
        $('kpi-obligations').textContent = data.kpis.upcoming_obligations;
        $('kpi-processed').textContent = data.kpis.processed_documents;

        // Charts
        renderRiskChart(data.charts.risk_distribution);
        renderClauseChart(data.charts.clause_types);
        renderStatusChart(data.charts.document_status);

        // Recent docs table
        renderRecentDocs(data.recent_documents);
    } catch (err) {
        console.error('Dashboard load error:', err);
        // Show friendly placeholder values
        $('kpi-total-docs').textContent = '0';
        $('kpi-high-risks').textContent = '0';
        $('kpi-obligations').textContent = '0';
        $('kpi-processed').textContent = '0';
    }
}

function renderRiskChart(dist) {
    const ctx = $('chart-risk');
    if (!ctx) return;
    if (chartRisk) chartRisk.destroy();
    chartRisk = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['High', 'Medium', 'Low'],
            datasets: [{
                data: [dist.High || 0, dist.Medium || 0, dist.Low || 0],
                backgroundColor: ['#ef4444', '#f59e0b', '#10b981'],
                borderWidth: 0,
                hoverOffset: 8,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '72%',
            plugins: {
                legend: { position: 'bottom', labels: { color: '#94a3b8', padding: 16, font: { size: 12 } } }
            }
        }
    });
}

function renderClauseChart(clauseTypes) {
    const ctx = $('chart-clauses');
    if (!ctx) return;
    if (chartClauses) chartClauses.destroy();
    const labels = clauseTypes.map(c => c.clause_type);
    const values = clauseTypes.map(c => c.count);
    chartClauses = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels.length ? labels : ['No data'],
            datasets: [{
                label: 'Count',
                data: values.length ? values : [0],
                backgroundColor: 'rgba(99,102,241,0.7)',
                borderRadius: 6,
                borderSkipped: false,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                x: { ticks: { color: '#64748b' }, grid: { display: false } },
                y: { ticks: { color: '#64748b', stepSize: 1 }, grid: { color: 'rgba(255,255,255,0.04)' } }
            }
        }
    });
}

function renderStatusChart(statusDist) {
    const ctx = $('chart-status');
    if (!ctx) return;
    if (chartStatus) chartStatus.destroy();
    chartStatus = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: ['Completed', 'Processing', 'Pending', 'Failed'],
            datasets: [{
                data: [
                    statusDist.completed || 0,
                    statusDist.processing || 0,
                    statusDist.pending || 0,
                    statusDist.failed || 0
                ],
                backgroundColor: ['#10b981', '#6366f1', '#f59e0b', '#ef4444'],
                borderWidth: 0,
                hoverOffset: 8,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'bottom', labels: { color: '#94a3b8', padding: 16, font: { size: 12 } } }
            }
        }
    });
}

function renderRecentDocs(docs) {
    const tbody = $('recent-docs-body');
    if (!docs || docs.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4" style="text-align:center;color:var(--text-muted);padding:2rem;">No documents yet. Upload your first contract.</td></tr>';
        return;
    }
    tbody.innerHTML = docs.map(doc => `
        <tr>
            <td><strong>${escapeHtml(doc.title)}</strong></td>
            <td>${statusBadge(doc.status)}</td>
            <td>${formatDate(doc.uploaded_at)}</td>
            <td>
                <button class="btn btn-ghost btn-sm" onclick="openAnalysis('${doc.id}')">
                    <i class="fas fa-eye"></i> View
                </button>
            </td>
        </tr>
    `).join('');
}

// ============================================================
// DOCUMENTS VIEW
// ============================================================
async function loadDocuments() {
    const tbody = $('docs-table-body');
    tbody.innerHTML = '<tr><td colspan="5"><div class="skeleton skeleton-text"></div></td></tr>'.repeat(4);
    hide($('docs-empty'));

    try {
        const res = await fetch(`${API_URL}/documents/`);
        const docs = await res.json();
        allDocuments = docs;
        $('doc-count').textContent = `${docs.length} total`;
        renderDocsTable(docs);
    } catch (err) {
        tbody.innerHTML = '<tr><td colspan="5" style="color:var(--red);text-align:center;padding:2rem;">Could not connect to backend. Is the server running?</td></tr>';
    }
}

function renderDocsTable(docs) {
    const tbody = $('docs-table-body');
    const empty = $('docs-empty');
    if (!docs || docs.length === 0) {
        tbody.innerHTML = '';
        show(empty);
        return;
    }
    hide(empty);
    tbody.innerHTML = docs.map(doc => `
        <tr>
            <td>
                <div style="display:flex;align-items:center;gap:0.75rem;">
                    <div class="doc-icon"><i class="fas fa-file-contract"></i></div>
                    <strong>${escapeHtml(doc.title)}</strong>
                </div>
            </td>
            <td>${statusBadge(doc.status)}</td>
            <td>${formatDate(doc.uploaded_at)}</td>
            <td>${riskBadge(doc)}</td>
            <td>
                <div style="display:flex;gap:0.5rem;">
                    <button class="btn btn-ghost btn-sm" onclick="openAnalysis('${doc.id}')" title="View Analysis">
                        <i class="fas fa-chart-bar"></i>
                    </button>
                    <button class="btn btn-ghost btn-sm btn-danger-hover" onclick="deleteDocument('${doc.id}', '${escapeHtml(doc.title)}')" title="Delete">
                        <i class="fas fa-trash-alt"></i>
                    </button>
                </div>
            </td>
        </tr>
    `).join('');
}

// Live search filter
$('doc-search-input').addEventListener('input', (e) => {
    const q = e.target.value.toLowerCase();
    const filtered = allDocuments.filter(d => d.title.toLowerCase().includes(q));
    renderDocsTable(filtered);
});

async function deleteDocument(docId, title) {
    if (!confirm(`Delete "${title}"? This action cannot be undone.`)) return;
    try {
        const res = await fetch(`${API_URL}/documents/${docId}/`, { method: 'DELETE' });
        if (res.status === 204) {
            showToast(`"${title}" deleted.`, 'success');
            loadDocuments();
        } else {
            showToast('Failed to delete document.', 'error');
        }
    } catch {
        showToast('Network error while deleting.', 'error');
    }
}

// ============================================================
// ANALYSIS VIEW
// ============================================================
async function openAnalysis(docId) {
    currentDocId = docId;
    navigateTo('analysis');

    // Reset UI to loading state
    $('analysis-doc-title').textContent = 'Loading…';
    $('analysis-doc-date').textContent = '—';
    $('analysis-doc-status').textContent = '—';
    $('analysis-summary-text').textContent = 'Loading AI analysis…';
    $('analysis-findings').innerHTML = '';
    $('analysis-actions').innerHTML = '';
    $('analysis-risks').innerHTML = '';
    $('analysis-clauses').innerHTML = '';
    $('analysis-obligations').innerHTML = '';

    try {
        const res = await fetch(`${API_URL}/documents/${docId}/analysis/`);
        if (!res.ok) {
            showToast('Analysis not ready yet. The document may still be processing.', 'info');
            $('analysis-doc-title').textContent = 'Analysis Pending';
            $('analysis-summary-text').textContent = 'This document is still being processed by the AI pipeline. Please wait a moment and try again.';
            return;
        }
        const data = await res.json();
        const doc = data.document;

        // Header
        $('analysis-doc-title').textContent = doc.title;
        $('analysis-doc-date').textContent = formatDate(doc.uploaded_at);
        $('analysis-doc-status').innerHTML = statusBadge(doc.status);

        // Summary
        if (data.summary) {
            $('analysis-summary-text').textContent = data.summary.executive_summary || 'No summary available.';
            $('analysis-findings').innerHTML = (data.summary.key_findings || []).map(f =>
                `<li><i class="fas fa-check-circle" style="color:var(--primary)"></i> ${escapeHtml(f)}</li>`
            ).join('');
            $('analysis-actions').innerHTML = (data.summary.action_items || []).map(a =>
                `<li><i class="fas fa-arrow-right" style="color:var(--amber)"></i> ${escapeHtml(a)}</li>`
            ).join('');
        } else {
            $('analysis-summary-text').textContent = 'AI summary is still being generated.';
        }

        // Risks
        const risksEl = $('analysis-risks');
        const risksEmpty = $('risks-empty');
        if (data.risks && data.risks.length > 0) {
            hide(risksEmpty);
            risksEl.innerHTML = data.risks.map(r => `
                <div class="risk-card risk-card--${r.risk_level.toLowerCase()}">
                    <div class="risk-card-header">
                        <span class="risk-type-badge">${escapeHtml(r.risk_type)}</span>
                        <span class="risk-level-badge risk-level--${r.risk_level.toLowerCase()}">${r.risk_level}</span>
                    </div>
                    <p class="risk-description">${escapeHtml(r.description)}</p>
                    ${r.clause_reference ? `<span class="risk-ref"><i class="fas fa-link"></i> ${escapeHtml(r.clause_reference)}</span>` : ''}
                </div>
            `).join('');
        } else {
            show(risksEmpty);
        }

        // Clauses
        const clausesEl = $('analysis-clauses');
        const clausesEmpty = $('clauses-empty');
        if (data.clauses && data.clauses.length > 0) {
            hide(clausesEmpty);
            clausesEl.innerHTML = data.clauses.map(c => `
                <div class="clause-item">
                    <div class="clause-item-header">
                        <span class="clause-type">${escapeHtml(c.clause_type)}</span>
                        <span class="badge ${c.is_standard ? 'badge-green' : 'badge-amber'}">
                            ${c.is_standard ? 'Standard' : 'Non-Standard'}
                        </span>
                    </div>
                    <p class="clause-text">"${escapeHtml(c.text)}"</p>
                </div>
            `).join('');
        } else {
            show(clausesEmpty);
        }

        // Obligations
        const obligationsEl = $('analysis-obligations');
        const obligationsEmpty = $('obligations-analysis-empty');
        if (data.obligations && data.obligations.length > 0) {
            hide(obligationsEmpty);
            obligationsEl.innerHTML = data.obligations.map(o => `
                <div class="obligation-item">
                    <div class="obligation-left">
                        <strong>${escapeHtml(o.party_responsible)}</strong>
                        <p>${escapeHtml(o.description)}</p>
                    </div>
                    <div class="obligation-right">
                        ${o.deadline ? `<span class="obligation-date"><i class="fas fa-calendar"></i> ${formatDate(o.deadline)}</span>` : ''}
                        <span class="badge ${o.status === 'completed' ? 'badge-green' : 'badge-outline'}">${o.status}</span>
                    </div>
                </div>
            `).join('');
        } else {
            show(obligationsEmpty);
        }

    } catch (err) {
        console.error('Analysis error:', err);
        $('analysis-summary-text').textContent = 'Could not load analysis. Ensure the backend is running.';
    }
}

// Back button
$('btn-back-analysis').addEventListener('click', () => navigateTo('documents'));

// Download report (placeholder)
$('btn-download-report').addEventListener('click', () => {
    showToast('Report generation requires a running backend. Connect your OpenAI API key for full reports.', 'info');
});

// Q&A
$('btn-qa-ask').addEventListener('click', askQuestion);
$('qa-input').addEventListener('keydown', (e) => { if (e.key === 'Enter') askQuestion(); });

async function askQuestion() {
    const q = $('qa-input').value.trim();
    if (!q || !currentDocId) return;

    const answerEl = $('qa-answer');
    const answerText = $('qa-answer-text');
    show(answerEl);
    answerText.textContent = 'Thinking…';
    $('btn-qa-ask').disabled = true;

    try {
        const res = await fetch(`${API_URL}/documents/${currentDocId}/ask/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question: q })
        });
        const data = await res.json();
        answerText.textContent = data.answer || 'No answer returned.';
    } catch {
        answerText.textContent = 'Could not reach the AI service. Is the backend running?';
    } finally {
        $('btn-qa-ask').disabled = false;
    }
}

// ============================================================
// OBLIGATIONS VIEW
// ============================================================
async function loadObligations() {
    const timeline = $('obligations-timeline');
    const empty = $('obligations-empty');
    timeline.innerHTML = '<div class="skeleton skeleton-text"></div>'.repeat(3);

    try {
        const res = await fetch(`${API_URL}/obligations/`);
        const obligations = await res.json();
        renderObligations(obligations, 'all');

        // Filter buttons
        document.querySelectorAll('.btn-filter').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.btn-filter').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                renderObligations(obligations, btn.dataset.filter);
            });
        });
    } catch {
        timeline.innerHTML = '<p style="color:var(--text-muted);text-align:center">Could not load obligations.</p>';
    }
}

function renderObligations(obligations, filter) {
    const timeline = $('obligations-timeline');
    const empty = $('obligations-empty');

    let filtered = obligations;
    if (filter !== 'all') filtered = obligations.filter(o => o.status === filter);

    if (filtered.length === 0) {
        timeline.innerHTML = '';
        show(empty);
        return;
    }
    hide(empty);

    timeline.innerHTML = filtered.map(o => {
        const isOverdue = o.deadline && new Date(o.deadline) < new Date() && o.status !== 'completed';
        return `
        <div class="timeline-item ${isOverdue ? 'timeline-item--overdue' : ''}">
            <div class="timeline-dot ${o.status === 'completed' ? 'timeline-dot--done' : isOverdue ? 'timeline-dot--overdue' : ''}"></div>
            <div class="glass-card timeline-card">
                <div class="timeline-header">
                    <strong>${escapeHtml(o.party_responsible)}</strong>
                    <span class="badge ${o.status === 'completed' ? 'badge-green' : isOverdue ? 'badge-red' : 'badge-outline'}">${isOverdue ? 'Overdue' : o.status}</span>
                </div>
                <p class="timeline-desc">${escapeHtml(o.description)}</p>
                ${o.deadline ? `<span class="timeline-date"><i class="fas fa-calendar-alt"></i> Due: ${formatDate(o.deadline)}</span>` : ''}
            </div>
        </div>`;
    }).join('');
}

// ============================================================
// SEARCH VIEW
// ============================================================
$('btn-global-search').addEventListener('click', doSearch);
$('global-search-input').addEventListener('keydown', (e) => { if (e.key === 'Enter') doSearch(); });

async function doSearch() {
    const q = $('global-search-input').value.trim();
    if (!q) return;

    const resultsArea = $('search-results-area');
    const searchEmpty = $('search-empty');
    hide(searchEmpty);
    show(resultsArea);
    $('search-list-documents').innerHTML = '<div class="skeleton skeleton-text"></div>';
    $('search-list-clauses').innerHTML = '<div class="skeleton skeleton-text"></div>';
    $('search-list-risks').innerHTML = '<div class="skeleton skeleton-text"></div>';

    try {
        const res = await fetch(`${API_URL}/search/?q=${encodeURIComponent(q)}`);
        const data = await res.json();

        $('search-list-documents').innerHTML = data.documents.length
            ? data.documents.map(d => `
                <div class="search-result-item" onclick="openAnalysis('${d.id}')">
                    <i class="fas fa-file-contract"></i>
                    <div>
                        <strong>${highlight(d.title, q)}</strong>
                        <small>${statusBadge(d.status)} &nbsp; ${formatDate(d.uploaded_at)}</small>
                    </div>
                </div>`).join('')
            : '<p class="no-results">No documents found.</p>';

        $('search-list-clauses').innerHTML = data.clauses.length
            ? data.clauses.map(c => `
                <div class="search-result-item">
                    <i class="fas fa-paragraph"></i>
                    <div>
                        <strong>${escapeHtml(c.clause_type)}</strong>
                        <small>${highlight(c.text.substring(0, 120), q)}…</small>
                    </div>
                </div>`).join('')
            : '<p class="no-results">No clauses found.</p>';

        $('search-list-risks').innerHTML = data.risks.length
            ? data.risks.map(r => `
                <div class="search-result-item">
                    <i class="fas fa-shield-alt"></i>
                    <div>
                        <strong>${escapeHtml(r.risk_type)} — ${r.risk_level}</strong>
                        <small>${highlight(r.description.substring(0, 120), q)}…</small>
                    </div>
                </div>`).join('')
            : '<p class="no-results">No risks found.</p>';

    } catch {
        $('search-list-documents').innerHTML = '<p style="color:var(--red)">Search failed. Is the backend running?</p>';
    }
}

// ============================================================
// COMPARE VIEW
// ============================================================
async function loadCompare() {
    const selA = $('compare-select-a');
    const selB = $('compare-select-b');

    try {
        const res = await fetch(`${API_URL}/versions/`);
        const versions = await res.json();

        const options = versions.map(v => `<option value="${v.id}">${v.id.substring(0, 8)}… — v${v.version_number}</option>`).join('');
        selA.innerHTML = '<option value="">Select version…</option>' + options;
        selB.innerHTML = '<option value="">Select version…</option>' + options;
    } catch {
        selA.innerHTML = '<option value="">Backend offline</option>';
        selB.innerHTML = '<option value="">Backend offline</option>';
    }
}

$('btn-compare').addEventListener('click', async () => {
    const vA = $('compare-select-a').value;
    const vB = $('compare-select-b').value;
    if (!vA || !vB || vA === vB) {
        showToast('Please select two different document versions to compare.', 'info');
        return;
    }

    try {
        const [resA, resB] = await Promise.all([
            fetch(`${API_URL}/versions/${vA}/`),
            fetch(`${API_URL}/versions/${vB}/`),
        ]);
        const [a, b] = await Promise.all([resA.json(), resB.json()]);

        const textA = (a.extracted_text || '').split('\n').filter(Boolean);
        const textB = (b.extracted_text || '').split('\n').filter(Boolean);

        const added = textB.filter(line => !textA.includes(line)).slice(0, 10);
        const removed = textA.filter(line => !textB.includes(line)).slice(0, 10);

        $('compare-added').innerHTML = added.map(l => `<div class="diff-line">${escapeHtml(l)}</div>`).join('') || '<p class="no-results">None detected.</p>';
        $('compare-removed').innerHTML = removed.map(l => `<div class="diff-line">${escapeHtml(l)}</div>`).join('') || '<p class="no-results">None detected.</p>';
        $('compare-modified').innerHTML = '<p class="no-results">Semantic diff requires an AI pipeline (available with OpenAI API key).</p>';

        show($('compare-results'));
        hide($('compare-empty'));
    } catch {
        showToast('Comparison failed. Ensure the backend is running.', 'error');
    }
});

// ============================================================
// UPLOAD MODAL
// ============================================================
function openUploadModal() {
    show($('upload-modal'));
    $('upload-title').value = '';
    $('upload-file').value = '';
    $('file-name-display').textContent = '';
    $('file-drop-zone').classList.remove('dragover');
}

function closeUploadModal() {
    hide($('upload-modal'));
}

// Open modal buttons
[$('btn-upload-top'), $('btn-upload-docs'), $('btn-upload-empty')].forEach(btn => {
    if (btn) btn.addEventListener('click', openUploadModal);
});

$('modal-close').addEventListener('click', closeUploadModal);
$('modal-cancel').addEventListener('click', closeUploadModal);
$('upload-modal').addEventListener('click', (e) => { if (e.target === $('upload-modal')) closeUploadModal(); });

// Drag & Drop
const dropZone = $('file-drop-zone');
dropZone.addEventListener('click', () => $('upload-file').click());

dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('dragover');
});
dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));
dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('dragover');
    if (e.dataTransfer.files.length) {
        $('upload-file').files = e.dataTransfer.files;
        updateFileDisplay($('upload-file').files[0].name);
    }
});

$('upload-file').addEventListener('change', () => {
    if ($('upload-file').files.length) updateFileDisplay($('upload-file').files[0].name);
});

function updateFileDisplay(name) {
    $('file-name-display').textContent = name;
    if (!$('upload-title').value) {
        $('upload-title').value = name.replace(/\.[^.]+$/, '');
    }
}

// Upload submit
$('btn-upload-submit').addEventListener('click', async () => {
    const title = $('upload-title').value.trim();
    const file = $('upload-file').files[0];

    if (!title) { showToast('Please enter a document title.', 'error'); return; }
    if (!file) { showToast('Please select a file to upload.', 'error'); return; }

    const btn = $('btn-upload-submit');
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Uploading…';

    const formData = new FormData();
    formData.append('title', title);
    formData.append('file', file);

    try {
        const res = await fetch(`${API_URL}/documents/`, { method: 'POST', body: formData });
        if (res.ok) {
            const data = await res.json();
            closeUploadModal();
            showToast(`"${data.title}" uploaded! AI processing has started.`, 'success');
            navigateTo('documents');
            // Poll for status updates
            pollDocumentStatus(data.id, data.title);
        } else {
            const err = await res.json().catch(() => ({}));
            showToast(err.detail || 'Upload failed. Check the backend.', 'error');
        }
    } catch {
        showToast('Network error. Is the Django server running on port 8000?', 'error');
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-upload"></i> Upload & Analyze';
    }
});

function pollDocumentStatus(docId, title) {
    let attempts = 0;
    const maxAttempts = 20;
    const interval = setInterval(async () => {
        attempts++;
        if (attempts > maxAttempts) {
            clearInterval(interval);
            return;
        }
        try {
            const res = await fetch(`${API_URL}/documents/${docId}/`);
            const doc = await res.json();
            if (doc.status === 'completed') {
                clearInterval(interval);
                showToast(`Analysis of "${title}" is complete!`, 'success');
                if ($('docs-table-body')) loadDocuments();
            } else if (doc.status === 'failed') {
                clearInterval(interval);
                showToast(`Processing of "${title}" failed. Check server logs.`, 'error');
            }
        } catch { /* ignore polling errors */ }
    }, 3000);
}

// ============================================================
// REFRESH BUTTON
// ============================================================
$('btn-refresh').addEventListener('click', () => {
    const activeNav = document.querySelector('.nav-item.active');
    const view = activeNav ? activeNav.dataset.view : 'dashboard';
    navigateTo(view);
    showToast('Refreshed.', 'success');
});

// ============================================================
// SETTINGS
// ============================================================
$('btn-toggle-key').addEventListener('click', () => {
    const input = $('settings-api-key');
    const icon = $('btn-toggle-key').querySelector('i');
    if (input.type === 'password') {
        input.type = 'text';
        icon.className = 'fas fa-eye-slash';
    } else {
        input.type = 'password';
        icon.className = 'fas fa-eye';
    }
});

// ============================================================
// UTILITY FUNCTIONS
// ============================================================
function escapeHtml(str) {
    if (!str) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}

function highlight(text, query) {
    if (!query) return escapeHtml(text);
    const escaped = escapeHtml(text);
    const re = new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
    return escaped.replace(re, '<mark>$1</mark>');
}

function formatDate(iso) {
    if (!iso) return '—';
    return new Date(iso).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
}

function statusBadge(status) {
    const map = {
        completed: ['badge-green', 'Completed'],
        processing: ['badge-blue', 'Processing'],
        pending: ['badge-amber', 'Pending'],
        failed: ['badge-red', 'Failed'],
    };
    const [cls, label] = map[status] || ['badge-outline', status];
    return `<span class="badge ${cls}">${label}</span>`;
}

function riskBadge(doc) {
    // Placeholder — in a full version this would pull from the analysis endpoint
    return `<span class="badge badge-outline">—</span>`;
}

// ============================================================
// INIT
// ============================================================
(function init() {
    navigateTo('dashboard');
})();
