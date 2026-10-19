/* First-login interactive guide for the hub (served at /tour.js).
 *
 * Auto-starts once per account (server flag has_seen_tour), after the boot
 * screen is dismissed. The "? GUIDE" button in the nav replays it any time
 * without touching the flag.
 *
 * Steps highlight real page elements with a spotlight. Two steps are
 * interactive: the player has to actually walk, and actually talk to an ally.
 * Targets that aren't on screen (small phones hide the side panels) fall back
 * to a centred card, so the tour works at every width.
 */
(function () {
    'use strict';

    var STEPS = [
        {
            title: 'WELCOME, RESPONDER',
            body: 'It is <b>23:17</b>. The NEXUS festival systems are going dark and something called <b>MIRA-7</b> is moving through them. ' +
                  'You are a member of the <b>NIGHTJAR Response Cell</b>. This 60-second guide shows you how everything works. You are playing <b>solo</b>: your score is yours alone.'
        },
        {
            sel: '#stage',
            title: 'MOVE AROUND THE HUB',
            body: 'This is the hub world. Walk with <kbd>W</kbd><kbd>A</kbd><kbd>S</kbd><kbd>D</kbd> or the arrow keys (the on-screen keys work too). <b>Try it now.</b>',
            wait: 'move',
            waitHint: 'Move your character to continue…',
            doneHint: '✓ Nice moves!'
        },
        {
            sel: '#room-list',
            alt: '#stage',
            title: '9 ROOMS · 4 FLAGS EACH',
            body: 'Every glowing door in the hub is a <b>room</b> with its own investigation. Walk up to a door and press <kbd>E</kbd>, or click a room in this list. ' +
                  'Each room hides <b>4 flags</b> worth <b>25 points</b> each. Clearing a room unlocks the next story beat.'
        },
        {
            sel: '#npc-tracker',
            alt: '#stage',
            title: 'TALK TO YOUR ALLIES',
            body: 'Three allies are somewhere in the hub: <b>Cmdr. Ila Sen</b>, <b>Rhea</b> and <b>Kabir</b>. Walk close to one and press <kbd>E</kbd> to talk. <b>Try it.</b>',
            wait: 'talk',
            waitHint: 'Find an ally and press E…',
            doneHint: '✓ Contact made!'
        },
        {
            sel: '#intel-feed',
            alt: '#stage',
            title: 'THE INTEL FEED',
            body: 'Everything your allies tell you is logged here. Reread it when you are stuck: allies drop <b>hints</b> that matter in the rooms.'
        },
        {
            sel: '#right-panel .panel-section',
            alt: '#nav-username',
            title: 'YOUR STATUS',
            body: 'Your <b>score</b> and rooms cleared live here. Points come only from correct flags, and each flag counts once.'
        },
        {
            sel: '#top-nav a[href="/board"]',
            title: 'THE CASE BOARD',
            body: 'Every flag you capture <b>pins a piece of evidence</b> to your personal Case Board. Drag cards around, tie <b>red string</b> between clues, and add your own sticky notes. ' +
                  'It is where you piece the whole incident together. A <b>NEW</b> badge shows when fresh evidence is waiting.'
        },
        {
            title: 'HOW FLAGS WORK',
            body: 'Inside a room, study the evidence files and find a flag shaped like <b>NIGHTJAR{...}</b>. Paste it into the submit box. ' +
                  'Wrong guesses cost nothing, but nobody can solve it for you. <b>Do not share answers.</b> The scoreboard is for individuals.'
        },
        {
            sel: '#top-nav a[href="/scoreboard"]',
            title: 'THE SCOREBOARD',
            body: 'See how you rank against every other responder, live. Fastest and most thorough investigators climb the board.'
        },
        {
            sel: '#admin-nav-link',
            adminOnly: true,
            title: 'ORGANISER CONSOLE',
            body: 'You are an admin, so you also get the <b>admin console</b> for managing players, scores and the event.'
        },
        {
            sel: '#tour-replay',
            title: 'YOU ARE READY',
            body: 'That is everything. Replay this guide any time from the <b>? GUIDE</b> button. Find the first door, talk to your allies, and trace the worm.<br><br><b>Good luck, responder.</b>',
            last: true
        }
    ];

    var CSS =
        '#tour-block{position:fixed;inset:0;z-index:9990;background:transparent}' +
        '#tour-block.thru{pointer-events:none}' +
        '#tour-spot{position:fixed;z-index:9991;pointer-events:none;border-radius:8px;border:2px solid #ffe600;' +
        'box-shadow:0 0 0 9999px rgba(3,0,6,.8),0 0 22px rgba(255,230,0,.55),inset 0 0 14px rgba(255,230,0,.18);' +
        'transition:top .35s cubic-bezier(.4,0,.2,1),left .35s cubic-bezier(.4,0,.2,1),width .35s cubic-bezier(.4,0,.2,1),height .35s cubic-bezier(.4,0,.2,1),opacity .2s}' +
        '#tour-spot.none{border-color:transparent;box-shadow:0 0 0 9999px rgba(3,0,6,.82);transition:none}' +
        '#tour-card{position:fixed;z-index:9992;width:min(360px,calc(100vw - 24px));background:#0c0014;border:1px solid #ffe600;border-radius:8px;' +
        'padding:14px 16px 12px;box-shadow:0 0 0 1px #000,0 12px 40px rgba(0,0,0,.7),0 0 26px rgba(255,230,0,.18);' +
        'font-family:"JetBrains Mono","Courier New",monospace;font-size:12px;line-height:1.55;color:#ffd9d9;animation:tourIn .25s ease}' +
        '@keyframes tourIn{from{opacity:0;transform:translateY(8px)}}' +
        '#tour-card .t-step{font-family:"Press Start 2P",monospace;font-size:7px;color:#00f0ff;letter-spacing:1px;margin-bottom:7px;display:flex;justify-content:space-between;align-items:center}' +
        '#tour-card .t-title{font-family:"Press Start 2P",monospace;font-size:10px;line-height:1.5;color:#ffe600;margin-bottom:8px;text-shadow:0 0 10px rgba(255,230,0,.3)}' +
        '#tour-card .t-body b{color:#fff}' +
        '#tour-card kbd{display:inline-block;min-width:18px;padding:0 5px;margin:0 2px;border:1px solid #ff1a1a;border-bottom-width:2px;border-radius:3px;background:#1a0008;color:#ffe600;font:700 10px "JetBrains Mono",monospace;text-align:center}' +
        '#tour-card .t-wait{margin-top:10px;padding:7px 9px;border:1px dashed #00f0ff;border-radius:5px;color:#00f0ff;font-size:11px}' +
        '#tour-card .t-wait.ok{border:1px solid #00ff6a;color:#00ff6a;background:rgba(0,255,106,.06)}' +
        '#tour-card .t-wait i{display:inline-block;width:7px;height:7px;border-radius:50%;background:currentColor;margin-right:7px;animation:tourBlink 1s steps(2) infinite}' +
        '#tour-card .t-wait.ok i{animation:none}' +
        '@keyframes tourBlink{50%{opacity:.25}}' +
        '#tour-card .t-row{display:flex;align-items:center;gap:8px;margin-top:13px}' +
        '#tour-card button{font-family:inherit;font-size:10px;font-weight:700;letter-spacing:.5px;padding:7px 12px;border-radius:5px;cursor:pointer;border:1px solid #5a0a0a;background:transparent;color:#ffd9d9}' +
        '#tour-card button:hover{border-color:#00f0ff;color:#00f0ff}' +
        '#tour-card button.primary{background:#ffe600;border-color:#ffe600;color:#000}' +
        '#tour-card button.primary:hover{box-shadow:0 0 14px rgba(255,230,0,.5);color:#000}' +
        '#tour-card button:disabled{opacity:.35;cursor:default;box-shadow:none}' +
        '#tour-card .t-skip{margin-left:auto;border:0;padding:7px 2px;color:#8a6a6a;font-weight:400;text-decoration:underline}' +
        '#tour-card .t-skip:hover{color:#ff1a1a}' +
        '#tour-card .t-dots{display:flex;gap:4px}' +
        '#tour-card .t-dots span{width:6px;height:6px;border-radius:50%;background:#3a1a1a}' +
        '#tour-card .t-dots span.on{background:#ffe600;box-shadow:0 0 6px #ffe600}' +
        '#tour-card .t-dots span.past{background:#a09200}' +
        '@media(max-width:640px){#tour-card{left:12px!important;right:12px;top:auto!important;bottom:12px;width:auto}#tour-card.t-top{top:60px!important;bottom:auto}}' +
        '.tour-open-btn{font-family:inherit}' +
        '@media(prefers-reduced-motion:reduce){#tour-spot,#tour-card{transition:none;animation:none}}';

    var state = null; // {steps, i, firstRun, cleanup[]}

    function $(sel) { try { return document.querySelector(sel); } catch (e) { return null; } }

    function visibleRect(el) {
        if (!el) return null;
        var cs = getComputedStyle(el);
        if (cs.display === 'none' || cs.visibility === 'hidden') return null;
        var r = el.getBoundingClientRect();
        if (r.width < 4 || r.height < 4) return null;
        if (r.bottom < 0 || r.right < 0 || r.top > innerHeight || r.left > innerWidth) return null;
        return r;
    }

    function ensureStyle() {
        if (document.getElementById('tour-style')) return;
        var s = document.createElement('style');
        s.id = 'tour-style';
        s.textContent = CSS;
        document.head.appendChild(s);
    }

    function buildSteps() {
        var out = [];
        STEPS.forEach(function (s) {
            if (s.adminOnly) {
                var a = $(s.sel);
                if (!a || getComputedStyle(a).display === 'none') return;
            }
            out.push(s);
        });
        return out;
    }

    function place(card, rect) {
        var vw = innerWidth, vh = innerHeight, m = 14;
        var cw = card.offsetWidth, ch = card.offsetHeight;
        if (vw <= 640) { card.style.left = ''; card.style.top = ''; return; }
        var x, y;
        if (!rect) { x = (vw - cw) / 2; y = (vh - ch) / 2; }
        else {
            var cands = [
                { x: rect.right + m, y: rect.top, ok: rect.right + m + cw <= vw - 8 },
                { x: rect.left - cw - m, y: rect.top, ok: rect.left - cw - m >= 8 },
                { x: rect.left, y: rect.bottom + m, ok: rect.bottom + m + ch <= vh - 8 },
                { x: rect.left, y: rect.top - ch - m, ok: rect.top - ch - m >= 8 }
            ];
            var pick = cands.filter(function (c) { return c.ok; })[0];
            if (!pick) pick = { x: (vw - cw) / 2, y: Math.max(8, vh - ch - 20) }; // big target: float at the bottom
            x = pick.x; y = pick.y;
        }
        card.style.left = Math.max(8, Math.min(vw - cw - 8, x)) + 'px';
        card.style.top = Math.max(8, Math.min(vh - ch - 8, y)) + 'px';
    }

    function teardownStep() {
        if (!state) return;
        state.cleanup.forEach(function (f) { try { f(); } catch (e) { /* noop */ } });
        state.cleanup = [];
    }

    function render() {
        var st = state, step = st.steps[st.i];
        var spot = document.getElementById('tour-spot'), card = document.getElementById('tour-card'), block = document.getElementById('tour-block');

        // Which element does this step point at?
        var target = null, rect = null;
        [step.sel, step.alt].forEach(function (sel) {
            if (!rect && sel) { var el = $(sel); var r = visibleRect(el); if (r) { target = el; rect = r; } }
        });

        // Spotlight
        if (rect) {
            var pad = 6;
            spot.className = '';
            spot.style.top = (rect.top - pad) + 'px';
            spot.style.left = (rect.left - pad) + 'px';
            spot.style.width = (rect.width + pad * 2) + 'px';
            spot.style.height = (rect.height + pad * 2) + 'px';
        } else {
            spot.className = 'none';
            spot.style.top = '50%'; spot.style.left = '50%'; spot.style.width = '0px'; spot.style.height = '0px';
        }

        // Interactive steps must let clicks and keys reach the game underneath.
        block.className = step.wait ? 'thru' : '';

        // Card content
        var dots = '';
        for (var d = 0; d < st.steps.length; d++) dots += '<span class="' + (d === st.i ? 'on' : d < st.i ? 'past' : '') + '"></span>';
        var isFirst = st.i === 0, isLast = !!step.last || st.i === st.steps.length - 1;
        card.innerHTML =
            '<div class="t-step"><span>GUIDE ' + (st.i + 1) + '/' + st.steps.length + '</span><span class="t-dots">' + dots + '</span></div>' +
            '<div class="t-title">' + step.title + '</div>' +
            '<div class="t-body">' + step.body + '</div>' +
            (step.wait ? '<div class="t-wait" id="t-wait"><i></i><span>' + step.waitHint + '</span></div>' : '') +
            '<div class="t-row">' +
            (isFirst ? '' : '<button type="button" data-a="back">◂ BACK</button>') +
            '<button type="button" class="primary" data-a="next">' + (isLast ? 'START PLAYING' : step.wait ? 'SKIP STEP ▸' : (isFirst ? "LET'S GO ▸" : 'NEXT ▸')) + '</button>' +
            (isLast ? '' : '<button type="button" class="t-skip" data-a="skip">skip guide</button>') +
            '</div>';
        card.classList.toggle('t-top', !!step.wait); // on phones, keep the on-screen game keys uncovered
        card.style.animation = 'none'; void card.offsetWidth; card.style.animation = '';
        place(card, rect);

        // Don't steal focus on interactive steps: Enter/Space would press the button instead of playing the game.
        var nextBtn = card.querySelector('[data-a="next"]');
        if (nextBtn && !step.wait) nextBtn.focus({ preventScroll: true });
        else if (document.activeElement && document.activeElement.blur && card.contains(document.activeElement)) document.activeElement.blur();

        // Interactive step: watch for the real action
        teardownStep();
        if (step.wait) armWait(step, card);
    }

    function completeWait(step, card) {
        var w = card.querySelector('#t-wait'); if (!w || w.classList.contains('ok')) return;
        w.classList.add('ok'); w.querySelector('span').textContent = step.doneHint;
        var nb = card.querySelector('[data-a="next"]'); if (nb) nb.textContent = 'NEXT ▸';
        var idx = state.i;
        var t = setTimeout(function () { if (state && state.i === idx) go(1); }, 1100);
        state.cleanup.push(function () { clearTimeout(t); });
    }

    function armWait(step, card) {
        var done = function () { completeWait(step, card); };
        if (step.wait === 'move') {
            var count = 0, keys = /^(KeyW|KeyA|KeyS|KeyD|ArrowUp|ArrowDown|ArrowLeft|ArrowRight)$/;
            var kd = function (e) { if (keys.test(e.code) && ++count >= 4) done(); };
            var pd = function (e) { if (e.target && e.target.closest && e.target.closest('.k')) { count += 2; if (count >= 4) done(); } };
            addEventListener('keydown', kd, true); addEventListener('pointerdown', pd, true);
            state.cleanup.push(function () { removeEventListener('keydown', kd, true); removeEventListener('pointerdown', pd, true); });
        } else if (step.wait === 'talk') {
            var dlg = document.getElementById('dlg');
            if (!dlg) return;
            var check = function () { if (!dlg.hidden && /\S/.test(dlg.textContent) && !/CLASSIFIED/.test(dlg.textContent)) done(); };
            var mo = new MutationObserver(check);
            mo.observe(dlg, { attributes: true, childList: true, subtree: true, characterData: true });
            state.cleanup.push(function () { mo.disconnect(); });
        }
    }

    function go(delta) {
        if (!state) return;
        var n = state.i + delta;
        if (n < 0) return;
        if (n >= state.steps.length) return finish();
        // Close any NPC dialog the talk step opened so it doesn't sit under the card
        if (state.steps[state.i].wait === 'talk') { var dlg = document.getElementById('dlg'); if (dlg) dlg.hidden = true; }
        state.i = n;
        render();
    }

    function onResize() { if (state) render(); }

    function finish() {
        if (!state) return;
        var firstRun = state.firstRun;
        teardownStep();
        ['tour-block', 'tour-spot', 'tour-card'].forEach(function (id) { var el = document.getElementById(id); if (el) el.remove(); });
        removeEventListener('resize', onResize);
        removeEventListener('keydown', onKey, true);
        state = null;
        if (firstRun) {
            try { fetch('/api/tour/complete', { method: 'POST', credentials: 'same-origin', keepalive: true }); } catch (e) { /* retried next login */ }
        }
    }

    function onKey(e) {
        // Esc skips the guide, but only when no text field has focus.
        if (e.code === 'Escape' && state) { e.stopPropagation(); finish(); }
    }

    function start(replay) {
        if (state) return;
        ensureStyle();
        var steps = buildSteps();
        if (!steps.length) return;
        state = { steps: steps, i: 0, firstRun: !replay, cleanup: [] };

        var block = document.createElement('div'); block.id = 'tour-block';
        var spot = document.createElement('div'); spot.id = 'tour-spot'; spot.className = 'none';
        var card = document.createElement('div'); card.id = 'tour-card'; card.setAttribute('role', 'dialog'); card.setAttribute('aria-live', 'polite');
        document.body.appendChild(block); document.body.appendChild(spot); document.body.appendChild(card);

        card.addEventListener('click', function (e) {
            var b = e.target.closest && e.target.closest('button'); if (!b) return;
            var a = b.dataset.a;
            if (a === 'next') go(1); else if (a === 'back') go(-1); else if (a === 'skip') finish();
        });
        addEventListener('resize', onResize);
        addEventListener('keydown', onKey, true);
        render();
    }

    // Wait until the player has gotten past the boot screen, then run.
    function whenInHub(cb) {
        var boot = document.getElementById('boot');
        if (!boot || boot.hidden) return cb();
        var iv = setInterval(function () { if (boot.hidden) { clearInterval(iv); setTimeout(cb, 500); } }, 400);
    }

    window.NJTour = { start: function () { start(true); }, finish: finish };

    function init() {
        var btn = document.getElementById('tour-replay');
        if (btn) btn.addEventListener('click', function () { start(true); });
        fetch('/api/me', { credentials: 'same-origin' })
            .then(function (r) { return r.ok ? r.json() : null; })
            .then(function (u) { if (u && !u.has_seen_tour) whenInHub(function () { start(false); }); })
            .catch(function () { /* no tour if we can't tell */ });
    }

    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
    else init();
})();
