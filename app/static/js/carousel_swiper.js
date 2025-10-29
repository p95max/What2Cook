document.addEventListener('DOMContentLoaded', function () {
  const swiper = new Swiper('.mySwiper', {
    slidesPerView: 'auto',
    spaceBetween: 16,
    freeMode: true,
    preloadImages: false,
    lazy: {
      loadOnTransitionStart: true,
      loadPrevNext: true,
    },
    keyboard: {
      enabled: true,
      onlyInViewport: true,
    },
    navigation: {
      nextEl: '.swiper-button-next',
      prevEl: '.swiper-button-prev',
    },
    pagination: {
      el: '.swiper-pagination',
      clickable: true,
    },
    breakpoints: {
      320: { slidesPerView: 1.2 },
      576: { slidesPerView: 2 },
      768: { slidesPerView: 2.5 },
      992: { slidesPerView: 3 },
      1200: { slidesPerView: 4 },
    },
    speed: 400,
  });
});