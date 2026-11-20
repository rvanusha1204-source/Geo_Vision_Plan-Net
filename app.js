/**
 * Geo Vision Plan-Net - Main Application Controller
 * Connects frontend UI/UX directly to Python ML model backend API.
 */

class AppController {
  constructor() {
    this.selectedDistrict = null;
    this.compareDistrict = null;
    this.activeTab = 'overview';
    this.currentTheme = 'light';
    this.trendChart = null;
    this.analyticsChart = null;
  }

  async init() {
    await this.populateDistrictSelectors();
    this.setupEventListeners();

    // Default to first real district from backend
    if (this.allDistricts && this.allDistricts.length > 0) {
      await this.selectDistrict(this.allDistricts[0].slug);
    }
  }

  async populateDistrictSelectors() {
    let districts = [];

    try {
      const res = await fetch('/api/districts');
      if (res.ok) {
        districts = await res.json();
      }
    } catch (e) {
      console.warn('Backend API fetch failed, fallback to offline data.');
    }

    if (!districts || districts.length === 0) {
      districts = getAllDistricts();
    }

    this.allDistricts = districts;

    const mainSelect = document.getElementById('district-select');
    const compareSelect = document.getElementById('compare-district-select');

    if (mainSelect) {
      mainSelect.innerHTML = districts.map(d => 
        `<option value="${d.slug}">${d.displayName} (${d.state})</option>`
      ).join('');
    }

    if (compareSelect) {
      compareSelect.innerHTML = districts.map(d => 
        `<option value="${d.slug}">${d.displayName} (${d.state})</option>`
      ).join('');
      if (districts.length > 1) {
        compareSelect.value = districts[1].slug;
        this.compareDistrict = districts[1];
      }
    }
  }

