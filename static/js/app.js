// Application State
let currentUser = null;
let currentView = 'explore';
let currentInternships = [];
let activeInternship = null;
let isRegisterMode = false;

// Initialize on Load
document.addEventListener('DOMContentLoaded', () => {
    initApp();
});

// Toast Notifications
function showToast(message, type = 'success') {
    const container = document.getElementById('toastContainer');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    let icon = 'fa-circle-check';
    if (type === 'warning') icon = 'fa-triangle-exclamation';
    if (type === 'danger') icon = 'fa-circle-exclamation';
    
    toast.innerHTML = `
        <i class="fa-solid ${icon}"></i>
        <span>${message}</span>
        <span class="toast-close" onclick="this.parentElement.remove()">&times;</span>
    `;

    container.appendChild(toast);
    
    // Auto-remove toast after 4 seconds
    setTimeout(() => {
        toast.style.animation = 'slideIn 0.3s cubic-bezier(0.4, 0, 0.2, 1) reverse forwards';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

// Unified App Init
async function initApp() {
    // Check local storage for theme preference
    const savedTheme = localStorage.getItem('theme') || 'dark';
    document.body.setAttribute('data-theme', savedTheme);
    updateThemeIcon(savedTheme);

    // Verify session
    const res = await API.checkSession();
    if (res.data && res.data.logged_in) {
        handleUserLoginSuccess(res.data.user);
    } else {
        showAuthModal(true);
    }
}

// Theme toggler
function toggleTheme() {
    const currentTheme = document.body.getAttribute('data-theme');
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';
    document.body.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    updateThemeIcon(newTheme);
    
    // Redraw charts if we are on admin panel to adjust grid lines
    if (currentView === 'admin' && currentUser && currentUser.role === 'admin') {
        loadAdminStats();
    }
}

function updateThemeIcon(theme) {
    const btn = document.getElementById('themeToggleBtn');
    if (!btn) return;
    if (theme === 'light') {
        btn.innerHTML = '<i class="fa-solid fa-moon"></i>';
    } else {
        btn.innerHTML = '<i class="fa-solid fa-sun"></i>';
    }
}

// Session Helpers
function handleUserLoginSuccess(user) {
    currentUser = user;
    
    // Set UI elements
    document.getElementById('authModalOverlay').classList.remove('active');
    document.getElementById('appLayout').style.display = 'flex';
    document.getElementById('userNameLabel').innerText = user.name || user.email.split('@')[0];
    document.getElementById('avatarLetter').innerText = (user.name || user.email)[0].toUpperCase();
    document.getElementById('userRoleLabel').innerText = user.role === 'admin' ? 'Administrator' : 'Candidate';

    // Show/Hide Role-based elements
    const candidatesOnly = document.querySelectorAll('.candidate-only');
    const adminsOnly = document.querySelectorAll('.admin-only');
    
    if (user.role === 'admin') {
        candidatesOnly.forEach(el => el.style.display = 'none');
        adminsOnly.forEach(el => el.style.display = 'block');
        document.getElementById('adminNavItem').style.display = 'block';
        switchView('admin');
    } else {
        candidatesOnly.forEach(el => el.style.display = 'flex');
        adminsOnly.forEach(el => el.style.display = 'none');
        document.getElementById('adminNavItem').style.display = 'none';
        
        // Load profile metrics
        loadProfileMetrics();
        switchView('explore');
    }
    
    showToast(`Welcome back, ${user.name || 'User'}!`);
}

function showAuthModal(show = true) {
    const overlay = document.getElementById('authModalOverlay');
    if (show) {
        overlay.classList.add('active');
        document.getElementById('appLayout').style.display = 'none';
    } else {
        overlay.classList.remove('active');
    }
}

// Toggle login vs register mode in modal
function toggleAuthMode(toRegister = true) {
    isRegisterMode = toRegister;
    const title = document.getElementById('authModalTitle');
    const subtitle = document.getElementById('authModalSubtitle');
    const submitBtn = document.getElementById('authSubmitBtn');
    const toggleMsg = document.getElementById('authToggleMessage');
    const roleGroup = document.getElementById('regRoleGroup');
    
    if (toRegister) {
        title.innerText = "Create Account";
        subtitle.innerText = "Join the PM Internship Scheme recommendation engine.";
        submitBtn.innerText = "Register Now";
        roleGroup.style.display = "block";
        toggleMsg.innerHTML = 'Already have an account? <span onclick="toggleAuthMode(false)">Sign In Instead</span>';
    } else {
        title.innerText = "Welcome Back";
        subtitle.innerText = "Sign in to search & match internships under the PM Scheme.";
        submitBtn.innerText = "Sign In";
        roleGroup.style.display = "none";
        toggleMsg.innerHTML = 'Don\'t have an account? <span onclick="toggleAuthMode(true)">Sign Up Now</span>';
    }
}

// Auth submission
async function handleAuthSubmit(e) {
    e.preventDefault();
    const email = document.getElementById('authEmail').value.trim();
    const password = document.getElementById('authPassword').value;
    
    if (isRegisterMode) {
        const role = document.getElementById('authRole').value;
        const res = await API.register(email, password, role);
        if (res.error) {
            showToast(res.error, 'danger');
        } else {
            showToast("Registration successful! Logging in...", 'success');
            // Auto login after signup
            const loginRes = await API.login(email, password);
            if (loginRes.data) {
                handleUserLoginSuccess(loginRes.data.user);
            }
        }
    } else {
        const res = await API.login(email, password);
        if (res.error) {
            showToast(res.error, 'danger');
        } else {
            handleUserLoginSuccess(res.data.user);
        }
    }
}

// Logout
async function triggerLogout() {
    const res = await API.logout();
    if (res.error) {
        showToast(res.error, 'danger');
    } else {
        currentUser = null;
        destroyAllCharts();
        showToast("Logged out successfully");
        // Clear forms
        document.getElementById('authEmail').value = '';
        document.getElementById('authPassword').value = '';
        toggleAuthMode(false);
        showAuthModal(true);
    }
}

// Tab/View navigation router
function switchView(viewName) {
    currentView = viewName;
    
    // Manage sidebar link active states
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        if (item.getAttribute('data-view') === viewName) {
            item.classList.add('active');
        } else {
            item.classList.remove('active');
        }
    });

    // Switch visible panels
    const panels = document.querySelectorAll('.view-panel');
    panels.forEach(p => p.classList.remove('active'));
    
    const targetPanel = document.getElementById(`view-${viewName}`);
    if (targetPanel) {
        targetPanel.classList.add('active');
    }

    // Set header Title text
    const titleLabel = document.getElementById('currentViewTitle');
    const titles = {
        explore: 'Explore Internships',
        recommendations: 'AI Recommendation Match Engine',
        profile: 'Candidate Profile & Portfolio Insights',
        saved: 'My Saved & Tracked Internships',
        admin: 'Admin Operations & System Analytics',
        details: 'Internship Information & Skill Roadmap'
    };
    titleLabel.innerText = titles[viewName] || 'Internship Portal';

    // View specific loading routines
    if (viewName === 'explore') {
        performSearch();
    } else if (viewName === 'recommendations') {
        loadRecommendations();
    } else if (viewName === 'profile') {
        loadProfileFormDetails();
    } else if (viewName === 'saved') {
        loadSavedAndApplied();
    } else if (viewName === 'admin') {
        loadAdminStats();
    }
}

// Skeleton loaders
function getSkeletonHTML(count = 3) {
    let html = '';
    for (let i = 0; i < count; i++) {
        html += `
            <div class="internship-card" style="opacity: 0.7;">
                <div class="card-top">
                    <div class="company-branding">
                        <div class="company-logo skeleton-loader"></div>
                        <div class="job-info">
                            <div class="skeleton-title skeleton-loader"></div>
                            <div class="skeleton-text skeleton-loader" style="width: 100px;"></div>
                        </div>
                    </div>
                </div>
                <div class="skeleton-text skeleton-loader"></div>
                <div class="skeleton-text skeleton-loader" style="width: 80%;"></div>
                <div class="card-actions">
                    <div class="skeleton-loader" style="height: 30px; width: 80px; border-radius: 6px;"></div>
                    <div class="skeleton-loader" style="height: 30px; width: 100px; border-radius: 6px;"></div>
                </div>
            </div>
        `;
    }
    return html;
}

// ----------------------------------------------------
// EXPLORE & SEARCH PANEL
// ----------------------------------------------------
function handleSearchKey(e) {
    if (e.key === 'Enter') {
        performSearch();
    }
}

async function performSearch() {
    const grid = document.getElementById('exploreGrid');
    grid.innerHTML = getSkeletonHTML(3);
    
    // Gather params
    const query = document.getElementById('searchInput').value.trim();
    const duration = document.getElementById('filterDuration').value;
    const location = document.getElementById('filterLocation').value.trim();
    const industry = document.getElementById('filterIndustry').value.trim();
    const sort = document.getElementById('sortSelect').value;
    
    // Gather mode checkbox array
    const modeCheckboxes = document.querySelectorAll('input[name="mode"]:checked');
    let mode = '';
    if (modeCheckboxes.length === 1) {
        mode = modeCheckboxes[0].value;
    }
    
    const params = {};
    if (query) params.q = query;
    if (mode) params.mode = mode;
    if (duration) params.duration = duration;
    if (location) params.location = location;
    if (industry) params.industry = industry;
    if (sort) params.sort = sort;

    const res = await API.getInternships(params);
    if (res.error) {
        showToast(res.error, 'danger');
        grid.innerHTML = `<div class="empty-state"><i class="fa-solid fa-triangle-exclamation empty-state-icon"></i><div class="empty-state-title">Search Failed</div><p class="empty-state-desc">${res.error}</p></div>`;
        return;
    }

    currentInternships = res.data;
    document.getElementById('listingsCountLabel').innerText = `Showing ${currentInternships.length} internships`;

    if (currentInternships.length === 0) {
        grid.innerHTML = `
            <div class="empty-state">
                <i class="fa-solid fa-magnifying-glass empty-state-icon"></i>
                <div class="empty-state-title">No Internships Found</div>
                <p class="empty-state-desc">Try clearing your filters or testing other search keywords.</p>
            </div>
        `;
        return;
    }

    renderExploreGrid(currentInternships, 'exploreGrid');
}

function renderExploreGrid(items, elementId) {
    const grid = document.getElementById(elementId);
    grid.innerHTML = '';

    items.forEach(inst => {
        const isCandidate = currentUser && currentUser.role === 'candidate';
        
        // Determine badge style
        let badgeClass = 'match-low';
        if (inst.match_score >= 75) badgeClass = 'match-high';
        else if (inst.match_score >= 50) badgeClass = 'match-med';

        // Render bookmark icon state
        const saveIcon = inst.status === 'saved' || inst.status === 'applied' 
            ? 'fa-solid fa-bookmark' 
            : 'fa-regular fa-bookmark';

        const actionButtons = isCandidate ? `
            <button class="btn btn-secondary btn-sm" onclick="toggleSave(${inst.id}, event)" id="bookmarkBtn-${elementId}-${inst.id}" title="Save Internship">
                <i class="${saveIcon}"></i>
            </button>
            <button class="btn btn-primary btn-sm" onclick="viewInternshipDetails(${inst.id})">
                <i class="fa-solid fa-circle-info"></i> View Match Analysis
            </button>
        ` : `
            <button class="btn btn-primary btn-sm" onclick="viewInternshipDetails(${inst.id})" style="width: 100%;">
                <i class="fa-solid fa-eye"></i> View Details
            </button>
        `;

        const skillsTags = inst.required_skills.slice(0, 4).map(skill => {
            return `<span class="skill-tag">${skill}</span>`;
        }).join('');

        const card = document.createElement('div');
        card.className = 'internship-card';
        card.innerHTML = `
            <div class="card-top">
                <div class="company-branding">
                    <img class="company-logo" src="${inst.company_logo}" alt="${inst.company_name} logo">
                    <div class="job-info">
                        <div class="job-title" onclick="viewInternshipDetails(${inst.id})">${inst.title}</div>
                        <div class="company-name">${inst.company_name}</div>
                    </div>
                </div>
                ${isCandidate ? `
                    <div class="match-badge ${badgeClass}" title="Recommendation Score based on Profile Similarity">
                        <i class="fa-solid fa-circle-nodes"></i> ${inst.match_score}% Match
                    </div>
                ` : ''}
            </div>

            <p style="font-size: 0.875rem; color: var(--text-secondary); line-height: 1.5; height: 42px; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;">
                ${inst.description}
            </p>

            <div class="job-metadata">
                <div class="metadata-item"><i class="fa-solid fa-location-dot"></i> ${inst.location}</div>
                <div class="metadata-item"><i class="fa-solid fa-house-laptop"></i> ${inst.mode}</div>
                <div class="metadata-item"><i class="fa-solid fa-calendar-days"></i> ${inst.duration} Months</div>
                <div class="metadata-item"><i class="fa-solid fa-indian-rupee-sign"></i> ₹${inst.stipend.toLocaleString()}/mo</div>
            </div>

            <div class="skills-tags">
                ${skillsTags}
            </div>

            <div class="card-actions">
                ${actionButtons}
            </div>
        `;

        grid.appendChild(card);
    });
}

// Toggle save bookmark
async function toggleSave(id, event) {
    if (event) event.stopPropagation();
    
    // Find current status
    const item = currentInternships.find(x => x.id === id);
    let isSave = true;
    if (item && (item.status === 'saved' || item.status === 'applied')) {
        isSave = false;
    }

    const res = await API.toggleSaveInternship(id, isSave);
    if (res.error) {
        showToast(res.error, 'danger');
    } else {
        if (item) {
            item.status = res.data.status;
        }
        showToast(res.data.message);
        
        // Refresh grid
        if (currentView === 'explore') performSearch();
        else if (currentView === 'recommendations') loadRecommendations();
        else if (currentView === 'saved') loadSavedAndApplied();
    }
}

// ----------------------------------------------------
// AI RECOMMENDATIONS
// ----------------------------------------------------
async function loadRecommendations() {
    const grid = document.getElementById('recommendationsGrid');
    grid.innerHTML = getSkeletonHTML(3);

    const res = await API.getRecommendations();
    if (res.error) {
        showToast(res.error, 'danger');
        grid.innerHTML = `<div class="empty-state"><i class="fa-solid fa-triangle-exclamation empty-state-icon"></i><div class="empty-state-title">Calculation Failed</div><p class="empty-state-desc">${res.error}</p></div>`;
        return;
    }

    if (res.data.code === 'PROFILE_INCOMPLETE') {
        grid.innerHTML = `
            <div class="empty-state">
                <i class="fa-solid fa-wand-magic-sparkles empty-state-icon"></i>
                <div class="empty-state-title">Setup Profile to Unlock Recommendations</div>
                <p class="empty-state-desc">We use Scikit-Learn algorithms to compute vector embeddings. Fill out your details to begin.</p>
                <button class="btn btn-primary" onclick="switchView('profile')" style="margin-top: 10px;">Go to Portfolio Dashboard</button>
            </div>
        `;
        return;
    }

    currentInternships = res.data;
    
    if (currentInternships.length === 0) {
        grid.innerHTML = `
            <div class="empty-state">
                <i class="fa-solid fa-hourglass-empty empty-state-icon"></i>
                <div class="empty-state-title">No Opportunities in Database</div>
                <p class="empty-state-desc">Ask system admin to populate internship lists.</p>
            </div>
        `;
        return;
    }

    renderExploreGrid(currentInternships, 'recommendationsGrid');
}

// Export PDF report (Bonus Features)
function exportRecommendationsPDF() {
    if (!currentInternships || !currentInternships.length) {
        showToast("No recommendations loaded to export.", 'warning');
        return;
    }

    const printWindow = window.open('', '_blank');
    const isDarkMode = document.body.getAttribute('data-theme') !== 'light';
    const themeBg = isDarkMode ? '#0B0B0F' : '#FFFFFF';
    const themeText = isDarkMode ? '#F3F4F6' : '#111827';
    const themeCard = isDarkMode ? '#1C1C24' : '#F1F5F9';
    const themeBorder = isDarkMode ? '#262636' : '#E2E8F0';

    let recommendationsHTML = '';
    currentInternships.slice(0, 5).forEach((rec, idx) => {
        recommendationsHTML += `
            <div style="background-color: ${themeCard}; border: 1px solid ${themeBorder}; border-radius: 8px; padding: 20px; margin-bottom: 20px; page-break-inside: avoid;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                    <h3 style="margin: 0; font-size: 1.2rem;">${idx + 1}. ${rec.title}</h3>
                    <span style="font-weight: bold; color: #6366F1; font-size: 1.1rem;">${rec.match_score}% Match</span>
                </div>
                <div style="font-weight: 600; color: #8B5CF6; margin-bottom: 8px;">${rec.company_name} - ${rec.location} (${rec.mode})</div>
                <p style="font-size: 0.9rem; margin-bottom: 12px; line-height: 1.5;">${rec.description}</p>
                <div style="margin-bottom: 10px;">
                    <strong>Required Skills:</strong> ${rec.required_skills.join(', ')}
                </div>
                <div style="background-color: rgba(99, 102, 241, 0.05); padding: 12px; border-radius: 6px; border-left: 3px solid #6366F1;">
                    <strong>Match Reasoning:</strong>
                    <ul style="margin: 6px 0 0 0; padding: 0; font-size: 0.85rem; list-style: none;">
                        ${rec.reasons.map(r => {
                            const isGap = r.toLowerCase().includes('gap') || 
                                          r.toLowerCase().includes('mismatch') || 
                                          r.toLowerCase().includes('complete your profile') ||
                                          r.toLowerCase().includes('not meet');
                            const icon = isGap ? '❌' : '✓';
                            const color = isGap ? '#EF4444' : '#10B981';
                            return `<li style="display: flex; align-items: flex-start; gap: 8px; margin-bottom: 6px;"><span style="color: ${color}; font-weight: bold; flex-shrink: 0;">${icon}</span><span>${r}</span></li>`;
                        }).join('')}
                    </ul>
                </div>
            </div>
        `;
    });

    printWindow.document.write(`
        <html>
        <head>
            <title>AI Internship Recommendation Report</title>
            <style>
                body {
                    font-family: 'Inter', sans-serif;
                    background-color: ${themeBg};
                    color: ${themeText};
                    padding: 40px;
                    line-height: 1.5;
                }
                h1, h2 { font-family: 'Outfit', sans-serif; }
                @media print {
                    body { padding: 0; background-color: #FFF; color: #000; }
                    button { display: none; }
                }
            </style>
        </head>
        <body>
            <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #6366F1; padding-bottom: 15px; margin-bottom: 30px;">
                <div>
                    <h1 style="margin: 0; font-size: 2rem;">AI Career Recommendation Report</h1>
                    <div style="font-size: 0.95rem; color: #8B5CF6;">PM Internship Scheme Intelligent Matching Portal</div>
                </div>
                <button onclick="window.print()" style="background-color: #6366F1; color: white; padding: 10px 20px; border: none; border-radius: 6px; font-weight: bold; cursor: pointer;">
                    Print / Save PDF
                </button>
            </div>
            
            <div style="margin-bottom: 35px;">
                <h2>Candidate Profile Summary</h2>
                <table style="width: 100%; border-collapse: collapse; margin-top: 10px;">
                    <tr>
                        <td style="padding: 8px; border-bottom: 1px solid ${themeBorder}; font-weight: bold; width: 30%;">Full Name:</td>
                        <td style="padding: 8px; border-bottom: 1px solid ${themeBorder};">${currentUser.name || 'User'}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border-bottom: 1px solid ${themeBorder}; font-weight: bold;">Email ID:</td>
                        <td style="padding: 8px; border-bottom: 1px solid ${themeBorder};">${currentUser.email}</td>
                    </tr>
                </table>
            </div>

            <h2>Top AI-Matched Recommendations</h2>
            <div style="margin-top: 20px;">
                ${recommendationsHTML}
            </div>

            <div style="margin-top: 40px; text-align: center; font-size: 0.8rem; color: #9CA3AF; border-top: 1px solid ${themeBorder}; padding-top: 15px;">
                Report compiled autonomously by the AI-Powered Internship Recommendation Engine.
            </div>
        </body>
        </html>
    `);
    
    printWindow.document.close();
}

// ----------------------------------------------------
// PORTFOLIO / CANDIDATE PROFILE PANEL
// ----------------------------------------------------
async function loadProfileMetrics() {
    const res = await API.getCandidateInsights();
    if (res.data) {
        const pct = res.data.completion_percentage;
        document.getElementById('topCompletionBar').style.width = `${pct}%`;
        document.getElementById('topCompletionText').innerText = `${pct}%`;
    }
}

async function loadProfileFormDetails() {
    const res = await API.getProfile();
    if (res.error) {
        showToast(res.error, 'danger');
        return;
    }

    const data = res.data;
    
    // Fill text inputs
    document.getElementById('profileFullName').value = data.full_name;
    document.getElementById('profilePhone').value = data.phone;
    document.getElementById('profileCollege').value = data.college;
    document.getElementById('profileEduLevel').value = data.education_level || 'Undergraduate';
    document.getElementById('profileDegree').value = data.degree;
    document.getElementById('profileBranch').value = data.branch;
    document.getElementById('profileGradYear').value = data.graduation_year;
    document.getElementById('profileCgpa').value = data.cgpa;
    document.getElementById('profileSkills').value = data.skills.join(', ');
    document.getElementById('profileInterests').value = data.interests.join(', ');
    document.getElementById('profilePrefIndustry').value = data.preferred_industry;
    document.getElementById('profilePrefLocation').value = data.preferred_location;

    // Render insights block on right side
    renderPortfolioInsights();
}

async function saveProfileForm(e) {
    if (e) e.preventDefault();

    const profileData = {
        full_name: document.getElementById('profileFullName').value.trim(),
        phone: document.getElementById('profilePhone').value.trim(),
        college: document.getElementById('profileCollege').value.trim(),
        education_level: document.getElementById('profileEduLevel').value,
        degree: document.getElementById('profileDegree').value.trim(),
        branch: document.getElementById('profileBranch').value.trim(),
        graduation_year: document.getElementById('profileGradYear').value,
        cgpa: document.getElementById('profileCgpa').value,
        skills: document.getElementById('profileSkills').value.split(',').map(s => s.trim()).filter(s => s),
        interests: document.getElementById('profileInterests').value.split(',').map(i => i.trim()).filter(i => i),
        preferred_industry: document.getElementById('profilePrefIndustry').value.trim(),
        preferred_location: document.getElementById('profilePrefLocation').value.trim()
    };

    const res = await API.updateProfile(profileData);
    if (res.error) {
        showToast(res.error, 'danger');
    } else {
        showToast("Profile details updated successfully!");
        loadProfileMetrics();
        renderPortfolioInsights();
    }
}

// Portfolio/Insights renderer
async function renderPortfolioInsights() {
    const box = document.getElementById('insightsContent');
    box.innerHTML = '<div class="skeleton-text skeleton-loader"></div><div class="skeleton-text skeleton-loader" style="width: 60%"></div>';

    const res = await API.getCandidateInsights();
    if (res.error) {
        box.innerHTML = `<p style="color: var(--text-secondary); font-size: 0.875rem;">Error loading insights details.</p>`;
        return;
    }

    const data = res.data;
    
    const topSkillsHTML = data.top_skills.length ? data.top_skills.map(s => `
        <span class="skill-tag matched" style="margin-right: 6px; margin-bottom: 6px; display: inline-block;">${s}</span>
    `).join('') : '<span style="color: var(--text-muted); font-size: 0.85rem;">None added yet.</span>';

    const weakSkillsHTML = data.weak_skills.length ? data.weak_skills.map(s => `
        <span class="skill-tag" style="margin-right: 6px; margin-bottom: 6px; display: inline-block; background-color: rgba(239, 68, 68, 0.08); color: var(--danger); border-color: rgba(239, 68, 68, 0.15);">${s}</span>
    `).join('') : '<span style="color: var(--success); font-size: 0.85rem; font-weight: 500;">✓ Excellent! No skill gaps found.</span>';

    const domainsHTML = data.suggested_domains.map(d => `
        <div style="font-size: 0.85rem; padding: 6px 10px; background-color: var(--bg-input); border-radius: 6px; margin-bottom: 8px; border-left: 3px solid var(--primary);">
            <strong>${d}</strong>
        </div>
    `).join('');

    const resourcesHTML = data.recommended_skills.length ? data.recommended_skills.slice(0, 3).map(r => `
        <div style="font-size: 0.8rem; margin-bottom: 10px;">
            <div style="font-weight: 600; display: flex; justify-content: space-between;">
                <span>${r.skill} Courses</span>
                <span style="color: var(--primary);">${r.hours} hrs</span>
            </div>
            <a href="${r.url}" target="_blank" style="color: var(--text-secondary); text-decoration: none; display: block; font-size: 0.75rem;">
                <i class="fa-solid fa-graduation-cap"></i> ${r.course} (${r.platform})
            </a>
        </div>
    `).join('') : '<span style="color: var(--text-muted); font-size: 0.85rem;">No missing skills matching available openings.</span>';

    box.innerHTML = `
        <div style="margin-bottom: 20px;">
            <div style="font-size: 0.85rem; color: var(--text-muted); font-weight: 600; margin-bottom: 8px;">Top Identified Skills</div>
            <div>${topSkillsHTML}</div>
        </div>

        <div style="margin-bottom: 20px;">
            <div style="font-size: 0.85rem; color: var(--text-muted); font-weight: 600; margin-bottom: 8px;">Weak Skills / Gaps</div>
            <div>${weakSkillsHTML}</div>
        </div>

        <div style="margin-bottom: 20px;">
            <div style="font-size: 0.85rem; color: var(--text-muted); font-weight: 600; margin-bottom: 10px;">Suggested Domains</div>
            <div>${domainsHTML}</div>
        </div>

        <div style="margin-bottom: 10px;">
            <div style="font-size: 0.85rem; color: var(--text-muted); font-weight: 600; margin-bottom: 10px;">Quick Learning Resources</div>
            <div>${resourcesHTML}</div>
        </div>
    `;
}

// Progress animation helper for resume scan
function animateProgress(statusEl, progressBarFillEl, progressContainerEl) {
    progressContainerEl.style.display = 'block';
    progressBarFillEl.style.width = '0%';
    
    const steps = [
        { label: 'Uploading Resume...', target: 15 },
        { label: 'Extracting Text...', target: 40 },
        { label: 'Analyzing Resume...', target: 70 },
        { label: 'Normalizing Skills...', target: 90 },
        { label: 'Preparing Autofill...', target: 95 }
    ];
    
    let currentStepIdx = 0;
    let currentProgress = 0;
    
    statusEl.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> ${steps[0].label}`;
    
    const interval = setInterval(() => {
        if (currentStepIdx >= steps.length) {
            clearInterval(interval);
            return;
        }
        
        const step = steps[currentStepIdx];
        if (currentProgress < step.target) {
            currentProgress += 1;
            progressBarFillEl.style.width = `${currentProgress}%`;
        } else {
            currentStepIdx += 1;
            if (currentStepIdx < steps.length) {
                statusEl.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> ${steps[currentStepIdx].label}`;
            }
        }
    }, 150);
    
    return {
        complete() {
            clearInterval(interval);
            progressBarFillEl.style.width = '100%';
            statusEl.innerHTML = '<i class="fa-solid fa-circle-check" style="color: var(--success);"></i> Analysis complete!';
            setTimeout(() => {
                progressContainerEl.style.display = 'none';
            }, 1000);
        },
        fail() {
            clearInterval(interval);
            progressBarFillEl.style.width = '0%';
            progressContainerEl.style.display = 'none';
        }
    };
}

