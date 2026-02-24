const CHART_CONTAINER_ID = 'chart-container';
const API_URL = '';

let settings = { gemini_api_key: '', daily_api_limit: 50, api_calls_today: 0 };
let chart;
let candlestickSeries;
let jwtToken = localStorage.getItem('jwt');
let totpCode = localStorage.getItem('totp_code');
let activeWatchlistId = null;
let searchTimeout = null;
let selectedSearchIndex = -1;
let isSignupMode = false;
let loginUsername = null; // Store username temporarily during 2FA login

document.addEventListener('DOMContentLoaded', () => {
    initChart();
    setupEventListeners();
    loadMarketOverview();
    updateUserUI();
    IdeaManager.init();
    if (jwtToken) {
        fetchWatchlists();
    }
});

// --- Auth Helpers ---
function getHeaders() {
    const headers = { 'Content-Type': 'application/json' };
    if (jwtToken) headers['Authorization'] = `Bearer ${jwtToken}`;
    if (totpCode) headers['X-TOTP-Code'] = totpCode;
    return headers;
}

function handleAuthError() {
    const code = prompt("Gesperrt! Bitte Master TOTP Code eingeben:");
    if (code) {
        localStorage.setItem('totp_code', code);
        totpCode = code;
        alert("Master Code gespeichert. Bitte Aktion wiederholen.");
        return true;
    }
    return false;
}
function initChart() {
    const container = document.getElementById(CHART_CONTAINER_ID);
    chart = LightweightCharts.createChart(container, {
        layout: { background: { color: '#0d1117' }, textColor: '#8b949e' },
        grid: { vertLines: { color: '#161b2233' }, horzLines: { color: '#161b2233' } },
        crosshair: { mode: LightweightCharts.CrosshairMode.Normal },
        rightPriceScale: { borderColor: '#30363d' },
        timeScale: { borderColor: '#30363d' },
        width: container.clientWidth,
        height: container.clientHeight,
    });
    candlestickSeries = chart.addCandlestickSeries({
        upColor: '#3fb950', downColor: '#f85149',
        borderUpColor: '#3fb950', borderDownColor: '#f85149',
        wickUpColor: '#3fb950', wickDownColor: '#f85149',
    });
    window.addEventListener('resize', () => {
        chart.applyOptions({ width: container.clientWidth, height: container.clientHeight });
    });
}

// --- Market Overview (Public, no auth) ---
async function loadMarketOverview() {
    try {
        const res = await fetch(`${API_URL}/market-overview`);
        const data = await res.json();
        renderTickerBar(data.indices);
        renderPopularStocks(data.popular);
        // Load chart for first popular stock
        if (data.popular.length > 0) {
            loadChartForSymbol(data.popular[0].symbol);
        }
    } catch (e) {
        console.error('Market overview error:', e);
        document.getElementById('tickerScroll').innerHTML = '<span class="loading-text">Marktdaten nicht verfügbar</span>';
    }
}

function renderTickerBar(indices) {
    const scroll = document.getElementById('tickerScroll');
    if (!indices || indices.length === 0) {
        scroll.innerHTML = '<span class="loading-text">Keine Indexdaten</span>';
        return;
    }
    scroll.innerHTML = indices.map(idx => {
        const arrow = idx.change_pct >= 0 ? '▲' : '▼';
        const cls = idx.change_pct >= 0 ? 'positive' : 'negative';
        return `<span class="ticker-item" onclick="loadChartForSymbol('${idx.symbol}')">
            <span class="ticker-name">${idx.name}</span>
            <span class="ticker-price">${idx.price.toLocaleString('de-DE', { minimumFractionDigits: 2 })}</span>
            <span class="ticker-change ${cls}">${arrow} ${Math.abs(idx.change_pct).toFixed(2)}%</span>
        </span>`;
    }).join('');
}

