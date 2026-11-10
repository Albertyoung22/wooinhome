// Global Toast Notification Helper
function showToast(message, type = 'info') {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = `toast-item toast-${type}`;
  toast.innerHTML = `
    <div class="toast-content">${message}</div>
    <button class="toast-close" onclick="this.parentElement.remove()">✕</button>
  `;
  container.appendChild(toast);

  setTimeout(() => {
    toast.classList.add('show');
  }, 10);

  setTimeout(() => {
    toast.classList.remove('show');
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

// UI Initializer
function initUI() {
  // Sticky Navbar
  const header = document.querySelector('.site-header');
  window.addEventListener('scroll', () => {
    if (window.scrollY > 40) {
      header?.classList.add('scrolled');
    } else {
      header?.classList.remove('scrolled');
    }
  });

  // Mobile Menu Drawer
  const hamburger = document.getElementById('mobile-menu-btn');
  const mobileDrawer = document.getElementById('mobile-nav-drawer');
  const mobileClose = document.getElementById('mobile-nav-close');
  const mobileOverlay = document.getElementById('mobile-nav-overlay');

  function openMobileMenu() {
    mobileDrawer?.classList.add('active');
    mobileOverlay?.classList.add('active');
    document.body.classList.add('menu-open');
  }

  function closeMobileMenu() {
    mobileDrawer?.classList.remove('active');
    mobileOverlay?.classList.remove('active');
    document.body.classList.remove('menu-open');
  }

  if (hamburger) hamburger.addEventListener('click', openMobileMenu);
  if (mobileClose) mobileClose.addEventListener('click', closeMobileMenu);
  if (mobileOverlay) mobileOverlay.addEventListener('click', closeMobileMenu);

  // Close menu when clicking nav links in mobile drawer
  mobileDrawer?.querySelectorAll('.nav-link').forEach(link => {
    link.addEventListener('click', closeMobileMenu);
  });

  // Portfolio Filters
  bindPortfolioFilters();

  // Contact / RFQ Form
  bindContactForm();

  // FAQ Accordion
  bindFaqAccordion();
}

function bindPortfolioFilters() {
  const filterBtns = document.querySelectorAll('.filter-tab-btn');
  const cards = document.querySelectorAll('.portfolio-card');

  filterBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      filterBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');

      const filter = btn.getAttribute('data-filter');
      cards.forEach(card => {
        const cat = card.getAttribute('data-category');
        if (filter === 'all' || cat === filter) {
          card.style.display = 'block';
          card.classList.add('fade-in');
        } else {
          card.style.display = 'none';
        }
      });
    });
  });
}

function bindFaqAccordion() {
  document.querySelectorAll('.faq-item-header').forEach(header => {
    header.addEventListener('click', () => {
      const parent = header.parentElement;
      const isOpen = parent.classList.contains('active');
      document.querySelectorAll('.faq-item').forEach(item => item.classList.remove('active'));
      if (!isOpen) {
        parent.classList.add('active');
      }
    });
  });
}

function bindContactForm() {
  const form = document.getElementById('rfq-main-form');
  if (!form) return;

  // Pre-fill RFQ Cart items into hidden field or summary
  const itemsContainer = document.getElementById('rfq-form-items-summary');
  if (itemsContainer) {
    const items = typeof RFQCart !== 'undefined' ? RFQCart.getItems() : [];
    if (items.length > 0) {
      let html = '<div class="rfq-attached-list-box"><div class="rfq-attached-header">📌 已隨附您的詢價委託項目（' + items.length + '項）：</div><ul>';
      items.forEach(it => {
        html += `<li><strong>${it.title}</strong> - ${it.price}</li>`;
      });
      html += '</ul></div>';
      itemsContainer.innerHTML = html;
    } else {
      itemsContainer.innerHTML = '<div class="rfq-attached-empty">💡 您尚未在詢價清單加入特定試算項目，將由專人直接為您的物業進行專屬評估。</div>';
    }
  }

  form.addEventListener('submit', async (e) => {
    e.preventDefault();

    const submitBtn = form.querySelector('button[type="submit"]');
    const origBtnText = submitBtn ? submitBtn.innerHTML : '送出';
    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.innerHTML = '⏳ 正在提交資料中...';
    }

    try {
      const formData = new FormData(form);

      // Append RFQ Cart Items JSON
      if (typeof RFQCart !== 'undefined') {
        const items = RFQCart.getItems();
        formData.append('cart_items', JSON.stringify(items));
      }

      const res = await fetch('/api/rfq/submit', {
        method: 'POST',
        body: formData
      });

      const data = await res.json();
      if (!res.ok || data.status !== 'success') {
        throw new Error(data.message || '提交失敗，請檢查輸入內容');
      }

      // Success
      if (typeof RFQCart !== 'undefined') {
        RFQCart.clear();
      }

      // Show Success Modal or notification
      showToast(`🎉 詢價單已成功送出！單號：#${data.rfq_number}`, 'success');

      const modalSuccess = document.getElementById('rfq-success-modal');
      if (modalSuccess) {
        document.getElementById('success-rfq-no').textContent = data.rfq_number;
        modalSuccess.classList.add('active');
      } else {
        alert(`感謝您的委託！我們已收到您的詢價申請（單號 #${data.rfq_number}），專業管家將儘速與您聯繫！`);
        window.location.href = '/';
      }

    } catch (err) {
      console.error(err);
      showToast(err.message || '連線錯誤，請稍後重試', 'error');
    } finally {
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.innerHTML = origBtnText;
      }
    }
  });
}

document.addEventListener('DOMContentLoaded', initUI);
window.addEventListener('contentLoaded', initUI);