let parsedDataToApply = null;

function openAutofillPreviewModal(parsedData) {
    parsedDataToApply = parsedData;
    const container = document.getElementById('autofillFieldsContainer');
    container.innerHTML = '';
    
    // Define the form inputs mapping
    const fieldDefinitions = [
        { key: 'full_name', label: 'Full Name', inputId: 'profileFullName', type: 'string' },
        { key: 'phone', label: 'Phone Number', inputId: 'profilePhone', type: 'string' },
        { key: 'college', label: 'College Name', inputId: 'profileCollege', type: 'string' },
        { key: 'education_level', label: 'Education Level', inputId: 'profileEduLevel', type: 'select' },
        { key: 'degree', label: 'Degree', inputId: 'profileDegree', type: 'string' },
        { key: 'branch', label: 'Branch / Stream', inputId: 'profileBranch', type: 'string' },
        { key: 'graduation_year', label: 'Graduation Year', inputId: 'profileGradYear', type: 'string' },
        { key: 'cgpa', label: 'CGPA / Percentage', inputId: 'profileCgpa', type: 'number' },
        { key: 'skills', label: 'Skills', inputId: 'profileSkills', type: 'array' },
        { key: 'interests', label: 'Interests', inputId: 'profileInterests', type: 'array' },
        { key: 'location', label: 'Preferred Location', inputId: 'profilePrefLocation', type: 'string' },
        { key: 'target_role', label: 'Preferred Industry', inputId: 'profilePrefIndustry', type: 'string' }
    ];
    
    let hasChanges = false;
    
    fieldDefinitions.forEach(field => {
        let detected = parsedData[field.key];
        
        let val = "";
        let confidence = 1.0;
        
        if (detected && typeof detected === 'object' && 'confidence' in detected) {
            val = detected.value;
            confidence = detected.confidence;
        } else {
            val = detected || "";
            confidence = parsedData[field.key + '_conf'] !== undefined ? parsedData[field.key + '_conf'] : 0.85;
        }
        
        if (val === null || val === undefined || val === "" || (Array.isArray(val) && val.length === 0)) {
            return;
        }
        
        // Get current form input value
        let current = "";
        const inputEl = document.getElementById(field.inputId);
        if (inputEl) {
            current = inputEl.value.trim();
        }
        
        let displayCurrent = current || "(blank)";
        let displayDetected = "";
        let rawDetectedValue = "";
        
        if (field.type === 'array') {
            const arr = Array.isArray(val) ? val : [];
            displayDetected = arr.join(', ');
            
            if (field.key === 'skills') {
                // For skills: REPLACE the current skills with the new parsed skills (user request)
                rawDetectedValue = arr.join(', ');
                
                const currentArr = current.split(',').map(s => s.trim()).filter(s => s);
                const newArr = arr.map(s => s.trim()).filter(s => s);
                
                if (currentArr.length === newArr.length && currentArr.every(x => newArr.includes(x))) {
                    return;
                }
            } else {
                // For other arrays (like interests): MERGE them
                const currentArr = current.split(',').map(s => s.trim()).filter(s => s);
                const mergedSet = new Set(currentArr);
                arr.forEach(item => mergedSet.add(item));
                rawDetectedValue = Array.from(mergedSet).join(', ');
                
                if (currentArr.length === mergedSet.size && currentArr.every(x => mergedSet.has(x))) {
                    return;
                }
            }
        } else {
            displayDetected = String(val);
            rawDetectedValue = String(val);
            
            if (current.toLowerCase() === displayDetected.toLowerCase()) {
                return;
            }
        }
        
        hasChanges = true;
        
        const isHighConf = confidence >= 0.70;
        const isChecked = isHighConf ? "checked" : "";
        const confPercent = Math.round(confidence * 100);
        
        const row = document.createElement('div');
        row.className = 'autofill-comparison-row';
        row.innerHTML = `
            <div class="comparison-header">
                <label class="comparison-field-label">
                    <input type="checkbox" id="applyField-${field.key}" data-field="${field.key}" data-input-id="${field.inputId}" data-value="${encodeURIComponent(rawDetectedValue)}" ${isChecked} style="width: 18px; height: 18px; accent-color: var(--primary); cursor: pointer;">
                    <span>${field.label}</span>
                </label>
                <div class="comparison-badge-container">
                    <span class="confidence-badge ${isHighConf ? 'confidence-high' : 'confidence-low'}">
                        ${confPercent}% Confidence
                    </span>
                </div>
            </div>
            
            <div class="comparison-values-grid">
                <div class="comparison-val-block">
                    <span class="val-title">Current Profile Value</span>
                    <span class="val-content" title="${displayCurrent}">${displayCurrent}</span>
                </div>
                <div class="val-arrow">
                    <i class="fa-solid fa-right-long"></i>
                </div>
                <div class="comparison-val-block">
                    <span class="val-title">New Detected Value</span>
                    <span class="val-content detected" title="${displayDetected}">${displayDetected}</span>
                </div>
            </div>
            
            ${!isHighConf ? `
                <div class="low-confidence-warning">
                    <i class="fa-solid fa-triangle-exclamation"></i> Verified with lower confidence. Double check details and verify checkbox before applying.
                </div>
            ` : ''}
        `;
        container.appendChild(row);
    });
    
    if (!hasChanges) {
        container.innerHTML = `
            <div class="empty-state" style="padding: 40px 20px;">
                <i class="fa-solid fa-circle-check empty-state-icon" style="color: var(--success); opacity: 1;"></i>
                <div class="empty-state-title">Profile is Up to Date</div>
                <p class="empty-state-desc">The resume contains the same information currently on your profile.</p>
            </div>
        `;
    }
    
    document.getElementById('autofillPreviewModalOverlay').classList.add('active');
}

