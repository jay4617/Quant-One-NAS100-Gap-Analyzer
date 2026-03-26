/**
 * app.js — Main application logic.
 * Fetches data from Flask API, renders all sections, initializes effects.
 */

(async function () {
    'use strict';

    // ── API helpers ──────────────────────────────────────────────────────────

    async function fetchJSON(url) {
        const res = await fetch(url);
        if (!res.ok) throw new Error(`API error: ${res.status}`);
        return res.json();
    }

    function fmt(val, decimals = 2) {
        if (val == null) return '—';
        return Number(val).toFixed(decimals);
    }

    function fmtPct(val, decimals = 1) {
        if (val == null) return '—';
        return (Number(val) * 100).toFixed(decimals) + '%';
    }

    function cardHTML(label, value, sub) {
        return `<div class="metric-card">
            <div class="label">${label}</div>
            <div class="value">${value}</div>
            ${sub ? `<div class="sub">${sub}</div>` : ''}
        </div>`;
    }

    // ── Boot ─────────────────────────────────────────────────────────────────

    try {
        // Fetch all data independently — one failure won't block others
        const results = await Promise.allSettled([
            fetchJSON('/api/overview'),
            fetchJSON('/api/by-size'),
            fetchJSON('/api/by-day'),
            fetchJSON('/api/by-market'),
            fetchJSON('/api/backtest'),
            fetchJSON('/api/distribution'),
            fetchJSON('/api/stats-tests'),
        ]);

        const [overview, bySize, byDay, byMarket, backtest, distribution, statsTests] =
            results.map(r => r.status === 'fulfilled' ? r.value : null);

        if (overview) renderHeroSubtitle(overview);
        if (overview) renderOverview(overview);
        if (distribution && bySize && byDay) renderCharts(distribution, bySize, byDay);
        if (statsTests) renderStatsTests(statsTests);
        if (backtest) renderBacktest(backtest);
        loadGapsTable(1);

        // JARVIS loads separately (real-time, may be slower)
        loadJarvis();

    } catch (err) {
        console.error('Boot error:', err);
    }

    // Initialize effects after DOM is populated
    setTimeout(() => {
        if (window.Effects) window.Effects.initEffects();
    }, 100);

    // ── Hero Subtitle ────────────────────────────────────────────────────────

    function renderHeroSubtitle(ov) {
        const el = document.getElementById('hero-subtitle');
        if (el) {
            el.textContent =
                `Analyzing ${ov.total_gaps.toLocaleString()} gaps | ${ov.date_range.start.slice(0, 10)} to ${ov.date_range.end.slice(0, 10)}`;
        }
    }

    // ── Overview Section ─────────────────────────────────────────────────────

    function renderOverview(ov) {
        const grid = document.getElementById('overview-cards');
        if (!grid) return;

        grid.innerHTML = [
            cardHTML('Total Gaps Analyzed', ov.total_gaps.toLocaleString(),
                `${ov.gap_up_count} up / ${ov.gap_down_count} down`),
            cardHTML('Overall Fill Rate', fmtPct(ov.overall_fill_rate),
                'gaps that filled within session'),
            cardHTML('Avg Gap Size', fmt(ov.avg_gap_percent, 3) + '%',
                'mean absolute gap percentage'),
            cardHTML('Avg Fill Extent', fmt(ov.avg_fill_percent, 0) + '%',
                'mean retracement toward close'),
        ].join('');
    }

    // ── Charts ───────────────────────────────────────────────────────────────

    function renderCharts(dist, bySize, byDay) {
        if (window.ChartFactory) {
            window.ChartFactory.createDistributionChart('chart-distribution', dist);
            window.ChartFactory.createFillBySizeChart('chart-by-size', bySize);
            window.ChartFactory.createFillByDayChart('chart-by-day', byDay);
        }
    }

    // ── Stats Tests ──────────────────────────────────────────────────────────

    function renderStatsTests(tests) {
        const grid = document.getElementById('stats-tests');
        if (!grid) return;

        let html = '<div class="section-label">STATISTICAL SIGNIFICANCE</div>';

        if (tests.overall_vs_50) {
            const t = tests.overall_vs_50;
            const sig = t.significant || t.p_value < 0.05;
            html += `<div class="stat-test">
                <div class="test-name">Overall Fill Rate vs 50%
                    <span class="badge ${sig ? 'sig' : 'not-sig'}">${sig ? 'SIGNIFICANT' : 'NOT SIGNIFICANT'}</span>
                </div>
                <div class="test-result">Z = ${fmt(t.z_statistic, 3)}, p = ${fmt(t.p_value, 4)} | Fill rate: ${fmtPct(t.fill_rate)}</div>
            </div>`;
        }

        if (tests.up_vs_down) {
            const t = tests.up_vs_down;
            const sig = t.significant || t.p_value < 0.05;
            html += `<div class="stat-test">
                <div class="test-name">Gap Up vs Gap Down Fill Rate
                    <span class="badge ${sig ? 'sig' : 'not-sig'}">${sig ? 'SIGNIFICANT' : 'NOT SIGNIFICANT'}</span>
                </div>
                <div class="test-result">Z = ${fmt(t.z_statistic, 3)}, p = ${fmt(t.p_value, 4)} | Up: ${fmtPct(t.gap_up_fill_rate)} vs Down: ${fmtPct(t.gap_down_fill_rate)}</div>
            </div>`;
        }

        if (tests.category_independence) {
            const t = tests.category_independence;
            const sig = t.significant || t.p_value < 0.05;
            html += `<div class="stat-test">
                <div class="test-name">Fill Rate Independence by Category (Chi-Square)
                    <span class="badge ${sig ? 'sig' : 'not-sig'}">${sig ? 'SIGNIFICANT' : 'NOT SIGNIFICANT'}</span>
                </div>
                <div class="test-result">Chi2 = ${fmt(t.chi2_statistic, 3)}, p = ${fmt(t.p_value, 4)}, df = ${t.degrees_of_freedom}</div>
            </div>`;
        }

        grid.innerHTML = html;
    }

    // ── Backtest ─────────────────────────────────────────────────────────────

    function renderBacktest(bt) {
        const grid = document.getElementById('backtest-cards');
        if (!grid) return;

        const s = bt.summary;
        grid.innerHTML = [
            cardHTML('Total Trades', s.total_trades.toLocaleString(), `${s.wins} wins / ${s.losses} losses`),
            cardHTML('Win Rate', fmt(s.win_rate * 100, 1) + '%', 'of all gap-fill trades'),
            cardHTML('Cumulative Return', fmt(s.total_return_pct, 1) + '%', 'total strategy return'),
            cardHTML('Avg Win / Avg Loss',
                fmt(s.avg_win_pct, 2) + ' / ' + fmt(s.avg_loss_pct, 2) + '%',
                'risk/reward profile'),
        ].join('');

        // Cumulative return chart
        if (window.ChartFactory && bt.cumulative_series) {
            window.ChartFactory.createCumulativeChart('chart-cumulative', bt.cumulative_series);
        }
    }

    // ── JARVIS ───────────────────────────────────────────────────────────────

    async function loadJarvis() {
        const loading = document.getElementById('jarvis-loading');
        const content = document.getElementById('jarvis-content');
        const error = document.getElementById('jarvis-error');

        try {
            const j = await fetchJSON('/api/jarvis');

            if (j.error) {
                loading.style.display = 'none';
                error.style.display = 'block';
                error.textContent = j.error;
                return;
            }

            // Banner
            const dirLabel = j.direction === 'UP' ? 'GAP UP' : 'GAP DOWN';
            document.getElementById('jarvis-banner').innerHTML = `
                <div class="banner-eyebrow">TODAY'S SESSION | ${j.day_name?.toUpperCase() || ''} ${j.today_date?.slice(0, 10) || ''}</div>
                <div class="banner-title">${dirLabel} &nbsp; ${fmt(j.abs_gap_pct * 100, 2)}% &nbsp; (${fmt(Math.abs(j.gap_size), 2)} pts)</div>
                <div class="banner-meta">Category: ${j.category} &nbsp;|&nbsp; Status: ${j.filled ? 'FILLED' : 'OPEN'} &nbsp;|&nbsp; Fill: ${fmt(j.fill_pct, 0)}% &nbsp;|&nbsp; Confidence: ${j.confidence}</div>
            `;

            // Price cards
            const priceVsOpen = j.price_vs_open_pct != null ? fmt(j.price_vs_open_pct, 2) + '% from open' : '';
            document.getElementById('jarvis-prices').innerHTML = [
                cardHTML('Yesterday Close', fmt(j.prev_close, 2), ''),
                cardHTML('Today Open', fmt(j.today_open, 2), ''),
                cardHTML('Current Price', fmt(j.current_price, 2), priceVsOpen),
                cardHTML('Gap Fill Probability', fmt(j.composite_fill_prob * 100, 0) + '%', j.confidence + ' confidence'),
            ].join('');

            // Insights
            const insightsEl = document.getElementById('jarvis-insights');
            if (j.insights && j.insights.length) {
                insightsEl.innerHTML = j.insights.map(text => {
                    const isStatus = text.startsWith('STATUS:');
                    return `<div class="insight-block ${isStatus ? 'status' : ''}">${text}</div>`;
                }).join('');
            }

            // Outlook
            document.getElementById('jarvis-outlook').innerHTML = `
                <div class="outlook-label">Trade Outlook</div>
                <div class="outlook-text">${j.action_hint || 'No outlook available'}</div>
            `;

            // Fill levels
            const fl = j.fill_levels;
            if (fl && fl.p25_price != null) {
                document.getElementById('fill-levels-desc').textContent =
                    `Based on ${fl.sample_size} historical ${j.category.toLowerCase()} ${j.direction.toLowerCase()} gaps — how far does the gap typically retrace?`;
                document.getElementById('jarvis-fill-levels').innerHTML = [
                    cardHTML('25th Percentile', fmt(fl.p25_price, 2), fmt(fl.p25_fill, 0) + '% of gap filled'),
                    cardHTML('Median (50th)', fmt(fl.p50_price, 2), fmt(fl.p50_fill, 0) + '% of gap filled'),
                    cardHTML('75th Percentile', fmt(fl.p75_price, 2), fmt(fl.p75_fill, 0) + '% of gap filled'),
                    cardHTML('Full Fill', fmt(fl.full_fill_price, 2), '100% = prev close'),
                ].join('');
            }

            // Win stats
            document.getElementById('jarvis-win-stats').innerHTML = [
                cardHTML(`Win Rate (${j.category} ${j.direction})`, fmt(j.dc_win_rate * 100, 0) + '%',
                    `${j.dc_wins}W / ${j.dc_losses}L`),
                cardHTML('Avg Fill Extent', fmt(j.dc_avg_fill_pct, 0) + '%', 'of gap retraced'),
                cardHTML('Continuation Risk', fmt(j.dc_continuation_rate * 100, 0) + '%', 'gaps that kept going'),
                cardHTML(`Best Day for ${j.direction}`, j.best_day?.slice(0, 3) || '—',
                    fmt(j.best_day_rate * 100, 0) + '% fill rate'),
            ].join('');

            // Historical breakdown
            const breakdownData = [
                { signal: `${j.category} + ${j.direction}`, fill_rate: j.dir_cat_fill_rate, count: j.dir_cat_count },
                { signal: `Similar size (${fmt(j.abs_gap_pct * 100, 2)}% +/- 0.1)`, fill_rate: j.similar_fill_rate, count: j.similar_count },
                { signal: `${j.day_name} + ${j.direction}`, fill_rate: j.day_dir_fill_rate, count: j.day_dir_count },
                { signal: `${j.market_condition} + ${j.direction}`, fill_rate: j.mkt_fill_rate, count: j.mkt_count },
                { signal: `Recent 20 ${j.direction.toLowerCase()} gaps`, fill_rate: j.recent_fill_rate, count: 20 },
                { signal: `All ${j.direction.toLowerCase()} gaps`, fill_rate: j.dir_fill_rate, count: j.dir_count },
            ];

            document.getElementById('jarvis-breakdown').innerHTML = `
                <table class="data-table">
                    <thead><tr><th>Signal</th><th>Fill Rate</th><th>Sample Size</th></tr></thead>
                    <tbody>
                        ${breakdownData.map(d => `
                            <tr>
                                <td>${d.signal}</td>
                                <td>${fmtPct(d.fill_rate)}</td>
                                <td style="text-align:right">${d.count}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            `;

            // Yesterday
            document.getElementById('jarvis-yesterday').innerHTML = [
                cardHTML('Open', fmt(j.prev_open, 2), ''),
                cardHTML('High', fmt(j.prev_high, 2), ''),
                cardHTML('Low', fmt(j.prev_low, 2), ''),
                cardHTML('Close', fmt(j.prev_close, 2), ''),
            ].join('');

            // Show content
            loading.style.display = 'none';
            content.style.display = 'block';

            // Re-trigger scroll reveals for newly added cards
            setTimeout(() => {
                if (window.Effects) window.Effects.refreshEffects();
            }, 50);

        } catch (err) {
            loading.style.display = 'none';
            error.style.display = 'block';
            error.textContent = 'Unable to fetch real-time data. Markets may be closed or server error.';
            console.error('JARVIS error:', err);
        }
    }

    // ── Raw Data Table ───────────────────────────────────────────────────────

    async function loadGapsTable(page) {
        try {
            const data = await fetchJSON(`/api/gaps?page=${page}&per_page=30`);
            const tbody = document.getElementById('gaps-tbody');

            tbody.innerHTML = data.data.map(row => `
                <tr>
                    <td>${row.date?.slice(0, 10) || ''}</td>
                    <td>${row.gap_direction || ''}</td>
                    <td>${fmt(row.gap_percent * 100, 3)}%</td>
                    <td>${row.gap_category || ''}</td>
                    <td>${row.gap_filled ? 'Yes' : 'No'}</td>
                    <td>${fmt(row.fill_percent, 0)}%</td>
                    <td>${fmt(row.day_return_pct, 3)}%</td>
                    <td>${row.day_name?.slice(0, 3) || ''}</td>
                </tr>
            `).join('');

            // Pagination
            const totalPages = Math.ceil(data.total / data.per_page);
            const pag = document.getElementById('pagination');
            let pagHTML = '';

            if (page > 1) {
                pagHTML += `<button class="page-btn" onclick="window.loadPage(${page - 1})">PREV</button>`;
            }

            const start = Math.max(1, page - 2);
            const end = Math.min(totalPages, page + 2);
            for (let i = start; i <= end; i++) {
                pagHTML += `<button class="page-btn ${i === page ? 'active' : ''}" onclick="window.loadPage(${i})">${i}</button>`;
            }

            if (page < totalPages) {
                pagHTML += `<button class="page-btn" onclick="window.loadPage(${page + 1})">NEXT</button>`;
            }

            pag.innerHTML = pagHTML;

        } catch (err) {
            console.error('Table load error:', err);
        }
    }

    // Expose for pagination buttons
    window.loadPage = loadGapsTable;

})();
