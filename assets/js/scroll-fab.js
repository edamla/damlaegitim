(function () {
  var btn = document.getElementById('scroll-fab');
  if (!btn) return;

  var icon = btn.querySelector('.scroll-fab__icon');
  var mode = 'down';

  function isScrollable() {
    return document.documentElement.scrollHeight > window.innerHeight + 48;
  }

  function getMode() {
    var scrollY = window.pageYOffset || document.documentElement.scrollTop;
    var distanceToBottom = document.documentElement.scrollHeight - (scrollY + window.innerHeight);
    return distanceToBottom < scrollY ? 'up' : 'down';
  }

  function updateButton() {
    if (!isScrollable()) {
      btn.hidden = true;
      return;
    }

    btn.hidden = false;
    mode = getMode();

    if (mode === 'up') {
      icon.classList.remove('fa-chevron-down');
      icon.classList.add('fa-chevron-up');
      btn.setAttribute('aria-label', 'Sayfa başına git');
    } else {
      icon.classList.remove('fa-chevron-up');
      icon.classList.add('fa-chevron-down');
      btn.setAttribute('aria-label', 'Sayfa sonuna git');
    }
  }

  function onClick() {
    var maxScroll = document.documentElement.scrollHeight - window.innerHeight;
    var target = mode === 'up' ? 0 : maxScroll;
    window.scrollTo({ top: target, behavior: 'auto' });
  }

  btn.addEventListener('click', onClick);
  window.addEventListener('scroll', updateButton, { passive: true });
  window.addEventListener('resize', updateButton);
  updateButton();
})();