function renderPopularStocks(stocks) {
    const container = document.getElementById('popularStocks');
    if (!stocks || stocks.length === 0) {
        container.innerHTML = '<p class="empty-state">Keine Daten verfügbar.</p>';
        return;
    }
    container.innerHTML = stocks.map(s => {
        const cls = s.change_pct >= 0 ? 'positive' : 'negative';
        const arrow = s.change_pct >= 0 ? '▲' : '▼';
        return `<div class="stock-card" onclick="loadChartForSymbol('${s.symbol}')">
            <div class="stock-card-header">
                <span class="stock-symbol">${s.symbol.replace('^', '')}</span>
                <span class="stock-change ${cls}">${arrow} ${Math.abs(s.change_pct).toFixed(2)}%</span>
            </div>
            <div class="stock-name">${s.name}</div>
            <div class="stock-price">${s.currency === 'EUR' ? '€' : '$'}${s.price.toLocaleString('de-DE', { minimumFractionDigits: 2 })}</div>
        </div>`;
    }).join('');
}

async function loadChartForSymbol(symbol) {
    try {
        const res = await fetch(`${API_URL}/chart-data?symbol=${encodeURIComponent(symbol)}`);
        if (res.ok) {
            const data = await res.json();
            candlestickSeries.setData(data);
            chart.timeScale().fitContent();
        }
    } catch (e) {
        console.error('Chart load error:', e);
    }
}

// --- Search (Public) ---
function setupEventListeners() {
    document.getElementById('send-btn').onclick = () => executeCommand();
    document.getElementById('command-bar').onkeypress = (e) => { if (e.key === 'Enter') executeCommand(); };

    const searchInput = document.getElementById('tickerSearch');
    searchInput.oninput = (e) => handleSearch(e.target.value);
    searchInput.onkeydown = handleSearchKey;
    document.addEventListener('click', (e) => {
        if (!e.target.closest('.search-container')) {
            hideSearchResults();
        }
    });

    document.getElementById('watchlistSelect').onchange = (e) => selectWatchlist(e.target.value);
    document.getElementById('addWatchlistBtn').onclick = addWatchlist;

    // Auth
    if (document.getElementById('login-btn')) {
        document.getElementById('login-btn').onclick = handleAuth;
    }
    if (document.getElementById('toggle-signup')) {
        document.getElementById('toggle-signup').onclick = (e) => {
            e.preventDefault();
            toggleAuthMode();
        };
    }

    // 2FA Setup in Settings
    document.getElementById('setup2FABtn').onclick = setup2FA;
    document.getElementById('verify2FABtn').onclick = verify2FA;

    // Settings
    document.getElementById('settingsBtn').onclick = showSettings;
    document.getElementById('closeSettingsBtn').onclick = () => document.getElementById('settingsModal').classList.add('hidden');
    document.getElementById('saveSettingsBtn').onclick = saveUserSettings;
    document.getElementById('logoutBtn').onclick = logout;
}

async function handleSearch(query) {
    if (searchTimeout) clearTimeout(searchTimeout);
    const resultsDiv = document.getElementById('searchResults');
    selectedSearchIndex = -1;

    if (!query || query.length < 2) {
        resultsDiv.classList.add('hidden');
        return;
    }

    searchTimeout = setTimeout(async () => {
        try {
            const useAuth = jwtToken || totpCode;
            const endpoint = useAuth ? `${API_URL}/search` : `${API_URL}/search-public`;
            const res = await fetch(`${endpoint}?query=${encodeURIComponent(query)}`, { headers: getHeaders() });
            if (res.status === 401) return handleAuthError();
            const results = await res.json();

            if (results.length === 0) {
                resultsDiv.innerHTML = '<div class="search-item no-result">Keine Ergebnisse</div>';
            } else {
                resultsDiv.innerHTML = results.map((r, i) => `
                    <div class="search-item" data-index="${i}" onclick="onSearchResultClick('${r.symbol}', '${(r.name || '').replace(/'/g, '')}', '${r.type}')">
                        <strong>${r.symbol}</strong>
                        <span class="search-item-name">${r.name || r.type}</span>
                        <span class="search-item-type">${r.type}</span>
                    </div>
                `).join('');
            }
            resultsDiv.classList.remove('hidden');
        } catch (e) { console.error('Search error:', e); }
    }, 300);
}

