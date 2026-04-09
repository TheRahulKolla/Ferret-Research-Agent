// ── Theme toggle ──────────────────────────────────────────────────
function toggleTheme() {
    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    document.documentElement.setAttribute('data-theme', isDark ? 'light' : 'dark');
    document.getElementById('theme-icon').textContent  = isDark ? '🌙' : '☀️';
    document.getElementById('theme-label').textContent = isDark ? 'Dark mode' : 'Light mode';
    localStorage.setItem('theme', isDark ? 'light' : 'dark');
}

// Load saved theme
(function() {
    const saved = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', saved);
    if (saved === 'dark') {
        document.addEventListener('DOMContentLoaded', () => {
            document.getElementById('theme-icon').textContent  = '☀️';
            document.getElementById('theme-label').textContent = 'Light mode';
        });
    }
})();

// ── Screen switching ──────────────────────────────────────────────
function showScreen(name, el) {
    document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    document.getElementById('screen-' + name).classList.add('active');
    if (el) el.classList.add('active');
    if (name === 'reports') loadReports();
}

// ── Upload mode toggle ────────────────────────────────────────────
function setMode(mode) {
    document.querySelectorAll('.mode').forEach(m => m.classList.remove('active'));
    document.querySelectorAll('.toggle-btn').forEach(b => b.classList.remove('active'));
    document.getElementById('mode-' + mode).classList.add('active');
    document.getElementById('toggle-' + mode).classList.add('active');
}

// ── Drag & drop ───────────────────────────────────────────────────
function onDragOver(e) {
    e.preventDefault();
    document.getElementById('drop-zone').classList.add('dragover');
}

function onDragLeave() {
    document.getElementById('drop-zone').classList.remove('dragover');
}

function onDrop(e) {
    e.preventDefault();
    document.getElementById('drop-zone').classList.remove('dragover');
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
}

function onFileSelect(input) {
    if (input.files[0]) handleFile(input.files[0]);
}

// ── File handling ─────────────────────────────────────────────────
let loadedTopics = [];

function handleFile(file) {
    const reader = new FileReader();
    reader.onload = e => {
        const lines = e.target.result.split('\n').map(l => l.trim()).filter(Boolean);
        loadedTopics = lines.slice(0, 10);
        showPreview(file.name, loadedTopics);
    };
    reader.readAsText(file);
}

function showPreview(filename, topics) {
    document.getElementById('preview-title').textContent =
        `${filename} · ${topics.length} topic${topics.length !== 1 ? 's' : ''} detected`;

    const grid = document.getElementById('topics-grid');
    grid.innerHTML = topics.map((t, i) =>
        `<div class="topic-chip">
            <span class="topic-num">${i + 1}</span>
            <span>${t}</span>
        </div>`
    ).join('');

    document.getElementById('topics-preview').style.display = 'block';
    document.getElementById('drop-zone').style.display = 'none';
}

function clearFile() {
    loadedTopics = [];
    document.getElementById('topics-preview').style.display = 'none';
    document.getElementById('drop-zone').style.display = 'block';
    document.getElementById('file-input').value = '';
}

// ── Run single topic ──────────────────────────────────────────────
function runSingle() {
    const query = document.getElementById('single-input').value.trim();
    if (!query) return;
    uploadTopics([query]);
}

// ── Run batch ─────────────────────────────────────────────────────
function runBatch() {
    if (!loadedTopics.length) return;
    uploadTopics(loadedTopics);
}

function uploadTopics(topics) {
    const blob = new Blob([topics.join('\n')], { type: 'text/plain' });
    const formData = new FormData();
    formData.append('file', blob, 'topics.txt');

    fetch('/upload', { method: 'POST', body: formData })
        .then(r => r.json())
        .then(data => {
            if (data.error) { alert('Error: ' + data.error); return; }
            initProgress(data.topics);
            document.querySelector('.nav-item:nth-child(2)').click();
            listenSSE();
        })
        .catch(() => alert('Upload failed.'));
}

// ── Progress ──────────────────────────────────────────────────────
let stats = { done: 0, running: 0, queued: 0 };

