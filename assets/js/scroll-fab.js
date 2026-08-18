(function () {
  var btn = document.getElementById('scroll-fab');
  if (!btn) return;

  var icon = btn.querySelector('.scroll-fab__icon');
  var reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var scrollBehavior = reducedMotion ? 'auto' : 'smooth';
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
      btn.setAttribute('aria-label', 'Yukarı çık');
    } else {
      icon.classList.remove('fa-chevron-up');
      icon.classList.add('fa-chevron-down');
      btn.setAttribute('aria-label', 'Aşağı in');
    }
  }

  function onClick() {
    if (mode === 'up') {
      window.scrollTo({ top: 0, behavior: scrollBehavior });
      return;
    }

    var scrollY = window.pageYOffset || document.documentElement.scrollTop;
    var maxScroll = document.documentElement.scrollHeight - window.innerHeight;
    var target = Math.min(scrollY + window.innerHeight * 0.85, maxScroll);
    window.scrollTo({ top: target, behavior: scrollBehavior });
  }

  btn.addEventListener('click', onClick);
  window.addEventListener('scroll', updateButton, { passive: true });
  window.addEventListener('resize', updateButton);
  updateButton();
})();
