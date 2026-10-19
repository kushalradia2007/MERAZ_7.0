/* Shared helper for the room pages (served at /room-common.js).
 *
 * The server is the single source of truth for flags and progress:
 *   NJ.submit(roomId, flag) -> {success, message, challenge, solved[], reward}
 *   NJ.progress()           -> {score, current_room, rooms:{"1":[1,3],...}, rewards:{"1":{"1":"..."}}} | null
 * A 401 (expired session) sends the player back to the login page.
 */
(function () {
    async function call(url, opts) {
        let res;
        try {
            res = await fetch(url, Object.assign({ credentials: 'same-origin' }, opts || {}));
        } catch (e) {
            return { ok: false, status: 0, data: { message: 'Network error. Check your connection and try again.' } };
        }
        if (res.status === 401) {
            window.location.href = '/';
            return { ok: false, status: 401, data: { message: 'Session expired. Please log in again.' } };
        }
        let data = {};
        try { data = await res.json(); } catch (e) { /* non-JSON error body */ }
        return { ok: res.ok, status: res.status, data: data };
    }

    window.NJ = {
        progress: async function () {
            const r = await call('/api/progress');
            return r.ok ? r.data : null;
        },
        submit: async function (roomId, flag) {
            const fd = new FormData();
            fd.append('room_id', roomId);
            fd.append('flag', flag);
            const r = await call('/api/submit_flag', { method: 'POST', body: fd });
            const d = r.data || {};
            const detail = typeof d.detail === 'string' ? d.detail : '';
            return {
                success: !!(r.ok && d.success),
                message: d.message || detail || 'Request failed. Please try again.',
                challenge: d.challenge || null,
                solved: d.solved || [],
                reward: d.reward || ''     // story text for the solved challenge (server-side, rooms 1-3)
            };
        }
    };
})();
