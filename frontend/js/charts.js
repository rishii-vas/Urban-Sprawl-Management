// Chart.js configurations for Urban Sprawl Management

// Chart.js default configuration
Chart.defaults.font.family = "'Inter', -apple-system, BlinkMacSystemFont, sans-serif";
Chart.defaults.color = '#64748b';
Chart.defaults.plugins.legend.labels.usePointStyle = true;
Chart.defaults.plugins.legend.labels.padding = 20;

// Color palette
const colors = {
    emerald: '#10b981',
    emeraldLight: '#34d399',
    sky: '#0ea5e9',
    skyLight: '#38bdf8',
    orange: '#f97316',
    orangeLight: '#fb923c',
    violet: '#8b5cf6',
    violetLight: '#a78bfa',
    amber: '#f59e0b',
    rose: '#f43f5e',
    success: '#22c55e',
    warning: '#eab308',
    error: '#ef4444',
    neutral: '#94a3b8'
};

// Initialize charts when DOM is loaded
document.addEventListener('DOMContentLoaded', function () {
    initializeLandUseChart();
    initializeSprawlTrendChart();
    initializeZoneDensityChart();
    initializeProjectionChart();
    initializeEvolutionChart();
    initializeSDGChart();
});

// Land Use Classification Donut Chart
function initializeLandUseChart() {
    const ctx = document.getElementById('landUseChart');
    if (!ctx) return;

    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Residential', 'Commercial', 'Industrial', 'Green Space', 'Agricultural', 'Mixed Use'],
            datasets: [{
                data: [35, 20, 15, 12, 10, 8],
                backgroundColor: [
                    colors.sky,
                    colors.emerald,
                    colors.orange,
                    colors.success,
                    colors.amber,
                    colors.violet
                ],
                borderWidth: 0,
                hoverOffset: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '65%',
            plugins: {
                legend: {
                    position: 'right',
                    labels: {
                        padding: 15,
                        font: { size: 12 }
                    }
                }
            }
        }
    });
}

