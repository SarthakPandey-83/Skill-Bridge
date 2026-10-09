/**
 * SIH Platform - Student Dashboard JavaScript
 * Handles student profile, skills, opportunities, and gap analysis
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize student dashboard
    initializeStudentDashboard();
});

/**
 * Initialize student dashboard
 */
async function initializeStudentDashboard() {
    const userId = sessionStorage.getItem('userId');
    const role = sessionStorage.getItem('role');
    
    if (!userId || role !== 'student') {
        window.location.href = 'index.html';
        return;
    }
    
    // Set user name in header
    const userName = localStorage.getItem('sih_user');
    if (userName) {
        const user = JSON.parse(userName);
        document.getElementById('studentUserName').textContent = user.name;
        document.getElementById('studentWelcomeName').textContent = user.name.split(' ')[0];
    }
    
    // Load all data
    await Promise.all([
        loadStudentProfile(userId),
        loadStudentSkills(userId),
        loadStudentOpportunities(),
        loadSkillGapAnalysis(userId)
    ]);
}

/**
 * Load student profile
 */
async function loadStudentProfile(userId) {
    showLoadingOnElement('statTotalSkills');
    
    try {
        const response = await fetch(`${API_BASE}/api/student/profile/${userId}`);
        if (!response.ok) throw new Error('Failed to load profile');
        
        const profile = await response.json();
        
        // Fill profile fields
        document.getElementById('editName').value = profile.name;
        document.getElementById('editEmail').value = profile.email;
        document.getElementById('editBranch').value = profile.branch || '';
        document.getElementById('editCourse').value = profile.course || '';
        document.getElementById('editBatch').value = profile.batch || '';
        document.getElementById('editSemester').value = profile.semester || '';
        document.getElementById('editCareerGoal').value = profile.career_goal || '';
        document.getElementById('editPreferredIndustry').value = profile.preferred_industry || '';
        document.getElementById('editOtherInfo').value = profile.other_info || '';
        
        // Get institute name
        const instituteResponse = await fetch(`${API_BASE}/api/institute/${profile.institute_id || 1}`);
        if (instituteResponse.ok) {
            const institute = await instituteResponse.json();
            document.getElementById('editInstitute').value = institute.name || '';
        }
        
        // Update stats
        const totalSkills = (profile.skills || []).length + (profile.technical_skills || []).length;
        document.getElementById('statTotalSkills').textContent = totalSkills;
        
    } catch (error) {
        console.error('Error loading profile:', error);
        showLoadingOnElement('statTotalSkills', 'Error loading');
    }
}

/**
 * Load student skills
 */
async function loadStudentSkills(userId) {
    try {
        const response = await fetch(`${API_BASE}/api/analytics/student/skills/${userId}`);
        if (!response.ok) throw new Error('Failed to load skills');
        
        const data = await response.json();
        
        // Display skills by category
        const categoriesContainer = document.getElementById('skillsByCategory');
        const categories = data.categories;
        
        if (Object.keys(categories).length > 0) {
            categoriesContainer.innerHTML = Object.entries(categories)
                .map(([category, skills]) => `
                    <div class="skill-category">
                        <h5><i class="fas fa-folder"></i> ${category.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}</h5>
                        <div class="skill-tags">
                            ${skills.map(skill => `<span class="skill-tag">${skill}</span>`).join('')}
                        </div>
                    </div>
                `).join('');
        } else {
            categoriesContainer.innerHTML = '<p class="text-muted">No skills added yet</p>';
        }
        
        // Display all skills
        const allSkillsContainer = document.getElementById('allSkillsList');
        const allSkills = [...(data.skills || []), ...(data.technical_skills || [])];
        
        if (allSkills.length > 0) {
            allSkillsContainer.innerHTML = allSkills
                .map(skill => `<span class="skill-tag"><i class="fas fa-check"></i> ${skill}</span>`)
                .join('');
        } else {
            allSkillsContainer.innerHTML = '<p class="text-muted">No skills added yet. Add your skills to get personalized recommendations.</p>';
        }
        
        // Store for later use
        window.currentSkills = allSkills;
        
    } catch (error) {
        console.error('Error loading skills:', error);
    }
}