function handleSearchKey(e) {
    const resultsDiv = document.getElementById('searchResults');
    const items = resultsDiv.querySelectorAll('.search-item:not(.no-result)');

    if (resultsDiv.classList.contains('hidden') && e.key !== 'Enter') {
        if (e.target.value.length >= 2) handleSearch(e.target.value);
        return;
    }

    if (e.key === 'ArrowDown') {
        e.preventDefault();
        selectedSearchIndex = Math.min(selectedSearchIndex + 1, items.length - 1);
        updateActiveSearchItem(items);
    } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        selectedSearchIndex = Math.max(selectedSearchIndex - 1, -1);
        updateActiveSearchItem(items);
    } else if (e.key === 'Enter') {
        e.preventDefault();
        if (selectedSearchIndex >= 0 && items[selectedSearchIndex]) {
            items[selectedSearchIndex].click();
        } else if (e.target.value.length >= 2) {
            // Default to first result if present
            if (items.length > 0) items[0].click();
        }
    } else if (e.key === 'Escape') {
        hideSearchResults();
    }
}

function updateActiveSearchItem(items) {
    items.forEach((item, i) => {
        if (i === selectedSearchIndex) {
            item.classList.add('active');
            item.scrollIntoView({ block: 'nearest' });
        } else {
            item.classList.remove('active');
        }
    });
}

function hideSearchResults() {
    document.getElementById('searchResults').classList.add('hidden');
    selectedSearchIndex = -1;
}

function onSearchResultClick(symbol, name, type) {
    document.getElementById('searchResults').classList.add('hidden');
    document.getElementById('tickerSearch').value = '';
    loadChartForSymbol(symbol);
    if (jwtToken && activeWatchlistId) {
        addTickerToWatchlist(symbol, name, type);
    }
}

// --- Multi-User Auth & 2FA ---
function toggleAuthMode() {
    isSignupMode = !isSignupMode;
    const title = document.getElementById('auth-title');
    const btn = document.getElementById('login-btn');
    const toggleText = document.getElementById('auth-toggle-text');

    if (isSignupMode) {
        title.innerText = '✨ Registrieren';
        btn.innerText = 'Konto erstellen';
        toggleText.innerHTML = 'Haben Sie bereits ein Konto? <a href="#" id="toggle-signup">Login</a>';
    } else {
        title.innerText = '🔐 Login';
        btn.innerText = 'Login';
        toggleText.innerHTML = 'Noch kein Konto? <a href="#" id="toggle-signup">Jetzt registrieren</a>';
    }
    // Re-bind toggle event
    document.getElementById('toggle-signup').onclick = (e) => {
        e.preventDefault();
        toggleAuthMode();
    };
}

async function handleAuth() {
    if (isSignupMode) {
        await signup();
    } else {
        await login();
    }
}

async function signup() {
    const userEl = document.getElementById('username');
    const passEl = document.getElementById('password');
    try {
        const res = await fetch(`${API_URL}/signup?username=${encodeURIComponent(userEl.value)}&password=${encodeURIComponent(passEl.value)}`, {
            method: 'POST'
        });
        const data = await res.json();
        if (res.ok) {
            alert("Konto erstellt! Bitte loggen Sie sich ein.");
            toggleAuthMode();
        } else {
            alert("Fehler: " + (data.detail || "Registrierung fehlgeschlagen"));
        }
    } catch (e) { console.error('Signup error:', e); }
}

async function login() {
    const userEl = document.getElementById('username');
    const passEl = document.getElementById('password');
    const codeEl = document.getElementById('login-2fa-code');

    // If 2FA section is visible, verify 2FA instead of regular login
    if (!document.getElementById('2fa-login-section').classList.contains('hidden')) {
        return verifyLogin2FA(loginUsername, codeEl.value);
    }

    const formData = new FormData();
    formData.append('username', userEl.value);
    formData.append('password', passEl.value);

    try {
        const res = await fetch(`${API_URL}/token`, {
            method: 'POST',
            body: formData
        });
        const data = await res.json();
        if (res.ok) {
            if (data.require_2fa) {
                loginUsername = data.username;
                document.getElementById('auth-inputs').classList.add('hidden');
                document.getElementById('2fa-login-section').classList.remove('hidden');
                document.getElementById('login-btn').innerText = 'Code verifizieren';
            } else {
                completeLogin(data.access_token);
            }
        } else {
            alert("Login fehlgeschlagen: " + (data.detail || "Falsche Daten"));
        }
    } catch (e) { console.error('Login error:', e); }
}

