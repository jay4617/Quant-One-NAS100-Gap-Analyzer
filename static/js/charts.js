/**
 * charts.js — Chart.js instances with dark theme.
 * All charts use white/grey on transparent background.
 */

// Chart.js defaults for dark theme
Chart.defaults.color = '#999';
Chart.defaults.borderColor = '#222';
Chart.defaults.font.family = "'JetBrains Mono', monospace";
Chart.defaults.font.size = 11;
Chart.defaults.plugins.legend.display = false;

const CHART_WHITE = 'rgba(255, 255, 255, 0.85)';
const CHART_WHITE_DIM = 'rgba(255, 255, 255, 0.4)';
const CHART_GRID = 'rgba(255, 255, 255, 0.06)';

/**
 * Gap size distribution histogram.
 */
function createDistributionChart(canvasId, data) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;

    return new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.labels,
            datasets: [
                {
                    label: 'Gap Up',
                    data: data.up_counts,
                    backgroundColor: CHART_WHITE,
                    borderColor: 'transparent',
                    borderWidth: 0,
                    borderRadius: 2,
                },
                {
                    label: 'Gap Down',
                    data: data.down_counts,
                    backgroundColor: CHART_WHITE_DIM,
                    borderColor: 'transparent',
                    borderWidth: 0,
                    borderRadius: 2,
                },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            aspectRatio: 2.5,
            animation: { duration: 0 },  // GSAP handles this
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                    align: 'end',
                    labels: {
                        boxWidth: 10,
                        padding: 16,
                        font: { size: 10, family: "'JetBrains Mono', monospace" },
                    },
                },
                tooltip: {
                    backgroundColor: '#111',
                    borderColor: '#333',
                    borderWidth: 1,
                    titleFont: { family: "'JetBrains Mono', monospace", size: 11 },
                    bodyFont: { family: "'JetBrains Mono', monospace", size: 11 },
                },
            },
            scales: {
                x: {
                    grid: { color: CHART_GRID },
                    ticks: {
                        maxTicksLimit: 10,
                        font: { size: 9 },
                    },
                    title: { display: true, text: 'Gap %', font: { size: 10 } },
                },
                y: {
                    grid: { color: CHART_GRID },
                    title: { display: true, text: 'Count', font: { size: 10 } },
                },
            },
        },
    });
}

/**
 * Fill rate by category (horizontal bar).
 */
function createFillBySizeChart(canvasId, data) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;

    return new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.map(d => d.category),
            datasets: [{
                data: data.map(d => (d.fill_rate * 100).toFixed(1)),
                backgroundColor: data.map((_, i) => {
                    const opacity = 0.3 + (i / data.length) * 0.6;
                    return `rgba(255, 255, 255, ${opacity})`;
                }),
                borderColor: 'rgba(255,255,255,0.7)',
                borderWidth: 1,
                borderRadius: 3,
            }],
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: true,
            aspectRatio: 1.5,
            animation: { duration: 0 },
            plugins: {
                tooltip: {
                    backgroundColor: '#111',
                    borderColor: '#333',
                    borderWidth: 1,
                    callbacks: {
                        label: (c) => `Fill Rate: ${c.raw}% (n=${data[c.dataIndex].count})`,
                    },
                },
            },
            scales: {
                x: {
                    grid: { color: CHART_GRID },
                    max: 100,
                    title: { display: true, text: 'Fill Rate %', font: { size: 10 } },
                },
                y: {
                    grid: { display: false },
                },
            },
        },
    });
}

/**
 * Fill rate by day of week (vertical bar).
 */
function createFillByDayChart(canvasId, data) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;

    return new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.map(d => d.day.slice(0, 3)),
            datasets: [{
                data: data.map(d => (d.fill_rate * 100).toFixed(1)),
                backgroundColor: 'rgba(255, 255, 255, 0.6)',
                borderColor: 'rgba(255, 255, 255, 0.8)',
                borderWidth: 1,
                borderRadius: 3,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            aspectRatio: 1.5,
            animation: { duration: 0 },
            plugins: {
                tooltip: {
                    backgroundColor: '#111',
                    borderColor: '#333',
                    borderWidth: 1,
                    callbacks: {
                        label: (c) => `Fill Rate: ${c.raw}% (n=${data[c.dataIndex].count})`,
                    },
                },
            },
            scales: {
                x: {
                    grid: { display: false },
                },
                y: {
                    grid: { color: CHART_GRID },
                    max: 100,
                    title: { display: true, text: 'Fill Rate %', font: { size: 10 } },
                },
            },
        },
    });
}

/**
 * Cumulative return line chart.
 */
function createCumulativeChart(canvasId, series) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;

    return new Chart(ctx, {
        type: 'line',
        data: {
            labels: series.map(d => d.date.slice(0, 10)),
            datasets: [{
                data: series.map(d => d.value),
                borderColor: CHART_WHITE,
                borderWidth: 1.5,
                pointRadius: 0,
                pointHitRadius: 8,
                tension: 0.3,
                fill: {
                    target: 'origin',
                    above: 'rgba(255,255,255,0.04)',
                    below: 'rgba(255,255,255,0.02)',
                },
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            aspectRatio: 2.5,
            animation: { duration: 0 },
            interaction: { mode: 'index', intersect: false },
            plugins: {
                tooltip: {
                    backgroundColor: '#111',
                    borderColor: '#333',
                    borderWidth: 1,
                    callbacks: {
                        label: (c) => `Cumulative Return: ${c.raw}%`,
                    },
                },
            },
            scales: {
                x: {
                    grid: { color: CHART_GRID },
                    ticks: {
                        maxTicksLimit: 8,
                        font: { size: 9 },
                    },
                },
                y: {
                    grid: { color: CHART_GRID },
                    title: { display: true, text: 'Return %', font: { size: 10 } },
                },
            },
        },
    });
}

// Expose globally
window.ChartFactory = {
    createDistributionChart,
    createFillBySizeChart,
    createFillByDayChart,
    createCumulativeChart,
};
