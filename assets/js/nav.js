(function () {
  var nav = document.getElementById('MagicMenu');
  if (!nav) return;

  var lastScrollTop = 0;
  var delta = 5;
  var didScroll = false;
  var navbarHeight = nav.offsetHeight;

  window.addEventListener('scroll', function () {
    didScroll = true;
  }, { passive: true });

  setInterval(function () {
    if (!didScroll) return;
    didScroll = false;

    var st = window.pageYOffset || document.documentElement.scrollTop;
    if (Math.abs(lastScrollTop - st) <= delta) return;

    if (st > lastScrollTop && st > navbarHeight) {
      nav.classList.remove('nav-down');
      nav.classList.add('nav-up');
      nav.style.top = -nav.offsetHeight + 'px';
    } else if (st + window.innerHeight < document.documentElement.scrollHeight) {
      nav.classList.remove('nav-up');
      nav.classList.add('nav-down');
      nav.style.top = '0';
    }

    lastScrollTop = st <= 0 ? 0 : st;
  }, 250);
})();