// Urban Sprawl Trend Line Chart
function initializeSprawlTrendChart() {
    const ctx = document.getElementById('sprawlTrendChart');
    if (!ctx) return;

    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: months,
            datasets: [{
                label: 'Sprawl Index',
                data: [58, 60, 59, 62, 64, 63, 65, 66, 65, 67, 68, 67],
                borderColor: colors.emerald,
                backgroundColor: 'rgba(16, 185, 129, 0.1)',
                fill: true,
                tension: 0.4,
                pointRadius: 4,
                pointHoverRadius: 6
            }, {
                label: 'Predicted',
                data: [null, null, null, null, null, null, null, null, null, 67, 69, 71],
                borderColor: colors.violet,
                borderDash: [5, 5],
                tension: 0.4,
                pointRadius: 4,
                pointHoverRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top'
                }
            },
            scales: {
                y: {
                    beginAtZero: false,
                    min: 50,
                    max: 80,
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    }
                },
                x: {
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}

// Zone-wise Population Density Bar Chart
function initializeZoneDensityChart() {
    const ctx = document.getElementById('zoneDensityChart');
    if (!ctx) return;

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Zone 1 - Central', 'Zone 2 - North', 'Zone 3 - South', 'Zone 4 - East', 'Zone 5 - West', 'Zone 6 - Outer'],
            datasets: [{
                label: 'Current Density (per km²)',
                data: [15200, 8500, 9200, 7800, 6500, 3200],
                backgroundColor: colors.sky,
                borderRadius: 6
            }, {
                label: 'Projected 2030',
                data: [17500, 11200, 12400, 10500, 9200, 5800],
                backgroundColor: colors.emerald,
                borderRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top'
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    }
                },
                x: {
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}

// 5/10/25 Year Projection Chart
function initializeProjectionChart() {
    const ctx = document.getElementById('projectionChart');
    if (!ctx) return;

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: ['2025', '2030', '2035', '2040', '2045', '2050'],
            datasets: [{
                label: 'Conservative',
                data: [67, 72, 76, 79, 82, 84],
                borderColor: colors.success,
                backgroundColor: 'rgba(34, 197, 94, 0.1)',
                fill: true,
                tension: 0.4
            }, {
                label: 'Moderate',
                data: [67, 75, 82, 88, 93, 97],
                borderColor: colors.amber,
                backgroundColor: 'rgba(245, 158, 11, 0.1)',
                fill: true,
                tension: 0.4
            }, {
                label: 'Aggressive',
                data: [67, 78, 88, 97, 105, 112],
                borderColor: colors.rose,
                backgroundColor: 'rgba(244, 63, 94, 0.1)',
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top'
                }
            },
            scales: {
                y: {
                    beginAtZero: false,
                    min: 60,
                    title: {
                        display: true,
                        text: 'Sprawl Index'
                    },
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    }
                },
                x: {
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}

// Historical Evolution Chart
function initializeEvolutionChart() {
    const ctx = document.getElementById('evolutionChart');
    if (!ctx) return;

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: ['2010', '2012', '2014', '2016', '2018', '2020', '2022', '2024'],
            datasets: [{
                label: 'Urban Area (km²)',
                data: [320, 345, 378, 412, 445, 468, 495, 520],
                borderColor: colors.sky,
                backgroundColor: 'rgba(14, 165, 233, 0.1)',
                fill: true,
                tension: 0.4,
                yAxisID: 'y'
            }, {
                label: 'Population (millions)',
                data: [1.8, 1.9, 2.0, 2.1, 2.2, 2.25, 2.35, 2.4],
                borderColor: colors.emerald,
                tension: 0.4,
                yAxisID: 'y1'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top'
                }
            },
            scales: {
                y: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    title: {
                        display: true,
                        text: 'Urban Area (km²)'
                    },
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    }
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    title: {
                        display: true,
                        text: 'Population (M)'
                    },
                    grid: {
                        drawOnChartArea: false
                    }
                },
                x: {
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}

// SDG Progress Radar Chart
function initializeSDGChart() {
    const ctx = document.getElementById('sdgChart');
    if (!ctx) return;

    new Chart(ctx, {
        type: 'radar',
        data: {
            labels: ['SDG 11', 'SDG 9', 'SDG 6', 'SDG 13', 'SDG 3'],
            datasets: [{
                label: '2024',
                data: [72, 65, 58, 45, 68],
                borderColor: colors.emerald,
                backgroundColor: 'rgba(16, 185, 129, 0.2)',
                pointBackgroundColor: colors.emerald
            }, {
                label: '2023',
                data: [65, 58, 52, 40, 62],
                borderColor: colors.sky,
                backgroundColor: 'rgba(14, 165, 233, 0.2)',
                pointBackgroundColor: colors.sky
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top'
                }
            },
            scales: {
                r: {
                    beginAtZero: true,
                    max: 100,
                    ticks: {
                        stepSize: 20
                    },
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    }
                }
            }
        }
    });
}

// Developer Dashboard specific charts
function initializeUserActivityChart() {
    const ctx = document.getElementById('userActivityChart');
    if (!ctx) return;

    const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: days,
            datasets: [{
                label: 'Builders',
                data: [45, 52, 48, 61, 55, 22, 18],
                backgroundColor: colors.emerald,
                borderRadius: 4
            }, {
                label: 'Users',
                data: [120, 135, 142, 158, 145, 88, 76],
                backgroundColor: colors.sky,
                borderRadius: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top'
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    }
                },
                x: {
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}

function initializeFeedbackSentimentChart() {
    const ctx = document.getElementById('feedbackSentimentChart');
    if (!ctx) return;

    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Positive', 'Neutral', 'Negative'],
            datasets: [{
                data: [65, 25, 10],
                backgroundColor: [colors.success, colors.amber, colors.error],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '70%',
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
}

// User Dashboard simple chart
function initializeSimpleSprawlChart() {
    const ctx = document.getElementById('simpleSprawlChart');
    if (!ctx) return;

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
            datasets: [{
                label: 'City Health Index',
                data: [72, 74, 73, 76, 75, 78],
                borderColor: colors.emerald,
                backgroundColor: 'rgba(16, 185, 129, 0.15)',
                fill: true,
                tension: 0.4,
                pointRadius: 5,
                pointHoverRadius: 8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: false,
                    min: 60,
                    max: 90,
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    }
                },
                x: {
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}