  setupEventListeners() {
    const mainSelect = document.getElementById('district-select');
    if (mainSelect) {
      mainSelect.addEventListener('change', (e) => this.selectDistrict(e.target.value));
    }

    const tabs = document.querySelectorAll('.tab-btn, .nav-item');
    tabs.forEach(tab => {
      tab.addEventListener('click', () => {
        const targetTab = tab.getAttribute('data-tab');
        if (targetTab) this.switchTab(targetTab);
      });
    });

    const themeBtn = document.getElementById('theme-toggle-btn');
    if (themeBtn) {
      themeBtn.addEventListener('click', () => this.toggleTheme());
    }

    const micBtn = document.getElementById('voice-mic-btn');
    if (micBtn) {
      micBtn.addEventListener('click', () => {
        if (window.voiceAssistant) window.voiceAssistant.toggleListening();
      });
    }

    const pdfBtn = document.getElementById('download-pdf-btn');
    if (pdfBtn) {
      pdfBtn.addEventListener('click', () => this.downloadPDF());
    }

    const compareSelect = document.getElementById('compare-district-select');
    if (compareSelect) {
      compareSelect.addEventListener('change', async (e) => {
        await this.loadCompareDistrict(e.target.value);
      });
    }

    const langSelect = document.getElementById('voice-lang-select');
    if (langSelect) {
      langSelect.addEventListener('change', (e) => {
        if (window.voiceAssistant) window.voiceAssistant.setLanguage(e.target.value);
      });
    }

    const sendChatBtn = document.getElementById('send-chat-btn');
    const chatInput = document.getElementById('chat-input-text');
    if (sendChatBtn && chatInput) {
      const handleChatSend = () => {
        const txt = chatInput.value.trim();
        if (txt) {
          if (window.voiceAssistant) {
            window.voiceAssistant.addChatMessage('user', txt);
            window.voiceAssistant.processVoiceCommand(txt);
          }
          chatInput.value = '';
        }
      };
      sendChatBtn.addEventListener('click', handleChatSend);
      chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') handleChatSend();
      });
    }
  }

  async selectDistrict(slug) {
    let detail = null;

    try {
      const res = await fetch(`/api/district/${slug}`);
      if (res.ok) {
        detail = await res.json();
      }
    } catch (e) {
      console.warn('Could not fetch district detail from API');
    }

    if (!detail) {
      detail = getDistrictBySlug(slug);
    }

    this.selectedDistrict = detail;

    const mainSelect = document.getElementById('district-select');
    if (mainSelect) mainSelect.value = slug;

    this.updateUI();

    if (window.mapRenderer) {
      window.mapRenderer.loadDistrictData(this.selectedDistrict);
    }

    if (window.voiceAssistant && window.voiceAssistant.currentLang) {
      const reportMsg = window.voiceAssistant.generateMultilingualReport(this.selectedDistrict, window.voiceAssistant.currentLang);
      window.voiceAssistant.addChatMessage('assistant', reportMsg);
      window.voiceAssistant.speak(reportMsg);
    }
  }

  async loadCompareDistrict(slug) {
    try {
      const res = await fetch(`/api/district/${slug}`);
      if (res.ok) {
        this.compareDistrict = await res.json();
        this.renderComparisonView();
      }
    } catch (e) {}
  }

  switchTab(tabName) {
    this.activeTab = tabName;

    document.querySelectorAll('.tab-btn, .nav-item').forEach(btn => {
      if (btn.getAttribute('data-tab') === tabName) {
        btn.classList.add('active');
      } else {
        btn.classList.remove('active');
      }
    });

    document.querySelectorAll('.tab-content').forEach(view => {
      if (view.id === `tab-${tabName}`) {
        view.classList.add('active');
      } else {
        view.classList.remove('active');
      }
    });

    if (tabName === 'analytics') {
      this.renderAnalyticsChart();
    } else if (tabName === 'map' && window.mapRenderer) {
      window.mapRenderer.resize();
    }
  }

  toggleTheme() {
    this.currentTheme = this.currentTheme === 'dark' ? 'light' : 'dark';
    document.body.setAttribute('data-theme', this.currentTheme);
    const themeBtn = document.getElementById('theme-toggle-btn');
    if (themeBtn) {
      themeBtn.innerHTML = this.currentTheme === 'dark' ? '🌙 Dark' : '☀️ Light';
    }

    if (window.mapRenderer) {
      window.mapRenderer.setTileStyle(this.currentTheme === 'dark' ? 'dark' : 'light');
    }
  }

  formatNum(num) {
    if (num === undefined || num === null) return '0';
    return Number(num).toLocaleString(undefined, { maximumFractionDigits: 1 });
  }

  /** Creates (once) and updates a small "Last updated" badge next to the
   *  district title. Built dynamically in JS so no index.html edit is
   *  needed - it just inserts itself right after #district-title. */
  renderLastUpdatedBadge(lastUpdatedIso) {
    const titleEl = document.getElementById('district-title');
    if (!titleEl) return;

    let badge = document.getElementById('last-updated-badge');
    if (!badge) {
      badge = document.createElement('span');
      badge.id = 'last-updated-badge';
      badge.style.cssText = 'display:inline-block;margin-left:10px;padding:2px 10px;' +
        'border-radius:999px;font-size:0.75em;font-weight:600;vertical-align:middle;' +
        'background:rgba(16,185,129,0.15);color:#10b981;';
      titleEl.insertAdjacentElement('afterend', badge);
    }

    if (!lastUpdatedIso) {
      badge.textContent = 'Data freshness unknown (run build_cache.py)';
      badge.style.background = 'rgba(148,163,184,0.2)';
      badge.style.color = '#64748b';
      return;
    }

    const updatedDate = new Date(lastUpdatedIso);
    const daysAgo = Math.floor((Date.now() - updatedDate.getTime()) / (1000 * 60 * 60 * 24));
    const dateLabel = updatedDate.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' });

    badge.textContent = daysAgo <= 0 ? `Updated today (${dateLabel})` : `Updated ${daysAgo}d ago (${dateLabel})`;

    // Visually flag stale data - if the refresh scheduler has silently
    // stopped running, users should be able to tell at a glance.
    if (daysAgo > 14) {
      badge.style.background = 'rgba(239,68,68,0.15)';
      badge.style.color = '#ef4444';
    } else {
      badge.style.background = 'rgba(16,185,129,0.15)';
      badge.style.color = '#10b981';
    }
  }

  updateUI() {
    const d = this.selectedDistrict;
    if (!d || !d.summary) return;

    const s = d.summary;

    document.getElementById('district-title').textContent = `${d.displayName} (${d.state})`;
    this.renderLastUpdatedBadge(d.lastUpdated);
    document.getElementById('study-period-text').textContent = `Study Period: ${s.studyPeriod || '2017 - 2025'}`;
    document.getElementById('exec-summary-text').textContent = d.executiveSummary || "Model analysis complete for this region.";

    document.getElementById('kpi-loss').textContent = `${this.formatNum(s.totalVegLossHa)} ha`;
    document.getElementById('kpi-gain').textContent = `${this.formatNum(s.totalVegGainHa)} ha`;
    document.getElementById('kpi-encroachment').textContent = `${this.formatNum(s.protectedAreaEncroachmentHa)} ha`;
    document.getElementById('kpi-buffer').textContent = `${this.formatNum(s.bufferZoneViolationHa)} ha`;
    document.getElementById('kpi-severe').textContent = `${this.formatNum(s.severeLossHa)} ha`;
    document.getElementById('kpi-total').textContent = `${this.formatNum(s.totalFlaggedViolationHa)} ha`;
    document.getElementById('kpi-risk').textContent = `${s.riskScore}/100`;

    this.renderTrendChart();
    this.renderComparisonView();
  }

  renderTrendChart() {
    const canvas = document.getElementById('trend-chart-canvas');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    const trend = this.selectedDistrict?.trend || [];

    if (this.trendChart) {
      this.trendChart.destroy();
    }

    const labels = trend.length > 0 ? trend.map(t => t.period) : ['2017-2019', '2019-2021', '2021-2023', '2023-2026'];
    const lossData = trend.length > 0 ? trend.map(t => t.lossHa) : [30000, 11500, 51300, 55000];
    const gainData = trend.length > 0 ? trend.map(t => t.gainHa) : [50500, 104900, 20000, 28400];

    this.trendChart = new Chart(ctx, {
      type: 'line',
      data: {
        labels: labels,
        datasets: [
          {
            label: 'Vegetation Loss (ha)',
            data: lossData,
            borderColor: '#ef4444',
            backgroundColor: 'rgba(239, 68, 68, 0.15)',
            fill: true,
            tension: 0.3
          },
          {
            label: 'Vegetation Gain (ha)',
            data: gainData,
            borderColor: '#10b981',
            backgroundColor: 'rgba(16, 185, 129, 0.15)',
            fill: true,
            tension: 0.3
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { labels: { color: this.currentTheme === 'dark' ? '#f0fdf4' : '#064e3b' } }
        }
      }
    });
  }

  renderAnalyticsChart() {
    const canvas = document.getElementById('analytics-chart-canvas');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    const trend = this.selectedDistrict?.trend || [];

    if (this.analyticsChart) {
      this.analyticsChart.destroy();
    }

    const labels = trend.length > 0 ? trend.map(t => t.period) : ['2017-2019', '2019-2021', '2021-2023', '2023-2026'];
    const violationsData = trend.length > 0 ? trend.map(t => t.violationsHa) : [4400, 2800, 5300, 7100];

    this.analyticsChart = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [
          {
            label: 'Flagged Violations (ha)',
            data: violationsData,
            backgroundColor: 'rgba(249, 115, 22, 0.85)',
            borderRadius: 8
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { labels: { color: this.currentTheme === 'dark' ? '#f0fdf4' : '#064e3b' } }
        }
      }
    });
  }

  renderComparisonView() {
    const container = document.getElementById('comparison-cards-container');
    if (!container) return;

    const d1 = this.selectedDistrict;
    const d2 = this.compareDistrict || d1;

    if (!d1 || !d1.summary) return;

    const s1 = d1.summary;
    const s2 = d2.summary || s1;

    container.innerHTML = `
      <div class="compare-card">
        <h3>${d1.displayName} (${d1.state})</h3>
        <p><strong>Risk Score:</strong> ${s1.riskScore}/100</p>
        <p><strong>Vegetation Loss:</strong> ${this.formatNum(s1.totalVegLossHa)} ha</p>
        <p><strong>Vegetation Gain:</strong> ${this.formatNum(s1.totalVegGainHa)} ha</p>
        <p><strong>Protected Encroachment:</strong> ${this.formatNum(s1.protectedAreaEncroachmentHa)} ha</p>
        <p><strong>Total Flagged Violations:</strong> ${this.formatNum(s1.totalFlaggedViolationHa)} ha</p>
      </div>
      <div class="compare-card">
        <h3>${d2.displayName || d1.displayName} (${d2.state || d1.state})</h3>
        <p><strong>Risk Score:</strong> ${s2.riskScore}/100</p>
        <p><strong>Vegetation Loss:</strong> ${this.formatNum(s2.totalVegLossHa)} ha</p>
        <p><strong>Vegetation Gain:</strong> ${this.formatNum(s2.totalVegGainHa)} ha</p>
        <p><strong>Protected Encroachment:</strong> ${this.formatNum(s2.protectedAreaEncroachmentHa)} ha</p>
        <p><strong>Total Flagged Violations:</strong> ${this.formatNum(s2.totalFlaggedViolationHa)} ha</p>
      </div>
    `;
  }

  downloadPDF() {
    if (typeof generateDistrictPDFReport === 'function') {
      generateDistrictPDFReport(this.selectedDistrict);
    }
  }
}

document.addEventListener('DOMContentLoaded', () => {
  window.appState = new AppController();
  window.appState.init();
});
