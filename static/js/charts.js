// Admin dashboard analytics visualization using Chart.js

let charts = {};

function destroyAllCharts() {
    Object.keys(charts).forEach(key => {
        if (charts[key]) {
            charts[key].destroy();
        }
    });
    charts = {};
}

function initAdminAnalytics(data) {
    // Prevent rendering errors if Chart.js is not loaded
    if (typeof Chart === 'undefined') {
        console.error('Chart.js library is not loaded');
        return;
    }

    // Destroy existing charts to avoid overlapping overlays
    destroyAllCharts();

    const isDarkMode = document.body.getAttribute('data-theme') !== 'light';
    const gridColor = isDarkMode ? '#262636' : '#E2E8F0';
    const textColor = isDarkMode ? '#9CA3AF' : '#475569';
    const accentColor = '#6366F1';
    
    Chart.defaults.color = textColor;
    Chart.defaults.font.family = "'Inter', sans-serif";

    // 1. Most Searched Skills (Vertical Bar Chart)
    const skillsCanvas = document.getElementById('skillsChart');
    if (skillsCanvas && data.most_searched_skills && data.most_searched_skills.length) {
        const labels = data.most_searched_skills.map(s => s.skill);
        const counts = data.most_searched_skills.map(s => s.count);
        
        charts.skills = new Chart(skillsCanvas, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Students with Skill',
                    data: counts,
                    backgroundColor: 'rgba(99, 102, 241, 0.7)',
                    borderColor: 'rgba(99, 102, 241, 1)',
                    borderWidth: 1.5,
                    borderRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    x: { grid: { color: gridColor } },
                    y: { 
                        grid: { color: gridColor },
                        ticks: { stepSize: 1 } 
                    }
                }
            }
        });
    }

    // 2. Internship Mode Distribution (Doughnut Chart)
    const modeCanvas = document.getElementById('modeChart');
    if (modeCanvas && data.mode_distribution) {
        const labels = Object.keys(data.mode_distribution);
        const counts = Object.values(data.mode_distribution);
        
        charts.mode = new Chart(modeCanvas, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: counts,
                    backgroundColor: [
                        'rgba(16, 185, 129, 0.7)', // success/green
                        'rgba(245, 158, 11, 0.7)', // warning/amber
                        'rgba(99, 102, 241, 0.7)'  // primary/indigo
                    ],
                    borderColor: isDarkMode ? '#1C1C24' : '#FFFFFF',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'bottom' }
                }
            }
        });
    }

    // 3. Most Applied Internships (Horizontal Bar Chart)
    const appliedCanvas = document.getElementById('appliedChart');
    if (appliedCanvas && data.most_applied_internships && data.most_applied_internships.length) {
        const labels = data.most_applied_internships.map(a => a.label);
        const counts = data.most_applied_internships.map(a => a.count);
        
        charts.applied = new Chart(appliedCanvas, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Applications',
                    data: counts,
                    backgroundColor: 'rgba(139, 92, 246, 0.7)', // purple
                    borderColor: 'rgba(139, 92, 246, 1)',
                    borderWidth: 1.5,
                    borderRadius: 6
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    x: { 
                        grid: { color: gridColor },
                        ticks: { stepSize: 1 }
                    },
                    y: { grid: { color: 'transparent' } }
                }
            }
        });
    }

    // 4. Popular Locations (Pie Chart)
    const locationCanvas = document.getElementById('locationChart');
    if (locationCanvas && data.popular_locations) {
        const labels = Object.keys(data.popular_locations);
        const counts = Object.values(data.popular_locations);
        
        charts.location = new Chart(locationCanvas, {
            type: 'pie',
            data: {
                labels: labels,
                datasets: [{
                    data: counts,
                    backgroundColor: [
                        'rgba(99, 102, 241, 0.7)',
                        'rgba(236, 72, 153, 0.7)', // pink
                        'rgba(20, 184, 166, 0.7)', // teal
                        'rgba(245, 158, 11, 0.7)',
                        'rgba(107, 114, 128, 0.7)'  // gray
                    ],
                    borderColor: isDarkMode ? '#1C1C24' : '#FFFFFF',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'bottom' }
                }
            }
        });
    }
}
