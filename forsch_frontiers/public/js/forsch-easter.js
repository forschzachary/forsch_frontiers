(function () {
  var KONAMI = [38, 38, 40, 40, 37, 39, 37, 39, 66, 65];
  var pos = 0;
  var rct2Active = false;

  var toast = null;

  function showToast(msg) {
    if (toast) document.body.removeChild(toast);
    toast = document.createElement('div');
    toast.textContent = msg;
    toast.style.cssText = [
      'position:fixed', 'bottom:24px', 'left:50%', 'transform:translateX(-50%)',
      'background:#2A1A0E', 'color:#F0B429',
      'font-family:"Press Start 2P",monospace', 'font-size:10px',
      'padding:10px 18px', 'border:2px solid #C8271A',
      'z-index:99999', 'pointer-events:none',
      'white-space:nowrap',
    ].join(';');
    document.body.appendChild(toast);
    setTimeout(function () {
      if (toast && toast.parentNode) toast.parentNode.removeChild(toast);
      toast = null;
    }, 3000);
  }

  function getBaseTheme() {
    try { return localStorage.getItem('theme') || 'light'; } catch(e) { return 'light'; }
  }

  const obs = new MutationObserver(() => {
    if (rct2Active && document.documentElement.getAttribute('data-theme') !== 'rct2') {
      document.documentElement.setAttribute('data-theme', 'rct2');
    }
  });
  obs.observe(document.documentElement, {attributes: true, attributeFilter: ['data-theme', 'class']});

  document.addEventListener('keydown', function (e) {
    if (e.keyCode === KONAMI[pos]) {
      pos++;
      if (pos === KONAMI.length) {
        pos = 0;
        rct2Active = !rct2Active;
        if (rct2Active) {
          document.documentElement.setAttribute('data-theme', 'rct2');
          showToast('★ RCT2 MODE ACTIVATED — ESC to exit ★');
        } else {
          document.documentElement.setAttribute('data-theme', getBaseTheme());
          showToast('Back to normal. Guests are still happy.');
        }
      }
    } else if (e.keyCode === 27 && rct2Active) {
      rct2Active = false;
      pos = 0;
      document.documentElement.setAttribute('data-theme', getBaseTheme());
      showToast('Back to normal. Guests are still happy.');
    } else {
      pos = 0;
    }
  });
})();