async function verifyLogin2FA(username, code) {
    try {
        const res = await fetch(`${API_URL}/2fa/verify?username=${encodeURIComponent(username)}&code=${encodeURIComponent(code)}`, {
            method: 'POST'
        });
        const data = await res.json();
        if (res.ok) {
            completeLogin(data.access_token);
        } else {
            alert("Fehler: " + (data.detail || "Ungültiger Code"));
        }
    } catch (e) { console.error('2FA Login error:', e); }
}

function completeLogin(token) {
    jwtToken = token;
    localStorage.setItem('jwt', jwtToken);
    document.getElementById('auth-modal').classList.add('hidden');
    fetchWatchlists();
    loadMarketOverview(); // Reload to get personalized views
}

async function showSettings() {
    const modal = document.getElementById('settingsModal');
    modal.classList.remove('hidden');

    if (!jwtToken) return;

    try {
        const res = await fetch(`${API_URL}/users/me`, { headers: getHeaders() });
        if (res.ok) {
            const user = await res.json();
            document.getElementById('geminiKey').value = user.gemini_api_key || '';
            document.getElementById('dailyLimit').value = user.daily_api_limit || 50;
            document.getElementById('apiUsageInfo').innerText = `Nutzung heute: ${user.api_calls_today} / ${user.daily_api_limit}`;

            // 2FA state
            document.getElementById('2faSection').classList.remove('hidden');
            if (user.two_fa_enabled) {
                document.getElementById('2faSetupContainer').classList.add('hidden');
                document.getElementById('2faQRContainer').classList.add('hidden');
                document.getElementById('2faEnabledState').classList.remove('hidden');
            } else {
                document.getElementById('2faSetupContainer').classList.remove('hidden');
                document.getElementById('2faEnabledState').classList.add('hidden');
            }
        }
    } catch (e) { console.error('Settings load error:', e); }
}

async function saveUserSettings() {
    const key = document.getElementById('geminiKey').value;
    const limit = document.getElementById('dailyLimit').value;
    try {
        const res = await fetch(`${API_URL}/users/me/settings?gemini_key=${encodeURIComponent(key)}&daily_limit=${limit}`, {
            method: 'POST',
            headers: getHeaders()
        });
        if (res.ok) {
            alert("Einstellungen gespeichert!");
            document.getElementById('settingsModal').classList.add('hidden');
        }
    } catch (e) { console.error('Save settings error:', e); }
}

async function setup2FA() {
    try {
        const res = await fetch(`${API_URL}/2fa/setup`, { method: 'POST', headers: getHeaders() });
        const data = await res.json();
        if (res.ok) {
            document.getElementById('2faSetupContainer').classList.add('hidden');
            document.getElementById('2faQRContainer').classList.remove('hidden');
            document.getElementById('totpSecret').innerText = data.secret;

            // Generate QR
            const qrContainer = document.getElementById('qrcode');
            qrContainer.innerHTML = '';
            new QRCode(qrContainer, {
                text: data.uri,
                width: 160,
                height: 160,
                colorDark: "#000000",
                colorLight: "#ffffff",
                correctLevel: QRCode.CorrectLevel.H
            });
        }
    } catch (e) { console.error('2FA Setup error:', e); }
}

async function verify2FA() {
    const code = document.getElementById('totpVerifyCode').value;
    const username = await getCurrentUsername(); // Helper to get username from JWT locally or from API

    try {
        const res = await fetch(`${API_URL}/2fa/verify?username=${encodeURIComponent(username)}&code=${encodeURIComponent(code)}`, {
            method: 'POST',
            headers: getHeaders()
        });
        if (res.ok) {
            alert("2FA erfolgreich aktiviert!");
            showSettings(); // Refresh UI
        } else {
            alert("Fehler: Verifizierung fehlgeschlagen");
        }
    } catch (e) { console.error('2FA Verify error:', e); }
}

async function getCurrentUsername() {
    const res = await fetch(`${API_URL}/users/me`, { headers: getHeaders() });
    const user = await res.json();
    return user.username;
}