/**
 * Enable skill editing
 */
function enableSkillEdit() {
    // Load current skills into edit fields
    fetch(`${API_BASE}/api/student/profile/${sessionStorage.getItem('userId')}`)
        .then(res => res.json())
        .then(profile => {
            document.getElementById('editSkills').value = (profile.skills || []).join(', ');
            document.getElementById('editTechnicalSkills').value = (profile.technical_skills || []).join(', ');
            document.getElementById('skillEditForm').style.display = 'block';
        });
}

/**
 * Save skills
 */
async function saveSkills() {
    const userId = sessionStorage.getItem('userId');
    const skillsText = document.getElementById('editSkills').value;
    const techSkillsText = document.getElementById('editTechnicalSkills').value;
    
    const skills = skillsText.split(',').map(s => s.trim()).filter(s => s);
    const technicalSkills = techSkillsText.split(',').map(s => s.trim()).filter(s => s);
    
    try {
        showLoading();
        
        const response = await fetch(`${API_BASE}/api/student/profile/${userId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                skills: skills,
                technical_skills: technicalSkills
            })
        });
        
        if (!response.ok) throw new Error('Failed to save skills');
        
        hideLoading();
        showSuccess('Skills updated successfully!');
        document.getElementById('skillEditForm').style.display = 'none';
        
        // Reload skills
        await loadStudentSkills(userId);
        
    } catch (error) {
        hideLoading();
        showError('Failed to save skills');
    }
}

/**
 * Load student opportunities
 */
async function loadStudentOpportunities(filterType = '', filterSkills = '') {
    showLoadingOnElement('recentOpportunities');
    
    try {
        let url = `${API_BASE}/api/opportunities`;
        const params = [];
        
        if (filterType) params.push(`type=${filterType}`);
        if (filterSkills) params.push(`skills=${encodeURIComponent(filterSkills)}`);
        
        if (params.length > 0) {
            url += '?' + params.join('&');
        }
        
        const response = await fetch(url);
        if (!response.ok) throw new Error('Failed to load opportunities');
        
        let opportunities = await response.json();
        hideLoading();
        
        // Check which opportunities have quizzes
        opportunities = await Promise.all(opportunities.map(async (opp) => {
            try {
                const quizResponse = await fetch(`${API_BASE}/api/jobs/${opp.id}/quiz`);
                const quizData = await quizResponse.json();
                return { ...opp, has_quiz: quizData.quiz !== null };
            } catch {
                return { ...opp, has_quiz: false };
            }
        }));
        
        // Update count
        document.getElementById('statOpportunities').textContent = opportunities.length;
        
        // Display recent opportunities (limit to 3 for dashboard)
        const recentContainer = document.getElementById('recentOpportunities');
        const recent = opportunities.slice(0, 3);
        
        if (recent.length > 0) {
            recentContainer.innerHTML = recent.map(opp => createOpportunityCard(opp)).join('');
        } else {
            recentContainer.innerHTML = '<p class="text-muted">No opportunities available</p>';
        }
        
        // Display full list
        const listContainer = document.getElementById('opportunitiesList');
        if (listContainer) {
            if (opportunities.length > 0) {
                listContainer.innerHTML = opportunities.map(opp => createOpportunityCard(opp)).join('');
            } else {
                listContainer.innerHTML = '<div class="text-center py-4"><p class="text-muted">No opportunities found matching your criteria</p></div>';
            }
        }
        
    } catch (error) {
        console.error('Error loading opportunities:', error);
        hideLoading();
    }
}

/**
 * Create opportunity card HTML
 */
function createOpportunityCard(opp, isOwn = false) {
    const skillsHtml = (opp.required_skills || []).slice(0, 5).map(skill => 
        `<span class="opportunity-skill">${skill}</span>`
    ).join('');
    
    const isInv = opp.opportunity_type === 'internship';
    const typeClass = isInv ? 'internship' : opp.opportunity_type === 'job' ? 'job' : 
                       opp.opportunity_type === 'event' ? 'event' : 'skill-program';
    
    const deadlineUrgent = isUrgent(opp.deadline);
    const userId = sessionStorage.getItem('userId');
    
    // Check if quiz is available by trying to load it
    const hasQuiz = opp.has_quiz ? true : false;
    
    const actionsHtml = isOwn ? `
        <button class="btn btn-sm btn-outline" style="color: var(--danger); border-color: var(--danger);" 
                onclick="deleteOpportunity(${opp.id})">
            <i class="fas fa-trash"></i>
        </button>
    ` : (`
        <button class="btn btn-sm btn-primary take-quiz-btn" data-opp-id="${opp.id}" 
                onclick="viewOpportunityDetails(${opp.id})" style="display: ${hasQuiz ? 'inline-flex' : 'none'}; margin-right: 8px;">
            <i class="fas fa-clipboard-list"></i> Take Quiz
        </button>
    `);
    
    return `
        <div class="opportunity-card">
            <div class="opportunity-card-header">
                <h4>${opp.title}</h4>
                <span class="opportunity-type ${typeClass}">${opp.opportunity_type.replace('-', ' ')}</span>
                ${hasQuiz ? '<span class="opportunity-type quiz-available"><i class="fas fa-clipboard-check"></i> Quiz Available</span>' : ''}
            </div>
            <div class="opportunity-card-body">
                <div class="opportunity-meta">
                    ${opp.location ? `<span class="meta-item"><i class="fas fa-map-pin"></i> ${opp.location}</span>` : ''}
                    ${opp.mode ? `<span class="meta-item"><i class="fas fa-laptop"></i> ${opp.mode}</span>` : ''}
                    ${opp.stipend ? `<span class="meta-item"><i class="fas fa-indian-rupee-sign"></i> ${opp.stipend}</span>` : ''}
                </div>
                ${skillsHtml ? `<div class="opportunity-skills">${skillsHtml}</div>` : ''}
                ${opp.description ? `<p class="opportunity-description">${opp.description.substring(0, 150)}${opp.description.length > 150 ? '...' : ''}</p>` : ''}
            </div>
            <div class="opportunity-card-footer">
                <span class="company-name"><i class="fas fa-building"></i> ${opp.company_name || 'Company'}</span>
                <div class="opportunity-actions">
                    ${actionsHtml}
                    <span class="opportunity-deadline ${deadlineUrgent ? 'urgent' : ''}">
                        <i class="fas fa-calendar"></i> ${formatDate(opp.deadline)}
                    </span>
                </div>
            </div>
        </div>
    `;
}

/**
 * Load skill gap analysis
 */
async function loadSkillGapAnalysis(userId) {
    showLoadingOnElement('skillGapTableBody');
    
    try {
        const response = await fetch(`${API_BASE}/api/analytics/student/skill-gap/${userId}`);
        if (!response.ok) throw new Error('Failed to load gap analysis');
        
        const data = await response.json();
        hideLoading();
        
        // Update stats
        const matched = data.skill_gaps.filter(g => g.status === 'matched').length;
        const weak = data.skill_gaps.filter(g => g.status === 'weak').length;
        const missing = data.skill_gaps.filter(g => g.status === 'missing').length;
        
        document.getElementById('statMatchedSkills').textContent = matched;
        document.getElementById('statGapSkills').textContent = weak + missing;
        
        document.getElementById('gapMatchedCount').textContent = matched;
        document.getElementById('gapWeakCount').textContent = weak;
        document.getElementById('gapMissingCount').textContent = missing;
        
        // Update gap table
        const tableBody = document.getElementById('skillGapTableBody');
        if (data.skill_gaps.length > 0) {
            tableBody.innerHTML = data.skill_gaps.slice(0, 10).map(gap => {
                const statusClass = gap.status === 'matched' ? 'matched' : 
                                   gap.status === 'weak' ? 'weak' : 'missing';
                const statusIcon = gap.status === 'matched' ? 'fa-check-circle' :
                                  gap.status === 'weak' ? 'fa-exclamation-triangle' : 'fa-times-circle';
                
                return `
                    <tr>
                        <td><strong>${gap.skill_name}</strong></td>
                        <td>
                            <div class="progress" style="width: 80px; height: 8px; background: #e2e8f0; border-radius: 4px; overflow: hidden;">
                                <div style="width: ${Math.min(gap.current_level / 5 * 100, 100)}%; height: 100%; 
                                    background: ${gap.status === 'matched' ? '#10b981' : gap.status === 'weak' ? '#f59e0b' : '#ef4444'}; 
                                    transition: width 0.3s"></div>
                            </div>
                            <small>${gap.current_level.toFixed(1)}/5</small>
                        </td>
                        <td>
                            <div class="progress" style="width: 80px; height: 8px; background: #e2e8f0; border-radius: 4px; overflow: hidden;">
                                <div style="width: ${gap.industry_demand / 5 * 100}%; height: 100%; 
                                    background: #3b82f6; transition: width 0.3s"></div>
                            </div>
                            <small>${gap.industry_demand.toFixed(1)}/5</small>
                        </td>
                        <td>
                            <span class="badge ${Math.abs(gap.gap) < 1 ? 'badge-success' : 
                                gap.gap > 0 ? 'badge-warning' : 'badge-info'}">
                                ${gap.gap > 0 ? '+' : ''}${gap.gap.toFixed(1)}
                            </span>
                        </td>
                        <td>
                            <i class="fas ${statusIcon}" style="color: ${gap.status === 'matched' ? '#10b981' : gap.status === 'weak' ? '#f59e0b' : '#ef4444'}"></i>
                            <span class="ml-1">${gap.status.charAt(0).toUpperCase() + gap.status.slice(1)}</span>
                        </td>
                    </tr>
                `;
            }).join('');
        } else {
            tableBody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">No skill gap data available</td></tr>';
        }
        
        // Update recommendations
        const recsContainer = document.getElementById('learningRecommendations');
        const recommendations = data.recommended_skills || [];
        
        if (recommendations.length > 0) {
            recsContainer.innerHTML = `
                <p class="text-muted mb-3">Based on your profile and industry demand, here are the top skills you should consider learning:</p>
                <ul class="recommendation-list">
                    ${recommendations.slice(0, 5).map((rec, i) => `
                        <li>
                            <i class="fas fa-star"></i>
                            <div>
                                <span class="rec-title">${i + 1}. ${rec.skill}</span>
                                <span class="rec-desc">
                                    ${rec.reason === 'missing' ? 'Not in your profile' : 'Needs improvement'} | 
                                    Category: ${(rec.category || 'general').replace('_', ' ')}
                                </span>
                            </div>
                        </li>
                    `).join('')}
                </ul>
            `;
        } else {
            recsContainer.innerHTML = '<p class="text-muted">Your skills are well aligned with industry requirements! Keep up the good work.</p>';
        }
        
        // Update recommended skills tags on dashboard
        const recSkillsContainer = document.getElementById('recommendedSkillsList');
        if (recommendations.length > 0) {
            recSkillsContainer.innerHTML = recommendations.slice(0, 6).map(rec => 
                `<span class="skill-tag ${rec.reason}"><i class="fas fa-star"></i> ${rec.skill}</span>`
            ).join('');
        } else {
            recSkillsContainer.innerHTML = '<p class="text-muted">No recommendations yet</p>';
        }
        
    } catch (error) {
        console.error('Error loading gap analysis:', error);
        hideLoading();
    }
}

/**
 * Enable profile editing
 */
function enableProfileEdit() {
    const fields = ['editName', 'editEmail', 'editInstitute', 'editBranch', 'editCourse', 
                   'editBatch', 'editSemester', 'editCareerGoal', 'editPreferredIndustry', 'editOtherInfo'];
    
    fields.forEach(id => {
        document.getElementById(id).disabled = false;
    });
    
    document.getElementById('saveProfileBtn').style.display = 'inline-block';
}

/**
 * Cancel profile edit
 */
function cancelProfileEdit() {
    // Reload profile
    loadStudentProfile(sessionStorage.getItem('userId'));
    
    document.getElementById('saveProfileBtn').style.display = 'none';
}

/**
 * Save profile changes
 */
async function saveProfile() {
    const userId = sessionStorage.getItem('userId');
    
    const profileData = {
        branch: document.getElementById('editBranch').value,
        course: document.getElementById('editCourse').value,
        batch: document.getElementById('editBatch').value ? parseInt(document.getElementById('editBatch').value) : null,
        semester: document.getElementById('editSemester').value ? parseInt(document.getElementById('editSemester').value) : null,
        career_goal: document.getElementById('editCareerGoal').value,
        preferred_industry: document.getElementById('editPreferredIndustry').value,
        other_info: document.getElementById('editOtherInfo').value
    };
    
    // Clean up empty strings
    Object.keys(profileData).forEach(key => {
        if (profileData[key] === '' || profileData[key] === null) {
            profileData[key] = null;
        }
    });
    
    try {
        showLoading();
        
        const response = await fetch(`${API_BASE}/api/student/profile/${userId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(profileData)
        });
        
        if (!response.ok) throw new Error('Failed to save profile');
        
        hideLoading();
        showSuccess('Profile updated successfully!');
        
        // Reload profile
        await loadStudentProfile(userId);
        
        // Disable fields again
        cancelProfileEdit();
        
    } catch (error) {
        hideLoading();
        showError('Failed to save profile');
    }
}

