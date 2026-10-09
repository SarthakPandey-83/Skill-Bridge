/**
 * SIH Platform - Faculty Dashboard JavaScript
 * Handles faculty profile, student insights and opportunities
 */

document.addEventListener('DOMContentLoaded', function() {
    initializeFacultyDashboard();
});

/**
 * Initialize faculty dashboard
 */
async function initializeFacultyDashboard() {
    const userId = sessionStorage.getItem('userId');
    const role = sessionStorage.getItem('role');

    if (!userId || role !== 'faculty') {
        window.location.href = 'index.html';
        return;
    }

    // Set user name
    const userName = localStorage.getItem('sih_user');
    if (userName) {
        const user = JSON.parse(userName);
        document.getElementById('facultyUserName').textContent = user.name;
        document.getElementById('facultyWelcomeName').textContent = user.name.split(' ')[0];
    }

    // Load faculty profile, opportunities and student insights
    await Promise.all([
        loadFacultyProfile(userId),
        loadFacultyOpportunities(),
        loadStudentInsights()
    ]);
}

/**
 * Load faculty profile
 */
async function loadFacultyProfile(userId) {
    try {
        const response = await fetch(`${API_BASE}/api/faculty/profile/${userId}`);
        if (!response.ok) throw new Error('Failed to load profile');

        const profile = await response.json();

        // Display profile info
        document.getElementById('facultyDepartment').textContent = profile.department || '-';
        document.getElementById('facultyDesignation').textContent = profile.designation || '-';
        document.getElementById('facultyExperience').textContent =
            profile.experience_years ? `${profile.experience_years} years` : '-';
        document.getElementById('facultySubjects').textContent =
            (profile.subjects_teaching || []).join(', ') || '-';

        // Display skills and expertise
        const expertiseContainer = document.getElementById('facultyExpertise');
        if (profile.expertise_areas && profile.expertise_areas.length > 0) {
            expertiseContainer.innerHTML = profile.expertise_areas
                .map(s => `<span class="skill-tag">${s}</span>`)
                .join('');
        } else {
            expertiseContainer.innerHTML = '<span class="text-muted">No expertise areas added</span>';
        }

        const skillsContainer = document.getElementById('facultySkills');
        if (profile.skills && profile.skills.length > 0) {
            skillsContainer.innerHTML = profile.skills
                .map(s => `<span class="skill-tag">${s}</span>`)
                .join('');
        } else {
            skillsContainer.innerHTML = '<span class="text-muted">No skills added</span>';
        }

        // Fill edit form with current data
        document.getElementById('editFName').value = profile.name;
        document.getElementById('editFEmail').value = profile.email;
        document.getElementById('editFDepartment').value = profile.department || '';
        document.getElementById('editFDesignation').value = profile.designation || '';
        document.getElementById('editFExperience').value = profile.experience_years || '';
        document.getElementById('editFSubjects').value = (profile.subjects_teaching || []).join(', ');
        document.getElementById('editFExpertise').value = (profile.expertise_areas || []).join(', ');
        document.getElementById('editFSkills').value = (profile.skills || []).join(', ');
        document.getElementById('editFCertifications').value = (profile.certifications || []).join(', ');
        document.getElementById('editFProjects').value = JSON.stringify(profile.research_projects || [], null, 2);

        // Get institute name (institute_id is returned by the faculty profile API)
        const instituteResponse = await fetch(`${API_BASE}/api/institute/${profile.institute_id || 1}`);
        if (instituteResponse.ok) {
            const institute = await instituteResponse.json();
            document.getElementById('editFInstitute').value = institute.name || '';
        }

        // Reset the edit state: save button hidden, editable fields locked
        document.getElementById('saveFacultyBtn').style.display = 'none';
        setFacultyEditFieldsDisabled(true);

    } catch (error) {
        console.error('Error loading faculty profile:', error);
    }
}

/**
 * Enable/disable the faculty profile fields that can be saved through the API.
 * Name, email and institute are identity fields and stay read-only.
 */