function updateUserUI() {
    const userInfo = document.getElementById('userInfo');
    const authModal = document.getElementById('auth-modal');
    const logoutBtn = document.getElementById('logoutBtn');

    if (jwtToken) {
        getCurrentUsername().then(username => {
            userInfo.innerText = username;
            logoutBtn.classList.remove('hidden');
        }).catch(() => {
            userInfo.innerText = 'Gast';
            logoutBtn.classList.add('hidden');
        });
        authModal.classList.add('hidden');
    } else {
        userInfo.innerText = 'Gast';
        logoutBtn.classList.add('hidden');
        authModal.classList.remove('hidden');
    }
}

function logout() {
    jwtToken = null;
    localStorage.removeItem('jwt');
    // Keep totp_code (Master Key) in case they want to use it as guest
    location.reload();
}

// --- Watchlists (Auth required) ---
async function addTickerToWatchlist(symbol, name, type) {
    if (!activeWatchlistId) return;
    await fetch(`${API_URL}/watchlists/${activeWatchlistId}/tickers?symbol=${symbol}&name=${encodeURIComponent(name)}&ticker_type=${type}`, {
        method: 'POST',
        headers: getHeaders()
    });
    fetchDashboardData();
}

async function fetchWatchlists() {
    try {
        const res = await fetch(`${API_URL}/watchlists`, {
            headers: getHeaders()
        });
        if (res.status === 401) {
            if (handleAuthError()) fetchWatchlists();
            return;
        }
        const lists = await res.json();
        const select = document.getElementById('watchlistSelect');
        select.innerHTML = lists.map(l => `<option value="${l.id}">${l.name}</option>`).join('');
        if (lists.length > 0) {
            activeWatchlistId = lists[0].id;
            fetchDashboardData();
        } else {
            addWatchlist("Main");
        }
    } catch (e) { console.error('Watchlist fetch error:', e); }
}

async function addWatchlist(nameArg) {
    const name = nameArg || prompt("Name der neuen Watchlist:");
    if (!name) return;
    await fetch(`${API_URL}/watchlists?name=${encodeURIComponent(name)}`, {
        method: 'POST',
        headers: getHeaders()
    });
    fetchWatchlists();
}

function selectWatchlist(id) {
    activeWatchlistId = id;
    fetchDashboardData();
}



// --- Dashboard Data ---
async function fetchDashboardData() {
    if (!activeWatchlistId) return;
    try {
        const res = await fetch(`${API_URL}/watchlists/${activeWatchlistId}/tickers`, {
            headers: getHeaders()
        });
        if (res.status === 401) {
            handleAuthError();
            return;
        }
        const tickers = await res.json();
        updateWatchlist(tickers);
    } catch (e) { console.error('Dashboard data error:', e); }
}

// --- Idea & Strategy Management ---
const IdeaManager = {
    tabs: [],
    activeTabId: null,

    init() {
        this.tabsContainer = document.getElementById('ideasTabs');
        this.contentContainer = document.getElementById('ideasContent');
    },

    addTab(title, results) {
        const id = 'tab-' + Date.now();
        const tab = { id, title, results };
        this.tabs.push(tab);
        this.renderTabs();
        this.selectTab(id);
    },

    removeTab(id, e) {
        if (e) e.stopPropagation();
        this.tabs = this.tabs.filter(t => t.id !== id);
        if (this.activeTabId === id) {
            this.activeTabId = this.tabs.length > 0 ? this.tabs[this.tabs.length - 1].id : null;
        }
        this.renderTabs();
        this.renderContent();
    },

    selectTab(id) {
        this.activeTabId = id;
        this.renderTabs();
        this.renderContent();
    },

    renderTabs() {
        if (!this.tabsContainer) return;
        if (this.tabs.length === 0) {
            this.tabsContainer.innerHTML = '';
            return;
        }
        this.tabsContainer.innerHTML = this.tabs.map(t => `
            <div class="tab-item ${t.id === this.activeTabId ? 'active' : ''}" onclick="IdeaManager.selectTab('${t.id}')">
                <span>${t.title}</span>
                <span class="tab-close" onclick="IdeaManager.removeTab('${t.id}', event)">×</span>
            </div>
        `).join('');
    },

    renderContent() {
        if (!this.contentContainer) return;
        const activeTab = this.tabs.find(t => t.id === this.activeTabId);
        if (!activeTab) {
            this.contentContainer.innerHTML = '<p class="empty-state">Frage die AI nach einer Strategie oder Analyse.</p>';
            return;
        }

        const { results } = activeTab;
        let html = `<div class="research-summary">${results.summary}</div>`;

        if (results.data && results.data.length > 0) {
            html += `<table class="research-table">
                <thead>
                    <tr>
                        ${results.columns.map(c => `<th>${c.label}</th>`).join('')}
                    </tr>
                </thead>
                <tbody>
                    ${results.data.map(row => `
                        <tr onclick="loadChartForSymbol('${row.symbol}')">
                            ${results.columns.map(c => {
                const val = row[c.key];
                const cls = c.key === 'symbol' ? 'symbol' : '';
                return `<td class="${cls}">${val !== null ? val : 'N/A'}</td>`;
            }).join('')}
                        </tr>
                    `).join('')}
                </tbody>
            </table>`;
        } else {
            html += '<p class="empty-state">Keine Daten für diese Analyse gefunden.</p>';
        }

        this.contentContainer.innerHTML = html;
    }
};

