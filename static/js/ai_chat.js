const AIChat = {
  isOpen: false,

  init() {
    const trigger = document.getElementById('ai-chat-trigger');
    const modal = document.getElementById('ai-chat-modal');
    const closeBtn = document.getElementById('ai-chat-close');
    const form = document.getElementById('ai-chat-form');
    const input = document.getElementById('ai-chat-input');
    const messages = document.getElementById('ai-chat-messages');

    if (!trigger || !modal) return;

    trigger.addEventListener('click', () => this.toggleModal());
    if (closeBtn) closeBtn.addEventListener('click', () => this.toggleModal(false));

    // Quick prompt pills
    document.querySelectorAll('.ai-prompt-pill').forEach(pill => {
      pill.addEventListener('click', () => {
        const query = pill.getAttribute('data-query');
        if (query) {
          if (input) input.value = query;
          this.sendMessage(query);
        }
      });
    });

    if (form) {
      form.addEventListener('submit', (e) => {
        e.preventDefault();
        const text = input.value.trim();
        if (text) {
          this.sendMessage(text);
          input.value = '';
        }
      });
    }
  },

  toggleModal(forceState) {
    const modal = document.getElementById('ai-chat-modal');
    if (!modal) return;
    this.isOpen = forceState !== undefined ? forceState : !this.isOpen;
    if (this.isOpen) {
      modal.classList.add('active');
      const input = document.getElementById('ai-chat-input');
      if (input) setTimeout(() => input.focus(), 200);
    } else {
      modal.classList.remove('active');
    }
  },

  async sendMessage(query) {
    const messages = document.getElementById('ai-chat-messages');
    if (!messages) return;

    // Append User Message
    const userMsg = document.createElement('div');
    userMsg.className = 'ai-msg user';
    userMsg.innerHTML = `<div class="msg-bubble">${this.escapeHtml(query)}</div>`;
    messages.appendChild(userMsg);
    messages.scrollTop = messages.scrollHeight;

    // Append Typing indicator
    const typingMsg = document.createElement('div');
    typingMsg.className = 'ai-msg bot typing';
    typingMsg.innerHTML = `
      <div class="msg-bubble">
        <span class="dot"></span><span class="dot"></span><span class="dot"></span>
      </div>
    `;
    messages.appendChild(typingMsg);
    messages.scrollTop = messages.scrollHeight;

    try {
      const lang = localStorage.getItem('wooinhome_lang') || 'zh-TW';
      const res = await fetch('/api/ai/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, lang })
      });
      const data = await res.json();
      typingMsg.remove();

      const botMsg = document.createElement('div');
      botMsg.className = 'ai-msg bot';
      // Format linebreaks & markdown bold
      const formatted = this.formatBotReply(data.reply || '謝謝您的提問，專人將為您進一步說明！');
      botMsg.innerHTML = `
        <div class="msg-avatar">窩</div>
        <div class="msg-content">
          <div class="msg-bubble">${formatted}</div>
          <div class="msg-actions">
            <button class="btn-chat-action" onclick="RFQCart.openDrawer()">📑 查看詢價清單</button>
            <a href="/contact" class="btn-chat-action accent" data-spa>📞 預約專人到府勘查</a>
          </div>
        </div>
      `;
      messages.appendChild(botMsg);
      messages.scrollTop = messages.scrollHeight;
    } catch (err) {
      typingMsg.remove();
      const errorMsg = document.createElement('div');
      errorMsg.className = 'ai-msg bot';
      errorMsg.innerHTML = `<div class="msg-bubble error">連線異常，請直接致電 (06) 289-4168 或加 LINE: @wooinhome 專人洽詢。</div>`;
      messages.appendChild(errorMsg);
      messages.scrollTop = messages.scrollHeight;
    }
  },

  escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  },

  formatBotReply(text) {
    let clean = this.escapeHtml(text);
    // Replace **bold**
    clean = clean.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    // Replace \n with <br>
    clean = clean.replace(/\n/g, '<br>');
    return clean;
  }
};

document.addEventListener('DOMContentLoaded', () => AIChat.init());
