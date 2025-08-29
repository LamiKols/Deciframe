(async function() {
    const orgId = window.__ORG_ID__ || 1;
    const userRole = window.__USER_ROLE__ || 'director';
    
    // Utility functions
    const q = (id) => document.getElementById(id);
    const get = async (url) => {
        const response = await fetch(url, {
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        });
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        return response.json();
    };

    // Chart instances for cleanup
    let charts = {};

    // Load and display data
    async function loadDashboard() {
        try {
            // Show loading state
            q("ai-summary").textContent = "Loading dashboard data...";

            // Load all metrics in parallel
            const [portfolio, roi, departments, summary] = await Promise.all([
                get(`/api/metrics/portfolio`),
                get(`/api/metrics/roi`),
                get(`/api/metrics/departments`),
                get(`/api/metrics/summary`)
            ]);

            // Update KPIs
            updateKPIs(portfolio, roi);
            
            // Update charts
            updateFunnelChart(portfolio);
            updateROIChart(roi);
            updateDepartmentChart(departments);
            
            // Update summary
            updateSummary(summary);
            
            // Update timestamp
            const timestamp = new Date(portfolio.generated_at * 1000).toLocaleString();
            q("data-timestamp").textContent = timestamp;

        } catch (error) {
            console.error('Dashboard loading error:', error);
            q("ai-summary").textContent = `Error loading dashboard: ${error.message}. Please refresh the page.`;
        }
    }

    function updateKPIs(portfolio, roi) {
        const funnel = portfolio.funnel;
        
        // Basic KPIs
        q("kpi-problems").textContent = funnel.problems || 0;
        q("kpi-cases").textContent = funnel.cases || 0;
        q("kpi-approved").textContent = funnel.approved_cases || 0;
        q("kpi-projects").textContent = funnel.projects || 0;
        q("kpi-done").textContent = funnel.done || 0;
        q("kpi-stalled").textContent = portfolio.stalled || 0;
        q("kpi-leadtime").textContent = portfolio.lead_time_days ? `${portfolio.lead_time_days}d` : "—";

        // Calculate and display conversion rates
        const conversionRate = funnel.problems > 0 ? 
            ((funnel.cases / funnel.problems) * 100).toFixed(1) : 0;
        const approvalRate = funnel.cases > 0 ? 
            ((funnel.approved_cases / funnel.cases) * 100).toFixed(1) : 0;
        const completionRate = funnel.projects > 0 ? 
            ((funnel.done / funnel.projects) * 100).toFixed(1) : 0;

        q("conversion-rate").textContent = `${conversionRate}%`;
        q("approval-rate").textContent = `${approvalRate}%`;
        q("completion-rate").textContent = `${completionRate}%`;

        // Recent activity
        if (portfolio.recent_activity) {
            q("recent-problems").textContent = portfolio.recent_activity.problems_30d || 0;
            q("recent-cases").textContent = portfolio.recent_activity.cases_30d || 0;
        }
    }

    function updateFunnelChart(portfolio) {
        const ctx = q("chart-funnel");
        if (!ctx) return;

        // Destroy existing chart
        if (charts.funnel) {
            charts.funnel.destroy();
        }

        const funnel = portfolio.funnel;
        charts.funnel = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['Problems', 'Cases', 'Approved', 'Projects', 'Completed'],
                datasets: [{
                    label: 'Count',
                    data: [
                        funnel.problems || 0,
                        funnel.cases || 0,
                        funnel.approved_cases || 0,
                        funnel.projects || 0,
                        funnel.done || 0
                    ],
                    backgroundColor: [
                        'rgba(13, 110, 253, 0.8)',   // Blue
                        'rgba(13, 202, 240, 0.8)',   // Cyan
                        'rgba(25, 135, 84, 0.8)',    // Green
                        'rgba(255, 193, 7, 0.8)',    // Yellow
                        'rgba(108, 117, 125, 0.8)'   // Gray
                    ],
                    borderColor: [
                        'rgb(13, 110, 253)',
                        'rgb(13, 202, 240)',
                        'rgb(25, 135, 84)',
                        'rgb(255, 193, 7)',
                        'rgb(108, 117, 125)'
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    title: {
                        display: true,
                        text: 'Portfolio Flow'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: { precision: 0 }
                    }
                }
            }
        });
    }

    function updateROIChart(roi) {
        const ctx = q("chart-roi");
        if (!ctx) return;

        // Destroy existing chart
        if (charts.roi) {
            charts.roi.destroy();
        }

        charts.roi = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['Projected Benefits', 'Realized Benefits'],
                datasets: [{
                    label: '£',
                    data: [roi.projected || 0, roi.realized || 0],
                    backgroundColor: [
                        'rgba(13, 202, 240, 0.8)',   // Cyan for projected
                        'rgba(25, 135, 84, 0.8)'     // Green for realized
                    ],
                    borderColor: [
                        'rgb(13, 202, 240)',
                        'rgb(25, 135, 84)'
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    title: {
                        display: true,
                        text: `Realization Rate: ${roi.realization_rate || 0}%`
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return '£' + value.toLocaleString();
                            }
                        }
                    }
                }
            }
        });
    }

    function updateDepartmentChart(departments) {
        const ctx = q("chart-departments");
        if (!ctx) return;

        // Destroy existing chart
        if (charts.departments) {
            charts.departments.destroy();
        }

        const breakdown = departments.breakdown || [];
        if (breakdown.length === 0) {
            ctx.style.display = 'none';
            return;
        }

        charts.departments = new Chart(ctx, {
            type: 'horizontalBar',
            data: {
                labels: breakdown.map(d => d.name),
                datasets: [{
                    label: 'Problems',
                    data: breakdown.map(d => d.count),
                    backgroundColor: 'rgba(13, 110, 253, 0.8)',
                    borderColor: 'rgb(13, 110, 253)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        ticks: { precision: 0 }
                    }
                }
            }
        });
    }

    function updateSummary(summary) {
        const summaryElement = q("ai-summary");
        if (summaryElement) {
            summaryElement.textContent = summary.summary || "No summary available";
        }
    }

    // Event listeners
    if (q("btn-refresh")) {
        q("btn-refresh").addEventListener("click", () => {
            loadDashboard();
        });
    }

    if (q("btn-refresh-summary")) {
        q("btn-refresh-summary").addEventListener("click", async () => {
            try {
                const summary = await get(`/api/metrics/summary`);
                updateSummary(summary);
            } catch (error) {
                q("ai-summary").textContent = `Error refreshing summary: ${error.message}`;
            }
        });
    }

    if (q("invalidate-cache")) {
        q("invalidate-cache").addEventListener("click", async (e) => {
            e.preventDefault();
            try {
                await fetch(`/api/metrics/cache/invalidate`, { method: 'POST' });
                loadDashboard(); // Reload with fresh data
            } catch (error) {
                console.error('Cache invalidation error:', error);
            }
        });
    }

    // Drill-through functionality
    function openDrill(stage, stageLabel) {
        let page = 1;
        let q = "";
        const modalEl = q("#drillModal");
        const tbody = q("#drillTableBody");
        const titleEl = q("#drillModalTitle");
        const pageInfo = q("#drillPageInfo");
        const prevBtn = q("#drillPrev");
        const nextBtn = q("#drillNext");
        
        if (titleEl) titleEl.textContent = `${stageLabel} Details`;
        
        const doFetch = async () => {
            try {
                const url = `/api/metrics/portfolio/list?stage=${stage}&page=${page}&per_page=20` + 
                           (q ? `&q=${encodeURIComponent(q)}` : "");
                const response = await fetch(url, {
                    headers: { 'X-Requested-With': 'XMLHttpRequest' }
                });
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }
                
                const data = await response.json();
                
                if (tbody) {
                    if (data.items && data.items.length > 0) {
                        tbody.innerHTML = data.items.map(item => 
                            `<tr>
                                <td>${item.id}</td>
                                <td>${item.name || "Untitled"}</td>
                                <td>${item.created ? new Date(item.created).toLocaleDateString() : ""}</td>
                            </tr>`
                        ).join("");
                    } else {
                        tbody.innerHTML = '<tr><td colspan="3" class="text-center text-muted">No items found</td></tr>';
                    }
                }
                
                if (pageInfo) pageInfo.textContent = `Page ${page}`;
                if (prevBtn) prevBtn.disabled = page <= 1;
                if (nextBtn) nextBtn.disabled = !data.items || data.items.length < 20;
                
            } catch (error) {
                console.error('Drill-through fetch error:', error);
                if (tbody) {
                    tbody.innerHTML = '<tr><td colspan="3" class="text-center text-danger">Error loading data</td></tr>';
                }
            }
        };

        // Event handlers
        if (q("#drillSearchBtn")) {
            q("#drillSearchBtn").onclick = () => {
                q = q("#drillSearch")?.value || "";
                page = 1;
                doFetch();
            };
        }

        if (prevBtn) {
            prevBtn.onclick = () => {
                page = Math.max(1, page - 1);
                doFetch();
            };
        }

        if (nextBtn) {
            nextBtn.onclick = () => {
                page = page + 1;
                doFetch();
            };
        }

        // Load initial data and show modal
        doFetch().then(() => {
            if (typeof bootstrap !== 'undefined' && modalEl) {
                const modal = new bootstrap.Modal(modalEl);
                modal.show();
            }
        });
    }

    // Chart click handlers
    if (charts.funnel) {
        const canvas = q("#chart-funnel");
        if (canvas) {
            canvas.onclick = (evt) => {
                try {
                    const chart = Chart.getChart("chart-funnel");
                    if (chart) {
                        const points = chart.getElementsAtEventForMode(evt, 'nearest', { intersect: true }, true);
                        if (points.length > 0) {
                            const idx = points[0].index;
                            const stages = [
                                { key: 'problems', label: 'Problems' },
                                { key: 'cases', label: 'Business Cases' },
                                { key: 'approved', label: 'Approved Cases' },
                                { key: 'projects', label: 'Projects' },
                                { key: 'done', label: 'Completed Projects' }
                            ];
                            
                            if (stages[idx]) {
                                openDrill(stages[idx].key, stages[idx].label);
                            }
                        }
                    }
                } catch (error) {
                    console.error('Chart click handler error:', error);
                }
            };
        }
    }

    // Initialize dashboard
    loadDashboard();

    // Auto-refresh every 5 minutes
    setInterval(loadDashboard, 5 * 60 * 1000);

})();