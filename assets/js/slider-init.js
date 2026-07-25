(function () {
  function initSlider() {
    if (typeof tns !== 'function' || !document.querySelector('.base')) {
      return;
    }
    tns({
      container: '.base',
      items: 1,
      autoWidth: true,
      slideBy: 'page',
      mouseDrag: true,
      swipeAngle: false,
      loop: true,
      autoplay: true,
      speed: 400,
      controls: false,
      nav: false,
      prevButton: false,
      nextButton: false,
      autoplayButton: false,
      lazyload: true,
      lazyloadSelector: '.tns-lazy-img'
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initSlider);
  } else {
    initSlider();
  }
})();
