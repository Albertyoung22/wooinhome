const TTSPlayer = {
  audio: new Audio(),
  currentPlayingBtn: null,
  isPlaying: false,

  init() {
    this.audio.addEventListener('ended', () => {
      this.resetState();
    });

    this.audio.addEventListener('error', (e) => {
      console.error('Audio error', e);
      this.resetState();
      showToast('語音播放失敗，請稍後再試', 'error');
    });

    this.bindButtons();
  },

  bindButtons() {
    document.querySelectorAll('.btn-tts-tour').forEach(btn => {
      btn.removeEventListener('click', this.handleBtnClick);
      btn.addEventListener('click', (e) => this.handleBtnClick(e, btn));
    });
  },

  resetState() {
    this.isPlaying = false;
    if (this.currentPlayingBtn) {
      this.currentPlayingBtn.classList.remove('playing', 'loading');
      const icon = this.currentPlayingBtn.querySelector('.tts-icon');
      if (icon) icon.textContent = '🔊';
      const label = this.currentPlayingBtn.querySelector('.tts-label');
      if (label) label.textContent = t('btn_audio_tour', '專人語音導覽');
    }
    this.currentPlayingBtn = null;
  },

  async handleBtnClick(e, btn) {
    e.preventDefault();

    // If clicking same active button, toggle pause
    if (this.currentPlayingBtn === btn && this.isPlaying) {
      this.audio.pause();
      this.isPlaying = false;
      btn.classList.remove('playing');
      const icon = btn.querySelector('.tts-icon');
      if (icon) icon.textContent = '▶️';
      showToast(t('audio_paused', '朗讀已暫停'));
      return;
    } else if (this.currentPlayingBtn === btn && !this.isPlaying) {
      this.audio.play();
      this.isPlaying = true;
      btn.classList.add('playing');
      const icon = btn.querySelector('.tts-icon');
      if (icon) icon.textContent = '⏸️';
      showToast(t('audio_playing', '正在朗讀導覽中...'));
      return;
    }

    // Stop previous
    if (this.isPlaying) {
      this.audio.pause();
      this.resetState();
    }

    const text = btn.getAttribute('data-tts-text') || document.querySelector(btn.getAttribute('data-tts-target'))?.innerText || '';
    if (!text.trim()) {
      showToast('暫無朗讀文字', 'warning');
      return;
    }

    this.currentPlayingBtn = btn;
    btn.classList.add('loading');
    const icon = btn.querySelector('.tts-icon');
    if (icon) icon.textContent = '⏳';

    try {
      const lang = localStorage.getItem('wooinhome_lang') || 'zh-TW';
      const res = await fetch('/api/tts/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: text.trim(), lang })
      });
      const data = await res.json();

      if (!res.ok || !data.url) {
        throw new Error(data.error || 'TTS generation failed');
      }

      btn.classList.remove('loading');
      btn.classList.add('playing');
      if (icon) icon.textContent = '⏸️';
      const label = btn.querySelector('.tts-label');
      if (label) label.textContent = '暫停朗讀';

      this.audio.src = data.url;
      await this.audio.play();
      this.isPlaying = true;
      showToast(t('audio_playing', '正在朗讀導覽中...'));
    } catch (err) {
      console.error(err);
      this.resetState();
      showToast('語音產生或連線異常，請稍候重試', 'error');
    }
  }
};

document.addEventListener('DOMContentLoaded', () => TTSPlayer.init());
window.addEventListener('contentLoaded', () => TTSPlayer.bindButtons());