async function executeCommand() {
    const input = document.getElementById('command-bar');
    const cmd = input.value;
    if (!cmd) return;

    try {
        const res = await fetch(`${API_URL}/command?text=${encodeURIComponent(cmd)}`, {
            method: 'POST',
            headers: getHeaders()
        });

        if (res.status === 401) {
            handleAuthError();
            return;
        }

        const data = await res.json();

        if (data.action === 'research') {
            IdeaManager.addTab(data.title, data.results);
        } else if (data.action === 'filter' && data.results) {
            renderFilterResults(data.results);
        } else if (Array.isArray(data)) {
            updateCandidates(data);
        } else if (data.message) {
            alert(data.message);
            fetchDashboardData();
        } else if (data.error) {
            alert('Fehler: ' + data.error);
        }
    } catch (e) {
        console.error('Command execution error:', e);
        alert('Befehl fehlgeschlagen. Bist du eingeloggt?');
    }
    input.value = '';
}



// --- Render Functions ---
function updateWatchlist(tickers) {
    const container = document.getElementById('watchlist');
    if (!tickers || tickers.length === 0) {
        container.innerHTML = '<p class="empty-state">Suche eine Aktie und füge sie hinzu.</p>';
        return;
    }
    container.innerHTML = tickers.map(t => `
        <div class="list-item" onclick="loadChartForSymbol('${t.symbol}')">
            <span class="symbol">${t.symbol}</span>
            <span class="price">${(t.last_price || 0).toFixed(2)}</span>
            <span class="change ${(t.change_pct || 0) >= 0 ? 'positive' : 'negative'}">${(t.change_pct || 0).toFixed(2)}%</span>
        </div>
    `).join('');
}

function renderFilterResults(results) {
    const container = document.getElementById('candidates-list');
    if (!results || results.length === 0) {
        container.innerHTML = '<p class="empty-state">Keine Treffer für diesen Filter.</p>';
        return;
    }
    container.innerHTML = results.map(r => `
        <div class="list-item" onclick="loadChartForSymbol('${r.symbol}')">
            <div>
                <span class="symbol">${r.symbol}</span>
                <span class="stock-name">${r.name || ''}</span>
            </div>
            <div class="filter-details">
                <span>KGV: ${r.pe_ratio ? r.pe_ratio.toFixed(1) : 'N/A'}</span>
                <span>$${r.price ? r.price.toFixed(2) : 'N/A'}</span>
            </div>
        </div>
    `).join('');
}

function updateCandidates(list) {
    const container = document.getElementById('candidates-list');
    container.innerHTML = list.map(item => `
        <div class="list-item">
            <div>
                <span class="light ${item.traffic_light}"></span>
                <span class="symbol">${item.ticker.symbol}</span>
            </div>
            <span class="change negative">${item.ticker.change_pct.toFixed(2)}%</span>
            <button class="trade-btn" onclick="trade('${item.ticker.symbol}')">Trade</button>
        </div>
    `).join('');
}

async function trade(symbol) {
    document.getElementById('command-bar').value = `Kauf 10 ${symbol}`;
    executeCommand();
}
