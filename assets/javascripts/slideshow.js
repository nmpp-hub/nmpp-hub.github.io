// Robust slideshow logic for .nmpp-slideshow
document.addEventListener('DOMContentLoaded', function() {
  var container = document.querySelector('.nmpp-slideshow');
  if (!container) return;
  var slides = Array.prototype.slice.call(container.querySelectorAll('.nmpp-slide'));
  var dots = Array.prototype.slice.call(container.querySelectorAll('.nmpp-dot'));
  var leftArrow = container.querySelector('.nmpp-arrow-left');
  var rightArrow = container.querySelector('.nmpp-arrow-right');
  var current = 0;
  var interval = null;

  function showSlide(idx) {
    slides.forEach(function(slide, i) {
      slide.classList.toggle('active', i === idx);
    });
    dots.forEach(function(dot, i) {
      dot.classList.toggle('active', i === idx);
    });
    current = idx;
  }

  function nextSlide() {
    showSlide((current + 1) % slides.length);
  }
  function prevSlide() {
    showSlide((current - 1 + slides.length) % slides.length);
  }

  function resetInterval() {
    if (interval) clearInterval(interval);
    interval = setInterval(nextSlide, 5000);
  }

  dots.forEach(function(dot, i) {
    dot.addEventListener('click', function() {
      showSlide(i);
      resetInterval();
    });
  });
  if (leftArrow) {
    leftArrow.addEventListener('click', function(e) {
      e.preventDefault();
      prevSlide();
      resetInterval();
    });
  }
  if (rightArrow) {
    rightArrow.addEventListener('click', function(e) {
      e.preventDefault();
      nextSlide();
      resetInterval();
    });
  }

  showSlide(0);
  resetInterval();
});
