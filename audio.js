/* Procedural audio for NIGHTJAR (served at /audio.js). No sound files: everything
 * is synthesised with the Web Audio API.
 *
 *   NJAudio.sfx(name)      step | select | talk | unlock | locked | success | error | door | toggle
 *   NJAudio.toggle()       mute / unmute (persisted in localStorage as nj_muted)
 *   NJAudio.isMuted()
 *
 * Browsers only allow audio after a user gesture, so the AudioContext is created
 * lazily on the first key press / click / tap. Until then every call is a no-op.
 * Any element with [data-sound-toggle] becomes a mute button automatically.
 */
(function () {
    'use strict';

    var KEY = 'nj_muted';
    var ctx = null, master = null, sfxBus = null, ambBus = null, verb = null;
    var muted = false, ambientOn = false, pingTimer = 0, started = false;
    var listeners = [];

    try { muted = localStorage.getItem(KEY) === '1'; } catch (e) { /* private mode */ }

    function ensure() {
        if (ctx) return ctx;
        var AC = window.AudioContext || window.webkitAudioContext;
        if (!AC) return null;
        try { ctx = new AC(); } catch (e) { return null; }
        master = ctx.createGain();
        master.gain.value = muted ? 0 : 1;
        master.connect(ctx.destination);
        sfxBus = ctx.createGain(); sfxBus.gain.value = 0.9; sfxBus.connect(master);
        ambBus = ctx.createGain(); ambBus.gain.value = 0.0; ambBus.connect(master);
        // a short feedback delay gives the pings a sense of space
        verb = ctx.createDelay(0.6); verb.delayTime.value = 0.28;
        var fb = ctx.createGain(); fb.gain.value = 0.38;
        var lp = ctx.createBiquadFilter(); lp.type = 'lowpass'; lp.frequency.value = 1800;
        verb.connect(lp); lp.connect(fb); fb.connect(verb); lp.connect(ambBus);
        return ctx;
    }

    function noiseBuffer(sec) {
        var len = Math.floor(ctx.sampleRate * sec), buf = ctx.createBuffer(1, len, ctx.sampleRate), d = buf.getChannelData(0);
        for (var i = 0; i < len; i++) d[i] = Math.random() * 2 - 1;
        return buf;
    }

    /* ─── ambience: slow detuned drone + server-room hush + sparse pings ─── */
    function startAmbient() {
        if (ambientOn || !ctx) return;
        ambientOn = true;
        var t = ctx.currentTime;

        var lp = ctx.createBiquadFilter(); lp.type = 'lowpass'; lp.frequency.value = 240; lp.Q.value = 3;
        var lfo = ctx.createOscillator(), lfoG = ctx.createGain();
        lfo.frequency.value = 0.06; lfoG.gain.value = 90; lfo.connect(lfoG); lfoG.connect(lp.frequency); lfo.start(t);
        var droneG = ctx.createGain(); droneG.gain.value = 0.5; lp.connect(droneG); droneG.connect(ambBus);
        [[55, 'sawtooth', 0], [55.35, 'sawtooth', 0], [82.4, 'triangle', 0], [110.1, 'sine', 0]].forEach(function (o) {
            var os = ctx.createOscillator(); os.type = o[1]; os.frequency.value = o[0]; os.connect(lp); os.start(t);
        });

        var nz = ctx.createBufferSource(); nz.buffer = noiseBuffer(3); nz.loop = true;
        var bp = ctx.createBiquadFilter(); bp.type = 'bandpass'; bp.frequency.value = 520; bp.Q.value = 0.7;
        var nzG = ctx.createGain(); nzG.gain.value = 0.07;
        var nl = ctx.createOscillator(), nlG = ctx.createGain(); nl.frequency.value = 0.11; nlG.gain.value = 0.03; nl.connect(nlG); nlG.connect(nzG.gain); nl.start(t);
        nz.connect(bp); bp.connect(nzG); nzG.connect(ambBus); nz.start(t);

        ambBus.gain.cancelScheduledValues(t);
        ambBus.gain.setValueAtTime(0, t);
        ambBus.gain.linearRampToValueAtTime(0.34, t + 3.5);
        schedulePing();
    }

    var PENT = [880, 987.8, 1174.7, 1318.5, 1568, 1760];
    function schedulePing() {
        clearTimeout(pingTimer);
        pingTimer = setTimeout(function () {
            if (ctx && !muted && !document.hidden) {
                var f = PENT[(Math.random() * PENT.length) | 0], t = ctx.currentTime;
                var o = ctx.createOscillator(), g = ctx.createGain();
                o.type = 'sine'; o.frequency.value = f;
                g.gain.setValueAtTime(0.0001, t); g.gain.exponentialRampToValueAtTime(0.09, t + 0.01); g.gain.exponentialRampToValueAtTime(0.0001, t + 0.55);
                o.connect(g); g.connect(ambBus); g.connect(verb); o.start(t); o.stop(t + 0.6);
            }
            schedulePing();
        }, 4500 + Math.random() * 8000);
    }

    /* ─── tiny synth helpers ─── */
    function tone(type, f0, f1, t0, dur, vol, bus) {
        var o = ctx.createOscillator(), g = ctx.createGain();
        o.type = type; o.frequency.setValueAtTime(f0, t0);
        if (f1 && f1 !== f0) o.frequency.exponentialRampToValueAtTime(f1, t0 + dur);
        g.gain.setValueAtTime(0.0001, t0); g.gain.exponentialRampToValueAtTime(vol, t0 + 0.008); g.gain.exponentialRampToValueAtTime(0.0001, t0 + dur);
        o.connect(g); g.connect(bus || sfxBus); o.start(t0); o.stop(t0 + dur + 0.05);
    }
    function burst(freq, q, t0, dur, vol) {
        var s = ctx.createBufferSource(); s.buffer = noiseBuffer(dur + 0.05);
        var f = ctx.createBiquadFilter(); f.type = 'bandpass'; f.frequency.value = freq; f.Q.value = q;
        var g = ctx.createGain(); g.gain.setValueAtTime(vol, t0); g.gain.exponentialRampToValueAtTime(0.0001, t0 + dur);
        s.connect(f); f.connect(g); g.connect(sfxBus); s.start(t0); s.stop(t0 + dur + 0.05);
    }

    var SFX = {
        step: function (t) { burst(150 + Math.random() * 60, 1.1, t, 0.05, 0.12); },
        select: function (t) { tone('square', 1300, 1000, t, 0.05, 0.05); },
        toggle: function (t) { tone('triangle', 660, 880, t, 0.09, 0.08); },
        talk: function (t) { for (var i = 0; i < 3; i++) tone('square', 330 + Math.random() * 260, 0, t + i * 0.055, 0.045, 0.045); },
        locked: function (t) { tone('square', 120, 90, t, 0.11, 0.09); tone('square', 120, 90, t + 0.15, 0.13, 0.09); },
        error: function (t) { tone('sawtooth', 200, 110, t, 0.22, 0.08); },
        door: function (t) { burst(240, 0.8, t, 0.14, 0.18); tone('triangle', 180, 320, t, 0.18, 0.08); },
        unlock: function (t) { burst(1800, 2, t, 0.06, 0.1); [523.3, 659.3, 784, 1046.5].forEach(function (f, i) { tone('triangle', f, 0, t + 0.07 + i * 0.075, 0.2, 0.1); }); },
        success: function (t) { [523.3, 659.3, 784, 1046.5, 1318.5].forEach(function (f, i) { tone('triangle', f, 0, t + i * 0.085, 0.3, 0.1); tone('sine', f * 2, 0, t + i * 0.085, 0.2, 0.03); }); }
    };

    function sfx(name) {
        if (!ctx || muted || ctx.state !== 'running') return;
        var fn = SFX[name]; if (!fn) return;
        try { fn(ctx.currentTime + 0.005); } catch (e) { /* never let audio break the game */ }
    }

    /* ─── state ─── */
    function paint() {
        Array.prototype.forEach.call(document.querySelectorAll('[data-sound-toggle]'), function (el) {
            el.classList.toggle('muted', muted);
            el.setAttribute('aria-pressed', muted ? 'true' : 'false');
            el.setAttribute('title', muted ? 'Sound is off (M)' : 'Sound is on (M)');
            var ico = el.querySelector('.ico'), lbl = el.querySelector('.lbl');
            if (ico) ico.textContent = muted ? '×' : '♪';
            if (lbl) lbl.textContent = muted ? 'MUTED' : 'SOUND';
        });
        listeners.forEach(function (f) { try { f(muted); } catch (e) { /* noop */ } });
    }

    function setMuted(m) {
        muted = !!m;
        try { localStorage.setItem(KEY, muted ? '1' : '0'); } catch (e) { /* noop */ }
        if (ctx) {
            var t = ctx.currentTime;
            master.gain.cancelScheduledValues(t);
            master.gain.setTargetAtTime(muted ? 0 : 1, t, 0.08);
            if (!muted && ctx.state === 'suspended') ctx.resume();
        }
        paint();
        if (!muted) { start(); sfx('toggle'); }
    }

    function start() {
        if (!ensure()) return;
        if (ctx.state === 'suspended') { try { ctx.resume(); } catch (e) { /* noop */ } }
        if (!muted) startAmbient();
        started = true;
    }

    // first user gesture unlocks audio
    function onGesture() {
        start();
        if (started && ctx && ctx.state === 'running') {
            ['pointerdown', 'keydown', 'touchend'].forEach(function (ev) { removeEventListener(ev, onGesture, true); });
        }
    }
    ['pointerdown', 'keydown', 'touchend'].forEach(function (ev) { addEventListener(ev, onGesture, true); });

    // save battery: silence the background tab
    document.addEventListener('visibilitychange', function () {
        if (!ctx) return;
        if (document.hidden) ctx.suspend();
        else if (!muted) ctx.resume();
    });

    function wire() {
        Array.prototype.forEach.call(document.querySelectorAll('[data-sound-toggle]'), function (el) {
            if (el._njw) return; el._njw = 1;
            el.addEventListener('click', function () { setMuted(!muted); });
        });
        paint();
    }

    window.NJAudio = {
        sfx: sfx,
        start: start,
        isMuted: function () { return muted; },
        setMuted: setMuted,
        toggle: function () { setMuted(!muted); },
        onChange: function (f) { listeners.push(f); }
    };

    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', wire); else wire();
})();
