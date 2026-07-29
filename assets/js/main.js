/**
 * CriptoTradey - Portal de Criptomoedas
 * Main JavaScript
 */

(function() {
  'use strict';

  // ============================================================
  // Dark / Light Theme Toggle
  // ============================================================
  const themeToggle = document.getElementById('themeToggle');
  const html = document.documentElement;

  // Load saved theme or use system preference
  const savedTheme = localStorage.getItem('criptotradey-theme');
  if (savedTheme) {
    html.setAttribute('data-theme', savedTheme);
  } else if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
    html.setAttribute('data-theme', 'dark');
  }

  if (themeToggle) {
    themeToggle.addEventListener('click', function() {
      const currentTheme = html.getAttribute('data-theme');
      const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
      html.setAttribute('data-theme', newTheme);
      localStorage.setItem('criptotradey-theme', newTheme);

      // Update icon
      const icon = themeToggle.querySelector('.theme-icon');
      if (icon) {
        icon.textContent = newTheme === 'dark' ? '☀️' : '🌙';
      }
    });

    // Set initial icon
    const icon = themeToggle.querySelector('.theme-icon');
    if (icon) {
      const currentTheme = html.getAttribute('data-theme');
      icon.textContent = currentTheme === 'dark' ? '☀️' : '🌙';
    }
  }

  // Listen for system theme changes
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', function(e) {
    if (!localStorage.getItem('criptotradey-theme')) {
      html.setAttribute('data-theme', e.matches ? 'dark' : 'light');
    }
  });

  // ============================================================
  // Mobile Menu Toggle
  // ============================================================
  const mobileMenuBtn = document.getElementById('mobileMenuBtn');
  const mainNav = document.getElementById('mainNav');

  if (mobileMenuBtn && mainNav) {
    mobileMenuBtn.addEventListener('click', function() {
      const isOpen = mainNav.classList.toggle('open');
      mobileMenuBtn.setAttribute('aria-expanded', isOpen);
      mobileMenuBtn.innerHTML = isOpen ? '✕' : '☰';
    });

    // Close menu when clicking outside
    document.addEventListener('click', function(e) {
      if (!mobileMenuBtn.contains(e.target) && !mainNav.contains(e.target)) {
        mainNav.classList.remove('open');
        mobileMenuBtn.setAttribute('aria-expanded', 'false');
        mobileMenuBtn.innerHTML = '☰';
      }
    });

    // Close menu when a link is clicked
    mainNav.querySelectorAll('a').forEach(function(link) {
      link.addEventListener('click', function() {
        mainNav.classList.remove('open');
        mobileMenuBtn.setAttribute('aria-expanded', 'false');
        mobileMenuBtn.innerHTML = '☰';
      });
    });
  }

  // ============================================================
  // Newsletter Form Handler
  // ============================================================
  const newsletterForms = document.querySelectorAll('.newsletter-form');

  newsletterForms.forEach(function(form) {
    form.addEventListener('submit', function(e) {
      e.preventDefault();
      const emailInput = form.querySelector('input[type="email"]');
      const button = form.querySelector('button');
      const originalText = button.textContent;

      if (!emailInput || !emailInput.value) {
        emailInput.focus();
        return;
      }

      // Simulate submission
      button.disabled = true;
      button.textContent = 'Enviando...';

      setTimeout(function() {
        button.textContent = '✓ Inscrito!';
        button.style.background = '#00D4AA';
        emailInput.value = '';
        emailInput.placeholder = 'Obrigado por se inscrever! 🎉';

        setTimeout(function() {
          button.disabled = false;
          button.textContent = originalText;
          button.style.background = '';
          emailInput.placeholder = 'Seu melhor e-mail';
        }, 3000);
      }, 1000);
    });
  });

  // ============================================================
  // Lazy Loading Images
  // ============================================================
  if ('IntersectionObserver' in window) {
    const lazyImages = document.querySelectorAll('img[loading="lazy"]');

    // Browser supports native lazy loading, no need for polyfill
    if ('loading' in HTMLImageElement.prototype) {
      return;
    }

    const imageObserver = new IntersectionObserver(function(entries) {
      entries.forEach(function(entry) {
        if (entry.isIntersecting) {
          const img = entry.target;
          if (img.dataset.src) {
            img.src = img.dataset.src;
            img.removeAttribute('data-src');
          }
          imageObserver.unobserve(img);
        }
      });
    });

    lazyImages.forEach(function(img) {
      imageObserver.observe(img);
    });
  }

  // ============================================================
  // Active Nav Link Highlight
  // ============================================================
  const currentPath = window.location.pathname;
  const navLinks = document.querySelectorAll('.main-nav a');

  navLinks.forEach(function(link) {
    const href = link.getAttribute('href');
    if (href === '/' && (currentPath === '/' || currentPath.endsWith('index.html'))) {
      link.classList.add('active');
    } else if (href && href !== '/' && currentPath.includes(href.replace(/^\//, ''))) {
      link.classList.add('active');
    }
  });

  // ============================================================
  // Smooth scroll for anchor links
  // ============================================================
  document.querySelectorAll('a[href^="#"]').forEach(function(anchor) {
    anchor.addEventListener('click', function(e) {
      const href = this.getAttribute('href');
      if (href === '#') return;

      const target = document.querySelector(href);
      if (target) {
        e.preventDefault();
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
  });

  // ============================================================
  // Back to Top Button
  // ============================================================
  const backToTopBtn = document.getElementById('backToTop');
  if (backToTopBtn) {
    window.addEventListener('scroll', function() {
      if (window.scrollY > 500) {
        backToTopBtn.classList.add('visible');
      } else {
        backToTopBtn.classList.remove('visible');
      }
    });

    backToTopBtn.addEventListener('click', function() {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
  }

})();
