(function () {
  var nav = document.getElementById('MagicMenu');
  if (!nav) return;

  function syncNavHeight() {
    document.documentElement.style.setProperty('--nav-height', nav.offsetHeight + 'px');
    nav.style.top = '0';
  }

  function onScroll() {
    var st = window.pageYOffset || document.documentElement.scrollTop;
    nav.classList.toggle('site-nav--scrolled', st > 0);
  }

  syncNavHeight();
  onScroll();

  window.addEventListener('scroll', onScroll, { passive: true });
  window.addEventListener('resize', syncNavHeight);

  if (typeof ResizeObserver !== 'undefined') {
    new ResizeObserver(syncNavHeight).observe(nav);
  }
})();