function setFacultyEditFieldsDisabled(disabled) {
    const editableFields = [
        'editFDepartment', 'editFDesignation', 'editFExperience', 'editFSubjects',
        'editFExpertise', 'editFSkills', 'editFCertifications', 'editFProjects'
    ];

    editableFields.forEach(id => {
        const field = document.getElementById(id);
        if (field) field.disabled = disabled;
    });
}

/**
 * Enable faculty profile editing
 */
function enableFacultyEdit() {
    setFacultyEditFieldsDisabled(false);
    document.getElementById('saveFacultyBtn').style.display = 'inline-block';

    // The editable fields live in the Profile section, so show it.
    if (typeof switchSection === 'function') {
        switchSection('profile');
    }
}

/**
 * Parse the research projects JSON textarea.
 * Returns an array, or null when the entered text is not valid JSON.
 */
function parseResearchProjects() {
    const raw = (document.getElementById('editFProjects').value || '').trim();
    if (!raw) return [];

    try {
        const parsed = JSON.parse(raw);
        return Array.isArray(parsed) ? parsed : null;
    } catch {
        return null;
    }
}

/**
 * Save faculty profile
 */
async function saveFacultyProfile() {
    const userId = sessionStorage.getItem('userId');

    const profileData = {
        department: document.getElementById('editFDepartment').value || null,
        designation: document.getElementById('editFDesignation').value || null,
        experience_years: document.getElementById('editFExperience').value ?
            parseInt(document.getElementById('editFExperience').value) : null,
        subjects_teaching: document.getElementById('editFSubjects').value.split(',')
            .map(s => s.trim()).filter(s => s),
        expertise_areas: document.getElementById('editFExpertise').value.split(',')
            .map(s => s.trim()).filter(s => s),
        skills: document.getElementById('editFSkills').value.split(',')
            .map(s => s.trim()).filter(s => s),
        certifications: document.getElementById('editFCertifications').value.split(',')
            .map(s => s.trim()).filter(s => s),
        research_projects: parseResearchProjects()
    };

    // Never overwrite saved projects with broken input
    if (profileData.research_projects === null) {
        showError('Research Projects must be valid JSON, for example: [{"title": "...", "funding": "..."}]');
        return;
    }

    try {
        showLoading();

        const response = await fetch(`${API_BASE}/api/faculty/profile/${userId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(profileData)
        });

        if (!response.ok) throw new Error('Failed to save profile');

        hideLoading();
        showSuccess('Profile updated successfully!');

        // Reload profile (this also re-locks the fields)
        await loadFacultyProfile(userId);

    } catch (error) {
        hideLoading();
        showError('Failed to save profile');
    }
}

/**
 * Load faculty opportunities (for sharing with students)
 */
async function loadFacultyOpportunities(filterType = '') {
    showLoadingOnElement('facultyOpportunitiesList');

    try {
        let url = `${API_BASE}/api/opportunities`;
        if (filterType) {
            url += `?type=${filterType}`;
        }

        const response = await fetch(url);
        if (!response.ok) throw new Error('Failed to load opportunities');

        const opportunities = await response.json();
        hideLoading();

        // Update stat
        document.getElementById('statActiveOpportunities').textContent = opportunities.length;

        if (opportunities.length > 0) {
            document.getElementById('facultyOpportunitiesList').innerHTML = opportunities
                .slice(0, 5)
                .map(opp => createOpportunityCard(opp))
                .join('');
        } else {
            document.getElementById('facultyOpportunitiesList').innerHTML =
                '<p class="text-muted">No opportunities posted yet</p>';
        }

    } catch (error) {
        console.error('Error loading opportunities:', error);
        hideLoading();
        const list = document.getElementById('facultyOpportunitiesList');
        if (list) {
            list.innerHTML = '<p class="text-muted">Unable to load opportunities. Please try again.</p>';
        }
    }
}

/**
 * Load student skill insights for the faculty's institute.
 * Uses the existing institute analytics endpoint, which reports the skill
 * gaps (high industry demand, low student supply) and the most demanded skills.
 */
async function loadStudentInsights() {
    const userId = sessionStorage.getItem('userId');
    const insightBlocks = ['skillGapTrends', 'industryRequiredSkills', 'curriculumRecommendations'];

    try {
        // The logged-in user record holds the institute id
        const userResponse = await fetch(`${API_BASE}/api/auth/me/${userId}`);
        const user = await userResponse.json();

        if (!user.institute_id) {
            insightBlocks.forEach(id => {
                const el = document.getElementById(id);
                if (el) el.innerHTML = '<p class="text-muted">No institute data available</p>';
            });
            return;
        }

        const response = await fetch(`${API_BASE}/api/analytics/institute/analytics/${user.institute_id}`);
        if (!response.ok) throw new Error('Failed to load insights');

        const analytics = await response.json();

        const topSkills = analytics.most_common_skills || [];
        const gaps = analytics.skill_gaps || [];
        const demanded = analytics.industry_demanded_skills || [];

        // --- Dashboard stats ---
        document.getElementById('statDepartmentStudents').textContent = analytics.total_students ?? 0;
        document.getElementById('statTopSkill').textContent = topSkills.length ? topSkills[0].skill : '-';
        document.getElementById('statSkillGaps').textContent = gaps.length;

        // --- Skill gap trends ---
        const gapContainer = document.getElementById('skillGapTrends');
        if (gaps.length > 0) {
            gapContainer.innerHTML = `
                <p class="text-muted mb-2">Skills with the highest industry demand but the lowest student supply:</p>
                <div class="skills-tags">
                    ${gaps.map(g => `
                        <span class="skill-tag">${g.skill} <small>(gap ${Math.round(g.gap)}%)</small></span>
                    `).join('')}
                </div>
            `;
        } else {
            gapContainer.innerHTML = '<p class="text-muted">No significant skill gaps identified for this institute.</p>';
        }

        // --- Industry-required skills ---
        const demandContainer = document.getElementById('industryRequiredSkills');
        if (demanded.length > 0) {
            demandContainer.innerHTML = `
                <p class="text-muted mb-2">Demand score = how often the skill appears in the posted demo opportunities.</p>
                <div class="skills-tags">
                    ${demanded.map(s => `
                        <span class="skill-tag">${s.skill} <small>(demand ${Math.round(s.demand_score)}%)</small></span>
                    `).join('')}
                </div>
            `;
        } else {
            demandContainer.innerHTML = '<p class="text-muted">No industry demand data available.</p>';
        }

        // --- Curriculum recommendations ---
        const recContainer = document.getElementById('curriculumRecommendations');
        if (gaps.length > 0) {
            recContainer.innerHTML = `
                <p class="text-muted mb-3">Suggested teaching focus based on industry demand and current student skills:</p>
                <ul class="recommendation-list">
                    ${gaps.slice(0, 5).map((g, i) => `
                        <li>
                            <i class="fas fa-star"></i>
                            <div>
                                <span class="rec-title">${i + 1}. Strengthen teaching for ${g.skill}</span>
                                <span class="rec-desc">
                                    High industry demand, limited student exposure | Priority: ${g.priority || 'medium'}
                                </span>
                            </div>
                        </li>
                    `).join('')}
                </ul>
            `;
        } else {
            recContainer.innerHTML = '<p class="text-muted">No curriculum changes suggested at the moment.</p>';
        }

    } catch (error) {
        console.error('Error loading insights:', error);
        insightBlocks.forEach(id => {
            const el = document.getElementById(id);
            if (el) el.innerHTML = '<p class="text-muted">Unable to load insights. Please try again.</p>';
        });
    }
}

/**
 * Debounce helper
 */
function debounce(func, delay) {
    let timeout;
    return function(...args) {
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(this, args), delay);
    };
}

/**
 * Debounced opportunities loading (reads the selected type from the filter)
 */
const debounceLoadFacultyOpps = debounce(function() {
    const type = document.getElementById('facultyOppFilter')?.value || '';
    loadFacultyOpportunities(type);
}, 300);

// Expose functions
window.loadFacultyOpportunities = loadFacultyOpportunities;
window.loadStudentInsights = loadStudentInsights;
window.enableFacultyEdit = enableFacultyEdit;
window.saveFacultyProfile = saveFacultyProfile;
window.debounceLoadFacultyOpps = debounceLoadFacultyOpps;