function closeAutofillModal() {
    document.getElementById('autofillPreviewModalOverlay').classList.remove('active');
}

async function applySelectedAutofill() {
    const checkboxes = document.querySelectorAll('[id^="applyField-"]:checked');
    let updatedCount = 0;
    
    checkboxes.forEach(cb => {
        const inputId = cb.getAttribute('data-input-id');
        const val = decodeURIComponent(cb.getAttribute('data-value'));
        const inputEl = document.getElementById(inputId);
        if (inputEl) {
            inputEl.value = val;
            updatedCount += 1;
        }
    });
    
    closeAutofillModal();
    
    if (updatedCount > 0) {
        showToast(`Prefilled ${updatedCount} fields! Click "Save Profile Details" to save changes.`, 'success');
        document.getElementById('profileForm').scrollIntoView({ behavior: 'smooth' });
    } else {
        showToast("No fields were updated.", "warning");
    }
}

// AI Resume Upload Handler
async function handleResumeUpload(e) {
    const file = e.target.files[0];
    if (!file) return;

    const statusEl = document.getElementById('resumeStatus');
    const progressBarFillEl = document.getElementById('resumeUploadProgressBar');
    const progressContainerEl = document.getElementById('resumeUploadProgressContainer');
    
    // Start progress loop animation
    const progress = animateProgress(statusEl, progressBarFillEl, progressContainerEl);

    const formData = new FormData();
    formData.append('resume', file);

    const res = await API.uploadResume(formData);
    if (res.error) {
        progress.fail();
        showToast(res.error, 'danger');
        statusEl.innerText = "Parsing failed. Check file size or format.";
    } else {
        progress.complete();
        showToast("Resume parsed and updates extracted successfully!");
        
        // Open comparison and confirm preview
        setTimeout(() => {
            openAutofillPreviewModal(res.data.parsed_data);
        }, 1200);
    }
}

