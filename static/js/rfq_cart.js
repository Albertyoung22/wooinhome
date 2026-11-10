const RFQCart = {
  STORAGE_KEY: 'wooinhome_rfq_cart',

  getItems() {
    try {
      return JSON.parse(localStorage.getItem(this.STORAGE_KEY)) || [];
    } catch (e) {
      return [];
    }
  },

  saveItems(items) {
    localStorage.setItem(this.STORAGE_KEY, JSON.stringify(items));
    this.updateBadges();
    this.renderDrawer();
  },

  addItem(item) {
    const items = this.getItems();
    // Default structure: { code, title, specs, price, timestamp }
    const newItem = {
      id: Date.now() + Math.random().toString(36).substring(2, 7),
      code: item.code || 'custom',
      title: item.title || '委託託管服務',
      specs: item.specs || {},
      price: item.price || '專人依屋況估價',
      timestamp: new Date().toISOString()
    };
    items.push(newItem);
    this.saveItems(items);
    showToast(t('toast_added', '已加入詢價清單！'));
  },

  removeItem(index) {
    const items = this.getItems();
    if (index >= 0 && index < items.length) {
      items.splice(index, 1);
      this.saveItems(items);
      showToast(t('toast_removed', '已從詢價清單移除'));
    }
  },

  clear() {
    localStorage.removeItem(this.STORAGE_KEY);
    this.updateBadges();
    this.renderDrawer();
  },

  updateBadges() {
    const items = this.getItems();
    const count = items.length;
    document.querySelectorAll('.rfq-badge-count').forEach(el => {
      el.textContent = count;
      if (count > 0) {
        el.style.display = 'inline-flex';
      } else {
        el.style.display = 'none';
      }
    });
  },

  renderDrawer() {
    const drawerList = document.getElementById('rfq-drawer-list');
    if (!drawerList) return;

    const items = this.getItems();
    if (items.length === 0) {
      drawerList.innerHTML = `
        <div class="empty-state">
          <div class="empty-icon">📂</div>
          <p data-i18n="rfq_drawer_empty">${t('rfq_drawer_empty', '目前尚未加入任何詢價項目。請瀏覽服務方案或使用試算機加入！')}</p>
        </div>
      `;
      return;
    }

    let html = '';
    items.forEach((item, idx) => {
      let specsHtml = '';
      if (item.specs && typeof item.specs === 'object') {
        const specPairs = Object.entries(item.specs).map(([k, v]) => `<span>${k}: <strong>${v}</strong></span>`);
        specsHtml = `<div class="rfq-item-specs">${specPairs.join(' ｜ ')}</div>`;
      }

      html += `
        <div class="rfq-item-card">
          <div class="rfq-item-main">
            <h4 class="rfq-item-title">${item.title}</h4>
            ${specsHtml}
            <div class="rfq-item-price">${item.price}</div>
          </div>
          <button class="rfq-item-remove" onclick="RFQCart.removeItem(${idx})" title="刪除此項目">✕</button>
        </div>
      `;
    });

    drawerList.innerHTML = html;
  },

  openDrawer() {
    const drawer = document.getElementById('rfq-drawer');
    const overlay = document.getElementById('rfq-drawer-overlay');
    if (drawer && overlay) {
      this.renderDrawer();
      drawer.classList.add('active');
      overlay.classList.add('active');
      document.body.classList.add('modal-open');
    }
  },

  closeDrawer() {
    const drawer = document.getElementById('rfq-drawer');
    const overlay = document.getElementById('rfq-drawer-overlay');
    if (drawer && overlay) {
      drawer.classList.remove('active');
      overlay.classList.remove('active');
      document.body.classList.remove('modal-open');
    }
  }
};

document.addEventListener('DOMContentLoaded', () => {
  RFQCart.updateBadges();

  // Bind trigger buttons
  document.querySelectorAll('.btn-open-rfq-drawer').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      RFQCart.openDrawer();
    });
  });

  const closeBtn = document.getElementById('btn-close-rfq-drawer');
  if (closeBtn) {
    closeBtn.addEventListener('click', () => RFQCart.closeDrawer());
  }

  const overlay = document.getElementById('rfq-drawer-overlay');
  if (overlay) {
    overlay.addEventListener('click', () => RFQCart.closeDrawer());
  }
});

