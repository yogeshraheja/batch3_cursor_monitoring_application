/**
 * Same-origin auto-refresh for metrics detail pages (10s).
 * Relies on the authenticated session cookie; no cross-origin requests.
 */
(function () {
  var meta = document.querySelector('meta[name="refresh-interval"]');
  if (!meta) return;
  var seconds = parseInt(meta.getAttribute("content") || "10", 10);
  if (!seconds || seconds < 1) return;
  window.setTimeout(function () {
    window.location.reload();
  }, seconds * 1000);
})();