// ----------------------------------------------------
// SAVED & APPLIED INTERNSHIPS
// ----------------------------------------------------
async function loadSavedAndApplied() {
    const savedGrid = document.getElementById('savedGrid');
    const appliedGrid = document.getElementById('appliedGrid');
    
    savedGrid.innerHTML = getSkeletonHTML(1);
    appliedGrid.innerHTML = getSkeletonHTML(1);

    // Fetch saved
    const savedRes = await API.getSavedInternships();
    if (savedRes.data) {
        if (savedRes.data.length === 0) {
            savedGrid.innerHTML = `
                <div class="empty-state" style="padding: 20px;">
                    <div class="empty-state-title" style="font-size: 1rem;">No Saved Listings</div>
                </div>
            `;
        } else {
            renderExploreGrid(savedRes.data, 'savedGrid');
        }
    }

    // Fetch applied
    const appliedRes = await API.getAppliedInternships();
    if (appliedRes.data) {
        if (appliedRes.data.length === 0) {
            appliedGrid.innerHTML = `
                <div class="empty-state" style="padding: 20px;">
                    <div class="empty-state-title" style="font-size: 1rem;">No Submitted Applications</div>
                </div>
            `;
        } else {
            appliedGrid.innerHTML = '';
            appliedRes.data.forEach(app => {
                const card = document.createElement('div');
                card.className = 'internship-card';
                card.style.flexDirection = 'row';
                card.style.justifyContent = 'space-between';
                card.style.alignItems = 'center';
                card.style.padding = '16px 20px';
                
                card.innerHTML = `
                    <div style="display: flex; align-items: center; gap: 16px;">
                        <img class="company-logo" style="width: 36px; height: 36px;" src="${app.company_logo}" alt="logo">
                        <div>
                            <div style="font-weight: 600; font-size: 0.95rem;">${app.title}</div>
                            <div style="font-size: 0.8rem; color: var(--text-secondary);">${app.company_name}</div>
                        </div>
                    </div>
                    
                    <div style="display: flex; gap: 20px; align-items: center; font-size: 0.85rem;">
                        <div style="color: var(--text-muted);"><i class="fa-solid fa-clock"></i> Applied on ${app.applied_at}</div>
                        <span class="match-badge match-high" style="padding: 4px 10px; font-size: 0.75rem;"><i class="fa-solid fa-check-double"></i> Submitted</span>
                    </div>
                `;
                appliedGrid.appendChild(card);
            });
        }
    }
}