/**
 * Enable faculty profile editing
 */
function enableFacultyEdit() {
    // This would be implemented in faculty.js
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
 * Debounced opportunity loading
 */
const debounceLoadOpportunities = debounce(function() {
    const type = document.getElementById('opportunityFilterType')?.value || '';
    const skills = document.getElementById('opportunityFilterSkills')?.value || '';
    loadStudentOpportunities(type, skills);
}, 300);

/**
 * View opportunity details and take quiz
 */
async function viewOpportunityDetails(oppId) {
    const userId = sessionStorage.getItem('userId');
    
    try {
        // Fetch opportunity details
        const oppResponse = await fetch(`${API_BASE}/api/opportunities/${oppId}`);
        if (!oppResponse.ok) throw new Error('Failed to load opportunity');
        
        const opp = await oppResponse.json();
        
        // Fetch quiz if available
        const quizResponse = await fetch(`${API_BASE}/api/jobs/${oppId}/quiz`);
        const quizData = await quizResponse.json();
        
        // Show modal with opportunity details and quiz
        showOpportunityModal(opp, quizData);
        
    } catch (error) {
        console.error('Error loading opportunity details:', error);
        showError('Failed to load opportunity details');
    }
}

/**
 * Show opportunity details modal with quiz
 */
function showOpportunityModal(opp, quizData) {
    // Create modal
    const modal = document.createElement('div');
    modal.className = 'modal active';
    modal.id = 'opportunityModal';
    modal.innerHTML = `
        <div class="modal-content opportunity-modal">
            <div class="modal-header">
                <h2>${opp.title}</h2>
                <button class="modal-close" onclick="closeOpportunityModal()">&times;</button>
            </div>
            <div class="modal-body">
                <div class="opp-details">
                    <div class="opp-meta">
                        ${opp.location ? `<div class="meta-item"><i class="fas fa-map-pin"></i> ${opp.location}</div>` : ''}
                        ${opp.mode ? `<div class="meta-item"><i class="fas fa-laptop"></i> ${opp.mode}</div>` : ''}
                        ${opp.stipend ? `<div class="meta-item"><i class="fas fa-indian-rupee-sign"></i> ${opp.stipend}</div>` : ''}
                        ${opp.deadline ? `<div class="meta-item"><i class="fas fa-calendar"></i> Deadline: ${formatDate(opp.deadline)}</div>` : ''}
                    </div>
                    
                    <div class="opp-skills">
                        <h5>Required Skills</h5>
                        <div class="skill-tags">
                            ${(opp.required_skills || []).map(s => `<span class="skill-tag">${s}</span>`).join('')}
                        </div>
                    </div>
                    
                    ${opp.description ? `
                        <div class="opp-description">
                            <h5>Description</h5>
                            <p>${opp.description}</p>
                        </div>
                    ` : ''}
                    
                    ${opp.eligibility ? `
                        <div class="opp-eligibility">
                            <h5>Eligibility</h5>
                            <pre>${JSON.stringify(opp.eligibility, null, 2)}</pre>
                        </div>
                    ` : ''}
                    
                    <div class="opp-company">
                        <h5>Posted by</h5>
                        <p><i class="fas fa-building"></i> ${opp.company_name || 'Company'}</p>
                    </div>
                </div>
                
                ${quizData.quiz ? `
                    <div class="quiz-section">
                        <h3><i class="fas fa-clipboard-list"></i> Skill Assessment Quiz</h3>
                        ${quizData.quiz.description ? `<p class="text-muted">${quizData.quiz.description}</p>` : ''}
                        
                        <div class="quiz-info">
                            <div class="info-item">
                                <span class="info-label">Questions</span>
                                <span class="info-value">${quizData.quiz.question_count}</span>
                            </div>
                            <div class="info-item">
                                <span class="info-label">Passing Score</span>
                                <span class="info-value">${quizData.quiz.passing_score}%</span>
                            </div>
                            ${quizData.quiz.time_limit_minutes ? `
                                <div class="info-item">
                                    <span class="info-label">Time Limit</span>
                                    <span class="info-value">${quizData.quiz.time_limit_minutes} minutes</span>
                                </div>
                            ` : ''}
                        </div>
                        
                        <div id="quizQuestions" class="quiz-questions">
                            ${quizData.quiz.questions.map((q, i) => `
                                <div class="quiz-question" data-question-id="${q.id}">
                                    <h4>Question ${i + 1}: ${q.question_text}</h4>
                                    <div class="form-group">
                                        <label class="option-label">
                                            <input type="radio" name="question_${q.id}" value="A" class="quiz-option">
                                            <span>A. ${q.option_a}</span>
                                        </label>
                                    </div>
                                    <div class="form-group">
                                        <label class="option-label">
                                            <input type="radio" name="question_${q.id}" value="B" class="quiz-option">
                                            <span>B. ${q.option_b}</span>
                                        </label>
                                    </div>
                                    <div class="form-group">
                                        <label class="option-label">
                                            <input type="radio" name="question_${q.id}" value="C" class="quiz-option">
                                            <span>C. ${q.option_c}</span>
                                        </label>
                                    </div>
                                    <div class="form-group">
                                        <label class="option-label">
                                            <input type="radio" name="question_${q.id}" value="D" class="quiz-option">
                                            <span>D. ${q.option_d}</span>
                                        </label>
                                    </div>
                                    ${q.skill_tag ? `<span class="skill-tag small"><i class="fas fa-tag"></i> ${q.skill_tag}</span>` : ''}
                                </div>
                            `).join('')}
                        </div>
                        
                        <div class="quiz-actions">
                            <button class="btn btn-secondary" onclick="closeOpportunityModal()">Close</button>
                            <button class="btn btn-primary" onclick="submitQuiz(${opp.id})">Submit Quiz</button>
                        </div>
                    </div>
                ` : `
                    <div class="no-quiz-section">
                        <p class="text-muted">No skill assessment quiz available for this opportunity.</p>
                        <button class="btn btn-secondary" onclick="closeOpportunityModal()">Close</button>
                    </div>
                `}
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Close on outside click
    modal.addEventListener('click', function(e) {
        if (e.target === modal) {
            closeOpportunityModal();
        }
    });
}

/**
 * Close opportunity modal
 */
function closeOpportunityModal() {
    const modal = document.getElementById('opportunityModal');
    if (modal) {
        modal.remove();
    }
}

/**
 * Submit quiz attempt
 */
async function submitQuiz(oppId) {
    const userId = sessionStorage.getItem('userId');
    
    // Collect answers
    const questionElements = document.querySelectorAll('.quiz-question');
    const answers = [];
    
    questionElements.forEach(qElement => {
        const questionId = qElement.dataset.questionId;
        const selected = qElement.querySelector('input[name="question_' + questionId + '"]:checked');
        
        if (!selected) {
            showError('Please answer all questions before submitting.');
            return;
        }
        
        answers.push({
            question_id: parseInt(questionId),
            selected_option: selected.value
        });
    });
    
    if (answers.length === 0) {
        showError('Please answer all questions before submitting.');
        return;
    }
    
    try {
        showLoading();
        
        const response = await fetch(`${API_BASE}/api/jobs/${oppId}/quiz/attempt?user_id=${userId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ answers: answers })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to submit quiz');
        }
        
        const result = await response.json();
        hideLoading();
        
        // Show results
        showQuizResults(result);
        
    } catch (error) {
        hideLoading();
        showError(error.message || 'Failed to submit quiz');
    }
}

