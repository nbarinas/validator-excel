// Activity Monitor / Heartbeat
(function () {
    let lastActivityTime = Date.now();
    let isUserActive = false;
    const HEARTBEAT_INTERVAL = 5 * 60 * 1000; // 5 minutes
    const TOKEN_KEY = 'token';

    // Track activity
    function registerActivity() {
        isUserActive = true;
        lastActivityTime = Date.now();
    }

    window.addEventListener('mousemove', registerActivity);
    window.addEventListener('keydown', registerActivity);
    window.addEventListener('click', registerActivity);
    window.addEventListener('scroll', registerActivity);

    // Send Heartbeat
    async function sendHeartbeat() {
        if (!isUserActive) return; // Don't send if truly idle

        const token = localStorage.getItem(TOKEN_KEY);
        if (!token) return;

        try {
            await fetch('/users/heartbeat', {
                method: 'POST',
                headers: {
                    'Authorization': 'Bearer ' + token
                }
            });
            console.log('Heartbeat sent');
            isUserActive = false; // Reset flag until next activity
        } catch (e) {
            console.error('Error sending heartbeat', e);
        }
    }

    // Initial heartbeat on load
    sendHeartbeat();

    // Loop
    setInterval(sendHeartbeat, HEARTBEAT_INTERVAL);
})();