// ----------------------------------------------------
// INTERNSHIP DETAILS PANEL
// ----------------------------------------------------
async function viewInternshipDetails(id) {
    switchView('details');
    
    // Set loading skeletons
    document.getElementById('detailCompanyLogo').src = '';
    document.getElementById('detailJobTitle').innerText = 'Loading...';
    document.getElementById('detailCompanyName').innerText = '';
    document.getElementById('detailDescription').innerText = 'Retrieving full details from server...';
    document.getElementById('detailExplainReasons').innerHTML = '<li>Analyzing matching matrices...</li>';
    document.getElementById('detailMissingSkillsTags').innerHTML = '';
    document.getElementById('detailRoadmapSteps').innerHTML = '';

    const res = await API.getInternshipDetail(id);
    if (res.error) {
        showToast(res.error, 'danger');
        switchView('explore');
        return;
    }

    activeInternship = res.data;

    // Fill UI
    document.getElementById('detailCompanyLogo').src = activeInternship.company_logo;
    document.getElementById('detailJobTitle').innerText = activeInternship.title;
    document.getElementById('detailCompanyName').innerText = activeInternship.company_name;
    document.getElementById('detailDescription').innerText = activeInternship.description;
    document.getElementById('detailResponsibilities').innerText = activeInternship.responsibilities || 'Not specified.';
    document.getElementById('detailEligibility').innerText = activeInternship.eligibility_criteria || 'Not specified.';
    document.getElementById('detailMatchPercent').innerText = `${activeInternship.match_score}%`;

    // Metadata Right-bar
    document.getElementById('detailMetaLocation').innerText = activeInternship.location;
    document.getElementById('detailMetaMode').innerText = activeInternship.mode;
    document.getElementById('detailMetaDuration').innerText = `${activeInternship.duration} Months`;
    document.getElementById('detailMetaStipend').innerText = `₹${activeInternship.stipend.toLocaleString()} / month`;
    document.getElementById('detailMetaDeadline').innerText = activeInternship.application_deadline || 'Open';

    // Set buttons state
    updateDetailButtonsState();

    // Render Explainable AI reasons
    const reasonsEl = document.getElementById('detailExplainReasons');
    reasonsEl.innerHTML = '';
    
    if (currentUser && currentUser.role === 'candidate') {
        activeInternship.reasons.forEach(reason => {
            const li = document.createElement('li');
            const isGap = reason.toLowerCase().includes('gap') || 
                          reason.toLowerCase().includes('mismatch') || 
                          reason.toLowerCase().includes('complete your profile') ||
                          reason.toLowerCase().includes('not meet');
            const iconClass = isGap ? 'fa-solid fa-circle-xmark' : 'fa-solid fa-circle-check';
            const iconColor = isGap ? 'var(--danger)' : 'var(--success)';
            li.innerHTML = `<i class="${iconClass}" style="margin-top: 3px; flex-shrink: 0; color: ${iconColor};"></i><span>${reason}</span>`;
            reasonsEl.appendChild(li);
        });
    } else {
        reasonsEl.innerHTML = '<li>Please log in as a student to see match explanations.</li>';
    }

    // Render Missing Skills
    const missingEl = document.getElementById('detailMissingSkillsTags');
    missingEl.innerHTML = '';
    if (activeInternship.missing_skills.length) {
        activeInternship.missing_skills.forEach(skill => {
            const tag = document.createElement('span');
            tag.className = 'skill-tag';
            tag.style.borderColor = 'rgba(239, 68, 68, 0.2)';
            tag.style.color = 'var(--danger)';
            tag.style.backgroundColor = 'rgba(239, 68, 68, 0.05)';
            tag.innerText = skill;
            missingEl.appendChild(tag);
        });
    } else {
        missingEl.innerHTML = '<span style="color: var(--success); font-size: 0.85rem; font-weight: 500;">✓ No missing skills! Your profile possesses all required technologies.</span>';
    }

    // Load Career Roadmap Steps
    loadDetailRoadmapSteps(id);
}

