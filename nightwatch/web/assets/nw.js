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

  window.NW = { esc, icon, paths: P, LEVELS, SEVERITY, badge, ladder, ring, updateRing, timeline, histKind, limitFor, contactsDone, post };
})();