function initProgress(topics) {
    stats = { done: 0, running: topics.length, queued: topics.length };
    updateStats();

    document.getElementById('progress-subtitle').textContent =
        `${topics.length} topic${topics.length !== 1 ? 's' : ''} · running in parallel`;

    const list = document.getElementById('progress-list');
    list.innerHTML = topics.map(topic => {
        const id = topicId(topic);
        return `
        <div class="progress-item" id="${id}">
            <div class="progress-info">
                <div class="progress-topic">${topic}</div>
                <div class="progress-hint">Queued...</div>
            </div>
            <span class="status-pill pill-queued">queued</span>
            <div>
                <div class="progress-bar-wrap">
                    <div class="progress-bar bar-queued"></div>
                </div>
            </div>
            <span class="progress-pct">0%</span>
        </div>`;
    }).join('');
}

function updateStats() {
    document.getElementById('stat-done').textContent = stats.done;
    document.getElementById('stat-running').textContent = stats.running;
    document.getElementById('stat-queued').textContent = stats.queued;
}

function topicId(topic) {
    return 'prog-' + btoa(encodeURIComponent(topic)).replace(/[^a-zA-Z0-9]/g, '');
}

// ── SSE ───────────────────────────────────────────────────────────
function listenSSE() {
    const es = new EventSource('/status');
    es.onmessage = e => {
        const ev = JSON.parse(e.data);
        const item = document.getElementById(topicId(ev.topic));

        if (ev.event === 'progress' && item) {
            const pct = ev.data.pct;
            item.querySelector('.progress-bar').style.width = pct + '%';
            item.querySelector('.progress-pct').textContent = pct + '%';
            item.querySelector('.progress-hint').textContent =
                `Iteration ${ev.data.iteration} of ${ev.data.max_iterations}`;
        }

        if (ev.event === 'started' && item) {
            item.querySelector('.progress-hint').textContent = 'Running research...';
            item.querySelector('.progress-hint').className = 'progress-hint blue';
            item.querySelector('.status-pill').className = 'status-pill pill-running';
            item.querySelector('.status-pill').textContent = 'running';
            item.querySelector('.progress-bar').className = 'progress-bar bar-running';
            item.querySelector('.progress-bar').style.width = '40%';
            item.querySelector('.progress-pct').textContent = '40%';
            stats.queued = Math.max(0, stats.queued - 1);
            updateStats();
        }

        if (ev.event === 'done' && item) {
            item.querySelector('.progress-hint').textContent = `Report saved · ${ev.data.duration_sec}s`;
            item.querySelector('.progress-hint').className = 'progress-hint green';
            item.querySelector('.status-pill').className = 'status-pill pill-done';
            item.querySelector('.status-pill').textContent = 'done';
            item.querySelector('.progress-bar').className = 'progress-bar bar-done';
            item.querySelector('.progress-bar').style.width = '100%';
            item.querySelector('.progress-pct').textContent = '100%';
            stats.running = Math.max(0, stats.running - 1);
            stats.done += 1;
            updateStats();
        }

        if (ev.event === 'failed' && item) {
            item.querySelector('.progress-hint').textContent = 'Failed: ' + ev.data.error;
            item.querySelector('.status-pill').className = 'status-pill pill-failed';
            item.querySelector('.status-pill').textContent = 'failed';
            item.querySelector('.progress-bar').className = 'progress-bar bar-failed';
            item.querySelector('.progress-bar').style.width = '100%';
            item.querySelector('.progress-pct').textContent = '—';
            stats.running = Math.max(0, stats.running - 1);
            updateStats();
        }

        if (ev.event === 'batch_complete') {
            es.close();
            loadReports();
        }
    };
}

// ── Reports ───────────────────────────────────────────────────────
function loadReports() {
    const now = new Date();
    document.getElementById('reports-date').textContent =
        now.toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });

    fetch('/reports')
        .then(r => r.json())
        .then(data => {
            const tbody = document.getElementById('reports-tbody');
            document.getElementById('reports-count').textContent = data.reports.length;

            if (!data.reports.length) {
                tbody.innerHTML = '<tr><td colspan="5" class="empty-msg">No reports yet.</td></tr>';
                return;
            }

            tbody.innerHTML = data.reports.map(f => {
                const parts = f.replace('.docx', '').split('_');
                const dateStr = parts.slice(-2).join('_');
                return `
                <tr>
                    <td>
                        <div class="file-name-cell">
                            <div class="file-icon"><div class="file-icon-inner"></div></div>
                            <span>${f}</span>
                        </div>
                    </td>
                    <td style="color:#6B7280;font-size:0.82rem">${dateStr}</td>
                    <td style="color:#6B7280;font-size:0.82rem">—</td>
                    <td><span class="pill-docx">.docx</span></td>
                    <td>
                        <div class="table-actions">
                            <a href="/download/${f}" download class="btn-primary" style="font-size:0.8rem;padding:0.35rem 0.8rem;text-decoration:none">Download</a>
                            <button class="btn-outline" style="font-size:0.8rem;padding:0.35rem 0.8rem" onclick="openPreview('${f}')">Preview</button>
                        </div>
                    </td>
                </tr>`;
            }).join('');
        });
}

