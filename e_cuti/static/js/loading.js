// static/js/loading.js
// Tangkap event sebelum unload
window.addEventListener('beforeunload', function() {
    if (document.querySelector('.loading-form:has(button[type="submit"]:disabled)')) {
      document.getElementById('loading-overlay').style.display = 'flex';
    }
  });