function updateDetailButtonsState() {
    const applyBtn = document.getElementById('detailApplyBtn');
    const saveBtn = document.getElementById('detailSaveBtn');
    
    if (!currentUser || currentUser.role !== 'candidate') {
        applyBtn.style.display = 'none';
        saveBtn.style.display = 'none';
        return;
    } else {
        applyBtn.style.display = 'block';
        saveBtn.style.display = 'block';
    }

    if (activeInternship.status === 'applied') {
        applyBtn.disabled = true;
        applyBtn.innerHTML = '<i class="fa-solid fa-circle-check"></i> Applied successfully';
        saveBtn.style.display = 'none'; // applied already, hide save
    } else {
        applyBtn.disabled = false;
        applyBtn.innerHTML = '<i class="fa-solid fa-paper-plane"></i> Apply for Internship';
        saveBtn.style.display = 'block';
    }

    if (activeInternship.status === 'saved') {
        saveBtn.className = 'btn btn-danger';
        saveBtn.innerHTML = '<i class="fa-solid fa-bookmark"></i> Remove Bookmark';
    } else {
        saveBtn.className = 'btn btn-secondary';
        saveBtn.innerHTML = '<i class="fa-regular fa-bookmark"></i> Bookmark Internship';
    }
}

async function loadDetailRoadmapSteps(internshipId) {
    const box = document.getElementById('detailRoadmapSteps');
    box.innerHTML = '<div class="skeleton-text skeleton-loader"></div><div class="skeleton-text skeleton-loader" style="width: 50%"></div>';

    const res = await API.getRoadmap(internshipId);
    if (res.error) {
        box.innerHTML = `<p style="color: var(--text-secondary); font-size: 0.875rem;">Failed to compute roadmap.</p>`;
        return;
    }

    const data = res.data;
    box.innerHTML = '';
    
    data.roadmap.forEach(step => {
        const stepEl = document.createElement('div');
        stepEl.className = 'roadmap-step';
        
        let metaHTML = '';
        if (step.course_name) {
            metaHTML = `
                <div class="roadmap-meta">
                    <span><i class="fa-solid fa-clock"></i> ${step.hours} Hrs</span>
                    <a href="${step.url}" target="_blank" style="color: var(--primary); text-decoration: none; font-weight: 500;">
                        <i class="fa-solid fa-graduation-cap"></i> ${step.course_name}
                    </a>
                </div>
            `;
        }

        const topicsTags = step.topics ? step.topics.map(t => `<span class="skill-tag" style="font-size: 0.7rem; margin-top: 4px; padding: 2px 6px;">${t}</span>`).join(' ') : '';

        stepEl.innerHTML = `
            <div class="roadmap-week">Week ${step.week}</div>
            <div class="roadmap-title">${step.title}</div>
            <div class="roadmap-desc">${step.description}</div>
            ${metaHTML}
            <div style="margin-top: 6px; display: flex; flex-wrap: wrap; gap: 4px;">
                ${topicsTags}
            </div>
        `;
        box.appendChild(stepEl);
    });
}

