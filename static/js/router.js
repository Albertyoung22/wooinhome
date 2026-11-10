const SPARouter = {
  isNavigating: false,

  init() {
    // Intercept clicks on links
    document.addEventListener('click', (e) => {
      const link = e.target.closest('a');
      if (!link) return;

      const href = link.getAttribute('href');
      // Ignore anchors, external links, javascript:, tel:, mailto:, admin links
      if (!href || href.startsWith('#') || href.startsWith('http') || href.startsWith('javascript') || href.startsWith('tel:') || href.startsWith('mailto:') || href.startsWith('/admin') || href.startsWith('/api') || href.startsWith('/static')) {
        return;
      }

      // Check if explicitly non-SPA or download
      if (link.getAttribute('target') === '_blank' || link.hasAttribute('download')) {
        return;
      }

      e.preventDefault();
      this.navigateTo(href);
    });

    // Handle browser Back / Forward buttons
    window.addEventListener('popstate', (e) => {
      this.loadPage(window.location.pathname, false);
    });

    this.updateActiveNav(window.location.pathname);
  },

  async navigateTo(url) {
    if (this.isNavigating || url === window.location.pathname) return;
    window.history.pushState(null, '', url);
    await this.loadPage(url, true);
  },

  async loadPage(url, shouldScroll = true) {
    this.isNavigating = true;
    this.showProgressBar();

    const mainContainer = document.getElementById('spa-main-content');
    if (mainContainer) {
      mainContainer.classList.add('page-transition-exit');
    }

    try {
      const res = await fetch(url, {
        headers: { 'X-Requested-With': 'SPA' }
      });

      if (!res.ok) {
        // Fallback to normal browser navigation if error
        window.location.href = url;
        return;
      }

      const contentType = res.headers.get('content-type') || '';
      if (contentType.includes('application/json')) {
        const data = await res.json();
        if (data.title) document.title = data.title;
        if (mainContainer && data.html) {
          mainContainer.innerHTML = data.html;
        }
      } else {
        // Parsed from full HTML response
        const htmlText = await res.text();
        const parser = new DOMParser();
        const doc = parser.parseFromString(htmlText, 'text/html');
        if (doc.title) document.title = doc.title;
        const newContent = doc.getElementById('spa-main-content');
        if (mainContainer && newContent) {
          mainContainer.innerHTML = newContent.innerHTML;
        } else {
          window.location.href = url;
          return;
        }
      }

      this.updateActiveNav(url);

      if (shouldScroll) {
        window.scrollTo({ top: 0, behavior: 'smooth' });
      }

      // Re-apply language translations to new elements
      const currentLang = localStorage.getItem('wooinhome_lang') || 'zh-TW';
      if (typeof setLanguage === 'function') {
        setLanguage(currentLang);
      }

      // Dispatch event for components to rebind
      window.dispatchEvent(new Event('contentLoaded'));

    } catch (err) {
      console.error('SPA load error, navigating naturally:', err);
      window.location.href = url;
    } finally {
      if (mainContainer) {
        mainContainer.classList.remove('page-transition-exit');
        mainContainer.classList.add('page-transition-enter');
        setTimeout(() => mainContainer.classList.remove('page-transition-enter'), 300);
      }
      this.hideProgressBar();
      this.isNavigating = false;
      // Close mobile menu if open
      const mobileMenu = document.getElementById('mobile-nav-drawer');
      if (mobileMenu && mobileMenu.classList.contains('active')) {
        mobileMenu.classList.remove('active');
        document.body.classList.remove('menu-open');
      }
    }
  },

  updateActiveNav(path) {
    document.querySelectorAll('.nav-link').forEach(link => {
      const href = link.getAttribute('href');
      if (href === path || (path === '/' && href === '/') || (href !== '/' && path.startsWith(href))) {
        link.classList.add('active');
      } else {
        link.classList.remove('active');
      }
    });
  },

  showProgressBar() {
    let bar = document.getElementById('spa-progress-bar');
    if (!bar) {
      bar = document.createElement('div');
      bar.id = 'spa-progress-bar';
      document.body.appendChild(bar);
    }
    bar.style.width = '35%';
    bar.style.opacity = '1';
    setTimeout(() => { if (this.isNavigating) bar.style.width = '75%'; }, 150);
  },

  hideProgressBar() {
    const bar = document.getElementById('spa-progress-bar');
    if (bar) {
      bar.style.width = '100%';
      setTimeout(() => {
        bar.style.opacity = '0';
        setTimeout(() => { bar.style.width = '0%'; }, 200);
      }, 150);
    }
  }
};

document.addEventListener('DOMContentLoaded', () => SPARouter.init());
