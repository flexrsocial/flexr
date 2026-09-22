/* FLEXR Admin-Tool.

   Bis zum 22.09.2026 stand dieses Skript inline in admin.html. Ausgelagert,
   damit /admin.html eine Content-Security-Policy ohne 'unsafe-inline' fuer
   Skripte bekommen kann (siehe deploy/nginx-flexr.conf): Ein eingeschleustes
   <script> oder onclick="..." laeuft dort dann schlicht nicht. */
(function(){
  const $ = (id) => document.getElementById(id);
  const API_BASE = (location.hostname === 'localhost' || location.hostname === '127.0.0.1')
    ? 'http://localhost:8000'
    : '';

  // Die Anmeldung steckt seit dem 22.09.2026 in einem HttpOnly-Cookie, das
  // dieses Skript gar nicht lesen kann (siehe backend security.get_current_admin).
  // Vorher lag das Token im localStorage - lesbar fuer jedes eingeschleuste
  // Skript, und dieses Token oeffnet Ausweisaufnahmen. Den Altbestand raeumen.
  try{ localStorage.removeItem('flexr_admin_token'); }catch(e){}
  let currentPhotoStatus = 'pending';

  function toast(msg){
    const t = document.createElement('div');
    t.className = 'toast';
    t.textContent = msg;
    document.body.appendChild(t);
    setTimeout(() => t.remove(), 2600);
  }

  function escapeHtml(s){
    return String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  }

  function fmtDate(iso){
    // parseUTC, nicht new Date: sonst rutscht alles zwischen Mitternacht und
    // dem lokalen UTC-Offset (im Sommer 2 Stunden) auf den Vortag.
    try{ return parseUTC(iso).toLocaleDateString('de-AT', {day:'2-digit', month:'2-digit', year:'numeric'}); }
    catch(e){ return iso; }
  }
  // Server liefert naive UTC-Zeitstempel ohne Zeitzone - als UTC interpretieren
  function parseUTC(iso){
    if(!iso) return null;
    const hasTz = /[zZ]|[+-]\d{2}:?\d{2}$/.test(iso);
    return new Date(hasTz ? iso : iso + 'Z');
  }
  function fmtDateTime(iso){
    try{ return parseUTC(iso).toLocaleString('de-AT', {day:'2-digit', month:'2-digit', year:'numeric', hour:'2-digit', minute:'2-digit'}); }
    catch(e){ return iso; }
  }
  function isMutedNow(iso){
    const d = parseUTC(iso);
    return d && d > new Date();
  }
  // Art. 17 DSA: Jede Beschränkung braucht eine Begründung, die der Betroffene
  // zu sehen bekommt. Gibt null zurück, wenn abgebrochen wurde.
  function askModerationReason(what){
    const note = prompt(
      `Begründung für die ${what} (bekommt der Nutzer wörtlich angezeigt):`,
      'Verstoß gegen die Nutzungsrichtlinien: ',
    );
    if(note === null) return null;
    if(note.trim().length < 3){ toast('Bitte eine Begründung angeben.'); return null; }
    return note.trim();
  }

  async function api(path, opts = {}){
    const headers = Object.assign({'Content-Type': 'application/json'}, opts.headers || {});
    // Pflicht-Header fuer schreibende Anfragen per Cookie (CSRF-Schutz) -
    // eine fremde Seite kann ihn ohne CORS-Freigabe nicht setzen.
    headers['X-Flexr-Admin'] = '1';
    const res = await fetch(API_BASE + path, Object.assign({credentials: 'include'}, opts, {headers}));
    if(res.status === 401){
      showLogin();
      throw new Error('Sitzung abgelaufen. Bitte erneut einloggen.');
    }
    let data = null;
    try{ data = await res.json(); }catch(e){}
    if(!res.ok){
      let msg = 'Fehler (' + res.status + ')';
      if(data && data.detail){
        msg = Array.isArray(data.detail) ? data.detail.map(d => d.msg).join(', ') : data.detail;
      }
      throw new Error(msg);
    }
    return data;
  }

  // ---------- Pagination fuer Listen/Warteschlangen ----------
  // Die Backend-Endpunkte liefern nur bis zu `limit` Eintraege pro Aufruf
  // (Default 50, Gyms 100). Ohne diesen Mechanismus blieben Eintraege ab
  // Position 51 im Admin-Dashboard unsichtbar, ohne jeden Hinweis, dass es
  // ueberhaupt mehr gibt - bei Warteschlangen mit DSA-Fristen (Meldungen,
  // foermliche Meldungen) waere das mehr als ein UX-Problem.
  const PAGE_SIZE = 50;
  // Muss mit den `le=`-Obergrenzen der jeweiligen Backend-Routen
  // uebereinstimmen (admin.py) - sonst wuerde "Weitere laden" irgendwann
  // einen 422-Validierungsfehler statt neuer Eintraege liefern.
  const listLimit = { users: 50, photos: 50, gyms: 100, notices: 50, reports: 50, flagged: 50, verifications: 50 };
  const listLimitMax = { users: 200, photos: 200, gyms: 500, notices: 200, reports: 200, flagged: 200, verifications: 200 };
  function appendLoadMore(wrap, key, count, reload){
    if(count < listLimit[key]) return; // weniger als angefragt -> keine weitere Seite
    if(listLimit[key] >= listLimitMax[key]) return; // Obergrenze erreicht
    const holder = document.createElement('div');
    holder.style.textAlign = 'center';
    holder.style.margin = '14px 0';
    const btn = document.createElement('button');
    btn.className = 'btn secondary small';
    btn.textContent = 'Weitere laden';
    btn.addEventListener('click', () => {
      listLimit[key] = Math.min(listLimit[key] + PAGE_SIZE, listLimitMax[key]);
      btn.disabled = true;
      btn.textContent = 'Lädt …';
      reload();
    });
    holder.appendChild(btn);
    wrap.appendChild(holder);
  }

  function showLogin(){
    $('loginScreen').style.display = 'flex';
    $('appScreen').classList.remove('active');
  }
  function showApp(){
    $('loginScreen').style.display = 'none';
    $('appScreen').classList.add('active');
    loadDashboard();
  }

  // ---------- Login ----------
  // Nutzt bewusst fetch() direkt statt api(): Die 401-Antworten hier tragen
  // ein Detail (totp_required/totp_invalid), das die generische 401-Behandlung
  // in api() (showLogin()) verschlucken wuerde.
  $('btnLogin').addEventListener('click', async () => {
    const errEl = $('loginErr');
    errEl.textContent = '';
    const email = $('l-email').value.trim();
    const password = $('l-password').value;
    const totpWrap = $('l-totp-wrap');
    const totpCode = $('l-totp').value.trim();
    if(!email || !password){ errEl.textContent = 'Bitte E-Mail und Passwort eingeben.'; return; }
    try{
      const res = await fetch(API_BASE + '/api/admin/auth/login', {
        method: 'POST',
        credentials: 'include',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({email, password, totp_code: totpCode || null}),
      });
      const data = await res.json().catch(() => null);
      if(!res.ok){
        const detail = data && data.detail;
        if(detail === 'totp_required'){
          totpWrap.style.display = 'block';
          errEl.textContent = 'Bitte den Code aus deiner Authenticator-App eingeben.';
          return;
        }
        if(detail === 'totp_invalid'){
          totpWrap.style.display = 'block';
          errEl.textContent = 'Code falsch oder abgelaufen. Erneut versuchen.';
          return;
        }
        errEl.textContent = detail || 'Login fehlgeschlagen.';
        return;
      }
      // Das Token in der Antwort bleibt ungenutzt - der Browser haelt das
      // Cookie, das der Server gesetzt hat.
      $('l-password').value = '';
      showApp();
    }catch(err){
      errEl.textContent = 'Login fehlgeschlagen.';
    }
  });

  $('btnLogout').addEventListener('click', async () => {
    try{
      await fetch(API_BASE + '/api/admin/auth/logout', {method: 'POST', credentials: 'include'});
    }catch(e){ /* offline - das Cookie laeuft ohnehin ab */ }
    showLogin();
  });

  // ---------- Nav ----------
  document.querySelectorAll('.sidebar nav button').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.sidebar nav button').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const view = btn.dataset.view;
      document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
      $('view-' + view).classList.add('active');
      if(view === 'dashboard') loadDashboard();
      if(view === 'users') loadUsers();
      if(view === 'photos') loadPhotos();
      if(view === 'verifications') loadVerifications();
      if(view === 'reports') loadReports();
      if(view === 'gyms') loadGyms();
      if(view === 'security') loadSecurity();
    });
  });

  // ---------- Gyms ----------
  let currentGymStatus = 'pending';
  document.querySelectorAll('.gym-tab').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.gym-tab').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      currentGymStatus = btn.dataset.gymStatus;
      listLimit.gyms = 100;
      loadGyms();
    });
  });

  async function loadGyms(){
    const wrap = $('gymsTableWrap');
    try{
      const gyms = await api('/api/admin/gyms?status=' + currentGymStatus + '&limit=' + listLimit.gyms);
      if(gyms.length === 0){
        wrap.innerHTML = '<div class="empty-state">Keine Gyms in diesem Status.</div>';
        return;
      }
      wrap.innerHTML = `
        <table>
          <thead><tr><th>Name</th><th>Adresse</th><th>Eingereicht</th><th></th></tr></thead>
          <tbody>
            ${gyms.map(g => `
              <tr id="gymrow-${g.id}">
                <td>${escapeHtml(g.name)}</td>
                <td>${escapeHtml([`${g.street} ${g.house_number}`.trim(), `${g.plz} ${g.city}`.trim()].filter(Boolean).join(', ') || '—')}</td>
                <td>${g.created_at ? fmtDate(g.created_at) : '—'}</td>
                <td style="white-space:nowrap;">
                  <button class="btn small secondary" data-edit-gym="${g.id}">Bearbeiten</button>
                  ${g.status !== 'approved' ? `<button class="btn small" data-approve-gym="${g.id}">Freigeben</button>` : ''}
                  ${g.status !== 'rejected' ? `<button class="btn small secondary" data-reject-gym="${g.id}">Ablehnen</button>` : ''}
                  ${g.status === 'rejected' ? `<button class="btn small danger" data-delete-gym="${g.id}">Löschen</button>` : ''}
                </td>
              </tr>`).join('')}
          </tbody>
        </table>`;
      const gymById = Object.fromEntries(gyms.map(g => [g.id, g]));
      wrap.querySelectorAll('button[data-approve-gym]').forEach(btn => {
        btn.addEventListener('click', async () => {
          try{ await api(`/api/admin/gyms/${btn.dataset.approveGym}/approve`, {method: 'POST'});
            toast('Gym freigegeben.'); loadGyms(); loadDashboard(); }
          catch(err){ toast(err.message); }
        });
      });
      wrap.querySelectorAll('button[data-reject-gym]').forEach(btn => {
        btn.addEventListener('click', async () => {
          try{ await api(`/api/admin/gyms/${btn.dataset.rejectGym}/reject`, {method: 'POST'});
            toast('Gym abgelehnt.'); loadGyms(); loadDashboard(); }
          catch(err){ toast(err.message); }
        });
      });
      wrap.querySelectorAll('button[data-delete-gym]').forEach(btn => {
        btn.addEventListener('click', async () => {
          if(!confirm('Diesen abgelehnten Eintrag endgültig löschen?')) return;
          try{ await api(`/api/admin/gyms/${btn.dataset.deleteGym}`, {method: 'DELETE'});
            toast('Eintrag gelöscht.'); loadGyms(); loadDashboard(); }
          catch(err){ toast(err.message); }
        });
      });
      wrap.querySelectorAll('button[data-edit-gym]').forEach(btn => {
        btn.addEventListener('click', () => editGymRow(gymById[btn.dataset.editGym]));
      });
      appendLoadMore(wrap, 'gyms', gyms.length, loadGyms);
    }catch(err){
      wrap.innerHTML = `<div class="empty-state">${escapeHtml(err.message)}</div>`;
    }
  }

  function editGymRow(g){
    const row = $(`gymrow-${g.id}`);
    if(!row) return;
    const canApprove = g.status !== 'approved';
    row.innerHTML = `
      <td colspan="4">
        <div class="gym-edit">
          <input class="gym-edit-input" data-f="name" placeholder="Name" value="${escapeHtml(g.name)}">
          <input class="gym-edit-input" data-f="street" placeholder="Straße" value="${escapeHtml(g.street)}">
          <input class="gym-edit-input short" data-f="house_number" placeholder="Nr." value="${escapeHtml(g.house_number)}">
          <input class="gym-edit-input short" data-f="plz" placeholder="PLZ" inputmode="numeric" maxlength="4" value="${escapeHtml(g.plz)}">
          <input class="gym-edit-input" data-f="city" placeholder="Ort" value="${escapeHtml(g.city)}">
          <div class="gym-edit-actions">
            ${canApprove ? `<button class="btn small" data-save-approve>Speichern &amp; Freigeben</button>` : ''}
            <button class="btn small secondary" data-save>Speichern</button>
            <button class="btn small secondary" data-cancel>Abbrechen</button>
          </div>
        </div>
      </td>`;

    const collect = () => {
      const vals = {};
      row.querySelectorAll('.gym-edit-input').forEach(i => { vals[i.dataset.f] = i.value.trim(); });
      return vals;
    };
    const validate = (v) => {
      if(v.name.length < 2){ toast('Name ist zu kurz.'); return false; }
      if(!/^\d{4}$/.test(v.plz)){ toast('PLZ muss 4 Ziffern haben.'); return false; }
      return true;
    };
    const save = async (thenApprove) => {
      const v = collect();
      if(!validate(v)) return;
      try{
        await api(`/api/admin/gyms/${g.id}`, {method: 'PATCH', body: JSON.stringify(v)});
        if(thenApprove) await api(`/api/admin/gyms/${g.id}/approve`, {method: 'POST'});
        toast(thenApprove ? 'Gespeichert & freigegeben.' : 'Änderungen gespeichert.');
        loadGyms(); loadDashboard();
      }catch(err){ toast(err.message); }
    };

    const sa = row.querySelector('button[data-save-approve]');
    if(sa) sa.addEventListener('click', () => save(true));
    row.querySelector('button[data-save]').addEventListener('click', () => save(false));
    row.querySelector('button[data-cancel]').addEventListener('click', () => loadGyms());
  }

  // ---------- Dashboard ----------
  const COUNTRY_NAMES = {AT:'Österreich', DE:'Deutschland', CH:'Schweiz', IT:'Italien',
    SI:'Slowenien', CZ:'Tschechien', SK:'Slowakei', HU:'Ungarn', XX:'Andere'};

  function setNavBadge(id, count){
    const badge = $(id);
    if(!badge) return;
    if(count > 0){ badge.textContent = count; badge.style.display = 'inline-block'; }
    else { badge.style.display = 'none'; }
  }

  function taskChip(count, label, sub, view){
    const has = count > 0;
    return `<div class="task-chip ${has ? 'has' : 'done'}" ${has ? `data-goto="${view}"` : ''}>
      <div class="t-count">${has ? count : '✓'}</div>
      <div><div class="t-lbl">${label}</div><div class="t-sub">${has ? sub : 'nichts offen'}</div></div>
    </div>`;
  }

  async function loadDashboard(){
    try{
      const stats = await api('/api/admin/stats');

      // Offene Aufgaben
      const tasks = [
        [stats.pending_photos, 'Fotos freigeben', 'warten auf Prüfung', 'photos'],
        [stats.pending_verifications, 'Verifizierungen', 'Alter & Identität prüfen', 'verifications'],
        [stats.open_notices, 'Förmliche Meldungen', 'nach Art. 16 DSA', 'reports'],
        [stats.open_reports, 'Meldungen', 'abzuarbeiten', 'reports'],
        [stats.flagged_messages, 'Auffällige Nachrichten', 'im Review', 'reports'],
        [stats.pending_gyms, 'Gym-Vorschläge', 'freizugeben', 'gyms'],
      ];
      const openCount = tasks.reduce((s, t) => s + (t[0] > 0 ? 1 : 0), 0);
      $('tasksPanel').innerHTML = `
        <div class="tasks-title">Offene Aufgaben ${openCount === 0 ? '— <span style="color:var(--lime)">alles erledigt 🎉</span>' : ''}</div>
        <div class="tasks-row">${tasks.map(t => taskChip(...t)).join('')}</div>`;
      $('tasksPanel').querySelectorAll('.task-chip[data-goto]').forEach(chip => {
        chip.addEventListener('click', () => {
          document.querySelector(`.sidebar nav button[data-view="${chip.dataset.goto}"]`).click();
        });
      });

      // Kennzahlen
      $('statGrid').innerHTML = `
        <div class="stat-card"><div class="val">${stats.active_today}</div><div class="lbl">Heute aktiv</div></div>
        <div class="stat-card"><div class="val">${stats.new_today}</div><div class="lbl">Neu heute</div></div>
        <div class="stat-card"><div class="val">${stats.total_users}</div><div class="lbl">Nutzer gesamt</div></div>
        <div class="stat-card"><div class="val">${stats.active_subscriptions}</div><div class="lbl">Aktive Abos</div></div>
        <div class="stat-card"><div class="val">${stats.free_users}</div><div class="lbl">Ohne Premium</div></div>
        <div class="stat-card"><div class="val">${stats.banned_users}</div><div class="lbl">Gesperrt</div></div>
        <div class="stat-card"><div class="val">${stats.deleted_users}</div><div class="lbl">In Löschung</div></div>
      `;

      // Nav-Badges
      setNavBadge('pendingBadge', stats.pending_photos);
      setNavBadge('verifyBadge', stats.pending_verifications);
      setNavBadge('reportsBadge', stats.open_notices + stats.open_reports + stats.flagged_messages);
      setNavBadge('gymsBadge', stats.pending_gyms);

      loadAccessStats();
    }catch(err){
      toast(err.message);
    }
  }

  async function loadAccessStats(){
    try{
      const data = await api('/api/admin/access-stats?days=14');
      const max = Math.max(1, ...data.daily.map(d => d.count));
      $('accessChart').innerHTML = data.daily.map(d => {
        const h = Math.round((d.count / max) * 100);
        const label = new Date(d.day).toLocaleDateString('de-AT', {day:'2-digit', month:'2-digit'});
        return `<div class="access-bar-wrap">
          <div class="access-bar" style="height:${h}%" data-count="${d.count}"></div>
          <div class="access-bar-lbl">${label}</div>
        </div>`;
      }).join('');

      if(data.countries.length === 0){
        $('countryList').innerHTML = '<div class="empty-state" style="padding:20px;">Heute noch keine Zugriffe.</div>';
      } else {
        const cmax = Math.max(1, ...data.countries.map(c => c.count));
        $('countryList').innerHTML = data.countries.map(c => `
          <div class="country-row">
            <span class="c-code" title="${COUNTRY_NAMES[c.country] || c.country}">${c.country}</span>
            <span class="c-bar"><i style="width:${Math.round((c.count/cmax)*100)}%"></i></span>
            <span class="c-count">${c.count}</span>
          </div>`).join('');
      }
    }catch(err){
      $('accessChart').innerHTML = `<div class="empty-state">${escapeHtml(err.message)}</div>`;
    }
  }

  // ---------- Users ----------
  let userSearchTimeout = null;
  function resetUsersAndReload(){
    listLimit.users = PAGE_SIZE;
    loadUsers();
  }
  function scheduleUserReload(){
    clearTimeout(userSearchTimeout);
    listLimit.users = PAGE_SIZE;
    userSearchTimeout = setTimeout(loadUsers, 300);
  }
  $('userSearch').addEventListener('input', scheduleUserReload);
  $('userFilterBanned').addEventListener('change', resetUsersAndReload);
  $('userFilterSubscribed').addEventListener('change', resetUsersAndReload);
  $('userFilterVerificationRejected').addEventListener('change', resetUsersAndReload);

  async function loadUsers(){
    const wrap = $('usersTableWrap');
    const params = new URLSearchParams();
    const q = $('userSearch').value.trim();
    if(q) params.set('q', q);
    if($('userFilterBanned').value) params.set('banned', $('userFilterBanned').value);
    if($('userFilterSubscribed').value) params.set('subscribed', $('userFilterSubscribed').value);
    if($('userFilterVerificationRejected').value) params.set('verification_rejected', $('userFilterVerificationRejected').value);
    params.set('limit', listLimit.users);
    try{
      const users = await api('/api/admin/users?' + params.toString());
      if(users.length === 0){
        wrap.innerHTML = '<div class="empty-state">Keine Nutzer gefunden.</div>';
        return;
      }
      wrap.innerHTML = `
        <table>
          <thead><tr>
            <th>Name</th><th>E-Mail</th><th>Alter</th><th>Stadt</th><th>Fotos</th>
            <th>Status</th><th>Registriert</th>
          </tr></thead>
          <tbody>
            ${users.map(u => `
              <tr data-user-id="${u.id}">
                <td>${escapeHtml(u.name)}${u.is_verified ? ' <span class="pill ok" title="Foto-verifiziert">✓</span>' : ''}</td>
                <td class="mono">${escapeHtml(u.email)}</td>
                <td>${u.age}</td>
                <td>${escapeHtml(u.city)}</td>
                <td>${u.photo_count}</td>
                <td>
                  ${u.deleted_at
                    ? `<span class="pill warn" title="Selbstlöschung am ${fmtDate(u.deleted_at)} — Karenzzeit läuft">Gelöscht</span>`
                    : (u.is_banned ? '<span class="pill warn">Gesperrt</span>'
                      : (u.verification_rejected ? '<span class="pill warn" title="Jüngster Verifizierungsversuch endgültig abgelehnt — Fotos bereits gelöscht, Deck/Match/Chat gesperrt">Verifizierung abgelehnt</span>'
                        : (u.is_subscribed ? '<span class="pill ok">Premium</span>' : '<span class="pill muted">Gratis</span>')))}
                </td>
                <td>${fmtDate(u.created_at)}</td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      `;
      wrap.querySelectorAll('tbody tr').forEach(tr => {
        tr.addEventListener('click', () => openUserModal(tr.dataset.userId));
      });
      appendLoadMore(wrap, 'users', users.length, loadUsers);
    }catch(err){
      wrap.innerHTML = `<div class="empty-state">${escapeHtml(err.message)}</div>`;
    }
  }

  async function openUserModal(userId){
    $('userModalBackdrop').classList.add('open');
    $('userModalBody').innerHTML = '<div class="loading">Lädt …</div>';
    try{
      const u = await api('/api/admin/users/' + userId);
      renderUserModal(u);
    }catch(err){
      $('userModalBody').innerHTML = `<div class="empty-state">${escapeHtml(err.message)}</div>`;
    }
  }

  function renderUserModal(u){
    // Selbstgelöschte Konten zuerst: solange die Karenzzeit läuft, ist das
    // Konto für andere unsichtbar und der Nutzer kommt nicht hinein. Ohne
    // diesen Hinweis wirkte es in der Ansicht wie ein normales aktives Konto.
    const statusBadge = u.deleted_at
      ? '<span class="pill warn">Gelöscht</span>'
      : (u.is_banned
        ? '<span class="pill warn">Gesperrt</span>'
        : (u.verification_rejected
          ? '<span class="pill warn" title="Jüngster Verifizierungsversuch endgültig abgelehnt — Fotos bereits gelöscht, Deck/Match/Chat gesperrt">Verifizierung abgelehnt</span>'
        // is_active gibt es seit dem 10.09.2026 nur noch als Altfeld und ist
        // immer true - die Bezahlwand ist abgeschafft, ein Konto kann nicht
        // mehr "inaktiv" sein. Unterschieden wird nur noch Premium/Gratis.
          : (u.is_subscribed
            ? '<span class="pill ok">FLEXR Premium</span>'
            : '<span class="pill muted">Gratis</span>')));

    $('userModalBody').innerHTML = `
      <h3>${escapeHtml(u.name)}, ${u.age}</h3>
      <div class="modal-sub">${escapeHtml(u.email)} · ${escapeHtml(u.city)} ${statusBadge}</div>
      ${u.photos.length ? `<div class="photo-strip">${u.photos.map(p => `<img src="${escapeHtml(p.url)}" title="${p.status}" style="${p.status !== 'approved' ? 'opacity:.5' : ''}">`).join('')}</div>` : '<p class="modal-sub">Keine Fotos hochgeladen.</p>'}
      <div class="detail-row"><span class="k">Geschlecht / Interesse</span><span>${escapeHtml(u.gender)} · sucht ${escapeHtml(u.interest)}</span></div>
      <div class="detail-row"><span class="k">Adresse</span><span>${escapeHtml(u.plz)} ${escapeHtml(u.city)}</span></div>
      <div class="detail-row"><span class="k">Gym</span><span>${escapeHtml(u.gym)}</span></div>
      <div class="detail-row"><span class="k">Bio</span><span>${escapeHtml(u.bio || '—')}</span></div>
      <div class="detail-row"><span class="k">Registriert am</span><span>${fmtDate(u.created_at)}</span></div>
      ${u.deleted_at ? `<div class="detail-row"><span class="k">Selbst gelöscht</span><span>${fmtDate(u.deleted_at)}${u.purge_at ? ` · endgültige Löschung ${fmtDate(u.purge_at)}` : ''}</span></div>` : ''}
      <!-- trial_ends_at ist ein Restfeld ohne Bedeutung (kein Probemonat mehr)
           und wird deshalb nicht mehr angezeigt. -->
      <div class="detail-row"><span class="k">Stripe-Kunde</span><span class="mono">${escapeHtml(u.stripe_customer_id || '—')}</span></div>
      <div class="detail-row"><span class="k">Telefon</span><span>${u.phone ? `${escapeHtml(u.phone)} ${u.phone_verified ? '<span class="pill ok">bestätigt</span>' : '<span class="pill muted">unbestätigt</span>'}` : '—'}</span></div>
      <div class="detail-row"><span class="k">Profil-Verifizierung</span><span>${u.is_verified ? '<span class="pill ok">verifiziert ✓</span>' : '<span class="pill muted">nicht verifiziert</span>'}</span></div>
      <div class="detail-row"><span class="k">Altersprüfung</span><span>${
        u.age_verified
          ? `<span class="pill ok">geprüft ✓</span> <span class="pill muted">${escapeHtml(u.verification_method || '')}${u.age_verified_at ? ' · ' + fmtDate(u.age_verified_at) : ''}</span>`
          : '<span class="pill muted">nicht geprüft</span>'}</span></div>
      <div class="detail-row"><span class="k">Konto freigeschaltet</span><span>${
        u.is_account_activated
          ? `<span class="pill ok">ja${u.activated_at ? ' · ' + fmtDate(u.activated_at) : ' (Bestandskonto)'}</span>`
          : '<span class="pill warn">nein — Prüfung offen</span>'}
        ${/* Zwei Fälle brauchen den Knopf: ein Bestandskonto, das noch nie
              geprüft werden musste - und ein Konto, das an einer endgültigen
              Ablehnung feststeckt. Beim zweiten war er bislang ausgeblendet,
              weil verification_required dort gesetzt bleibt. Genau dieses
              Konto kommt aber ohne ihn nie wieder heraus: Fotos sind gelöscht,
              /verification/start verweigert wegen der bindenden Entscheidung,
              und require-verification ist der einzige Weg, der die frühere
              Ablehnung durch ein neues verification_required_at entwertet. */''}
        ${(!u.verification_required || !u.is_account_activated)
          ? `<button class="btn secondary small" id="btnRequireVerification" data-user="${escapeHtml(u.id)}" style="margin-left:8px;">${u.verification_required ? 'Prüfung neu anfordern' : 'Prüfung nachfordern'}</button>`
          : ''}
      </span></div>
      <div class="detail-row"><span class="k">Chat-Sperre</span><span>${
        isMutedNow(u.messaging_muted_until)
          ? `<span class="pill warn">gesperrt bis ${fmtDateTime(u.messaging_muted_until)} Uhr</span>`
          : '<span class="pill ok">Chat frei</span>'}</span></div>
      ${u.moderation_reason ? `
      <div class="detail-row"><span class="k">Begründung</span><span>${escapeHtml(u.moderation_reason)}${
        u.moderation_action_at ? ` <span class="pill muted">${fmtDate(u.moderation_action_at)}</span>` : ''}</span></div>` : ''}
      <div class="detail-row"><span class="k">Geräte</span><span>${
        u.devices && u.devices.length
          ? u.devices.map(d => `<span class="mono">${escapeHtml(d.device_id.slice(0, 14))}…</span>${
              d.shared_with.length
                ? ` <span class="pill warn" title="Weitere Konten auf diesem Gerät">auch: ${escapeHtml(d.shared_with.join(', '))}</span>`
                : ''
            }`).join('<br>')
          : '—'
      }</span></div>
      <div class="modal-actions tight">
        <select id="muteDur">
          <option value="h1">1 Stunde</option>
          <option value="h5">5 Stunden</option>
          <option value="h12">12 Stunden</option>
          <option value="d1">1 Tag</option>
          <option value="d3">3 Tage</option>
          <option value="d7" selected>7 Tage</option>
          <option value="d14">14 Tage</option>
          <option value="d30">30 Tage</option>
        </select>
        <button class="btn secondary" id="btnMute">Chat sperren</button>
        ${isMutedNow(u.messaging_muted_until)
          ? `<button class="btn secondary" id="btnUnmute">Sperre aufheben</button>`
          : ''}
        ${u.is_banned
          ? `<button class="btn secondary" id="btnUnban">Entsperren</button>`
          : `<button class="btn secondary" id="btnBan">Sperren</button>`}
        <button class="btn danger" id="btnDeleteUser">Endgültig löschen</button>
      </div>
    `;

    $('btnMute').addEventListener('click', async () => {
      const val = $('muteDur').value;               // z. B. "h5" oder "d7"
      const n = parseInt(val.slice(1), 10);
      // Art. 17 DSA: ohne Begründung keine Sperre — der Text geht an den Nutzer.
      const reason = askModerationReason('Chat-Sperre');
      if(reason === null) return;
      const body = val[0] === 'h' ? {hours: n, reason} : {days: n, reason};
      const label = val[0] === 'h'
        ? `${n} Stunde(n)` : `${n} Tag(e)`;
      try{
        await api(`/api/admin/users/${u.id}/mute`, {method: 'POST', body: JSON.stringify(body)});
        toast(`Chat für ${label} gesperrt.`);
        openUserModal(u.id);
      }catch(err){ toast(err.message); }
    });
    // Bestandskonto gezielt in die neue Alters-/Identitätsprüfung holen. Das
    // Konto ist danach bis zur bestandenen Prüfung nicht mehr nutzbar.
    if($('btnRequireVerification')){
      $('btnRequireVerification').addEventListener('click', async () => {
        const erneut = !u.is_account_activated;
        if(!confirm(erneut
          ? 'Neuen Prüfungsdurchlauf freigeben? Eine frühere Ablehnung blockiert danach nicht mehr; das Konto bleibt bis zur bestandenen Prüfung gesperrt.'
          : 'Alters- und Identitätsprüfung nachfordern? Das Konto ist bis zur bestandenen Prüfung gesperrt.')) return;
        try{
          await api(`/api/admin/users/${u.id}/require-verification`, {method: 'POST'});
          toast('Prüfung nachgefordert.');
          openUserModal(u.id);
        }catch(err){ toast(err.message); }
      });
    }

    if($('btnUnmute')){
      $('btnUnmute').addEventListener('click', async () => {
        try{
          await api(`/api/admin/users/${u.id}/unmute`, {method: 'POST'});
          toast('Chat-Sperre aufgehoben.');
          openUserModal(u.id);
        }catch(err){ toast(err.message); }
      });
    }

    if(u.is_banned){
      $('btnUnban').addEventListener('click', async () => {
        try{ await api(`/api/admin/users/${u.id}/unban`, {method: 'POST'}); toast('Nutzer entsperrt.'); closeUserModal(); loadUsers(); loadDashboard(); }
        catch(err){ toast(err.message); }
      });
    } else {
      $('btnBan').addEventListener('click', async () => {
        const reason = askModerationReason('Kontosperre');
        if(reason === null) return;
        try{
          await api(`/api/admin/users/${u.id}/ban`, {method: 'POST', body: JSON.stringify({reason})});
          toast('Nutzer gesperrt.'); closeUserModal(); loadUsers(); loadDashboard();
        }
        catch(err){ toast(err.message); }
      });
    }
    $('btnDeleteUser').addEventListener('click', async () => {
      if(!confirm(`${u.name} (${u.email}) wirklich endgültig löschen? Das kann nicht rückgängig gemacht werden.`)) return;
      try{ await api(`/api/admin/users/${u.id}`, {method: 'DELETE'}); toast('Nutzer gelöscht.'); closeUserModal(); loadUsers(); loadDashboard(); }
      catch(err){ toast(err.message); }
    });
  }

  function closeUserModal(){
    $('userModalBackdrop').classList.remove('open');
  }
  $('userModalClose').addEventListener('click', closeUserModal);
  $('userModalBackdrop').addEventListener('click', (e) => {
    if(e.target === $('userModalBackdrop')) closeUserModal();
  });

  // ---------- Photos ----------
  // Nur die Foto-Tabs, nicht jeder .tab-btn: Die Gym-Tabs tragen dieselbe
  // Klasse, aber data-gym-status. Ungefiltert fing dieser Handler sie mit ab,
  // setzte currentPhotoStatus auf undefined und lud die Foto-Freigabe mit
  // status=undefined neu - das Backend antwortete 400, und die Foto-Freigabe
  // blieb bis zum Neuladen der Seite auf der Fehlermeldung stehen.
  const photoTabs = document.querySelectorAll('.tab-btn[data-status]');
  photoTabs.forEach(btn => {
    btn.addEventListener('click', () => {
      photoTabs.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      currentPhotoStatus = btn.dataset.status;
      listLimit.photos = PAGE_SIZE;
      loadPhotos();
    });
  });

  // Art. 17 DSA: Eine Fotoablehnung braucht einen konkreten Grund. Das Backend
  // unterstützt diese strukturierten Gründe bereits; das Admin-Tool muss sie
  // deshalb mitsenden, statt jede Ablehnung pauschal als "technisch unbrauchbar"
  // zu verbuchen.
  const PHOTO_REJECTION_REASONS = [
    ['no_person', 'Keine Person erkennbar'],
    ['not_account_holder', 'Zeigt nicht den Kontoinhaber'],
    ['multiple_people', 'Mehrere Personen / Zuordnung unklar'],
    ['nudity', 'Sexuell explizite Darstellung'],
    ['violence', 'Gewalt- oder Hassdarstellung'],
    ['minor', 'Offenkundig minderjährige Person'],
    ['contact_details', 'Kontaktdaten oder Links im Bild'],
    ['third_party_rights', 'Fremdes Bildmaterial oder Werbung'],
    ['unusable', 'Technisch nicht ausreichend nutzbar'],
    ['other', 'Anderer Verstoß gegen die Profilfoto-Richtlinien'],
  ];

  /* Ablehnungsdialog statt zweier prompt()-Fenster.

     Vorher musste der Prüfer die Nummer eines Grundes aus einer Liste 1-10
     abtippen - bei einem Schritt, der mehrmals täglich vorkommt, und ohne das
     Bild vor Augen: prompt() blendet die Seite aus. Ein Vertipper landete
     nicht etwa beim falschen Grund, sondern brach den ganzen Vorgang ab.

     Der Dialog zeigt das betroffene Bild, die Gründe als Auswahlliste und das
     Ergänzungsfeld für "Anderer Verstoß" erst dann, wenn es gebraucht wird.
     Geliefert wird dieselbe Struktur wie vorher ({reason} bzw.
     {reason, note}) - am Server ändert sich nichts. */
  let rejectAufloesen = null;

  function fuelleAblehnungsgruende(){
    const wrap = $('rejectReasons');
    wrap.innerHTML = PHOTO_REJECTION_REASONS.map(([wert, label]) => `
      <label data-reason="${wert}">
        <input type="radio" name="rejectReason" value="${wert}">
        <span>${escapeHtml(label)}</span>
      </label>`).join('');
    wrap.querySelectorAll('input[name="rejectReason"]').forEach(radio => {
      radio.addEventListener('change', () => {
        wrap.querySelectorAll('label').forEach(l => l.classList.toggle('picked', l.dataset.reason === radio.value));
        // Das Ergänzungsfeld gehört nur zu "other" - sonst steht es im Weg.
        $('rejectNoteWrap').style.display = radio.value === 'other' ? 'block' : 'none';
        $('rejectErr').textContent = '';
        if(radio.value === 'other') $('rejectNote').focus();
      });
    });
  }

  /* Öffnet den Dialog und liefert ein Promise auf {reason[, note]} bzw. null
     bei Abbruch - damit bleibt die Aufrufstelle so schlicht wie mit prompt(). */
  function askPhotoRejection(photo){
    return new Promise(resolve => {
      fuelleAblehnungsgruende();
      $('rejectPreviewImg').src = photo && photo.url ? photo.url : '';
      $('rejectPreviewImg').alt = photo ? `Zu prüfendes Foto von ${photo.user_name}` : '';
      $('rejectPreviewName').textContent = photo ? photo.user_name : '';
      $('rejectPreviewMail').textContent = photo ? photo.user_email : '';
      $('rejectNote').value = '';
      $('rejectNoteWrap').style.display = 'none';
      $('rejectErr').textContent = '';
      $('rejectModalBackdrop').classList.add('open');
      rejectAufloesen = resolve;
    });
  }

  function schliesseAblehnung(ergebnis){
    $('rejectModalBackdrop').classList.remove('open');
    const aufloesen = rejectAufloesen;
    rejectAufloesen = null;
    if(aufloesen) aufloesen(ergebnis);
  }

  $('rejectConfirm').addEventListener('click', () => {
    const gewaehlt = document.querySelector('input[name="rejectReason"]:checked');
    if(!gewaehlt){
      $('rejectErr').textContent = 'Bitte einen Grund auswählen.';
      return;
    }
    if(gewaehlt.value !== 'other'){
      schliesseAblehnung({reason: gewaehlt.value});
      return;
    }
    const note = $('rejectNote').value.trim();
    if(note.length < 3){
      $('rejectErr').textContent = 'Bitte den anderen Ablehnungsgrund kurz erläutern.';
      $('rejectNote').focus();
      return;
    }
    schliesseAblehnung({reason: gewaehlt.value, note});
  });

  $('rejectCancel').addEventListener('click', () => schliesseAblehnung(null));
  $('rejectModalClose').addEventListener('click', () => schliesseAblehnung(null));
  $('rejectModalBackdrop').addEventListener('click', (e) => {
    if(e.target === $('rejectModalBackdrop')) schliesseAblehnung(null);
  });
  document.addEventListener('keydown', (e) => {
    if(e.key === 'Escape' && $('rejectModalBackdrop').classList.contains('open')) schliesseAblehnung(null);
  });

  async function loadPhotos(){
    const wrap = $('photoGridWrap');
    wrap.innerHTML = '<div class="loading">Lädt …</div>';
    try{
      const photos = await api('/api/admin/photos?status=' + currentPhotoStatus + '&limit=' + listLimit.photos);
      if(photos.length === 0){
        wrap.innerHTML = '<div class="empty-state">Keine Fotos in diesem Status.</div>';
        return;
      }
      wrap.innerHTML = `<div class="photo-mod-grid">${photos.map(p => `
        <div class="photo-mod-card" data-photo-id="${p.id}">
          <img src="${escapeHtml(p.url)}" loading="lazy">
          <div class="meta">
            <div class="nm">${escapeHtml(p.user_name)}</div>
            <div class="mono">${escapeHtml(p.user_email)}</div>
          </div>
          <div class="actions">
            ${p.status !== 'approved' ? `<button class="btn small" data-action="approve">Freigeben</button>` : ''}
            ${p.status !== 'rejected' ? `<button class="btn secondary small" data-action="reject">Ablehnen</button>` : ''}
            <button class="btn danger small" data-action="delete">Löschen</button>
          </div>
        </div>
      `).join('')}</div>`;

      wrap.querySelectorAll('.photo-mod-card').forEach(card => {
        const photoId = card.dataset.photoId;
        // Der Ablehnungsdialog zeigt das Bild - dafuer wird der ganze Datensatz
        // gebraucht, nicht nur die ID.
        const photo = photos.find(x => x.id === photoId);
        card.querySelectorAll('button[data-action]').forEach(btn => {
          btn.addEventListener('click', async () => {
            const action = btn.dataset.action;
            try{
              if(action === 'approve') await api(`/api/admin/photos/${photoId}/approve`, {method: 'POST'});
              if(action === 'reject'){
                const rejection = await askPhotoRejection(photo);
                if(rejection === null) return;
                await api(`/api/admin/photos/${photoId}/reject`, {
                  method: 'POST', body: JSON.stringify(rejection),
                });
              }
              if(action === 'delete'){
                if(!confirm('Foto wirklich löschen?')) return;
                await api(`/api/admin/photos/${photoId}`, {method: 'DELETE'});
              }
              toast('Erledigt.');
              loadPhotos();
              loadDashboard();
            }catch(err){ toast(err.message); }
          });
        });
      });
      appendLoadMore(wrap, 'photos', photos.length, loadPhotos);
    }catch(err){
      wrap.innerHTML = `<div class="empty-state">${escapeHtml(err.message)}</div>`;
    }
  }

  // ---------- Alters- und Identitätsprüfung ----------
  // Eine konsolidierte Ansicht pro Vorgang: Accountdaten, Profilfotos,
  // Verifizierungs-Selfies und Ausweisaufnahmen. Freigeben ist erst möglich,
  // wenn jeder Punkt der Checkliste bestätigt wurde (der Server prüft das
  // ebenfalls und lehnt unvollständige Bestätigungen ab).
  const CHECKLIST = [
    ['selfie_matches_profile_photos', 'Selfie entspricht den Profilbildern'],
    ['selfie_matches_document', 'Selfie entspricht der Person auf dem Ausweis'],
    ['document_shows_min_age', 'Ausweis zeigt ein Alter von mindestens 18 Jahren'],
    ['document_dob_matches_registration', 'Geburtsdatum auf dem Ausweis stimmt mit der Registrierung überein'],
    ['document_legible', 'Dokument ist für die Prüfung ausreichend lesbar'],
    ['document_plausible', 'Dokument wirkt plausibel/gültig'],
  ];

  const REASON_OPTIONS = [
    ['document_unreadable', 'Dokument unleserlich'],
    ['details_not_visible', 'Notwendige Angaben nicht sichtbar'],
    ['person_mismatch', 'Person stimmt nicht überein'],
    ['dob_mismatch', 'Geburtsdatum stimmt nicht überein'],
    ['underage', 'Unter 18'],
    ['document_unsuitable', 'Dokument ungeeignet'],
    ['selfie_unusable', 'Selfies nicht verwertbar'],
    ['other', 'Sonstiger Prüfgrund'],
  ];

  const DOC_TYPE_LABELS = {
    id_card: 'Personalausweis',
    passport: 'Reisepass',
    drivers_license: 'Führerschein',
  };

  const SIDE_LABELS = {front: 'Vorderseite', back: 'Rückseite'};

  // Das Geburtsdatum kommt als reines Datum ("1997-06-15"). fmtDate() hängt für
  // Zeitstempel ein "Z" an - bei einem Datum ohne Uhrzeit lehnen strengere
  // Browser das ab, deshalb hier eine eigene, simple Umformung.
  function fmtDateOnly(iso){
    const parts = String(iso || '').split('-');
    return parts.length === 3 ? `${parts[2]}.${parts[1]}.${parts[0]}` : escapeHtml(iso || '—');
  }

  async function loadVerifications(){
    const wrap = $('verificationsWrap');
    wrap.innerHTML = '<div class="loading">Lädt …</div>';
    renderCleanupWarning();
    try{
      const reqs = await api('/api/admin/verifications?limit=' + listLimit.verifications);
      if(reqs.length === 0){
        wrap.innerHTML = '<div class="empty-state">Keine offenen Verifizierungen.</div>';
        return;
      }
      wrap.innerHTML = reqs.map(renderVerificationCard).join('');
      wrap.querySelectorAll('.verify-review-card').forEach(wireVerificationCard);
      appendLoadMore(wrap, 'verifications', reqs.length, loadVerifications);
    }catch(err){
      wrap.innerHTML = `<div class="empty-state">${escapeHtml(err.message)}</div>`;
    }
  }

  // Warnt, wenn nach einer Entscheidung noch Aufnahmen im Storage liegen
  // (Löschung fehlgeschlagen). Der Aufräumlauf wiederholt sie beim nächsten
  // Login eines Nutzers.
  async function renderCleanupWarning(){
    const box = $('cleanupWarning');
    box.innerHTML = '';
    try{
      const stats = await api('/api/admin/stats');
      if(stats.pending_verification_cleanups > 0){
        box.innerHTML = `<div class="cleanup-warning">
          <b>${stats.pending_verification_cleanups} entschiedene Prüfung(en) sind noch nicht aufgeräumt.</b>
          Die Aufnahmen konnten nicht aus dem Storage gelöscht werden. Der Aufräumlauf
          versucht es automatisch erneut — bleibt die Zahl bestehen, den
          Storage-Zugang prüfen.
        </div>`;
      }
    }catch(err){ /* Statistik ist hier nur ein Hinweis */ }
  }

  function renderVerificationCard(r){
    const docLabel = r.document_type ? (DOC_TYPE_LABELS[r.document_type] || r.document_type) : null;
    return `
      <div class="verify-review-card" data-req-id="${r.id}">
        <div class="meta">
          <div class="nm">${escapeHtml(r.user_name)}</div>
          <div class="mono">${escapeHtml(r.user_email)}</div>
        </div>
        <div class="verify-facts">
          <span><span class="k">Account-ID</span><span class="v">${escapeHtml(r.user_id)}</span></span>
          <span><span class="k">Angegebenes Geburtsdatum</span><span class="v">${fmtDateOnly(r.user_birthdate)}</span></span>
          <span><span class="k">Errechnetes Alter</span><span class="v">${r.user_age}</span></span>
          <span><span class="k">Registriert</span><span class="v">${fmtDate(r.user_registered_at)}</span></span>
          <span><span class="k">Eingereicht</span><span class="v">${fmtDate(r.submitted_at || r.created_at)}</span></span>
        </div>

        <div class="verify-cols">
          <div>
            <div class="verify-col-title">Verifizierungs-Selfies (mit der Anweisung, die der Server gestellt hat)</div>
            <!-- Kein loading="lazy": Diese URLs sind nur 60 Sekunden gültig
                 (storage.DOCUMENT_VIEW_URL_TTL_SECONDS) - mit Lazy-Loading laedt
                 der Browser sie erst beim Scrollen ins Bild und die Signatur ist
                 bis dahin oft schon abgelaufen (kaputtes Bild statt Foto). -->
            <div class="verify-imgs">
              ${r.selfie_urls.length
                ? r.selfie_urls.map(s => `
                  <figure>
                    <img src="${escapeHtml(s.url)}">
                    <figcaption>${escapeHtml(s.prompt)}</figcaption>
                  </figure>`).join('')
                : '<div class="verify-doc-missing">Keine Selfies vorhanden.</div>'}
            </div>
          </div>
          <div>
            <div class="verify-col-title">Profilfotos</div>
            <div class="verify-imgs">
              ${r.profile_photo_urls.length
                ? r.profile_photo_urls.map(u => `<figure><img src="${escapeHtml(u)}" loading="lazy"></figure>`).join('')
                : '<div class="mono">Keine Profilfotos</div>'}
            </div>
          </div>
        </div>

        <div style="margin-top:18px;">
          <div class="verify-col-title">
            Amtlicher Lichtbildausweis${docLabel ? ' — ' + escapeHtml(docLabel) : ''}
          </div>
          ${r.document_urls.length
            ? `<div class="verify-doc-imgs">${r.document_urls.map(d => `
                <figure>
                  <a href="${escapeHtml(d.url)}" target="_blank" rel="noopener">
                    <img src="${escapeHtml(d.url)}">
                  </a>
                  <figcaption>${escapeHtml(SIDE_LABELS[d.side] || d.side)} — zum Vergrößern anklicken</figcaption>
                </figure>`).join('')}</div>`
            : `<div class="verify-doc-missing">Keine Ausweisaufnahme vorhanden — dieser
                Vorgang stammt aus der Zeit vor der Ausweisprüfung. Über
                "Neue Aufnahme anfordern" den Ausweis nachfordern.</div>`}
        </div>

        <div class="verify-checklist">
          <div class="title">Prüfcheckliste — alle Punkte nötig</div>
          ${CHECKLIST.map(([key, label]) => `
            <label><input type="checkbox" data-check="${key}"> <span>${escapeHtml(label)}</span></label>
          `).join('')}
        </div>

        <div class="verify-reason">
          <label for="reason-${r.id}">Prüfgrund (für Ablehnung / neue Aufnahme):</label>
          <select id="reason-${r.id}" data-reason>
            ${REASON_OPTIONS.map(([v, l]) => `<option value="${v}">${escapeHtml(l)}</option>`).join('')}
          </select>
          <label>
            <input type="checkbox" data-redo-selfie> Selfies ebenfalls neu aufnehmen lassen
          </label>
        </div>

        <div class="actions">
          <button class="btn small" data-action="approve" disabled>Freigeben (blauer Haken)</button>
          <button class="btn secondary small" data-action="reupload">Neue Aufnahme anfordern</button>
          <button class="btn secondary small" data-action="reject">Endgültig ablehnen</button>
        </div>
      </div>`;
  }

  function wireVerificationCard(card){
    const reqId = card.dataset.reqId;
    const approveBtn = card.querySelector('button[data-action="approve"]');
    const checks = [...card.querySelectorAll('input[data-check]')];

    function refreshApproveState(){
      approveBtn.disabled = !checks.every(c => c.checked);
    }
    checks.forEach(c => c.addEventListener('change', refreshApproveState));

    card.querySelectorAll('button[data-action]').forEach(btn => {
      btn.addEventListener('click', async () => {
        const action = btn.dataset.action;
        const reasonCode = card.querySelector('select[data-reason]').value;
        const redoSelfie = card.querySelector('input[data-redo-selfie]').checked;
        try{
          let result;
          if(action === 'approve'){
            const checklist = {};
            checks.forEach(c => { checklist[c.dataset.check] = c.checked; });
            result = await api(`/api/admin/verifications/${reqId}/approve`, {
              method: 'POST', body: JSON.stringify(checklist),
            });
          } else if(action === 'reupload'){
            result = await api(`/api/admin/verifications/${reqId}/request-reupload`, {
              method: 'POST',
              body: JSON.stringify({reason_code: reasonCode, redo_selfie: redoSelfie}),
            });
          } else {
            if(!confirm('Verifizierung endgültig ablehnen? Das Konto bleibt gesperrt und kann die Prüfung nicht selbst neu starten.')) return;
            result = await api(`/api/admin/verifications/${reqId}/reject`, {
              method: 'POST', body: JSON.stringify({reason_code: reasonCode}),
            });
          }
          toast(result && result.documents_deleted === false
            ? 'Entschieden — ACHTUNG: Aufnahmen konnten nicht gelöscht werden, Aufräumlauf läuft nach.'
            : 'Erledigt — Selfies und Ausweisaufnahmen wurden gelöscht.');
          loadVerifications();
          loadDashboard();
        }catch(err){ toast(err.message); }
      });
    });
  }

  // ---------- Reports ----------
  async function loadReports(){
    // Auffällige Nachrichten immer laden - unabhängig davon, ob es offene
    // Meldungen gibt (sonst bliebe die Tabelle bei 0 Meldungen auf "Lädt …")
    loadNotices();
    loadFlaggedMessages();
    const wrap = $('reportsTableWrap');
    try{
      const reports = await api('/api/admin/reports?limit=' + listLimit.reports);
      if(reports.length === 0){
        wrap.innerHTML = '<div class="empty-state">Keine Meldungen.</div>';
        return;
      }
      wrap.innerHTML = `
        <table>
          <thead><tr><th>Aktenzeichen</th><th>Gemeldet von</th><th>Gemeldete Person</th><th>Grund</th><th>Datum</th><th></th></tr></thead>
          <tbody>
            ${reports.map(r => `
              <tr>
                <td class="mono">${escapeHtml(r.reference)}</td>
                <td>${escapeHtml(r.reporter_name)}</td>
                <td>${escapeHtml(r.reported_name)}</td>
                <td>${escapeHtml(r.reason)}</td>
                <td>${fmtDate(r.created_at)}</td>
                <td style="white-space:nowrap;">
                  <button class="btn small secondary" data-view-user="${r.reported_id}">Ansehen</button>
                  <button class="btn small secondary" data-decide-report="${r.id}" data-outcome="no_action">Kein Verstoß</button>
                  <button class="btn small secondary" data-decide-report="${r.id}" data-outcome="action_taken">Eingeschritten</button>
                </td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      `;
      wrap.querySelectorAll('button[data-view-user]').forEach(btn => {
        btn.addEventListener('click', (e) => {
          e.stopPropagation();
          openUserModal(btn.dataset.viewUser);
        });
      });
      // Art. 16 Abs. 5 DSA: Die Meldung wird nicht still abgehakt — der
      // Melder bekommt Ergebnis und Begründung zu sehen.
      wrap.querySelectorAll('button[data-decide-report]').forEach(btn => {
        btn.addEventListener('click', async (e) => {
          e.stopPropagation();
          const outcome = btn.dataset.outcome;
          const preset = outcome === 'no_action'
            ? 'Wir haben die Meldung geprüft und keinen Verstoß gegen die Nutzungsrichtlinien festgestellt.'
            : 'Wir haben die Meldung geprüft und Maßnahmen gegen das gemeldete Konto ergriffen.';
          const note = prompt('Begründung für den Melder (wird ihm wörtlich angezeigt):', preset);
          if(note === null) return;
          if(note.trim().length < 3){ toast('Bitte eine Begründung angeben.'); return; }
          try{
            await api(`/api/admin/reports/${btn.dataset.decideReport}/decide`, {
              method: 'POST',
              body: JSON.stringify({outcome, decision_note: note.trim()}),
            });
            toast('Meldung abgeschlossen, der Melder wird informiert.');
            loadReports();
            loadDashboard();
          }catch(err){ toast(err.message); }
        });
      });
      appendLoadMore(wrap, 'reports', reports.length, loadReports);
    }catch(err){
      wrap.innerHTML = `<div class="empty-state">${escapeHtml(err.message)}</div>`;
    }
  }

  const NOTICE_CATEGORY_LABELS = {
    csam:'Sexueller Kindesmissbrauch', minor:'Mutmaßlich minderjährige Person',
    trafficking:'Menschenhandel / Ausbeutung', threat:'Drohung / akute Gefahr',
    sexual_content:'Nicht einvernehmliche intime Aufnahme',
    impersonation:'Identitätsmissbrauch', fraud:'Betrug / Scam', hate:'Hass / Verhetzung',
    ip_infringement:'Urheber- oder Kennzeichenrecht',
    data_protection:'Datenschutz', other_illegal:'Sonstiger rechtswidriger Inhalt',
  };

  async function loadNotices(){
    const wrap = $('noticesTableWrap');
    try{
      const notices = await api('/api/admin/notices?limit=' + listLimit.notices);
      if(notices.length === 0){
        wrap.innerHTML = '<div class="empty-state">Keine förmlichen Meldungen.</div>';
        return;
      }
      wrap.innerHTML = `
        <div class="table-wrap"><table>
          <thead><tr><th>Aktenzeichen</th><th>Kategorie</th><th>Fundstelle</th><th>Begründung</th><th>Melder</th><th>Datum</th><th></th></tr></thead>
          <tbody>${notices.map(n => `
            <tr>
              <td class="mono">${escapeHtml(n.reference)}</td>
              <td>${escapeHtml(NOTICE_CATEGORY_LABELS[n.category] || n.category)}</td>
              <td class="msg-cell">${escapeHtml(n.content_reference)}</td>
              <td class="msg-cell">${escapeHtml(n.explanation)}</td>
              <td>${n.reporter_name ? escapeHtml(n.reporter_name) : '<span class="pill muted">anonym</span>'}</td>
              <td>${fmtDate(n.created_at)}</td>
              <td style="white-space:nowrap;">
                <select data-notice-outcome="${n.id}" aria-label="Ergebnis für ${escapeHtml(n.reference)}">
                  <option value="no_action">Kein Verstoß</option>
                  <option value="action_taken">Maßnahmen ergriffen</option>
                  <option value="forwarded">Weitergeleitet</option>
                  <option value="insufficient">Angaben unzureichend</option>
                </select>
                <button class="btn small secondary" data-decide-notice="${n.id}">Entscheiden</button>
              </td>
            </tr>`).join('')}</tbody>
        </table></div>`;

      wrap.querySelectorAll('button[data-decide-notice]').forEach(btn => {
        btn.addEventListener('click', async () => {
          const id = btn.dataset.decideNotice;
          const outcome = wrap.querySelector(`select[data-notice-outcome="${id}"]`).value;
          const reason = prompt('Begründung für die Entscheidung (wird dem Melder wörtlich angezeigt):');
          if(reason === null) return;
          if(reason.trim().length < 10){
            toast('Bitte die Entscheidung nachvollziehbar begründen (mindestens 10 Zeichen).');
            return;
          }
          try{
            const result = await api(`/api/admin/notices/${id}/decide`, {
              method: 'POST',
              body: JSON.stringify({
                outcome, decision_reason: reason.trim(), decision_automated: false,
              }),
            });
            toast(result.reporter_can_be_informed
              ? 'Förmliche Meldung entschieden; der Melder wird informiert.'
              : 'Förmliche Meldung entschieden; anonyme Meldung ohne Rückkanal.');
            loadNotices();
            loadDashboard();
          }catch(err){ toast(err.message); }
        });
      });
      appendLoadMore(wrap, 'notices', notices.length, loadNotices);
    }catch(err){
      wrap.innerHTML = `<div class="empty-state">${escapeHtml(err.message)}</div>`;
    }
  }

  async function loadFlaggedMessages(){
    const wrap = $('flaggedTableWrap');
    try{
      const msgs = await api('/api/admin/flagged-messages?limit=' + listLimit.flagged);
      if(msgs.length === 0){
        wrap.innerHTML = '<div class="empty-state">Keine auffälligen Nachrichten.</div>';
        return;
      }
      wrap.innerHTML = `
        <div class="table-wrap">
        <table>
          <thead><tr><th>Absender</th><th>Original</th><th>Empfänger sah</th><th>Grund</th><th>Status</th><th>Datum</th><th></th></tr></thead>
          <tbody>
            ${msgs.map(m => `
              <tr>
                <td>${escapeHtml(m.sender_name)}</td>
                <td class="msg-cell">${escapeHtml(m.content)}</td>
                <td class="msg-cell">${m.was_censored
                      ? `${escapeHtml(m.display_content)} <span class="pill warn">zensiert</span>`
                      : `<span style="color:var(--chalk-dim);">unverändert</span>`}</td>
                <td>${escapeHtml(m.flag_reason || '—')}</td>
                <td style="white-space:nowrap;">
                  <span class="pill ok">zugestellt</span>
                  ${m.read_at
                      ? `<span class="pill ok">gelesen</span>`
                      : `<span class="pill muted">ungelesen</span>`}
                </td>
                <td>${fmtDate(m.created_at)}</td>
                <td style="white-space:nowrap;">
                  <button class="btn small secondary" data-view-user="${m.sender_id}">Ansehen</button>
                  <button class="btn small secondary" data-clear-flag="${m.id}">OK</button>
                </td>
              </tr>
            `).join('')}
          </tbody>
        </table>
        </div>
      `;
      wrap.querySelectorAll('button[data-view-user]').forEach(btn => {
        btn.addEventListener('click', () => openUserModal(btn.dataset.viewUser));
      });
      wrap.querySelectorAll('button[data-clear-flag]').forEach(btn => {
        btn.addEventListener('click', async () => {
          try{
            await api(`/api/admin/flagged-messages/${btn.dataset.clearFlag}/clear`, {method: 'POST'});
            toast('Als unbedenklich markiert.');
            loadFlaggedMessages();
            loadDashboard();
          }catch(err){ toast(err.message); }
        });
      });
      appendLoadMore(wrap, 'flagged', msgs.length, loadFlaggedMessages);
    }catch(err){
      wrap.innerHTML = `<div class="empty-state">${escapeHtml(err.message)}</div>`;
    }
  }

  // ---------- Security / 2FA ----------
  async function loadSecurity(){
    const box = $('totpStatusBox');
    try{
      const status = await api('/api/admin/auth/totp/status');
      if(status.totp_enabled){
        box.innerHTML = `
          <div class="dash-card-title">Zwei-Faktor-Authentifizierung</div>
          <p class="hint">✅ Aktiv — der Login verlangt zusätzlich zum Passwort einen Code aus deiner Authenticator-App.</p>
          <label for="sec-disable-code">Code zum Deaktivieren</label>
          <input type="text" id="sec-disable-code" placeholder="123456" inputmode="numeric" maxlength="6">
          <div class="field-err" id="secErr" role="alert" aria-live="polite"></div>
          <button class="btn secondary full" id="btnTotpDisable" type="button" style="margin-top:14px;">2FA deaktivieren</button>
        `;
        $('btnTotpDisable').addEventListener('click', async () => {
          const errEl = $('secErr');
          errEl.textContent = '';
          const code = $('sec-disable-code').value.trim();
          if(!code){ errEl.textContent = 'Bitte Code eingeben.'; return; }
          try{
            await api('/api/admin/auth/totp/disable', {method: 'POST', body: JSON.stringify({totp_code: code})});
            toast('2FA deaktiviert.');
            loadSecurity();
          }catch(err){ errEl.textContent = err.message; }
        });
      } else {
        box.innerHTML = `
          <div class="dash-card-title">Zwei-Faktor-Authentifizierung</div>
          <p class="hint">⚠️ Noch nicht aktiv — der Login funktioniert bisher nur mit Passwort.</p>
          <button class="btn full" id="btnTotpSetup" type="button">2FA einrichten</button>
        `;
        $('btnTotpSetup').addEventListener('click', startTotpSetup);
      }
    }catch(err){
      box.innerHTML = `<div class="empty-state">${escapeHtml(err.message)}</div>`;
    }
  }

  async function startTotpSetup(){
    const box = $('totpStatusBox');
    try{
      const setup = await api('/api/admin/auth/totp/setup', {method: 'POST'});
      box.innerHTML = `
        <div class="dash-card-title">2FA einrichten</div>
        <p class="hint">QR-Code mit Google Authenticator, Authy o.ä. scannen, dann den angezeigten
          6-stelligen Code unten eingeben.</p>
        <img src="data:image/png;base64,${setup.qr_code_png_base64}" alt="QR-Code"
          style="display:block; margin:16px auto; border-radius:8px; width:220px; height:220px;">
        <p class="hint" style="text-align:center; word-break:break-all;">Manuell: ${escapeHtml(setup.secret)}</p>
        <label for="sec-confirm-code">Code aus der App</label>
        <input type="text" id="sec-confirm-code" placeholder="123456" inputmode="numeric" maxlength="6">
        <div class="field-err" id="secErr" role="alert" aria-live="polite"></div>
        <button class="btn full" id="btnTotpConfirm" type="button" style="margin-top:14px;">Bestätigen &amp; aktivieren</button>
      `;
      $('btnTotpConfirm').addEventListener('click', async () => {
        const errEl = $('secErr');
        errEl.textContent = '';
        const code = $('sec-confirm-code').value.trim();
        if(!code){ errEl.textContent = 'Bitte Code eingeben.'; return; }
        try{
          await api('/api/admin/auth/totp/confirm', {method: 'POST', body: JSON.stringify({totp_code: code})});
          toast('2FA aktiviert.');
          loadSecurity();
        }catch(err){ errEl.textContent = err.message; }
      });
    }catch(err){
      box.innerHTML = `<div class="empty-state">${escapeHtml(err.message)}</div>`;
    }
  }

  // ---------- Boot ----------
  // Ob noch ein gueltiges Cookie da ist, weiss nur der Server: einmal fragen.
  (async () => {
    try{
      const res = await fetch(API_BASE + '/api/admin/auth/totp/status', {credentials: 'include'});
      if(res.ok){ showApp(); return; }
    }catch(e){ /* offline */ }
    showLogin();
  })();
})();
