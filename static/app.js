// LeadPilot — the UI. It shows what the backend sends; the server is the source of truth for every lead.
(() => {
  'use strict';
  const $ = (id) => document.getElementById(id);

  // ---------- icons (lucide, MIT) ----------
  const P = {
    dashboard: '<rect x="3" y="3" width="7" height="9" rx="1"/><rect x="14" y="3" width="7" height="5" rx="1"/><rect x="14" y="12" width="7" height="9" rx="1"/><rect x="3" y="16" width="7" height="5" rx="1"/>',
    list: '<path d="M3 12h.01M3 18h.01M3 6h.01M8 12h13M8 18h13M8 6h13"/>',
    columns: '<rect width="18" height="18" x="3" y="3" rx="2"/><path d="M9 3v18M15 3v18"/>',
    inbox: '<path d="M22 12h-6l-2 3h-4l-2-3H2"/><path d="M5.45 5.11 2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z"/>',
    sparkles: '<path d="M9.94 14.06 8 20l-1.94-5.94L0 12l6.06-1.94L8 4l1.94 6.06L16 12z" transform="translate(3 -1) scale(.85)"/><path d="M20 3v4M22 5h-4M19 17v3M20.5 18.5h-3"/>',
    template: '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/><path d="M13 8H7M17 12H7"/>',
    refresh: '<path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/><path d="M8 16H3v5"/>',
    download: '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><path d="m7 10 5 5 5-5M12 15V3"/>',
    moon: '<path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"/>',
    sun: '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2m-7.07-14.07 1.41 1.41m11.32 11.32 1.41 1.41M2 12h2m16 0h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41"/>',
    logout: '<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><path d="m16 17 5-5-5-5M21 12H9"/>',
    plus: '<path d="M5 12h14M12 5v14"/>',
    x: '<path d="M18 6 6 18M6 6l12 12"/>',
    users: '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/>',
    workflow: '<rect width="8" height="8" x="3" y="3" rx="2"/><path d="M7 11v4a2 2 0 0 0 2 2h4"/><rect width="8" height="8" x="13" y="13" rx="2"/>',
    flame: '<path d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.07-2.14-.22-4.05 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.15.43-2.29 1-3a2.5 2.5 0 0 0 2.5 2.5z"/>',
    check: '<path d="M21.8 10A10 10 0 1 1 17 3.34"/><path d="m9 11 3 3L22 4"/>',
    phoneOff: '<path d="M10.68 13.31a16 16 0 0 0 3.41 2.6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7 2 2 0 0 1 1.72 2v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.42 19.42 0 0 1-3.33-2.67m-2.67-3.34a19.79 19.79 0 0 1-3.07-8.63A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91"/><path d="M22 2 2 22"/>',
    alert: '<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3"/><path d="M12 9v4M12 17h.01"/>',
    wa: '<path d="M7.9 20A9 9 0 1 0 4 16.1L2 22z"/>',
    phone: '<path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/>',
    search: '<circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>',
    send: '<path d="m22 2-7 20-4-9-9-4Z"/><path d="M22 2 11 13"/>',
    copy: '<rect width="14" height="14" x="8" y="8" rx="2"/><path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"/>',
    clock: '<circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/>',
    database: '<ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M3 5v14a9 3 0 0 0 18 0V5"/><path d="M3 12a9 3 0 0 0 18 0"/>',
    msg: '<path d="M7.9 20A9 9 0 1 0 4 16.1L2 22z"/>',
    edit: '<path d="M12 20h9"/><path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4Z"/>',
    star: '<path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01z"/>',
    paperclip: '<path d="m21.44 11.05-9.19 9.19a6 6 0 0 1-8.49-8.49l8.57-8.57A4 4 0 1 1 18 8.84l-8.59 8.57a2 2 0 0 1-2.83-2.83l8.49-8.48"/>',
    sort: '<path d="m21 16-4 4-4-4M17 20V4M3 8l4-4 4 4M7 4v16"/>',
  };
  const ic = (n, cls = '') => `<svg class="icon ${cls}" viewBox="0 0 24 24" aria-hidden="true">${P[n] || ''}</svg>`;
  const paintIcons = (root = document) => root.querySelectorAll('[data-i]').forEach((el) => { el.outerHTML = ic(el.dataset.i); });

  // ---------- state ----------
  const EMPTY_FILTERS = { q: '', stage: '', status: '', hot: false, stale: false, dup: false, reply: false };
  const S = {
    user: null, meta: null, leads: [], templates: [], syncedAt: null, loading: false,
    tab: readPref('tab', 'overview'), filters: { ...EMPTY_FILTERS }, sort: { key: 'created_at', dir: -1 },
    openId: null, openDetail: null, inboxId: null, drafts: {}, tone: 'friendly',
    chat: { conversations: [], current: null, streaming: false, image: null, messages: [] },
  };
  function readPref(k, d) { try { return localStorage.getItem('lp.' + k) || d; } catch (_) { return d; } }
  function writePref(k, v) { try { localStorage.setItem('lp.' + k, v); } catch (_) {} }

  // ---------- helpers ----------
  const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const pct = (n) => `${Math.round((n || 0) * 100)}%`;
  const statusDef = (id) => S.meta.statuses.find((s) => s.id === id);
  const stageDef = (id) => S.meta.stages.find((s) => s.id === id);
  const leadById = (id) => S.leads.find((l) => l.id === id);
  const toast = (text) => { const t = document.createElement('div'); t.className = 'toast'; t.textContent = text; document.body.appendChild(t); setTimeout(() => t.remove(), 2600); };

  async function api(path, options = {}) {
    const res = await fetch(path, { headers: { 'Content-Type': 'application/json' }, credentials: 'same-origin', ...options });
    if (res.status === 401) { showLogin(); throw new Error('יש להתחבר.'); }
    if (!res.ok) {
      let detail = res.statusText;
      try { const j = await res.json(); detail = typeof j.detail === 'string' ? j.detail : (j.detail?.[0]?.msg || JSON.stringify(j.detail)); } catch (_) {}
      throw new Error(detail);
    }
    return res.status === 204 ? null : res.json();
  }
  function showError(msg) { $('error-text').textContent = msg; $('error').classList.remove('hidden'); }
  $('error-close').onclick = () => $('error').classList.add('hidden');

  function relDay(iso) {
    const d = new Date(iso + 'Z'); const now = new Date();
    const days = Math.floor((new Date(now.toDateString()) - new Date(d.toDateString())) / 86400000);
    if (days <= 0) return 'היום'; if (days === 1) return 'אתמול'; return `לפני ${days} ימים`;
  }
  function relTime(iso) {
    const mins = Math.round((Date.now() - new Date(iso + 'Z')) / 60000);
    if (mins < 1) return 'עכשיו'; if (mins < 60) return `לפני ${mins} דק׳`;
    const h = Math.round(mins / 60); if (h < 24) return `לפני ${h} שע׳`;
    return relDay(iso);
  }
  const waLink = (lead, text = '') => `https://wa.me/${lead.phone_norm}${text ? '?text=' + encodeURIComponent(text) : ''}`;
  const latestText = (l) => l.last_update || l.second_attempt || l.first_attempt || '';
  const badge = (l) => l.status ? `<span class="badge t-${statusDef(l.status).tone}">${esc(statusDef(l.status).label)}</span>` : '<span class="badge t-gray">ללא סטטוס</span>';
  const stageBadge = (id) => `<span class="badge stage t-${stageDef(id).tone}">${esc(stageDef(id).label)}</span>`;
  const phoneHtml = (l) => `<span class="ltr num">${esc(l.phone_display)}</span>`;
  const nameHtml = (l) => `${l.hot ? '🔥 ' : ''}${esc(l.name || 'ללא שם')}`;

  // ---------- auth ----------
  function showLogin() { $('login').classList.remove('hidden'); $('app').classList.add('hidden'); $('login-name').focus(); }
  $('login-form').addEventListener('submit', async (e) => {
    e.preventDefault(); $('login-error').textContent = '';
    try {
      S.user = await api('/api/login', { method: 'POST', body: JSON.stringify({ name: $('login-name').value.trim(), password: $('login-password').value }) });
      $('login-password').value = ''; await boot();
    } catch (err) { $('login-error').textContent = err.message; }
  });
  $('btn-logout').onclick = async () => { await api('/api/logout', { method: 'POST' }).catch(() => {}); S.user = null; showLogin(); };

  // ---------- theme ----------
  function paintTheme() { const dark = document.documentElement.classList.contains('dark'); $('btn-theme').innerHTML = ic(dark ? 'sun' : 'moon'); $('btn-theme').setAttribute('aria-label', dark ? 'מצב בהיר' : 'מצב כהה'); }
  $('btn-theme').onclick = () => { const dark = document.documentElement.classList.toggle('dark'); try { localStorage.setItem('theme', dark ? 'dark' : 'light'); } catch (_) {} paintTheme(); };

  // ---------- data ----------
  async function loadLeads() {
    S.loading = true; paintRefresh();
    try {
      const [data, tpls] = await Promise.all([api('/api/leads'), S.templates.length ? Promise.resolve(S.templates) : api('/api/templates')]);
      S.leads = data.leads; S.syncedAt = new Date(); S.templates = tpls;
    } catch (err) { showError(err.message); }
    finally { S.loading = false; paintRefresh(); renderHeader(); renderTabs(); render(); }
  }
  function paintRefresh() { $('btn-refresh').innerHTML = ic('refresh', S.loading ? 'spin' : '') + '<span class="lbl-txt">רענון</span>'; $('btn-refresh').disabled = S.loading; }
  $('btn-refresh').onclick = loadLeads;

  function replaceLead(detail) {
    const i = S.leads.findIndex((l) => l.id === detail.id);
    const dup = S.leads.filter((l) => l.phone_norm === detail.phone_norm && l.id !== detail.id).length > 0;
    const slim = { ...detail, duplicate: dup }; delete slim.activity; delete slim.recommended_template;
    if (i >= 0) S.leads[i] = slim; else S.leads.unshift(slim);
  }

  // ---------- metrics (client side, same rules as the server) ----------
  function metrics(leads) {
    const m = { total: leads.length, byStage: {}, byStatus: {}, hot: 0, stale: 0, paid: 0, reply: 0, noName: 0, noStatus: 0 };
    S.meta.stages.forEach((s) => (m.byStage[s.id] = 0)); S.meta.statuses.forEach((s) => (m.byStatus[s.id] = 0));
    for (const l of leads) {
      m.byStage[l.stage]++; if (l.status) m.byStatus[l.status]++; else m.noStatus++;
      m.hot += l.hot; m.stale += l.stale; m.paid += l.paid; m.reply += l.needs_reply; m.noName += !l.name;
    }
    m.active = m.byStage.new + m.byStage.engaged + m.byStage.closing;
    m.won = m.byStage.won; m.lost = m.byStage.lost; m.paused = m.byStage.paused;
    m.conversion = m.total ? m.won / m.total : 0; m.winRate = m.won + m.lost ? m.won / (m.won + m.lost) : 0;
    const groups = {}; leads.forEach((l) => (groups[l.phone_norm] = [...(groups[l.phone_norm] || []), l]));
    m.duplicates = Object.values(groups).filter((g) => g.length > 1);
    return m;
  }

  function applyFilters(leads) {
    const f = S.filters; const q = f.q.trim().toLowerCase(); const digits = q.replace(/\D/g, '');
    let qn = digits; if (qn.startsWith('0')) qn = '972' + qn.slice(1);
    return leads.filter((l) => {
      if (f.stage === 'active' && !['new', 'engaged', 'closing'].includes(l.stage)) return false;
      if (f.stage && f.stage !== 'active' && l.stage !== f.stage) return false;
      if (f.status === '__none' && l.status) return false;
      if (f.status && f.status !== '__none' && l.status !== f.status) return false;
      if (f.hot && !l.hot) return false; if (f.stale && !l.stale) return false;
      if (f.dup && !l.duplicate) return false; if (f.reply && !l.needs_reply) return false;
      if (q) {
        const hay = [l.name, l.first_attempt, l.second_attempt, l.last_update, l.notes, l.last_incoming, l.source].join(' ').toLowerCase();
        const phoneHit = digits.length >= 3 && (l.phone_norm.includes(digits) || l.phone_norm.includes(qn));
        if (!hay.includes(q) && !phoneHit) return false;
      }
      return true;
    });
  }
  function sorted(leads) {
    const { key, dir } = S.sort; const order = S.meta.statuses.map((s) => s.id);
    return [...leads].sort((a, b) => {
      let x, y;
      if (key === 'status') { x = a.status ? order.indexOf(a.status) : 99; y = b.status ? order.indexOf(b.status) : 99; }
      else if (key === 'name') { x = a.name || 'תתת'; y = b.name || 'תתת'; return dir * x.localeCompare(y, 'he'); }
      else { x = a[key]; y = b[key]; }
      return x < y ? -dir : x > y ? dir : 0;
    });
  }

  // ---------- header + tabs ----------
  const TABS = [
    { id: 'overview', label: 'סקירה', icon: 'dashboard' },
    { id: 'leads', label: 'לידים', icon: 'list' },
    { id: 'board', label: 'לוח', icon: 'columns' },
    { id: 'inbox', label: 'מענה חכם', icon: 'inbox', count: () => S.leads.filter((l) => l.needs_reply).length },
    { id: 'assistant', label: 'עוזר AI', icon: 'sparkles' },
    { id: 'templates', label: 'תבניות וואטסאפ', icon: 'template' },
  ];
  function renderHeader() {
    const ai = S.meta.ai === 'anthropic'
      ? `<span class="pill ai">${ic('sparkles')} מענה חכם: Claude</span>`
      : `<span class="pill off" title="הגדירו ANTHROPIC_API_KEY כדי להפעיל את Claude">${ic('sparkles')} מענה חכם: מצב כללים (אופליין)</span>`;
    $('subline').innerHTML = `${ic('database')}<span>${esc(S.meta.business)}</span>${ai}${S.syncedAt ? `<span>· עודכן ${S.syncedAt.toLocaleTimeString('he-IL', { hour: '2-digit', minute: '2-digit' })}</span>` : ''}<span>· ${esc(S.user.name)}</span>`;
  }
  function renderTabs() {
    $('tabs').innerHTML = TABS.map((t) => {
      const c = t.count ? t.count() : 0;
      return `<button class="tab" role="tab" data-tab="${t.id}" aria-selected="${S.tab === t.id}">${ic(t.icon)} ${t.label}${c ? ` <span class="count num">${c}</span>` : ''}</button>`;
    }).join('');
  }
  function setTab(id) { S.tab = id; writePref('tab', id); renderTabs(); render(); window.scrollTo({ top: 0 }); }
  $('tabs').addEventListener('click', (e) => { const b = e.target.closest('[data-tab]'); if (b) setTab(b.dataset.tab); });

  // ---------- views ----------
  function render() {
    const v = $('view');
    if (!S.meta) return;
    if (S.loading && !S.leads.length) { v.innerHTML = `<div class="kpis">${'<div class="skeleton"></div>'.repeat(6)}</div>`; return; }
    if (S.tab !== 'assistant') S.chatMounted = false;
    ({ overview: viewOverview, leads: viewLeads, board: viewBoard, inbox: viewInbox, assistant: viewAssistant, templates: viewTemplates }[S.tab] || viewOverview)(v);
  }

  function tile(icon, label, value, sub, filter) {
    return `<button class="tile" data-filter='${JSON.stringify(filter)}'><div class="lbl">${ic(icon)}${label}</div><div class="val">${value}</div>${sub ? `<div class="sub2">${sub}</div>` : ''}</button>`;
  }
  function bars(items, total, kind) {
    const max = Math.max(1, ...items.map((i) => i.value));
    return `<ul class="bars">${items.map((i) => `<li><button class="bar" data-bar-${kind}="${i.key}" data-tipt="${esc(i.label)} · ${i.value} לידים · ${total ? Math.round(i.value / total * 100) : 0}% מהסך" aria-label="${esc(i.label)}: ${i.value}">
      <span class="l">${esc(i.label)}</span><span class="track"><span class="fill ${i.muted ? 'm' : ''}" style="width:${i.value / max * 100}%;min-width:${i.value ? 3 : 0}px"></span></span><span class="v">${i.value}</span></button></li>`).join('')}</ul>`;
  }

  function leadRow(l, { showIncoming = false } = {}) {
    const snip = showIncoming && l.last_incoming ? `💬 ${l.last_incoming}` : latestText(l);
    return `<li class="row-lead">
      <button class="who" data-open="${l.id}"><strong>${nameHtml(l)}</strong> · ${phoneHtml(l)} ${badge(l)}
        <div class="next">← ${esc(l.next_action)}</div>${snip ? `<div class="snip">${esc(snip)}</div>` : ''}</button>
      <div class="actions">${l.needs_reply ? `<button class="btn primary sm" data-reply="${l.id}">${ic('sparkles')}מענה חכם</button>` : ''}
        <a class="btn wa sm" href="${waLink(l)}" target="_blank" rel="noreferrer" aria-label="וואטסאפ ל${esc(l.name)}">${ic('wa')}וואטסאפ</a></div></li>`;
  }

  function viewOverview(v) {
    const m = metrics(S.leads);
    const prio = (l) => (l.status === 'callback' || l.status === 'call_scheduled' ? 0 : l.stage === 'closing' ? 1 : 2);
    const hot = S.leads.filter((l) => l.hot).sort((a, b) => prio(a) - prio(b)).slice(0, 8);
    const waiting = S.leads.filter((l) => l.needs_reply).slice(0, 6);
    v.innerHTML = `<div class="stack">
      <div class="kpis">
        ${tile('users', 'סה״כ לידים', m.total, m.noName ? `${m.noName} בלי שם` : '', {})}
        ${tile('workflow', 'בתהליך פעיל', m.active, m.stale ? `${m.stale} לא עודכנו מעל 3 ימים` : 'כולם עודכנו לאחרונה', { stage: 'active' })}
        ${tile('flame', 'חמים לטיפול', m.hot, `${m.reply} ממתינים למענה`, { hot: true })}
        ${tile('check', 'נסגרו', m.won, `המרה ${pct(m.conversion)} · ${m.paid} שולמו`, { stage: 'won' })}
        ${tile('phoneOff', 'תקועים / מושהים', m.paused, `${m.byStatus.no_response} לא מגיבים`, { stage: 'paused' })}
        ${tile('alert', 'אבודים', m.lost, `שיעור זכייה מההוכרעו ${pct(m.winRate)}`, { stage: 'lost' })}
      </div>
      <div class="g2">
        <section class="card"><header><h2>משפך מכירה לפי שלב</h2><span class="muted" style="font-size:12px">המרה כוללת ${pct(m.conversion)}</span></header>
          ${bars(S.meta.stages.map((s) => ({ key: s.id, label: s.label, value: m.byStage[s.id], muted: !s.active })), m.total, 'stage')}</section>
        <section class="card"><header><h2>פילוח לפי סטטוס</h2></header>
          ${bars(S.meta.statuses.map((s) => ({ key: s.id, label: s.label, value: m.byStatus[s.id], muted: !stageDef(s.stage).active })).filter((i) => i.value).sort((a, b) => b.value - a.value), m.total, 'status')}</section>
      </div>
      <div class="g2">
        <section class="card"><header><h2>${ic('flame')} לטיפול היום</h2><button class="btn ghost sm" data-filter='{"hot":true}'>לכל החמים</button></header>
          ${hot.length ? `<ul class="list">${hot.map((l) => leadRow(l)).join('')}</ul>` : '<p class="empty-state">אין לידים חמים כרגע 🎉</p>'}</section>
        <div class="stack">
          <section class="card"><header><h2>${ic('inbox')} ממתינים למענה</h2><button class="btn ghost sm" data-tab-go="inbox">לתיבת המענה</button></header>
            ${waiting.length ? `<ul class="list">${waiting.map((l) => leadRow(l, { showIncoming: true })).join('')}</ul>` : '<p class="empty-state">כל ההודעות נענו ✅</p>'}</section>
          <section class="card"><header><h2>איכות נתונים ומעקב</h2></header><div class="dq">
            <button class="dq-item" data-filter='{"stale":true}'><span>⏳ לידים פעילים שלא עודכנו מעל 3 ימים</span><b>${m.stale}</b></button>
            <button class="dq-item" data-filter='{"dup":true}'><span>👥 מספרים כפולים ${m.duplicates.length ? `<span class="muted">(${m.duplicates.map((g) => `<span class="ltr">${esc(g[0].phone_display)}</span>`).join(', ')})</span>` : ''}</span><b>${m.duplicates.length}</b></button>
            <button class="dq-item" data-filter='{"q":""}' data-noname="1"><span>❔ לידים בלי שם</span><b>${m.noName}</b></button>
            <button class="dq-item" data-filter='{"status":"__none"}'><span>🏷️ לידים בלי סטטוס</span><b>${m.noStatus}</b></button>
          </div></section>
        </div>
      </div></div>`;
  }

  function filterBar(count) {
    const f = S.filters;
    const opt = (val, label, cur) => `<option value="${val}" ${cur === val ? 'selected' : ''}>${esc(label)}</option>`;
    return `<div class="filters">
      <label class="search">${ic('search')}<input class="input" id="f-q" type="search" placeholder="חיפוש: שם, טקסט או טלפון" value="${esc(f.q)}" aria-label="חיפוש"></label>
      <select class="input" id="f-stage" aria-label="שלב">${opt('', 'כל השלבים', f.stage)}${opt('active', 'פעילים בלבד', f.stage)}${S.meta.stages.map((s) => opt(s.id, s.label, f.stage)).join('')}</select>
      <select class="input" id="f-status" aria-label="סטטוס">${opt('', 'כל הסטטוסים', f.status)}${S.meta.statuses.map((s) => opt(s.id, s.label, f.status)).join('')}${opt('__none', 'ללא סטטוס', f.status)}</select>
      <button class="toggle" data-toggle="hot" aria-pressed="${f.hot}">🔥 חמים</button>
      <button class="toggle" data-toggle="reply" aria-pressed="${f.reply}">💬 ממתינים</button>
      <button class="toggle" data-toggle="stale" aria-pressed="${f.stale}">⏳ לא עודכנו</button>
      <button class="toggle" data-toggle="dup" aria-pressed="${f.dup}">👥 כפולים</button>
      <button class="btn ghost sm" data-clear="1">ניקוי</button>
      <span class="result num">${count} תוצאות</span></div>`;
  }
  function bindFilterInputs() {
    const q = $('f-q');
    if (q) q.oninput = () => { S.filters.q = q.value; const pos = q.selectionStart; render(); const n = $('f-q'); n.focus(); n.setSelectionRange(pos, pos); };
    if ($('f-stage')) $('f-stage').onchange = (e) => { S.filters.stage = e.target.value; render(); };
    if ($('f-status')) $('f-status').onchange = (e) => { S.filters.status = e.target.value; render(); };
  }

  function viewLeads(v) {
    let rows = sorted(applyFilters(S.leads));
    if (S.noNameOnly) rows = rows.filter((l) => !l.name);
    const sortBtn = (key, label) => `<button data-sort="${key}">${label} ${S.sort.key === key ? (S.sort.dir < 0 ? '↓' : '↑') : ic('sort')}</button>`;
    v.innerHTML = `<div class="stack">${filterBar(rows.length)}
      <div class="table-wrap"><table><thead><tr><th>${sortBtn('name', 'שם')}</th><th>נייד</th><th>${sortBtn('status', 'סטטוס')}</th><th>שלב</th><th>עדכון אחרון</th><th>הערות / תשלום</th><th>${sortBtn('created_at', 'נוצר')}</th><th>פעולות</th></tr></thead>
      <tbody>${rows.map((l) => `<tr data-open="${l.id}">
        <td style="white-space:nowrap;font-weight:500">${nameHtml(l)}${l.needs_reply ? ' <span title="ממתין למענה">💬</span>' : ''}</td>
        <td style="white-space:nowrap">${phoneHtml(l)}${l.duplicate ? '<div class="dup">⚠ מספר כפול</div>' : ''}</td>
        <td>${badge(l)}</td><td>${stageBadge(l.stage)}</td>
        <td class="clip" title="${esc(latestText(l))}">${esc(latestText(l)) || '<span class="muted">—</span>'}</td>
        <td class="clip" title="${esc(l.notes)}">${esc(l.notes) || '<span class="muted">—</span>'}</td>
        <td style="white-space:nowrap" class="muted">${relDay(l.created_at)}</td>
        <td style="white-space:nowrap"><a class="btn ghost sm icon-only" href="${waLink(l)}" target="_blank" rel="noreferrer" aria-label="וואטסאפ" data-stop="1">${ic('wa')}</a><a class="btn ghost sm icon-only" href="tel:+${l.phone_norm}" aria-label="חיוג" data-stop="1">${ic('phone')}</a></td>
      </tr>`).join('')}</tbody></table>${rows.length ? '' : '<div class="empty-state">אין לידים שמתאימים לסינון</div>'}</div></div>`;
    bindFilterInputs();
  }

  function viewBoard(v) {
    const rows = applyFilters(S.leads);
    v.innerHTML = `<div class="stack">${filterBar(rows.length)}<div class="board">${S.meta.stages.map((st) => {
      const items = rows.filter((l) => l.stage === st.id);
      return `<section class="col" data-drop="${st.id}" aria-label="${esc(st.label)}"><header><div class="h"><span>${esc(st.label)}</span><span class="num muted">${items.length}</span></div><small>${esc(st.description)}</small></header>
        ${items.map((l) => `<button class="kcard" draggable="true" data-drag="${l.id}" data-open="${l.id}"><div class="t"><span>${nameHtml(l)}</span>${l.needs_reply ? '💬' : ''}</div><div class="p">${phoneHtml(l)}</div><div style="margin-top:6px">${badge(l)}</div>${latestText(l) ? `<div class="s">${esc(latestText(l))}</div>` : ''}</button>`).join('')}</section>`;
    }).join('')}</div></div>`;
    bindFilterInputs();
    v.querySelectorAll('[data-drag]').forEach((c) => {
      c.addEventListener('dragstart', (e) => { e.dataTransfer.setData('text/plain', c.dataset.drag); c.classList.add('dragging'); });
      c.addEventListener('dragend', () => c.classList.remove('dragging'));
    });
    v.querySelectorAll('[data-drop]').forEach((col) => {
      col.addEventListener('dragover', (e) => { e.preventDefault(); col.classList.add('over'); });
      col.addEventListener('dragleave', () => col.classList.remove('over'));
      col.addEventListener('drop', async (e) => {
        e.preventDefault(); col.classList.remove('over');
        const id = Number(e.dataTransfer.getData('text/plain')); const lead = leadById(id); const st = stageDef(col.dataset.drop);
        if (!lead || lead.stage === st.id) return;
        try { replaceLead(await api(`/api/leads/${id}`, { method: 'PATCH', body: JSON.stringify({ status: st.default_status }) })); toast(`הועבר ל"${st.label}" · ${statusDef(st.default_status).label}`); renderTabs(); render(); }
        catch (err) { showError(err.message); }
      });
    });
  }

  // ---------- smart reply (shared by drawer + inbox) ----------
  function smartReplyBox(l) {
    const d = S.drafts[l.id] || {};
    const tones = [['friendly', 'חם'], ['short', 'קצר'], ['formal', 'רשמי']];
    const sug = d.suggested_status ? statusDef(d.suggested_status) : null;
    return `<div class="sr" data-sr="${l.id}">
      <h3>${ic('sparkles')} מענה חכם</h3>
      <label class="field"><span>ההודעה האחרונה מהליד (אפשר להדביק מוואטסאפ)</span>
        <textarea class="input" data-incoming="${l.id}" rows="2" placeholder="למשל: כמה זה עולה? אפשר לדבר מחר?">${esc(d.incoming ?? l.last_incoming ?? '')}</textarea></label>
      <div class="gen"><div class="tones" role="group" aria-label="טון">${tones.map(([k, t]) => `<button data-tone="${k}" aria-pressed="${S.tone === k}">${t}</button>`).join('')}</div>
        <button class="btn primary" data-generate="${l.id}" ${d.loading ? 'disabled' : ''}>${ic('sparkles', d.loading ? 'spin' : '')}${d.reply ? 'נסח מחדש' : 'צור מענה'}</button></div>
      ${d.error ? `<p class="warn" style="color:#b91c1c">${esc(d.error)}</p>` : ''}
      ${d.reply ? `<div class="draft">
        <div class="why">${d.summary ? `<b>${esc(d.summary)}</b>` : ''}${sug ? `· סטטוס מוצע: <span class="badge t-${sug.tone}">${esc(sug.label)}</span>` : ''}<span class="muted">· ${d.engine === 'ai' ? 'נוסח ע״י Claude' : 'נוסח ע״י מנוע הכללים'}</span></div>
        <textarea class="input" data-draft="${l.id}" aria-label="טיוטת התשובה">${esc(d.reply)}</textarea>
        ${d.warning ? `<div class="warn">${esc(d.warning)}</div>` : ''}
        <div class="actions" style="margin-top:8px">
          <a class="btn wa" data-send="${l.id}" href="${waLink(l, d.reply)}" target="_blank" rel="noreferrer">${ic('send')}שליחה בוואטסאפ${sug ? ' + עדכון סטטוס' : ''}</a>
          <button class="btn secondary" data-copy="${l.id}">${ic('copy')}העתקה</button>
          ${sug ? `<button class="btn ghost" data-apply="${l.id}">רק לעדכן סטטוס</button>` : ''}
        </div></div>` : ''}
    </div>`;
  }
  async function generate(id) {
    const lead = leadById(id); const ta = document.querySelector(`[data-incoming="${id}"]`);
    const incoming = ta ? ta.value : lead.last_incoming;
    S.drafts[id] = { ...(S.drafts[id] || {}), incoming, loading: true, error: null }; rerenderSR(id);
    try {
      const r = await api(`/api/leads/${id}/smart-reply`, { method: 'POST', body: JSON.stringify({ incoming, tone: S.tone }) });
      S.drafts[id] = { ...r, incoming, loading: false };
      if (incoming && incoming.trim() !== (lead.last_incoming || '').trim()) { lead.last_incoming = incoming.trim(); lead.needs_reply = true; renderTabs(); }
    } catch (err) { S.drafts[id] = { ...S.drafts[id], loading: false, error: err.message }; }
    rerenderSR(id);
  }
  function rerenderSR(id) {
    document.querySelectorAll(`[data-sr="${id}"]`).forEach((el) => { el.outerHTML = smartReplyBox(leadById(id)); });
  }
  async function markSent(id, applyOnly = false) {
    const d = S.drafts[id]; const ta = document.querySelector(`[data-draft="${id}"]`); const reply = ta ? ta.value : d.reply;
    try {
      let detail;
      if (applyOnly) detail = await api(`/api/leads/${id}`, { method: 'PATCH', body: JSON.stringify({ status: d.suggested_status }) });
      else detail = await api(`/api/leads/${id}/sent`, { method: 'POST', body: JSON.stringify({ reply, status: d.suggested_status }) });
      replaceLead(detail); if (S.openId === id) S.openDetail = detail;
      if (!applyOnly) delete S.drafts[id]; else S.drafts[id].suggested_status = null;
      toast(applyOnly ? 'הסטטוס עודכן' : 'סומן כנענה ✓');
      renderTabs(); render(); if (S.openId === id) renderDrawer();
    } catch (err) { showError(err.message); }
  }

  function viewInbox(v) {
    const waiting = S.leads.filter((l) => l.needs_reply).sort((a, b) => (a.updated_at < b.updated_at ? 1 : -1));
    if (!S.inboxId || !leadById(S.inboxId)) S.inboxId = waiting[0]?.id || null;
    const cur = S.inboxId ? leadById(S.inboxId) : null;
    const others = S.leads.filter((l) => !l.needs_reply && !['lost'].includes(l.stage));
    v.innerHTML = `<div class="inbox">
      <section class="card" style="padding:8px"><header style="padding:8px 8px 0;margin-bottom:8px"><h2>${ic('inbox')} ממתינים למענה <span class="muted num">(${waiting.length})</span></h2></header>
        ${waiting.length ? `<ul class="inbox-list">${waiting.map((l) => `<li><button class="inbox-item" data-inbox="${l.id}" aria-current="${l.id === S.inboxId}">
          <div class="top"><span>${nameHtml(l)}</span><time>${relTime(l.updated_at)}</time></div><div class="msg">💬 ${esc(l.last_incoming)}</div><div style="margin-top:4px">${badge(l)}</div></button></li>`).join('')}</ul>` : '<p class="empty-state">כל ההודעות נענו ✅</p>'}
        <div style="padding:8px"><label class="field"><span>או בחרו ליד אחר להודעת המשך</span>
          <select class="input" id="inbox-pick"><option value="">בחירת ליד…</option>${others.map((l) => `<option value="${l.id}" ${l.id === S.inboxId ? 'selected' : ''}>${esc(l.name || 'ללא שם')} · ${esc(l.phone_display)}</option>`).join('')}</select></label></div>
      </section>
      <div>${cur ? `<section class="card stack">
          <header style="margin-bottom:0"><div><h2>${nameHtml(cur)}</h2><div class="muted" style="font-size:14px">${phoneHtml(cur)} · ${esc(cur.source || '')}</div></div><button class="btn secondary sm" data-open="${cur.id}">${ic('edit')}כרטיס ליד</button></header>
          <div class="actions">${badge(cur)} ${stageBadge(cur.stage)}</div>
          <div class="next-box">${ic('clock')}<div><b>הצעד הבא:</b> ${esc(cur.next_action)}</div></div>
          ${cur.last_incoming ? `<div><div class="muted" style="font-size:12px;margin-bottom:4px">${esc(cur.name || 'הליד')} כתב:</div><div class="bubble-in">${esc(cur.last_incoming)}</div></div>` : ''}
          ${smartReplyBox(cur)}</section>` : '<section class="card empty-state">בחרו ליד מהרשימה כדי לנסח מענה חכם</section>'}</div></div>`;
    const pick = $('inbox-pick'); if (pick) pick.onchange = () => { if (pick.value) { S.inboxId = Number(pick.value); render(); } };
  }

  function viewTemplates(v) {
    v.innerHTML = `<div class="tpls">${S.templates.map((t) => `<section class="card tpl"><header><h2>${ic('template')} ${esc(t.lead_type)}</h2></header>
      <p class="muted">${esc(t.goal)}</p>
      ${[['stage_a', "הודעה שלב א'"], ['stage_b', "הודעה שלב ב'"], ['extra', 'הודעה נוספת']].filter(([k]) => t[k]).map(([k, label]) => `<div class="k">${label}</div><p>${esc(t[k])}</p><button class="btn ghost sm" data-copytext="${esc(t[k])}" style="margin-bottom:8px">${ic('copy')}העתקה</button>`).join('')}
    </section>`).join('')}</div>`;
  }

  // ---------- drawer ----------
  async function openLead(id) {
    S.openId = id; S.openDetail = null; renderDrawer();
    try { S.openDetail = await api(`/api/leads/${id}`); replaceLead(S.openDetail); renderDrawer(); }
    catch (err) { showError(err.message); closeLayer(); }
  }
  const EV = { created: ['plus', 'נוצר'], status: ['workflow', 'שינוי סטטוס'], edit: ['edit', 'עריכה'], note: ['template', 'הערה'], ai_reply: ['send', 'נשלח מענה'], incoming: ['msg', 'הודעה מהליד'] };
  function renderDrawer() {
    const l = leadById(S.openId); if (!l) return;
    const d = S.openDetail; const tpl = d?.recommended_template;
    const tplOptions = S.templates.flatMap((t) => [['stage_a', "שלב א'"], ['stage_b', "שלב ב'"], ['extra', 'נוספת']].filter(([k]) => t[k]).map(([k, n]) => ({ id: `${t.id}:${k}`, label: `${t.lead_type} – ${n}`, text: t[k], rec: tpl && t.lead_type === tpl.lead_type && k === 'stage_a' })));
    const recId = (tplOptions.find((o) => o.rec) || tplOptions[0] || {}).id;
    const fill = (s) => s.replace(/\{שם\}/g, (l.name || '').split(' ')[0]).replace(/\{שירות\}/g, 'השירות שביקשת').replace(/\{מועד\}/g, 'המועד שנוח לך').replace(/\s+,/g, ',');
    const recText = fill((tplOptions.find((o) => o.id === recId) || {}).text || '');
    const opt = (val, label, cur) => `<option value="${val}" ${cur === val ? 'selected' : ''}>${esc(label)}</option>`;
    $('layer').innerHTML = `<div class="overlay" data-close="1"></div><aside class="drawer" role="dialog" aria-modal="true" aria-label="כרטיס ליד">
      <header><div style="flex:1;min-width:0"><h2>${nameHtml(l)}</h2><div class="muted" style="font-size:14px;margin-top:2px">${phoneHtml(l)} · נוצר ${relDay(l.created_at)}${l.source ? ` · ${esc(l.source)}` : ''}</div>
        <div class="actions" style="margin-top:8px">${badge(l)} ${stageBadge(l.stage)}${l.duplicate ? ' <span class="badge t-yellow">מספר כפול</span>' : ''}${l.paid ? ' <span class="badge t-green">שולם</span>' : ''}</div></div>
        <button class="btn ghost icon-only" data-close="1" aria-label="סגירה">${ic('x')}</button></header>
      <div class="body stack">
        <div class="next-box">${ic('clock')}<div><b>הצעד הבא:</b> ${esc(l.next_action)}</div></div>
        ${smartReplyBox(l)}
        <section class="sr"><h3>${ic('wa')} פנייה מהירה מתבנית</h3>
          <select class="input" id="tpl-pick">${tplOptions.map((o) => `<option value="${o.id}" ${o.id === recId ? 'selected' : ''}>${o.rec ? '⭐ ' : ''}${esc(o.label)}</option>`).join('')}</select>
          <div class="bubble-in" id="tpl-text" style="margin-top:8px">${esc(recText)}</div>
          <div class="actions" style="margin-top:8px"><a class="btn wa" id="tpl-wa" href="${waLink(l, recText)}" target="_blank" rel="noreferrer">${ic('wa')}פתיחה בוואטסאפ</a><a class="btn secondary" href="tel:+${l.phone_norm}">${ic('phone')}חיוג</a></div></section>
        <section class="sr"><h3>${ic('edit')} פרטי הליד</h3><form class="form" id="lead-form">
          <div class="row2"><label class="field"><span>שם</span><input class="input" name="name" value="${esc(l.name)}"></label>
            <label class="field"><span>נייד</span><input class="input ltr" style="text-align:right;display:block" name="phone" value="${esc(l.phone)}"></label></div>
          <div class="row2"><label class="field"><span>סטטוס</span><select class="input" name="status">${opt('', 'ללא סטטוס', l.status || '')}${S.meta.statuses.map((s) => opt(s.id, s.label, l.status)).join('')}</select></label>
            <label class="field"><span>מקור</span><select class="input" name="source">${opt('', '—', l.source)}${S.meta.sources.map((s) => opt(s, s, l.source)).join('')}</select></label></div>
          <label class="field"><span>ניסיון ראשון</span><textarea class="input" name="first_attempt" rows="2">${esc(l.first_attempt)}</textarea></label>
          <label class="field"><span>ניסיון שני</span><textarea class="input" name="second_attempt" rows="2">${esc(l.second_attempt)}</textarea></label>
          <label class="field"><span>עדכון אחרון</span><textarea class="input" name="last_update" rows="2">${esc(l.last_update)}</textarea></label>
          <label class="field"><span>הערות / תשלום</span><textarea class="input" name="notes" rows="2">${esc(l.notes)}</textarea></label>
          <div class="actions"><button class="btn primary" type="submit" id="save-lead" disabled>שמירה</button><span class="muted" style="font-size:12px;align-self:center">נשמרים רק השדות שהשתנו</span></div>
        </form></section>
        <section class="sr"><h3>${ic('clock')} היסטוריית פעילות</h3>${d ? (d.activity.length ? `<ul class="timeline">${d.activity.map((e) => `<li><span class="dot">${ic((EV[e.kind] || EV.edit)[0])}</span><div><div><b>${(EV[e.kind] || EV.edit)[1]}</b> · ${esc(e.text)}</div><div class="when">${esc(e.by)} · ${relTime(e.at)}</div></div></li>`).join('')}</ul>` : '<p class="muted">אין פעילות עדיין</p>') : '<p class="muted">טוען…</p>'}</section>
      </div></aside>`;
    const form = $('lead-form'); const initial = new FormData(form);
    form.oninput = () => { const now = new FormData(form); $('save-lead').disabled = [...now.keys()].every((k) => now.get(k) === initial.get(k)); };
    form.onsubmit = async (e) => {
      e.preventDefault(); const now = new FormData(form); const patch = {};
      for (const k of now.keys()) if (now.get(k) !== initial.get(k)) patch[k] = now.get(k);
      if ('status' in patch && !patch.status) { delete patch.status; patch.clear_status = true; }
      try { S.openDetail = await api(`/api/leads/${l.id}`, { method: 'PATCH', body: JSON.stringify(patch) }); replaceLead(S.openDetail); toast('נשמר ✓'); renderTabs(); render(); renderDrawer(); }
      catch (err) { showError(err.message); }
    };
    $('tpl-pick').onchange = (e) => { const o = tplOptions.find((x) => x.id === e.target.value); const t = fill(o.text); $('tpl-text').textContent = t; $('tpl-wa').href = waLink(l, t); };
  }
  function closeLayer() { $('layer').innerHTML = ''; S.openId = null; S.openDetail = null; }
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape' && $('layer').innerHTML) closeLayer(); });

  function openNewLead() {
    const opt = (val, label) => `<option value="${val}">${esc(label)}</option>`;
    $('layer').innerHTML = `<div class="overlay" data-close="1"></div><div class="dialog" role="dialog" aria-modal="true" aria-labelledby="nl-t"><h2 id="nl-t">ליד חדש</h2>
      <form class="form" id="new-form"><div class="row2"><label class="field"><span>נייד *</span><input class="input" name="phone" required minlength="7" inputmode="tel" placeholder="050-000-0000"></label>
      <label class="field"><span>שם</span><input class="input" name="name"></label></div>
      <div class="row2"><label class="field"><span>מקור</span><select class="input" name="source">${opt('', '—')}${S.meta.sources.map((s) => opt(s, s)).join('')}</select></label>
      <label class="field"><span>סטטוס</span><select class="input" name="status">${S.meta.statuses.map((s) => opt(s.id, s.label)).join('')}</select></label></div>
      <label class="field"><span>הערות</span><textarea class="input" name="notes" rows="2"></textarea></label>
      <p class="warn hidden" id="new-err" style="color:#b91c1c;margin:0"></p>
      <div class="actions"><button class="btn primary" type="submit">יצירה</button><button class="btn ghost" type="button" data-close="1">ביטול</button></div></form></div>`;
    $('new-form').querySelector('[name=phone]').focus();
    $('new-form').onsubmit = async (e) => {
      e.preventDefault(); const body = Object.fromEntries(new FormData(e.target));
      try { const d = await api('/api/leads', { method: 'POST', body: JSON.stringify(body) }); replaceLead(d); closeLayer(); toast('הליד נוצר ✓'); renderTabs(); render(); openLead(d.id); }
      catch (err) { $('new-err').textContent = err.message; $('new-err').classList.remove('hidden'); }
    };
  }
  $('btn-new').onclick = openNewLead;

  // ---------- CSV ----------
  $('btn-csv').onclick = () => {
    const rows = sorted(applyFilters(S.leads));
    const cols = [['name', 'שם'], ['phone_display', 'נייד'], ['status_label', 'סטטוס'], ['stage_label', 'שלב'], ['source', 'מקור'], ['first_attempt', 'ניסיון ראשון'], ['second_attempt', 'ניסיון שני'], ['last_update', 'עדכון אחרון'], ['notes', 'הערות / תשלום'], ['last_incoming', 'הודעה אחרונה מהליד'], ['created_at', 'נוצר']];
    const q = (v) => `"${String(v ?? '').replace(/"/g, '""')}"`;
    const csv = '﻿' + [cols.map((c) => q(c[1])).join(','), ...rows.map((r) => cols.map((c) => q(r[c[0]])).join(','))].join('\r\n');
    const url = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8' }));
    Object.assign(document.createElement('a'), { href: url, download: `leads-${new Date().toISOString().slice(0, 10)}.csv` }).click();
    URL.revokeObjectURL(url);
  };

  // ---------- delegated clicks ----------
  document.addEventListener('click', async (e) => {
    const t = e.target.closest('[data-open],[data-filter],[data-toggle],[data-clear],[data-sort],[data-bar-stage],[data-bar-status],[data-close],[data-reply],[data-generate],[data-tone],[data-send],[data-copy],[data-apply],[data-inbox],[data-tab-go],[data-copytext],[data-stop]');
    if (!t) return;
    if (t.dataset.stop) return; // a link inside a clickable row
    if (t.dataset.close) return closeLayer();
    if (t.dataset.generate) return generate(Number(t.dataset.generate));
    if (t.dataset.tone) { S.tone = t.dataset.tone; t.parentElement.querySelectorAll('[data-tone]').forEach((b) => b.setAttribute('aria-pressed', b.dataset.tone === S.tone)); return; }
    if (t.dataset.send) { setTimeout(() => markSent(Number(t.dataset.send)), 50); return; } // the link itself opens WhatsApp
    if (t.dataset.apply) return markSent(Number(t.dataset.apply), true);
    if (t.dataset.copy) { const ta = document.querySelector(`[data-draft="${t.dataset.copy}"]`); await navigator.clipboard?.writeText(ta.value).catch(() => {}); return toast('הועתק ✓'); }
    if (t.dataset.copytext) { await navigator.clipboard?.writeText(t.dataset.copytext).catch(() => {}); return toast('הועתק ✓'); }
    if (t.dataset.reply) { S.inboxId = Number(t.dataset.reply); return setTab('inbox'); }
    if (t.dataset.inbox) { S.inboxId = Number(t.dataset.inbox); return render(); }
    if (t.dataset.tabGo) return setTab(t.dataset.tabGo);
    if (t.dataset.open) return openLead(Number(t.dataset.open));
    if (t.dataset.filter) { S.filters = { ...EMPTY_FILTERS, ...JSON.parse(t.dataset.filter) }; S.noNameOnly = !!t.dataset.noname; return setTab('leads'); }
    if (t.dataset.barStage) { S.filters = { ...EMPTY_FILTERS, stage: t.dataset.barStage }; S.noNameOnly = false; return setTab('leads'); }
    if (t.dataset.barStatus) { S.filters = { ...EMPTY_FILTERS, status: t.dataset.barStatus }; S.noNameOnly = false; return setTab('leads'); }
    if (t.dataset.toggle) { const k = t.dataset.toggle; S.filters[k] = !S.filters[k]; return render(); }
    if (t.dataset.clear) { S.filters = { ...EMPTY_FILTERS }; S.noNameOnly = false; return render(); }
    if (t.dataset.sort) { const k = t.dataset.sort; S.sort = { key: k, dir: S.sort.key === k ? -S.sort.dir : (k === 'created_at' ? -1 : 1) }; return render(); }
  });
  document.addEventListener('input', (e) => {
    const d = e.target.dataset;
    if (d.draft) { const id = Number(d.draft); S.drafts[id].reply = e.target.value; const a = document.querySelector(`[data-send="${id}"]`); if (a) a.href = waLink(leadById(id), e.target.value); }
    if (d.incoming) { const id = Number(d.incoming); S.drafts[id] = { ...(S.drafts[id] || {}), incoming: e.target.value }; }
  });
  // bar tooltips
  document.addEventListener('mouseover', (e) => { const b = e.target.closest('[data-tipt]'); document.querySelectorAll('.tip').forEach((x) => x.remove()); if (b) { const tip = document.createElement('div'); tip.className = 'tip'; tip.setAttribute('role', 'tooltip'); tip.textContent = b.dataset.tipt; b.parentElement.appendChild(tip); } });

  // ---------- assistant (agent chat) ----------
  function renderMd(md) {
    if (window.marked) { try { return marked.parse(md, { breaks: true }); } catch (_) {} }
    // Minimal fallback when the CDN is unreachable: bold, italics, code, bullets, quotes.
    const inline = (t) => esc(t).replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>').replace(/(^|\s)_(.+?)_(?=\s|$)/g, '$1<em>$2</em>').replace(/`(.+?)`/g, '<code>$1</code>');
    const out = []; let list = false;
    for (const line of md.split('\n')) {
      const li = line.match(/^\s*[-*]\s+(.*)/);
      if (li) { if (!list) { out.push('<ul>'); list = true; } out.push(`<li>${inline(li[1])}</li>`); continue; }
      if (list) { out.push('</ul>'); list = false; }
      const q = line.match(/^>\s?(.*)/);
      if (q) out.push(`<blockquote>${inline(q[1])}</blockquote>`); else if (line.trim()) out.push(`<p>${inline(line)}</p>`);
    }
    if (list) out.push('</ul>');
    return out.join('');
  }
  function viewAssistant(v) {
    if (S.chatMounted && $('messages')) return;
    S.chatMounted = true;
    v.innerHTML = `<div class="chat">
      <section class="card" style="padding:12px"><button class="btn primary" id="new-chat" style="width:100%;margin-bottom:10px">${ic('plus')}שיחה חדשה</button><nav class="convs" id="convs" aria-label="שיחות"></nav></section>
      <section class="card chat-main"><header><h2 id="conv-title">${ic('sparkles')} עוזר המכירות</h2><span class="muted" id="chat-status" style="font-size:13px"></span></header>
        <div class="messages" id="messages" aria-live="polite"></div>
        <p id="attachment" class="attachment hidden"></p>
        <form class="composer" id="composer"><label class="attach" title="צירוף צילום מסך של שיחה">${ic('paperclip')}<input id="image" type="file" accept="image/png,image/jpeg,image/webp,image/gif" aria-label="צירוף תמונה"></label>
          <textarea id="input" class="input" rows="1" placeholder="שאלו על הלידים, בקשו מענה לליד, או עדכנו מה קרה בשיחה…"></textarea>
          <button id="send" class="btn primary" type="submit" aria-label="שליחה">${ic('send')}</button></form></section></div>`;
    bindChat(); loadConversations();
  }
  function chatEmpty() {
    const hints = S.meta.ai === 'anthropic'
      ? ['מה לטפל היום?', 'נסח מענה לאורי כהן', 'כמה לידים חמים יש ומה אחוז ההמרה?', 'דיברתי עם דוד מזרחי, הוא רוצה לחכות לחודש הבא – תעדכן']
      : ['מה לטפל היום?', 'כמה לידים יש?', 'מי ממתין לתשובה?', 'חפש 052-771'];
    $('messages').innerHTML = `<div class="chat-empty"><div class="big">שלום ${esc(S.user.name)} 👋</div><div>אני העוזר של צוות המכירות. אני רואה את כל הלידים בזמן אמת.</div>
      <div class="hints">${hints.map((h) => `<button class="hint" data-hint="${esc(h)}">${esc(h)}</button>`).join('')}</div></div>`;
    $('messages').querySelectorAll('[data-hint]').forEach((b) => (b.onclick = () => { $('input').value = b.dataset.hint; $('composer').requestSubmit(); }));
  }
  async function loadConversations() {
    try { S.chat.conversations = await api('/api/conversations'); } catch (_) { S.chat.conversations = []; }
    renderConvs(); if (S.chat.current) await openConversation(S.chat.current); else chatEmpty();
  }
  function renderConvs() {
    const nav = $('convs'); if (!nav) return;
    nav.innerHTML = S.chat.conversations.map((c) => `<button data-conv="${c.id}" class="${c.id === S.chat.current ? 'active' : ''}" title="${esc(c.title)}">${esc(c.title)}</button>`).join('') || '<p class="muted" style="font-size:13px;padding:4px 8px">אין שיחות עדיין</p>';
    nav.querySelectorAll('[data-conv]').forEach((b) => (b.onclick = () => openConversation(Number(b.dataset.conv))));
  }
  async function openConversation(id) {
    S.chat.current = id; renderConvs();
    const msgs = await api(`/api/conversations/${id}/messages`).catch(() => []);
    $('messages').innerHTML = ''; msgs.forEach((m) => addBubble(m.role, m.content, { hasImage: m.has_image, time: m.created_at }));
    if (!msgs.length) chatEmpty();
  }
  function addBubble(role, text, { hasImage = false, imageDataUrl = null, time = null } = {}) {
    const div = document.createElement('div'); div.className = `msg ${role}`;
    const who = role === 'user' ? S.user.name : 'LeadPilot';
    const stamp = (time ? new Date(time + 'Z') : new Date()).toLocaleTimeString('he-IL', { hour: '2-digit', minute: '2-digit' });
    let inner = imageDataUrl ? `<img class="img" src="${imageDataUrl}" alt="צילום מסך מצורף">` : hasImage ? `<span class="chip">${ic('paperclip')} תמונה</span>` : '';
    inner += role === 'user' ? `<p>${esc(text).replace(/\n/g, '<br>')}</p>` : renderMd(text);
    div.innerHTML = `<div class="avatar ${role}">${role === 'user' ? esc(who.trim().charAt(0)) : 'L'}</div><div class="msg-body"><div class="msg-head"><span class="author">${esc(who)}</span><span class="time">${stamp}</span></div><div class="body">${inner}</div></div>`;
    $('messages').appendChild(div); $('messages').scrollTop = $('messages').scrollHeight; return div;
  }
  function bindChat() {
    $('new-chat').onclick = () => { S.chat.current = null; renderConvs(); chatEmpty(); $('input').focus(); };
    $('image').onchange = () => {
      const file = $('image').files[0]; if (!file) { S.chat.image = null; $('attachment').classList.add('hidden'); return; }
      if (file.size > 5 * 1024 * 1024) { showError('התמונה גדולה מ-5MB.'); $('image').value = ''; return; }
      const r = new FileReader(); r.onload = () => { S.chat.image = { media_type: file.type, data: r.result.split(',')[1], dataUrl: r.result }; $('attachment').textContent = `מצורף: ${file.name}`; $('attachment').classList.remove('hidden'); }; r.readAsDataURL(file);
    };
    $('input').onkeydown = (e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); $('composer').requestSubmit(); } };
    $('input').oninput = () => { const t = $('input'); t.style.height = 'auto'; t.style.height = Math.min(t.scrollHeight, 160) + 'px'; };
    $('composer').onsubmit = sendChat;
  }
  async function sendChat(e) {
    e.preventDefault(); if (S.chat.streaming) return;
    const text = $('input').value.trim(); const image = S.chat.image; if (!text && !image) return;
    $('input').value = ''; $('input').style.height = 'auto'; S.chat.image = null; $('image').value = ''; $('attachment').classList.add('hidden');
    if ($('messages').querySelector('.chat-empty')) $('messages').innerHTML = '';
    addBubble('user', text || '(צילום מסך)', { imageDataUrl: image?.dataUrl });
    const bot = addBubble('assistant', ''); const body = bot.querySelector('.body'); body.classList.add('cursor');
    const meta = document.createElement('div'); meta.className = 'meta'; bot.querySelector('.msg-body').appendChild(meta);
    S.chat.streaming = true; $('send').disabled = true; $('chat-status').textContent = 'חושב…';
    let full = ''; let wrote = false;
    try {
      const res = await fetch('/api/chat', { method: 'POST', credentials: 'same-origin', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ conversation_id: S.chat.current, message: text, image: image ? { media_type: image.media_type, data: image.data } : null }) });
      if (!res.ok) { let d = res.statusText; try { d = (await res.json()).detail || d; } catch (_) {} throw new Error(d); }
      const reader = res.body.getReader(); const dec = new TextDecoder(); let buf = '';
      for (;;) {
        const { value, done } = await reader.read(); if (done) break;
        buf += dec.decode(value, { stream: true }); let i;
        while ((i = buf.indexOf('\n\n')) >= 0) {
          const raw = buf.slice(0, i); buf = buf.slice(i + 2);
          const line = raw.split('\n').find((x) => x.startsWith('data: ')); if (!line) continue;
          const ev = JSON.parse(line.slice(6));
          if (ev.type === 'meta') S.chat.current = ev.conversation_id;
          else if (ev.type === 'text') { full += ev.text; body.innerHTML = renderMd(full); $('messages').scrollTop = $('messages').scrollHeight; }
          else if (ev.type === 'tool') {
            if (ev.status === 'done' && ['update_lead', 'create_lead'].includes(ev.name)) wrote = true;
            const c = document.createElement('span'); c.className = `chip tool ${ev.status}`; c.textContent = `${ev.status === 'start' ? '⚙' : '✓'} ${ev.name}${ev.status === 'done' && ev.summary ? ': ' + ev.summary : ''}`; meta.appendChild(c);
            $('chat-status').textContent = `משתמש ב-${ev.name}…`;
          } else if (ev.type === 'done') { const u = ev.usage || {}; if (u.input_tokens) { const c = document.createElement('span'); c.className = 'chip'; c.textContent = `${u.input_tokens} in · ${u.output_tokens} out · $${(ev.cost_usd || 0).toFixed(4)}`; meta.appendChild(c); } }
          else if (ev.type === 'error') { full += `\n\n**שגיאה:** ${ev.message}`; body.innerHTML = renderMd(full); }
        }
      }
    } catch (err) { full += `\n\n**שגיאה:** ${err.message}`; body.innerHTML = renderMd(full); }
    finally {
      body.classList.remove('cursor'); S.chat.streaming = false; $('send').disabled = false; $('chat-status').textContent = '';
      try { S.chat.conversations = await api('/api/conversations'); renderConvs(); } catch (_) {}
      if (wrote) { const data = await api('/api/leads').catch(() => null); if (data) { S.leads = data.leads; renderTabs(); } }
    }
  }

  // ---------- boot ----------
  async function boot() {
    $('login').classList.add('hidden'); $('app').classList.remove('hidden');
    paintIcons(); paintTheme();
    S.meta = await api('/api/meta');
    renderHeader(); renderTabs(); render();
    await loadLeads();
  }
  (async () => {
    try { S.user = await api('/api/me'); await boot(); } catch (_) { showLogin(); }
  })();
})();
