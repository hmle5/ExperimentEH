// static/js/disable_copy.js

(function() {
  // 3) Block right-click / context menu
  document.addEventListener('contextmenu', function(e) {
    e.preventDefault();
  });

  // 4) Intercept copy / cut events
  document.addEventListener('copy', function(e) {
    e.preventDefault();
    alert('Copying is disabled on this page.');
  });
  document.addEventListener('cut', function(e) {
    e.preventDefault();
    alert('Cutting is disabled on this page.');
  });

  // 5) Prevent selection via keyboard (Shift+Arrow, Ctrl+A, etc.)
  document.addEventListener('selectstart', function(e) {
    e.preventDefault();
  });

  // 6) Prevent drag-and-drop selection
  document.addEventListener('dragstart', function(e) {
    e.preventDefault();
  });

  // 7) Warn on PrintScreen key (cannot truly block, but discourage)
  document.addEventListener('keydown', function(e) {
    if (e.key === 'PrintScreen') {
      e.preventDefault();
      alert('Screenshots are discouraged.');
    }
  });

  // If you ever want to re-enable selection for a specific element,
  // you can give it a class "allow-select" and remove these listeners,
  // or check e.target for that class and skip .preventDefault().
})();