// Action button triggers from details panel
async function triggerApply() {
    if (!activeInternship) return;
    
    const confirmed = confirm(`Are you sure you want to apply to ${activeInternship.company_name} for the ${activeInternship.title} position?`);
    if (!confirmed) return;

    const res = await API.applyInternship(activeInternship.id);
    if (res.error) {
        showToast(res.error, 'danger');
    } else {
        showToast(res.data.message);
        activeInternship.status = 'applied';
        updateDetailButtonsState();
    }
}

async function triggerToggleSave() {
    if (!activeInternship) return;
    
    const isSave = activeInternship.status !== 'saved';
    const res = await API.toggleSaveInternship(activeInternship.id, isSave);
    if (res.error) {
        showToast(res.error, 'danger');
    } else {
        showToast(res.data.message);
        activeInternship.status = res.data.status;
        updateDetailButtonsState();
    }
}

// ----------------------------------------------------
// ADMIN DASHBOARD
// ----------------------------------------------------
async function loadAdminStats() {
    const res = await API.getAdminStats();
    if (res.error) {
        showToast(res.error, 'danger');
        return;
    }

    const data = res.data;
    
    // Set counters
    document.getElementById('adminStatUsers').innerText = data.total_users;
    document.getElementById('adminStatInternships').innerText = data.total_internships;
    document.getElementById('adminStatScore').innerText = `${data.average_match_score}%`;

    // Render charts
    initAdminAnalytics(data);

    // Load registered users table
    loadAdminUsersList();
}