function downloadAll() {
    alert('Download all as .zip coming soon.');
}

// ── Preview modal ─────────────────────────────────────────────────
function openPreview(filename) {
    fetch(`/preview/${filename}`)
        .then(r => r.json())
        .then(data => {
            if (data.error) { alert('Preview failed: ' + data.error); return; }
            document.getElementById('modal-filename').textContent = data.filename;
            document.getElementById('modal-body').textContent = data.content;
            document.getElementById('preview-modal').style.display = 'flex';
        });
}

function closePreview(e) {
    if (!e || e.target.id === 'preview-modal') {
        document.getElementById('preview-modal').style.display = 'none';
    }
}

// ── Settings ──────────────────────────────────────────────────────
const counterLimits = { subqueries: [1, 5], iterations: [3, 20], concurrent: [1, 10] };

function adjustCounter(id, delta) {
    const el = document.getElementById(id + '-val');
    const [min, max] = counterLimits[id];
    const newVal = Math.min(max, Math.max(min, parseInt(el.textContent) + delta));
    el.textContent = newVal;
    el.style.transform = 'scale(1.3)';
    setTimeout(() => el.style.transform = 'scale(1)', 150);
}

function toggleShow(inputId, btn) {
    const input = document.getElementById(inputId);
    const isHidden = input.type === 'password';
    input.type = isHidden ? 'text' : 'password';
    btn.textContent = isHidden ? 'Hide' : 'Show';
}

function saveKey(provider) {
    const key = document.getElementById(provider + '-key').value.trim();
    const statusEl = document.getElementById(provider + '-status');
    if (!key) {
        showKeyStatus(statusEl, 'error', 'Please enter a key');
        return;
    }
    fetch('/save-key', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ provider, key })
    })
    .then(r => r.json())
    .then(data => {
        if (data.error) showKeyStatus(statusEl, 'error', data.error);
        else showKeyStatus(statusEl, 'success', 'Key saved · validated successfully');
    })
    .catch(() => showKeyStatus(statusEl, 'error', 'Failed to save key'));
}

function showKeyStatus(el, type, msg) {
    el.className = 'key-status ' + type;
    el.textContent = msg;
    el.style.display = 'flex';
}

function saveConfig() {
    const config = {
        max_subqueries: parseInt(document.getElementById('subqueries-val').textContent),
        max_iterations: parseInt(document.getElementById('iterations-val').textContent),
        max_concurrent: parseInt(document.getElementById('concurrent-val').textContent)
    };
    fetch('/save-config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config)
    })
    .then(r => r.json())
    .then(data => {
        const el = document.getElementById('config-status');
        el.textContent = data.error ? '✗ ' + data.error : '✓ Configuration saved';
        el.className = 'config-status show';
        setTimeout(() => el.classList.remove('show'), 2500);
    });
}

function clearReports() {
    if (!confirm('Delete all reports? This cannot be undone.')) return;
    fetch('/clear-reports', { method: 'POST' })
        .then(r => r.json())
        .then(data => alert(data.message || data.error));
}

// Load saved settings on page load
function loadSettings() {
    fetch('/get-settings')
        .then(r => r.json())
        .then(data => {
            if (data.max_subqueries) document.getElementById('subqueries-val').textContent = data.max_subqueries;
            if (data.max_iterations) document.getElementById('iterations-val').textContent = data.max_iterations;
            if (data.max_concurrent) document.getElementById('concurrent-val').textContent = data.max_concurrent;
            if (data.has_anthropic)  showKeyStatus(document.getElementById('anthropic-status'), 'success', 'Key saved · validated successfully');
            if (data.has_tavily)     showKeyStatus(document.getElementById('tavily-status'), 'success', 'Key saved · validated successfully');
        });
}

// Init
document.getElementById('reports-date') && loadReports();
loadSettings();