/**
 * Show quiz results
 */
function showQuizResults(result) {
    const modal = document.getElementById('opportunityModal');
    if (!modal) return;
    
    const passed = result.passed;
    const scoreColor = passed ? '#10b981' : '#ef4444';
    
    modal.querySelector('.modal-body').innerHTML = `
        <div class="quiz-results">
            <h3>Quiz Results</h3>
            
            <div class="result-score" style="background: ${scoreColor}; color: white;">
                <div class="score-value">${result.score_percentage}%</div>
                <div class="score-label">${passed ? 'Passed' : 'Not Passed'}</div>
            </div>
            
            <div class="result-stats">
                <div class="stat-item">
                    <span class="stat-value">${result.correct_answers}</span>
                    <span class="stat-label">Correct Answers</span>
                </div>
                <div class="stat-item">
                    <span class="stat-value">${result.total_questions}</span>
                    <span class="stat-label">Total Questions</span>
                </div>
            </div>
            
            ${result.skill_scores && result.skill_scores.length > 0 ? `
                <div class="skill-scores">
                    <h4>Performance by Skill</h4>
                    <div class="skill-score-list">
                        ${result.skill_scores.map(skill => `
                            <div class="skill-score-item">
                                <span class="skill-name">${skill.skill_tag}</span>
                                <div class="progress" style="flex: 1;">
                                    <div style="width: ${skill.percentage}%; height: 8px; background: ${skill.percentage >= 60 ? '#10b981' : skill.percentage >= 40 ? '#f59e0b' : '#ef4444'};"></div>
                                </div>
                                <span class="skill-score">${skill.percentage}%</span>
                            </div>
                        `).join('')}
                    </div>
                </div>
            ` : ''}
            
            <div class="result-actions">
                <button class="btn btn-primary" onclick="window.location.href = 'student.html';">Back to Dashboard</button>
                <button class="btn btn-secondary" onclick="closeOpportunityModal()">Close</button>
            </div>
        </div>
    `;
}

// Expose functions
window.loadStudentOpportunities = loadStudentOpportunities;
window.debounceLoadOpportunities = debounceLoadOpportunities;
window.viewOpportunityDetails = viewOpportunityDetails;
window.closeOpportunityModal = closeOpportunityModal;
window.submitQuiz = submitQuiz;
