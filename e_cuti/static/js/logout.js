document.addEventListener('DOMContentLoaded', function() {
    // Clear all caches on logout
    if (window.performance && performance.navigation.type === 1) {
        // This page was reloaded - force fresh load
        window.location.reload(true);
    }
    
    // Intercept logout links
    document.querySelectorAll('a[href*="logout"]').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            // Clear local storage
            localStorage.clear();
            // Clear session storage
            sessionStorage.clear();
            // Force hard redirect
            window.location.href = this.href + '?nocache=' + Date.now();
        });
    });
});