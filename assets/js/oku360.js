(function () {
  var root = document.querySelector('.oku360');
  if (!root) return;

  var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var layers = root.querySelectorAll('[data-oku-layer]');

  function updateLayers() {
    if (reduceMotion) return;
    var vh = window.innerHeight || 1;
    for (var i = 0; i < layers.length; i++) {
      var el = layers[i];
      var speed = parseFloat(el.getAttribute('data-oku-layer')) || 0.18;
      var rect = el.getBoundingClientRect();
      var progress = (vh * 0.45 - (rect.top + rect.height / 2)) / vh;
      el.style.transform = 'translate3d(0,' + (progress * speed * 72).toFixed(2) + 'px,0)';
    }
  }

  var ticking = false;
  function onScroll() {
    if (ticking) return;
    ticking = true;
    window.requestAnimationFrame(function () {
      updateLayers();
      ticking = false;
    });
  }

  if (!reduceMotion && layers.length) {
    window.addEventListener('scroll', onScroll, { passive: true });
    window.addEventListener('resize', onScroll, { passive: true });
    updateLayers();
  }

  var heroVideo = root.querySelector('[data-oku-hero-video]');
  if (heroVideo) {
    heroVideo.setAttribute('playsinline', '');
    heroVideo.muted = true;

    function playHeroVideo() {
      if (reduceMotion) {
        heroVideo.pause();
        heroVideo.removeAttribute('autoplay');
        return;
      }
      var playPromise = heroVideo.play();
      if (playPromise && typeof playPromise.catch === 'function') {
        playPromise.catch(function () { /* autoplay engellendi; poster kalır */ });
      }
    }

    playHeroVideo();

    document.addEventListener('visibilitychange', function () {
      if (document.hidden || reduceMotion) {
        heroVideo.pause();
        return;
      }
      playHeroVideo();
    });
  }

  var desktopQuery = window.matchMedia('(min-width: 768px)');

  function escapeHtml(str) {
    if (!str) return '';
    var div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  function openCatalog(title, url) {
    if (!url) return;
    if (desktopQuery.matches && typeof window.openPopup === 'function') {
      window.openPopup({
        title: title,
        bodyHtml: '<iframe src="' + escapeHtml(url) + '" title="' + escapeHtml(title) + '" loading="lazy" allowfullscreen></iframe>',
        variant: 'media'
      });
      return;
    }
    window.open(url, '_blank', 'noopener');
  }

  root.querySelectorAll('[data-oku-catalog-open]').forEach(function (trigger) {
    trigger.addEventListener('click', function (event) {
      var title = trigger.getAttribute('data-oku-catalog-title') || 'Katalog';
      var url = trigger.getAttribute('data-oku-catalog-url') || '';
      if (!url) return;
      event.preventDefault();
      openCatalog(title, url);
    });
  });
})();
