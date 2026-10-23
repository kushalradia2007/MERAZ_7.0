/* NIGHTJAR story engine (served at /assets/story.js, needs /assets/room-ui.css).
 *
 * A room page creates one Story and wires four calls:
 *
 *   const story = NJStory.create({ ...room script... });
 *   story.mount(document.getElementById('npc-comms'));   // the comms panel
 *   story.boot(solvedChallengeNumbers, score);           // after /api/progress
 *   story.onSolved(challengeNumber, solvedList);         // after a correct flag
 *   story.onWrong(challengeNumber);                      // after a wrong flag
 *
 * What it does:
 *   - first visit: a full-screen typewriter briefing from an NPC (skippable)
 *   - comms panel: NPC messages that depend on how many challenges are solved,
 *     which one was just solved, wrong answers and long idle spells
 *   - last challenge solved: a debrief cutscene ending on a "proceed" card
 *
 * The story text lives in each room page. Keep it free of answers: this file
 * and the room pages are readable by every player.
 */
(function () {
    'use strict';

    var REDUCED = false;
    try { REDUCED = window.matchMedia('(prefers-reduced-motion: reduce)').matches; } catch (e) { /* old browser */ }

    /* ───────────── tiny helpers ───────────── */
    function el(tag, cls, html) {
        var e = document.createElement(tag);
        if (cls) e.className = cls;
        if (html != null) e.innerHTML = html;
        return e;
    }
    function sleep(ms) { return new Promise(function (r) { setTimeout(r, ms); }); }
    function clock() {
        var d = new Date();
        return ('0' + d.getHours()).slice(-2) + ':' + ('0' + d.getMinutes()).slice(-2);
    }
    function sget(k) { try { return localStorage.getItem('nj.story.v1.' + k); } catch (e) { return null; } }
    function sset(k, v) { try { localStorage.setItem('nj.story.v1.' + k, v); } catch (e) { /* storage blocked */ } }
    function pick(list, n) { return list[n % list.length]; }

    /* ───────────── optional typing sound (off by default) ───────────── */
    var audio = null;
    var soundOn = sget('sound') === '1';
    function setSound(on) {
        soundOn = !!on;
        sset('sound', soundOn ? '1' : '0');
        if (soundOn) {
            try {
                audio = audio || new (window.AudioContext || window.webkitAudioContext)();
                if (audio.state === 'suspended') audio.resume();
            } catch (e) { /* no audio */ }
        }
        Array.prototype.forEach.call(document.querySelectorAll('[data-act="sound"]'), function (b) {
            b.setAttribute('aria-pressed', soundOn ? 'true' : 'false');
            b.textContent = soundOn ? '♪ ON' : '♪ OFF';
            b.title = 'Typing sound ' + (soundOn ? 'on' : 'off');
        });
    }
    function blip(freq) {
        if (!soundOn || !audio) return;
        try {
            var o = audio.createOscillator(), g = audio.createGain();
            o.type = 'square';
            o.frequency.value = freq || (480 + Math.random() * 120);
            g.gain.value = 0.010;
            o.connect(g); g.connect(audio.destination);
            o.start();
            g.gain.exponentialRampToValueAtTime(0.0001, audio.currentTime + 0.05);
            o.stop(audio.currentTime + 0.06);
        } catch (e) { /* ignore */ }
    }

    /* ───────────── NPC cast ───────────── */
    var NPCS = {
        ila:     { name: 'ILA SEN',              role: 'INCIDENT COMMANDER',      color: '#38bdf8', speed: 20 },
        rhea:    { name: "RHEA D'SOUZA",         role: 'NEXUS ENGINEER',          color: '#a78bfa', speed: 19 },
        kite:    { name: 'KABIR "KITE" MEHRA',   role: 'FESTIVAL TECHNICAL LEAD', color: '#fbbf24', speed: 17 },
        curator: { name: 'THE CURATOR',          role: 'UNKNOWN OPERATOR',        color: '#f43f5e', speed: 34, glitch: true, cls: 'curator' },
        system:  { name: 'NIGHTJAR.OS',          role: 'SYSTEM',                  color: '#34d399', speed: 12, cls: 'sys' }
    };

    /* Procedural portraits: no image files, tinted per NPC. */
    function portrait(id) {
        var c = (NPCS[id] || NPCS.system).color;
        var body = '<rect width="120" height="140" fill="' + c + '" fill-opacity=".10"/>';
        var shoulders = '<path d="M6 140C6 112 32 100 60 100S114 112 114 140Z" fill="#0b1324" stroke="' + c + '" stroke-width="1.5"/>';
        var neck = '<rect x="52" y="86" width="16" height="18" fill="#0b1324"/>';
        var head = '<ellipse cx="60" cy="62" rx="23" ry="27" fill="#0e182c" stroke="' + c + '" stroke-width="1.5"/>';
        var eyes = '<rect x="49" y="61" width="8" height="2.4" rx="1" fill="' + c + '"/><rect x="63" y="61" width="8" height="2.4" rx="1" fill="' + c + '"/>';
        var extra = '';
        if (id === 'ila') {
            extra = '<path d="M34 52C36 30 84 30 86 52L86 55L34 55Z" fill="#0b1324" stroke="' + c + '" stroke-width="1.5"/>' +
                '<path d="M29 55H91" stroke="' + c + '" stroke-width="2.6" stroke-linecap="round"/>' +
                '<path d="M37 65C30 79 38 91 52 93" fill="none" stroke="' + c + '" stroke-width="2"/><circle cx="53" cy="93" r="3" fill="' + c + '"/>' +
                '<rect x="52" y="112" width="16" height="4" rx="2" fill="' + c + '" fill-opacity=".7"/>';
            return svg(body + shoulders + neck + head + extra + eyes);
        }
        if (id === 'rhea') {
            extra = '<path d="M35 64C30 36 52 28 62 30C80 30 92 42 85 64C84 50 74 42 60 42C46 42 38 50 35 64Z" fill="#150f2a" stroke="' + c + '" stroke-width="1.5"/>' +
                '<circle cx="87" cy="30" r="9" fill="#150f2a" stroke="' + c + '" stroke-width="1.5"/>' +
                '<circle cx="51" cy="63" r="8.5" fill="' + c + '" fill-opacity=".14" stroke="' + c + '" stroke-width="1.6"/>' +
                '<circle cx="69" cy="63" r="8.5" fill="' + c + '" fill-opacity=".14" stroke="' + c + '" stroke-width="1.6"/>' +
                '<path d="M59.5 63H60.5" stroke="' + c + '" stroke-width="1.8"/>';
            return svg(body + shoulders + neck + head + extra);
        }
        if (id === 'kite') {
            extra = '<path d="M27 76C20 38 44 20 60 20C76 20 100 38 93 76C87 55 77 44 60 44C43 44 33 55 27 76Z" fill="#241a05" stroke="' + c + '" stroke-width="1.5"/>' +
                '<path d="M52 77Q60 83 68 77" fill="none" stroke="' + c + '" stroke-width="1.8" stroke-linecap="round"/>' +
                '<path d="M47 102L57 126M73 102L63 126" stroke="' + c + '" stroke-width="1.5"/>' +
                '<rect x="53" y="124" width="14" height="12" rx="2" fill="' + c + '" fill-opacity=".25" stroke="' + c + '" stroke-width="1.2"/>';
            return svg(body + shoulders + neck + head + extra + eyes);
        }
        if (id === 'curator') {
            return svg(body +
                '<path d="M20 124C10 62 32 12 60 12C88 12 110 62 100 124Z" fill="#12050b" stroke="' + c + '" stroke-width="1.5"/>' +
                '<ellipse cx="60" cy="66" rx="21" ry="27" fill="#000"/>' +
                '<text x="60" y="80" text-anchor="middle" font-family="monospace" font-size="38" font-weight="700" fill="' + c + '">?</text>' +
                '<path d="M20 124H100" stroke="' + c + '" stroke-width="1.5"/>');
        }
        /* system / default: a terminal window */
        return svg(body +
            '<rect x="16" y="30" width="88" height="66" rx="6" fill="#04130d" stroke="' + c + '" stroke-width="1.5"/>' +
            '<rect x="16" y="30" width="88" height="11" fill="' + c + '" fill-opacity=".22"/>' +
            '<path d="M29 54L42 64L29 74" fill="none" stroke="' + c + '" stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round"/>' +
            '<rect x="48" y="72" width="24" height="4" fill="' + c + '"/>');
    }
    function svg(inner) {
        return '<svg viewBox="0 0 120 140" xmlns="http://www.w3.org/2000/svg" aria-hidden="true" focusable="false">' + inner + '</svg>';
    }
    function npc(id) { return NPCS[id] || NPCS.system; }

    /* Character art from /assets/npc; the drawn SVG above stays as the fallback
     * (system terminal, or if an image fails to load). */
    var ART = { ila: 1, rhea: 1, kite: 1, curator: 1 };
    function portraitHTML(id) {
        if (!ART[id]) return portrait(id);
        return '<img class="nj-art" src="/assets/npc/' + id + '-portrait.webp" alt="" decoding="async" ' +
            'onerror="this.outerHTML=window.NJStory.fallback(\'' + id + '\')">';
    }

    /* ───────────── typewriter ───────────── */
    function typewriter(node, text, o) {
        o = o || {};
        var speed = REDUCED ? 0 : (o.speed || 22);
        var textNode = document.createTextNode('');
        var caret = el('span', 'nj-caret');
        node.textContent = '';
        node.appendChild(textNode);
        node.appendChild(caret);
        var i = 0, timer = null, done = false, resolve;
        var p = new Promise(function (r) { resolve = r; });
        function finish() {
            if (done) return;
            done = true;
            clearTimeout(timer);
            textNode.data = text;
            if (caret.parentNode) caret.parentNode.removeChild(caret);
            if (o.onTick) o.onTick();
            resolve();
        }
        function step() {
            if (done) return;
            if (i >= text.length) { finish(); return; }
            var ch = text.charAt(i++);
            textNode.data = text.slice(0, i);
            if (ch.trim() && i % 2 === 0) blip(o.pitch);
            if (o.onTick) o.onTick();
            var d = speed, next = text.charAt(i);
            if ('.!?'.indexOf(ch) > -1 && (next === ' ' || next === '')) d = speed * 11;
            else if (ch === '…') d = speed * 10;
            else if (',;:—'.indexOf(ch) > -1) d = speed * 5;
            timer = setTimeout(step, d + (o.jitter ? Math.random() * o.jitter : 0));
        }
        if (speed === 0) finish(); else step();
        return { done: p, finish: finish, isDone: function () { return done; } };
    }

    /* ───────────── cutscene overlay ───────────── */
    function runCutscene(story, kind) {
        var cfg = story.cfg;
        var isDebrief = kind === 'debrief';
        var beats = (isDebrief ? cfg.debrief : cfg.briefing) || [];
        beats = beats.filter(Boolean);
        if (!beats.length) return Promise.resolve();

        return new Promise(function (resolve) {
            var prevFocus = document.activeElement;
            var ov = el('div', 'nj-ov nj-ov-' + kind);
            ov.setAttribute('role', 'dialog');
            ov.setAttribute('aria-modal', 'true');
            ov.setAttribute('aria-label', isDebrief ? 'Room debrief' : 'Mission briefing');
            ov.innerHTML =
                '<div class="nj-ov-bg"></div><div class="nj-ov-vig"></div>' +
                '<div class="nj-bar nj-bar-top">' +
                    '<span class="nj-rec"><i></i>' + (isDebrief ? 'DEBRIEF' : 'INCOMING TRANSMISSION') + '</span>' +
                    '<span class="nj-ov-room"></span>' +
                    '<span class="nj-ov-tools">' +
                        '<button type="button" class="nj-tool" data-act="sound" aria-pressed="false">♪ OFF</button>' +
                        '<button type="button" class="nj-tool nj-skip" data-act="skip">SKIP ▸▸</button>' +
                    '</span>' +
                '</div>' +
                '<div class="nj-stage" data-mode="dialog">' +
                    '<div class="nj-scene"><span class="nj-scene-stamp" data-el="stamp"></span><p class="nj-scene-text" data-el="scenetext" aria-hidden="true"></p></div>' +
                    '<div class="nj-dialog">' +
                        '<div class="nj-portrait" data-el="portrait"></div>' +
                        '<div class="nj-box">' +
                            '<div class="nj-plate"><b data-el="who"></b><span class="role" data-el="role"></span>' +
                                '<span class="nj-sig" aria-hidden="true"><i></i><i></i><i></i><i></i></span></div>' +
                            '<p class="nj-text" data-el="text" aria-hidden="true"></p>' +
                            '<div class="nj-foot"><span class="nj-dots" data-el="dots" aria-hidden="true"></span>' +
                                '<button type="button" class="nj-go" data-act="next">CONTINUE<kbd>␣</kbd></button></div>' +
                        '</div>' +
                    '</div>' +
                    '<div class="nj-title-card"><span class="k" data-el="tk"></span><h2 data-el="th"></h2><span class="sub" data-el="ts"></span><span class="hint">PRESS SPACE</span></div>' +
                    '<div class="nj-cta" data-el="cta"></div>' +
                '</div>' +
                '<div class="nj-bar nj-bar-bot"><span>TAP / SPACE / ENTER — CONTINUE</span><span>ESC — SKIP</span></div>' +
                '<p class="nj-sr" data-el="sr" aria-live="polite"></p>';
            document.body.appendChild(ov);
            document.body.classList.add('nj-ov-open');
            story.overlayOpen = true;

            function q(name) { return ov.querySelector('[data-el="' + name + '"]'); }
            var stage = ov.querySelector('.nj-stage');
            var textEl = q('text'), sceneEl = q('scenetext'), srEl = q('sr'), dotsEl = q('dots');
            ov.querySelector('.nj-ov-room').textContent = 'ROOM ' + cfg.room + ' // ' + cfg.title;
            setSound(soundOn);

            var idx = -1, typer = null, mode = 'dialog', closed = false, glitchTimer = null;

            dotsEl.innerHTML = beats.map(function () { return '<i></i>'; }).join('');
            function paintDots() {
                Array.prototype.forEach.call(dotsEl.children, function (d, n) {
                    d.className = n <= idx ? 'on' + (n === idx ? ' cur' : '') : '';
                });
            }
            function setMode(m) { mode = m; stage.setAttribute('data-mode', m); }

            function show(i) {
                idx = i;
                var b = beats[i];
                if (typer) typer.finish();
                ov.classList.remove('glitch');
                clearTimeout(glitchTimer);
                paintDots();

                if (b.scene) {
                    setMode('scene');
                    q('stamp').textContent = b.stamp || '';
                    q('stamp').style.display = b.stamp ? '' : 'none';
                    ov.style.setProperty('--npc', 'var(--accent)');
                    srEl.textContent = (b.stamp ? b.stamp + '. ' : '') + b.scene;
                    typer = typewriter(sceneEl, b.scene, { speed: 26 });
                    return;
                }
                if (b.title) {
                    setMode('title');
                    q('tk').textContent = b.kicker || '';
                    q('th').textContent = b.title;
                    q('ts').textContent = b.sub || '';
                    typer = null;
                    srEl.textContent = b.title + '. ' + (b.sub || '');
                    return;
                }
                var who = npc(b.npc || cfg.lead);
                setMode('dialog');
                ov.style.setProperty('--npc', who.color);
                q('portrait').innerHTML = portraitHTML(b.npc || cfg.lead);
                q('portrait').style.animation = 'none';
                void q('portrait').offsetWidth;              // restart the slide-in
                q('portrait').style.animation = '';
                q('who').textContent = who.name;
                q('role').textContent = who.role;
                srEl.textContent = who.name + ': ' + b.text;
                if (who.glitch || b.fx === 'glitch') {
                    ov.classList.add('glitch');
                    glitchTimer = setTimeout(function () { ov.classList.remove('glitch'); }, 1200);
                }
                typer = typewriter(textEl, b.text, { speed: who.speed, jitter: who.glitch ? 26 : 6, pitch: who.glitch ? 220 : 0 });
            }

            function showCTA() {
                if (typer) typer.finish();
                ov.classList.remove('glitch');
                setMode('cta');
                ov.style.setProperty('--npc', 'var(--accent)');
                var n = cfg.next || {};
                var c = q('cta');
                c.innerHTML = '';
                c.appendChild(el('span', 'k', 'ROOM ' + cfg.room + ' CLEARED'));
                c.appendChild(el('h2', null, ''));
                c.lastChild.textContent = cfg.title;
                var stats = el('div', 'nj-stats');
                var solvedN = Math.max(story.done.length, 4);
                stats.innerHTML = '<div><b>' + solvedN + '/4</b>FLAGS</div><div><b>+' + (solvedN * 25) + '</b>POINTS</div>';
                c.appendChild(stats);
                if (n.teaser) {
                    var t = el('div', 'tease', '<small></small><span></span>');
                    t.querySelector('small').textContent = 'INCOMING // ' + (npc(n.from || cfg.lead).name);
                    t.querySelector('span').textContent = n.teaser;
                    c.appendChild(t);
                }
                var row = el('div', 'row');
                var go = el('a', 'nj-btn');
                go.href = n.href || '/hub';
                go.textContent = (n.label || 'RETURN TO HUB') + ' ▸';
                var stay = el('button', 'nj-btn ghost');
                stay.type = 'button';
                stay.textContent = 'STAY IN ROOM';
                stay.addEventListener('click', function () { close(); });
                row.appendChild(go); row.appendChild(stay);
                c.appendChild(row);
                ov.querySelector('.nj-skip').style.visibility = 'hidden';
                ov.querySelector('.nj-bar-bot').style.visibility = 'hidden';
                srEl.textContent = 'Room cleared. ' + (n.label || '');
                setTimeout(function () { go.focus(); }, 60);
            }

            function next() {
                if (closed || mode === 'cta') return;
                if (typer && !typer.isDone()) { typer.finish(); return; }
                if (idx < beats.length - 1) show(idx + 1);
                else if (isDebrief) showCTA();
                else close();
            }
            function skip() {
                if (closed || mode === 'cta') return;
                if (isDebrief) showCTA(); else close();
            }
            function close() {
                if (closed) return;
                closed = true;
                if (typer) typer.finish();
                clearTimeout(glitchTimer);
                document.removeEventListener('keydown', onKey, true);
                story.markSeen(kind);
                ov.classList.add('out');
                setTimeout(function () {
                    if (ov.parentNode) ov.parentNode.removeChild(ov);
                    document.body.classList.remove('nj-ov-open');
                    story.overlayOpen = false;
                    try { if (prevFocus && prevFocus.focus) prevFocus.focus(); } catch (e) { /* gone */ }
                    resolve();
                }, REDUCED ? 0 : 350);
            }
            function onKey(e) {
                if (e.key === 'Escape') { e.preventDefault(); e.stopPropagation(); if (mode === 'cta') close(); else skip(); return; }
                if (e.key === 'Tab') {                                   // keep focus inside the dialog
                    var f = Array.prototype.filter.call(ov.querySelectorAll('button, a[href]'), function (n) {
                        return n.offsetParent !== null && getComputedStyle(n).visibility !== 'hidden';
                    });
                    if (!f.length) return;
                    var first = f[0], last = f[f.length - 1];
                    if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
                    else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
                    else if (!ov.contains(document.activeElement)) { e.preventDefault(); first.focus(); }
                    return;
                }
                if (mode === 'cta') return;                              // let buttons handle Enter/Space
                if (e.key === ' ' || e.key === 'Enter' || e.key === 'ArrowRight') {
                    e.preventDefault(); e.stopPropagation(); next();
                }
            }
            document.addEventListener('keydown', onKey, true);

            ov.addEventListener('click', function (e) {
                var act = e.target.closest && e.target.closest('[data-act]');
                if (act) {
                    var a = act.getAttribute('data-act');
                    if (a === 'skip') skip();
                    else if (a === 'next') next();
                    else if (a === 'sound') setSound(!soundOn);
                    return;
                }
                if (e.target.closest('a, button')) return;
                if (mode !== 'cta') next();
            });

            show(0);
            var goBtn = ov.querySelector('.nj-go');
            if (goBtn) goBtn.focus({ preventScroll: true });
        });
    }

    /* ───────────── comms panel ───────────── */
    function Comms(story, mount) {
        this.story = story;
        this.mount = mount;
        this.q = [];
        this.busy = false;
        mount.classList.add('nj-comms');
        mount.innerHTML =
            '<div class="nj-comms-head"><span class="live"></span><span class="lbl">SECURE LINK</span> <b data-el="who"></b>' +
                '<span class="nj-comms-tools">' +
                    '<button type="button" class="nj-tool" data-act="replay" title="Watch the briefing again">↻ BRIEFING</button>' +
                    '<button type="button" class="nj-tool" data-act="sound" aria-pressed="false">♪ OFF</button>' +
                '</span></div>' +
            '<div class="nj-comms-log" data-el="log" role="log" aria-live="off"></div>';
        this.log = mount.querySelector('[data-el="log"]');
        this.who = mount.querySelector('[data-el="who"]');
        this.who.textContent = npc(story.cfg.lead).name;
        var self = this;
        mount.addEventListener('click', function (e) {
            var b = e.target.closest && e.target.closest('[data-act]');
            if (!b) return;
            var a = b.getAttribute('data-act');
            if (a === 'replay') story.playBriefing();
            else if (a === 'sound') setSound(!soundOn);
        });
        setSound(soundOn);
    }
    Comms.prototype.say = function (id, text, o) {
        this.q.push({ id: id, text: text, o: o || {} });
        this._pump();
    };
    Comms.prototype._pump = function () {
        var self = this;
        if (self.busy) return;
        self.busy = true;
        (function loop() {
            var m = self.q.shift();
            if (!m) { self.busy = false; return; }
            self._show(m).then(loop, loop);
        })();
    };
    Comms.prototype._scroll = function () { this.log.scrollTop = this.log.scrollHeight; };
    Comms.prototype._show = function (m) {
        var self = this, who = npc(m.id);
        var row = el('div', 'nj-cmsg ' + (who.cls || ''));
        row.style.setProperty('--npc', who.color);
        row.innerHTML = '<div class="nj-av"></div><div class="nj-bub"><div class="h"><b></b><span></span></div><div class="t"></div></div>';
        row.querySelector('.nj-av').innerHTML = portraitHTML(m.id);
        row.querySelector('.h b').textContent = who.name;
        row.querySelector('.h span').textContent = clock();
        var t = row.querySelector('.t');
        self.who.textContent = who.name;
        self.log.appendChild(row);
        while (self.log.children.length > 40) self.log.removeChild(self.log.firstChild);
        self._scroll();

        if (m.o.instant || REDUCED) {
            t.textContent = m.text;
            self._scroll();
            return sleep(REDUCED ? 0 : 120);
        }
        t.innerHTML = '<span class="nj-typing"><i></i><i></i><i></i></span>';
        var typingMs = Math.min(1100, 380 + m.text.length * 5);
        return sleep(typingMs).then(function () {
            var tw = typewriter(t, m.text, { speed: Math.max(11, who.speed * 0.7), onTick: function () { self._scroll(); } });
            return tw.done;
        }).then(function () {
            var sr = el('span', 'nj-sr');                                  // one polite announcement per finished message
            sr.setAttribute('role', 'status');
            sr.textContent = who.name + ': ' + m.text;
            row.appendChild(sr);
            return sleep(450);
        });
    };

    /* ───────────── story controller ───────────── */
    function Story(cfg) {
        this.cfg = cfg;
        this.done = [];                // solved challenge numbers (1-based)
        this.wrongCount = {};
        this.lastReact = 0;
        this.nudges = 0;
        this.overlayOpen = false;
        this.comms = null;
        this.uid = 'anon';
        this._idleTimer = null;
        this._nextShown = false;
    }
    Story.prototype._key = function (what) { return this.uid + '.r' + this.cfg.room + '.' + what; };
    Story.prototype._seen = function (kind) { return sget(this._key(kind)) === '1'; };
    Story.prototype.markSeen = function (kind) { sset(this._key(kind), '1'); };

    Story.prototype.mount = function (mountEl) {
        if (!mountEl) return;
        this.comms = new Comms(this, mountEl);
    };

    Story.prototype._say = function (line, o) {
        if (!line || !this.comms) return;
        if (typeof line === 'string') line = { npc: this.cfg.lead, text: line };
        this.comms.say(line.npc || this.cfg.lead, line.text, o);
    };
    Story.prototype._sayAll = function (lines, o) {
        var self = this;
        (lines || []).forEach(function (l) { self._say(l, o); });
    };

    Story.prototype._identify = function () {
        var self = this;
        return fetch('/api/me', { credentials: 'same-origin' })
            .then(function (r) { return r.ok ? r.json() : {}; })
            .then(function (d) { if (d && d.username) self.uid = String(d.username).toLowerCase(); })
            .catch(function () { /* keep anon */ });
    };

    Story.prototype._hud = function (score) {
        var done = this.done;
        Array.prototype.forEach.call(document.querySelectorAll('[data-nj-pips]'), function (box) {
            if (!box.children.length) box.innerHTML = '<i></i><i></i><i></i><i></i>';
            Array.prototype.forEach.call(box.children, function (pip, n) {
                pip.classList.toggle('on', done.indexOf(n + 1) > -1);
            });
            box.setAttribute('aria-label', done.length + ' of 4 challenges solved');
        });
        if (typeof score === 'number') {
            Array.prototype.forEach.call(document.querySelectorAll('[data-nj-score]'), function (s) {
                s.textContent = ('000' + score).slice(-4);
            });
        }
    };

    Story.prototype.toast = function (title, body) {
        var box = document.querySelector('.nj-toasts');
        if (!box) { box = el('div', 'nj-toasts'); box.setAttribute('aria-hidden', 'true'); document.body.appendChild(box); }
        var t = el('div', 'nj-toast', '<b></b><span></span>');
        t.querySelector('b').textContent = title;
        t.querySelector('span').textContent = body;
        box.appendChild(t);
        setTimeout(function () {
            t.classList.add('out');
            setTimeout(function () { if (t.parentNode) t.parentNode.removeChild(t); }, 450);
        }, 3600);
    };

    Story.prototype.boot = function (solved, score) {
        var self = this, cfg = this.cfg;
        this.done = (solved || []).slice().sort();
        return this._identify().then(function () {
            self._hud(typeof score === 'number' ? score : undefined);
            var n = self.done.length;
            if (n >= 4) {
                if (!self._seen('debrief')) {
                    return self.playDebrief().then(function () { self.renderNext(); });
                }
                self._say(cfg.complete || 'Room clear. Go when you are ready.', { instant: true });
                self.renderNext();
                return null;
            }
            self._armIdle();
            if (!self._seen('briefing')) {
                return self.playBriefing().then(function () {
                    self._say(cfg.objective || 'Four leads. Start anywhere.', { instant: true });
                });
            }
            var tier = (cfg.greet || {})[Math.min(n, 3)];
            self._sayAll(tier);
            return null;
        });
    };

    Story.prototype.playBriefing = function () {
        if (this.overlayOpen) return Promise.resolve();
        return runCutscene(this, 'briefing');
    };
    Story.prototype.playDebrief = function () {
        if (this.overlayOpen) return Promise.resolve();
        return runCutscene(this, 'debrief');
    };
    Story.prototype.replayDebrief = function () { return this.playDebrief(); };

    Story.prototype.onSolved = function (n, list) {
        var self = this, cfg = this.cfg;
        var prev = this.done.slice();
        list = (list && list.length) ? list.slice() : prev.concat(n);
        var fresh = list.filter(function (x) { return prev.indexOf(x) === -1; });
        this.done = list.slice().sort();
        this._hud();
        if (!fresh.length) return;

        if (window.NJ && NJ.progress) {
            NJ.progress().then(function (p) { if (p) self._hud(p.score); });
        }
        fresh.forEach(function (f) {
            self.toast('+25 PTS', 'Target ' + cfg.room + '.' + f + ' secured');
            self._sayAll((cfg.onSolve || {})[f]);
        });
        var c = this.done.length;
        if (c < 4) {
            self._sayAll((cfg.milestone || {})[c]);
        } else {
            clearTimeout(this._idleTimer);
            setTimeout(function () {
                self.playDebrief().then(function () { self.renderNext(); });
            }, REDUCED ? 200 : 2800);
        }
    };

    Story.prototype.onWrong = function (n) {
        var cfg = this.cfg;
        var c = this.wrongCount[n] = (this.wrongCount[n] || 0) + 1;
        var now = Date.now();
        if (now - this.lastReact < 9000) return;
        var line = null;
        var hint = (cfg.hints || {})[n];
        if (c >= 2 && c % 2 === 0 && hint) line = hint;
        else if ((c === 1 || c % 3 === 1) && cfg.wrong && cfg.wrong.length) line = pick(cfg.wrong, c);
        if (!line) return;
        this.lastReact = now;
        this._say(line);
    };

    Story.prototype._armIdle = function () {
        var self = this, ms = this.cfg.idleMs || 240000;
        function reset() {
            clearTimeout(self._idleTimer);
            if (self.done.length >= 4) return;
            self._idleTimer = setTimeout(nudge, ms);
        }
        function nudge() {
            if (self.done.length >= 4 || self.overlayOpen || self.nudges >= 3) return;
            var open = [1, 2, 3, 4].filter(function (x) { return self.done.indexOf(x) === -1; })[0];
            var hint = (self.cfg.hints || {})[open];
            if (hint) { self.nudges++; self._say(hint); }
            reset();
        }
        if (!this._idleBound) {
            this._idleBound = true;
            ['pointerdown', 'keydown'].forEach(function (ev) { document.addEventListener(ev, reset, { passive: true }); });
        }
        reset();
    };

    Story.prototype.renderNext = function () {
        var cfg = this.cfg, self = this;
        if (this._nextShown) return;
        var slot = cfg.nextMount ? document.querySelector(cfg.nextMount) : null;
        if (!slot) return;
        this._nextShown = true;
        var n = cfg.next || {};
        var card = el('div', 'nj-next', '<div class="k"></div><q></q><div class="row"></div>');
        card.querySelector('.k').textContent = '>> INCOMING TRANSMISSION // ' + npc(n.from || cfg.lead).name;
        card.querySelector('q').textContent = n.teaser || '';
        var row = card.querySelector('.row');
        var go = el('a', 'nj-btn');
        go.href = n.href || '/hub';
        go.textContent = (n.label || 'RETURN TO HUB') + ' ▸';
        var re = el('button', 'nj-btn ghost');
        re.type = 'button';
        re.textContent = '↻ REPLAY DEBRIEF';
        re.addEventListener('click', function () { self.replayDebrief(); });
        row.appendChild(go); row.appendChild(re);
        slot.appendChild(card);
    };

    /* ───────────── page wiring shared by every room ─────────────
     * NJStory.room({ id, story, log?, onMarked?, onResult? })
     *
     * Expects the standard room markup: cards #target-N holding .nj-form (input #flag-N +
     * button), .nj-reward #reward-N, an optional #solved-count, and the evidence modal
     * (#evidence-modal, #modal-iframe, #modal-title, #modal-close). It restores solved state
     * from the server, verifies flags through NJ.submit, feeds the story, and defines the
     * globals the inline onclick handlers use: verifyFlag(n), openEvidence(title, url),
     * closeModal().
     *   log(message, type)         optional: write to the page's own log panel
     *   onMarked(n, fresh)         a card was marked solved (restore or live)
     *   onResult(ok, n, solvedNow) after every verify attempt
     */
    function wireRoom(opts) {
        var ROOM = opts.id, story = opts.story;
        function $(id) { return document.getElementById(id); }
        function log(m, t) { if (opts.log) opts.log(m, t); }

        function markSolved(n, reward, fresh) {
            var card = $('target-' + n);
            if (!card) return;
            var was = card.classList.contains('solved');
            card.classList.add('solved');
            if (fresh && !was) {
                card.classList.add('stamp');
                setTimeout(function () { card.classList.remove('stamp'); }, 800);
            }
            var rw = $('reward-' + n);
            if (rw && (reward || !rw.textContent)) rw.textContent = reward || 'Evidence verified.';
            var input = $('flag-' + n);
            if (input) { input.value = 'FLAG ACCEPTED'; input.disabled = true; }
            var form = card.querySelector('.nj-form');
            if (form) { form.classList.remove('bad'); form.classList.add('ok'); }
            var btn = card.querySelector('.nj-form button');
            if (btn) btn.disabled = true;
            var c = $('solved-count');
            if (c) c.textContent = document.querySelectorAll('.nj-card.solved').length + '/4';
            if (opts.onMarked) opts.onMarked(n, !!(fresh && !was));
        }

        function init() {
            NJ.progress().then(function (p) {
                var solved = p ? ((p.rooms || {})[ROOM] || []) : [];
                var rewards = (p && p.rewards && p.rewards[ROOM]) || {};
                solved.forEach(function (n) { markSolved(n, rewards[n], false); });
                story.boot(solved, p ? p.score : undefined);
            });
        }

        function verify(n) {
            var input = $('flag-' + n);
            if (!input) return;
            var val = input.value.trim();
            if (!val) return;
            var form = input.closest('.nj-form');
            var btn = form.querySelector('button');
            if (btn.disabled) return;
            btn.disabled = true;
            btn.classList.add('busy');
            log('Verifying target ' + ROOM + '.' + n + '...', 'info');
            NJ.submit(ROOM, val).then(function (res) {
                btn.classList.remove('busy');
                btn.disabled = false;
                if (res.success) {
                    var hit = res.challenge || n;
                    var solved = (res.solved && res.solved.length) ? res.solved : [n];
                    log('Target ' + ROOM + '.' + hit + ' VERIFIED.', 'ok');
                    solved.forEach(function (k) { markSolved(k, k === hit ? res.reward : undefined, true); });
                    story.onSolved(hit, solved);
                    if (opts.onResult) opts.onResult(true, hit, solved);
                } else {
                    log('Target ' + ROOM + '.' + n + ' FAILED. ' + res.message, 'err');
                    form.classList.remove('bad');
                    void form.offsetWidth;
                    form.classList.add('bad');
                    btn.title = res.message || '';
                    story.onWrong(n);
                    if (opts.onResult) opts.onResult(false, n, []);
                }
            });
        }

        Array.prototype.forEach.call(document.querySelectorAll('.nj-form input'), function (inp) {
            inp.addEventListener('keydown', function (e) {
                if (e.key === 'Enter') verify(Number(inp.id.replace('flag-', '')));
            });
        });

        var modal = $('evidence-modal'), frame = $('modal-iframe');
        window.verifyFlag = verify;
        window.openEvidence = function (title, url) {
            if (!modal) return;
            log('Accessing evidence file: ' + title + '...', 'info');
            $('modal-title').textContent = 'EVIDENCE VIEWER // ' + String(title).toUpperCase();
            frame.src = url;
            modal.classList.add('open');
            var x = $('modal-close');
            if (x) x.focus();
        };
        window.closeModal = function () {
            if (!modal) return;
            modal.classList.remove('open');
            frame.src = 'about:blank';
        };
        if (modal) {
            modal.addEventListener('click', function (e) { if (e.target === modal) window.closeModal(); });
            document.addEventListener('keydown', function (e) {
                if (e.key === 'Escape' && modal.classList.contains('open')) window.closeModal();
            });
        }

        if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
        return { markSolved: markSolved, verify: verify };
    }

    window.NJStory = {
        create: function (cfg) {
            cfg.lead = cfg.lead || 'ila';
            return new Story(cfg);
        },
        room: wireRoom,
        npcs: NPCS,
        fallback: portrait
    };
})();
