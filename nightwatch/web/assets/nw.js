// NightWatch shared helpers: escaping, inline icons, level names, API posts. No dependencies, works offline.
(function () {
  const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

  // 24x24 stroke icons (inline SVG only).
  const P = {
    moon: '<path d="M20 14.5A8.5 8.5 0 0 1 9.5 4 8.5 8.5 0 1 0 20 14.5Z"/>',
    sun: '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>',
    logo: '<path d="M19 14.2A7.5 7.5 0 0 1 9.8 5 7.5 7.5 0 1 0 19 14.2Z"/><circle cx="17.5" cy="5.5" r="1.3" fill="currentColor" stroke="none"/>',
    bell: '<path d="M6 8a6 6 0 1 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/><path d="M10.3 21a1.9 1.9 0 0 0 3.4 0"/>',
    door: '<path d="M14 3H6v18h8"/><path d="M14 3l5 2v14l-5 2z"/><circle cx="16" cy="12" r=".9" fill="currentColor"/>',
    siren: '<path d="M7 18v-6a5 5 0 0 1 10 0v6"/><path d="M5 21h14v-3H5z"/><path d="M12 2v2M3.5 6l1.5 1M20.5 6 19 7"/>',
    check: '<path d="M20 6 9 17l-5-5"/>',
    shield: '<path d="M12 3 4 6v6c0 5 3.5 8 8 9 4.5-1 8-4 8-9V6z"/><path d="m9 12 2 2 4-4"/>',
    bulb: '<path d="M9 18h6M10 22h4"/><path d="M12 2a7 7 0 0 0-4 12.7c.6.5 1 1.3 1 2.3h6c0-1 .4-1.8 1-2.3A7 7 0 0 0 12 2Z"/>',
    chip: '<rect x="6" y="6" width="12" height="12" rx="2"/><path d="M9 2v4M15 2v4M9 18v4M15 18v4M2 9h4M2 15h4M18 9h4M18 15h4"/>',
    camera: '<path d="M3 7h3l2-3h8l2 3h3v13H3z"/><circle cx="12" cy="13" r="4"/>',
    wifiOff: '<path d="m2 2 20 20"/><path d="M8.5 16.5a5 5 0 0 1 7 0M5 13a10 10 0 0 1 5-2.7M19 13a10 10 0 0 0-2.3-1.7M2 8.8a15 15 0 0 1 4.2-2.6M22 8.8A15 15 0 0 0 11 5"/><circle cx="12" cy="20" r=".8" fill="currentColor"/>',
    user: '<circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/>',
    thermo: '<path d="M14 14.8V4a2 2 0 0 0-4 0v10.8a4 4 0 1 0 4 0Z"/>',
    clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    phone: '<path d="M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3.1 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.1 4.2 2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1 1 .4 1.9.7 2.8a2 2 0 0 1-.5 2.1L8 9.9a16 16 0 0 0 6 6l1.3-1.3a2 2 0 0 1 2.1-.4c.9.3 1.8.6 2.8.7a2 2 0 0 1 1.7 2Z"/>',
    walk: '<circle cx="13" cy="4" r="2"/><path d="m9 21 2.5-6.5L14 17v4M7 11l3-3 3 1 2 3 3 1M11.5 14.5 10 8"/>',
    note: '<path d="M14 3H6v18h12V7z"/><path d="M14 3v4h4M9 13h6M9 17h4"/>',
    eye: '<path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12Z"/><circle cx="12" cy="12" r="3"/>',
    bed: '<path d="M3 18V6M3 14h18v4M21 14v-2a3 3 0 0 0-3-3h-7v5"/><circle cx="7" cy="11" r="1.6"/>',
    play: '<path d="M7 4v16l13-8z"/>',
    reset: '<path d="M3 12a9 9 0 1 0 3-6.7L3 8"/><path d="M3 3v5h5"/>',
    pin: '<path d="M12 21s7-6.2 7-12a7 7 0 0 0-14 0c0 5.8 7 12 7 12Z"/><circle cx="12" cy="9" r="2.5"/>',
    window: '<rect x="4" y="3" width="16" height="18" rx="1"/><path d="M12 3v18M4 12h16"/>',
    report: '<rect x="5" y="4" width="14" height="17" rx="2"/><path d="M9 4V2h6v2M9 10h6M9 14h6M9 18h3"/>',
    radar: '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><path d="M12 12 18 6"/>',
    next: '<path d="m9 6 6 6-6 6"/>',
    back: '<path d="m15 6-6 6 6 6"/>',
    print: '<path d="M6 9V3h12v6M6 18H4v-7h16v7h-2"/><rect x="6" y="14" width="12" height="7"/>',
    volume: '<path d="M11 5 6 9H2v6h4l5 4z"/><path d="M15.5 8.5a5 5 0 0 1 0 7M19 5a10 10 0 0 1 0 14"/>',
    mute: '<path d="M11 5 6 9H2v6h4l5 4z"/><path d="m22 9-6 6M16 9l6 6"/>',
    help: '<circle cx="12" cy="12" r="9"/><path d="M9.5 9a2.5 2.5 0 1 1 3.5 2.3c-.6.3-1 .9-1 1.6V14"/><circle cx="12" cy="17.3" r=".8" fill="currentColor"/>',
    heart: '<path d="M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.7l-1-1.1a5.5 5.5 0 0 0-7.8 7.8L12 21l8.8-8.6a5.5 5.5 0 0 0 0-7.8Z"/>',
  };
  const icon = (name, cls = '') =>
    `<svg class="nw-ico ${cls}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${P[name] || ''}</svg>`;

  const LEVELS = {
    1: { name: 'Heads-up', word: 'HEADS-UP', icon: 'bell' },
    2: { name: 'Urgent', word: 'URGENT', icon: 'door' },
    3: { name: 'Emergency', word: 'EMERGENCY', icon: 'siren' },
  };
  const SEVERITY = { 1: 'routine', 2: 'notable', 3: 'escalation' };

  const badge = (level) => {
    const L = LEVELS[level] || LEVELS[1];
    return `<span class="nw-badge nw-l${level}">${icon(L.icon)}Level ${level} · ${L.word}</span>`;
  };
  const ladder = (level) => `<span class="nw-ladder nw-l${level}" aria-hidden="true">${[1, 2, 3].map((i) => `<i class="${i <= level ? 'on' : ''}"></i>`).join('')}</span>`;

  // Countdown ring. frac in [0,1] = time left before the next escalation.
  const RING_C = 2 * Math.PI * 26;
  const ring = (secs, frac, caption) => `<div class="nw-ring" role="timer" aria-label="${esc(caption)} in ${secs} seconds">
      <svg viewBox="0 0 64 64"><circle class="track" cx="32" cy="32" r="26" fill="none" stroke-width="5"/>
      <circle class="prog" cx="32" cy="32" r="26" fill="none" stroke-width="5" stroke-dasharray="${RING_C.toFixed(1)}" stroke-dashoffset="${(RING_C * (1 - Math.max(0, Math.min(1, frac)))).toFixed(1)}"/></svg>
      <div class="val"><b>${secs}</b><span>sec</span></div></div>`;
  const updateRing = (el, secs, frac, caption) => {
    if (!el) return;
    el.querySelector('.prog').setAttribute('stroke-dashoffset', (RING_C * (1 - Math.max(0, Math.min(1, frac)))).toFixed(1));
    el.querySelector('.val b').textContent = secs;
    el.setAttribute('aria-label', `${caption} in ${secs} seconds`);
  };

  // Classify an escalation-history line for the timeline dot.
  const histKind = (h) => {
    const m = /^Level (\d)/.exec(h);
    if (m) return 'l' + m[1];
    if (/^Acknowledged/.test(h)) return 'ack';
    if (/^Resolved/.test(h)) return 'resolved';
    if (/simulated|alarm|Calling|Emergency services/i.test(h)) return 'contact';
    return '';
  };
  const timeline = (history) => `<ol class="nw-timeline">${history.map(([t, h]) =>
    `<li class="k-${histKind(h)}"><time>${esc(t)}</time><span class="what">${esc(h).replace(/^(Level \d)/, '<b>$1</b>')}</span></li>`).join('')}</ol>`;

  // Seconds an alert waits at its level before climbing (from state.timeouts).
  const limitFor = (a, s) => (a.level === 1 ? s.timeouts.l1 : s.timeouts.ack) || 1;
  const contactsDone = (a) => a.history.some(([, h]) => /^Emergency services/.test(h));

  const post = (url, body) => fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });

  // "Offline · still protecting": shown whenever the browser loses the network. The pages are
  // served by the laptop itself, so polling keeps working with Wi-Fi off.
  const offlineBadge = (host) => {
    const el = document.createElement('span');
    el.className = 'nw-offline';
    el.setAttribute('role', 'status');
    el.innerHTML = `${icon('wifiOff')}Offline · still protecting`;
    host.appendChild(el);
    const sync = () => { el.classList.toggle('is-on', !navigator.onLine); document.body.classList.toggle('nw-is-offline', !navigator.onLine); };
    window.addEventListener('online', sync); window.addEventListener('offline', sync); sync();
    return el;
  };

  // Camera privacy state. Order matters: off beats paused beats not-started.
  const camState = (c) => {
    if (c.enabled === false) return { key: 'off', word: 'OFF', long: 'Camera off', sub: 'Turned off by staff · frames dropped, nothing analysed' };
    if (c.active === false) return { key: 'paused', word: 'PAUSED', long: 'Paused · night only', sub: `${c.paused_reason ? c.paused_reason.replace(/^night only/i, 'Watches at night only') : 'Watches at night only'} · nothing analysed now` };
    if (!c.live) return { key: 'idle', word: 'NOT STARTED', long: 'Not started', sub: 'On, but no frames yet · start it on /camera/' };
    const n = (c.tracks || []).length || c.persons || 0;
    return n ? { key: 'hit', word: `${n} ${n > 1 ? 'PEOPLE' : 'PERSON'}`, long: 'Watching', sub: '' } : { key: 'on', word: 'CLEAR', long: 'Watching', sub: '' };
  };
  const camStateHTML = (c) => { const st = camState(c); return `<span class="nw-camstate is-${st.key}"><span class="nw-dot ${st.key === 'on' ? 'is-live' : st.key === 'hit' ? 'is-hit' : ''}"></span>${st.word}</span>`; };
  // On/off switch + Always / Night only. Click handling: NW.handleCameraClick in each page.
  const cameraControls = (c) => `<div class="nw-camctl" data-camctl="${esc(c.id)}">
      <button class="nw-switch" role="switch" aria-checked="false" data-cam-enable="${esc(c.id)}" aria-label="${esc(c.label)} on or off"><span class="trk" aria-hidden="true"></span><span class="txt">OFF</span></button>
      <span class="nw-seg" role="group" aria-label="${esc(c.label)} schedule">
        <button data-cam-schedule="${esc(c.id)}" data-v="always" aria-pressed="false">Always</button><button data-cam-schedule="${esc(c.id)}" data-v="night" aria-pressed="false">Night only</button></span></div>`;
  const syncCameraControls = (root, c) => {
    const el = root.querySelector(`[data-camctl="${CSS.escape(c.id)}"]`); if (!el) return;
    const on = c.enabled !== false, sw = el.querySelector('[data-cam-enable]');
    sw.setAttribute('aria-checked', String(on)); sw.querySelector('.txt').textContent = on ? 'ON' : 'OFF'; sw.disabled = false;
    el.querySelectorAll('[data-cam-schedule]').forEach((b) => { b.setAttribute('aria-pressed', String(b.dataset.v === (c.schedule || 'always'))); b.disabled = !on; });
  };
  const handleCameraClick = (e, by, after) => {
    const sw = e.target.closest('[data-cam-enable]'), sc = e.target.closest('[data-cam-schedule]');
    if (sw) { sw.disabled = true; post('/api/camera/config', { camera: sw.dataset.camEnable, enabled: sw.getAttribute('aria-checked') !== 'true', by }).then(after); return true; }
    if (sc) { post('/api/camera/config', { camera: sc.dataset.camSchedule, schedule: sc.dataset.v, by }).then(after); return true; }
    return false;
  };

  // Night band from state.night_hours (configurable): "21:00-05:00".
  const hh = (h) => `${String(h).padStart(2, '0')}:00`;
  const nightBand = (s) => { const [a, b] = (s && s.night_hours) || [21, 5]; return { start: hh(a), end: hh(b), label: `${hh(a)}-${hh(b)}` }; };

  // Care-record filing form (shared by dashboard, report, staff). Pick-lists come from state.taxonomy.
  const opts = (list, first) => `<option value="">${esc(first)}</option>` + (list || []).map((v) => `<option>${esc(v)}</option>`).join('');
  const recordForm = (a, tax, labels = {}) => {
    const L = { title: 'Confirm and file', affect: 'Affect', intervention: 'Intervention', alt: 'Non-drug alternative', optional: 'optional',
                note: 'Note', choose: 'Choose…', none: 'None', file: 'File record', ...labels };
    return `<form class="nw-recform" data-rec="${esc(a.id)}" novalidate>
      <div class="k">${icon('note')}${esc(L.title)}</div>
      <label class="nw-field">${esc(L.affect)}<select class="nw-select" name="affect" required>${opts(tax && tax.affect, L.choose)}</select></label>
      <label class="nw-field">${esc(L.intervention)}<select class="nw-select" name="intervention" required>${opts(tax && tax.intervention, L.choose)}</select></label>
      <label class="nw-field">${esc(L.alt)} <span class="opt">(${esc(L.optional)})</span><select class="nw-select" name="nondrug_alt">${opts(tax && tax.nondrug_alt, L.none)}</select></label>
      <label class="nw-field full">${esc(L.note)} <span class="opt">(${esc(L.optional)})</span><textarea class="nw-textarea" name="note" maxlength="500" rows="2"></textarea></label>
      <div class="row"><button class="nw-btn nw-btn--primary" type="submit">${icon('check')}${esc(L.file)}</button><span class="nw-err" role="alert"></span></div>
    </form>`;
  };
  // One delegated submit handler per page. getBy() -> name; after(result) on success.
  const bindRecordForms = (getBy, after, msgs = {}) => {
    document.addEventListener('submit', async (e) => {
      const f = e.target.closest('form.nw-recform'); if (!f) return;
      e.preventDefault();
      const err = f.querySelector('.nw-err'), btn = f.querySelector('button[type=submit]');
      f.querySelectorAll('.nw-field').forEach((x) => x.classList.remove('bad'));
      const missing = ['affect', 'intervention'].filter((k) => !f.elements[k].value);
      if (missing.length) {
        missing.forEach((k) => f.elements[k].closest('.nw-field').classList.add('bad'));
        err.textContent = msgs.missing || 'Choose an affect and an intervention.'; f.elements[missing[0]].focus(); return;
      }
      btn.disabled = true; err.textContent = '';
      try {
        const res = await post('/api/record', { alert: +f.dataset.rec, affect: f.elements.affect.value, intervention: f.elements.intervention.value,
          nondrug_alt: f.elements.nondrug_alt.value || null, note: f.elements.note.value, by: getBy() });
        const out = await res.json().catch(() => ({ error: `Server error (${res.status})` }));
        if (out.error) { err.textContent = out.error; btn.disabled = false; return; }
        f.dataset.done = '1'; after && after(out, f);
      } catch { err.textContent = msgs.network || 'Could not reach the laptop. Try again.'; btn.disabled = false; }
    });
  };
  const filedBadge = (r) => `<span class="nw-filed">${icon('check')}Filed by ${esc(r.confirmed_by || 'staff')}${r.confirmed_at ? ` at ${esc(String(r.confirmed_at).slice(0, 5))}` : ''}</span>`;
  const isDirty = (root = document) => [...root.querySelectorAll('form.nw-recform')].some((f) =>
    !f.dataset.done && ([...f.elements].some((el) => (el.tagName === 'SELECT' || el.tagName === 'TEXTAREA') && el.value) || f.contains(document.activeElement)));

  // Alert tones (WebAudio). Needs a user gesture before the context can start.
  let actx = null;
  const audio = () => { try { actx = actx || new (window.AudioContext || window.webkitAudioContext)(); if (actx.state === 'suspended') actx.resume(); } catch {} return actx; };
  const tone = (level) => {
    const ctx = actx; if (!ctx || ctx.state !== 'running') return;
    const seq = level >= 3 ? [988, 740, 988, 740, 988] : level === 2 ? [660, 880] : [520];
    seq.forEach((f, i) => {
      const o = ctx.createOscillator(), g = ctx.createGain(), t = ctx.currentTime + i * 0.28;
      o.type = level >= 3 ? 'square' : 'sine'; o.frequency.value = f;
      g.gain.setValueAtTime(0.0001, t); g.gain.exponentialRampToValueAtTime(level >= 3 ? 0.12 : 0.18, t + 0.02); g.gain.exponentialRampToValueAtTime(0.0001, t + 0.22);
      o.connect(g).connect(ctx.destination); o.start(t); o.stop(t + 0.24);
    });
  };

  // Keep keyboard focus inside an open dialog/drawer.
  const trapFocus = (root, e) => {
    if (e.key !== 'Tab') return;
    const f = [...root.querySelectorAll('a[href], button:not([disabled]), select, textarea, input, [tabindex]:not([tabindex="-1"])')].filter((x) => x.offsetParent !== null);
    if (!f.length) return;
    if (e.shiftKey && document.activeElement === f[0]) { e.preventDefault(); f[f.length - 1].focus(); }
    else if (!e.shiftKey && document.activeElement === f[f.length - 1]) { e.preventDefault(); f[0].focus(); }
  };
  const typing = (e) => { const t = e.target; return t && (t.tagName === 'INPUT' || t.tagName === 'SELECT' || t.tagName === 'TEXTAREA' || t.isContentEditable); };

  window.NW = { nightBand, recordForm, bindRecordForms, filedBadge, isDirty, audio, tone, trapFocus, typing, camState, camStateHTML, cameraControls, syncCameraControls, handleCameraClick, offlineBadge, esc, icon, paths: P, LEVELS, SEVERITY, badge, ladder, ring, updateRing, timeline, histKind, limitFor, contactsDone, post };
})();