async function loadAdminUsersList() {
    const tbody = document.getElementById('adminUsersTableBody');
    tbody.innerHTML = '<tr><td colspan="6" style="text-align: center;">Loading candidate directory...</td></tr>';

    const res = await API.getAdminUsers();
    if (res.error) {
        tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--danger);">${res.error}</td></tr>`;
        return;
    }

    tbody.innerHTML = '';
    if (res.data.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; color: var(--text-secondary);">No student profiles registered yet.</td></tr>';
        return;
    }

    res.data.forEach(user => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td style="font-weight: 600;">${user.name}</td>
            <td>${user.email}</td>
            <td>${user.college}</td>
            <td>${user.degree} (${user.branch})</td>
            <td>${user.cgpa ? user.cgpa.toFixed(1) : 'N/A'}</td>
            <td>${user.created_at}</td>
        `;
        tbody.appendChild(tr);
    });
}

// Add/Edit listing modal forms
function openAddInternshipModal() {
    document.getElementById('internshipModalTitle').innerText = "Add New Internship Opportunity";
    document.getElementById('editInternshipId').value = '';
    document.getElementById('internshipForm').reset();
    document.getElementById('adminInstDeadline').value = new Date().toISOString().split('T')[0];
    document.getElementById('internshipModalOverlay').classList.add('active');
}

function closeInternshipModal() {
    document.getElementById('internshipModalOverlay').classList.remove('active');
}

async function saveInternshipForm(e) {
    e.preventDefault();

    const data = {
        company_name: document.getElementById('adminInstCompany').value.trim(),
        company_logo: document.getElementById('adminInstLogo').value.trim(),
        title: document.getElementById('adminInstTitle').value.trim(),
        stipend: document.getElementById('adminInstStipend').value,
        mode: document.getElementById('adminInstMode').value,
        location: document.getElementById('adminInstLocation').value.trim(),
        duration: document.getElementById('adminInstDuration').value,
        application_deadline: document.getElementById('adminInstDeadline').value,
        category: document.getElementById('adminInstCategory').value.trim(),
        industry: document.getElementById('adminInstIndustry').value.trim(),
        description: document.getElementById('adminInstDesc').value.trim(),
        responsibilities: document.getElementById('adminInstResp').value.trim(),
        required_skills: document.getElementById('adminInstSkills').value.split(',').map(s => s.trim()).filter(s => s),
        degree_requirement: document.getElementById('adminInstDegree').value.trim(),
        branch_requirement: document.getElementById('adminInstBranches').value.split(',').map(b => b.trim()).filter(b => b),
        eligibility_criteria: document.getElementById('adminInstEligibility').value.trim()
    };

    const id = document.getElementById('editInternshipId').value;
    
    let res;
    if (id) {
        res = await API.updateInternship(id, data);
    } else {
        res = await API.addInternship(data);
    }

    if (res.error) {
        showToast(res.error, 'danger');
    } else {
        showToast(id ? "Internship updated successfully!" : "Internship added successfully!");
        closeInternshipModal();
        loadAdminStats();
    }
}
