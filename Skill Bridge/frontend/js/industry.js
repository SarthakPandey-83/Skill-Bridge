/**
 * SIH Platform - Industry Dashboard JavaScript
 * Handles company profile, opportunities, and talent analytics
 */

document.addEventListener('DOMContentLoaded', function() {
    initializeIndustryDashboard();
    setupSkillSuggestions();
});

/**
 * Initialize industry dashboard
 */
async function initializeIndustryDashboard() {
    const userId = sessionStorage.getItem('userId');
    const role = sessionStorage.getItem('role');
    
    if (!userId || role !== 'industry') {
        window.location.href = 'index.html';
        return;
    }
    
    const userName = localStorage.getItem('sih_user');
    if (userName) {
        const user = JSON.parse(userName);
        document.getElementById('industryUserName').textContent = user.name;
    }
    
    // Load all data
    await Promise.all([
        loadIndustryProfile(userId),
        loadMyOpportunities(userId),
        loadTalentAnalytics()
    ]);
}

/**
 * Load industry/company profile
 */
async function loadIndustryProfile(userId) {
    try {
        const response = await fetch(`${API_BASE}/api/industry/profile/${userId}`);
        if (!response.ok) throw new Error('Failed to load profile');
        
        const profile = await response.json();
        
        // Display profile info
        document.getElementById('editCompanyName').value = profile.company_name || '';
        document.getElementById('editIndustryType').value = profile.industry_type || '';
        document.getElementById('editLocation').value = profile.location || '';
        document.getElementById('editSize').value = profile.size || '';
        document.getElementById('editDescription').value = profile.description || '';
        
        // Update company quick info
        const companyInfo = document.getElementById('companyQuickInfo');
        companyInfo.innerHTML = `
            <div class="info-item">
                <span class="info-label">Company</span>
                <span class="info-value"><i class="fas fa-building" style="color: var(--primary-color); margin-right: 8px;"></i>${profile.company_name || '-'}</span>
            </div>
            <div class="info-item">
                <span class="info-label">Industry</span>
                <span class="info-value">${profile.industry_type || '-'}</span>
            </div>
            <div class="info-item">
                <span class="info-label">Location</span>
                <span class="info-value">${profile.location || '-'}</span>
            </div>
            <div class="info-item">
                <span class="info-label">Size</span>
                <span class="info-value">${profile.size || '-'}</span>
            </div>
        `;
        
        // Update posted opportunities count
        document.getElementById('statPostedOpps').textContent = 0; // Will be updated by loadMyOpportunities
        
        // Hide save button
        document.getElementById('saveCompanyBtn').style.display = 'none';
        
    } catch (error) {
        console.error('Error loading industry profile:', error);
    }
}

/**
 * Enable company profile editing
 */
function enableCompanyEdit() {
    const fields = ['editCompanyName', 'editIndustryType', 'editLocation', 'editSize', 'editDescription'];
    
    fields.forEach(id => {
        document.getElementById(id).disabled = false;
    });
    
    document.getElementById('saveCompanyBtn').style.display = 'inline-block';
}

/**
 * Save company profile
 */
async function saveCompanyProfile() {
    const userId = sessionStorage.getItem('userId');
    
    const profileData = {
        company_name: document.getElementById('editCompanyName').value || null,
        industry_type: document.getElementById('editIndustryType').value || null,
        location: document.getElementById('editLocation').value || null,
        size: document.getElementById('editSize').value || null,
        description: document.getElementById('editDescription').value || null
    };
    
    try {
        showLoading();
        
        const response = await fetch(`${API_BASE}/api/industry/profile/${userId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(profileData)
        });
        
        if (!response.ok) throw new Error('Failed to save profile');
        
        hideLoading();
        showSuccess('Company profile updated successfully!');
        
        // Reload profile
        await loadIndustryProfile(userId);
        
        // Disable fields
        document.getElementById('saveCompanyBtn').style.display = 'none';
        
    } catch (error) {
        hideLoading();
        showError('Failed to save profile');
    }
}

/**
 * Post new opportunity
 */
async function postOpportunity() {
    const userId = sessionStorage.getItem('userId');
    
    const title = document.getElementById('newOppTitle').value.trim();
    const type = document.getElementById('newOppType').value;
    const skillsText = document.getElementById('newOppSkills').value;
    const location = document.getElementById('newOppLocation').value.trim();
    const mode = document.getElementById('newOppMode').value;
    const deadline = document.getElementById('newOppDeadline').value;
    const stipend = document.getElementById('newOppStipend').value.trim();
    const description = document.getElementById('newOppDescription').value.trim();
    const eligibilityText = document.getElementById('newOppEligibility').value.trim();
    
    if (!title) {
        showError('Please enter a title for the opportunity');
        return;
    }
    
    // Parse skills
    const skills = skillsText.split(',').map(s => s.trim()).filter(s => s);
    
    // Parse eligibility
    let eligibility = null;
    if (eligibilityText) {
        try {
            eligibility = JSON.parse(eligibilityText);
        } catch (e) {
            showError('Invalid JSON format for eligibility criteria');
            return;
        }
    }
    
    // Get quiz data if provided
    const quizData = getQuizData();
    
    try {
        showLoading();
        
        // First create the opportunity
        const oppResponse = await fetch(`${API_BASE}/api/opportunities?user_id=${userId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                title,
                opportunity_type: type,
                required_skills: skills,
                location: location || null,
                mode: mode || null,
                deadline: deadline || null,
                stipend: stipend || null,
                description: description || null,
                eligibility: eligibility
            })
        });
        
        if (!oppResponse.ok) {
            const error = await oppResponse.json();
            throw new Error(error.detail || 'Failed to post opportunity');
        }
        
        const opp = await oppResponse.json();
        
        // If quiz data provided, create the quiz
        if (quizData && quizData.questions && quizData.questions.length > 0) {
            try {
                const quizResponse = await fetch(`${API_BASE}/api/opportunities/${opp.id}/quiz?user_id=${userId}`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(quizData)
                });
                
                if (!quizResponse.ok) {
                    console.error('Warning: Failed to create quiz:', await quizResponse.json());
                } else {
                    console.log('Quiz created successfully');
                }
            } catch (quizError) {
                console.error('Warning: Quiz creation failed:', quizError);
            }
        }
        
        hideLoading();
        
        showSuccess('Opportunity posted successfully!');
        
        // Clear form
        document.getElementById('newOppTitle').value = '';
        document.getElementById('newOppSkills').value = '';
        document.getElementById('newOppLocation').value = '';
        document.getElementById('newOppMode').value = '';
        document.getElementById('newOppDeadline').value = '';
        document.getElementById('newOppStipend').value = '';
        document.getElementById('newOppDescription').value = '';
        document.getElementById('newOppEligibility').value = '';
        
        // Reset quiz editor
        resetQuizEditor();
        
        // Reload opportunities
        await loadMyOpportunities(userId);
        await loadTalentAnalytics();
        
    } catch (error) {
        hideLoading();
        showError(error.message || 'Failed to post opportunity');
    }
}

/**
 * Toggle quiz editor visibility
 */
function toggleQuizEditor() {
    const quizEditor = document.getElementById('quizEditor');
    if (quizEditor.style.display === 'none' || quizEditor.style.display === '') {
        quizEditor.style.display = 'block';
    } else {
        quizEditor.style.display = 'none';
    }
}

/**
 * Add a new question to the quiz
 */
function addQuestion() {
    const questionsList = document.getElementById('questionsList');
    
    // Remove empty placeholder if exists
    const emptyPlaceholder = questionsList.querySelector('.empty');
    if (emptyPlaceholder) {
        emptyPlaceholder.remove();
    }
    
    const questionId = `question_${Date.now()}`;
    const questionItem = document.createElement('div');
    questionItem.className = 'question-item';
    questionItem.id = questionId;
    questionItem.innerHTML = `
        <div class="question-header">
            <h5>Question ${questionsList.children.length + 1}</h5>
            <button class="btn btn-icon btn-sm" onclick="removeQuestion('${questionId}')">
                <i class="fas fa-trash"></i>
            </button>
        </div>
        <div class="form-group">
            <label>Question Text</label>
            <textarea class="form-control question-text" rows="2" placeholder="Enter your question..."></textarea>
        </div>
        <div class="form-row">
            <div class="form-group">
                <label>Option A</label>
                <input type="text" class="form-control option-input" data-option="A" placeholder="Option A">
            </div>
            <div class="form-group">
                <label>Option B</label>
                <input type="text" class="form-control option-input" data-option="B" placeholder="Option B">
            </div>
        </div>
        <div class="form-row">
            <div class="form-group">
                <label>Option C</label>
                <input type="text" class="form-control option-input" data-option="C" placeholder="Option C">
            </div>
            <div class="form-group">
                <label>Option D</label>
                <input type="text" class="form-control option-input" data-option="D" placeholder="Option D">
            </div>
        </div>
        <div class="form-row">
            <div class="form-group">
                <label>Correct Answer</label>
                <select class="form-control correct-option">
                    <option value="A">A</option>
                    <option value="B">B</option>
                    <option value="C">C</option>
                    <option value="D">D</option>
                </select>
            </div>
            <div class="form-group">
                <label>Skill Tag (optional)</label>
                <input type="text" class="form-control skill-tag" placeholder="e.g., Python, SQL">
            </div>
            <div class="form-group">
                <label>Difficulty</label>
                <select class="form-control difficulty">
                    <option value="easy">Easy</option>
                    <option value="medium" selected>Medium</option>
                    <option value="hard">Hard</option>
                </select>
            </div>
        </div>
    `;
    
    questionsList.appendChild(questionItem);
}

/**
 * Remove a question from the quiz
 */
function removeQuestion(questionId) {
    const questionElement = document.getElementById(questionId);
    if (questionElement) {
        questionElement.remove();
    }
    
    // Show empty placeholder if no questions
    const questionsList = document.getElementById('questionsList');
    if (questionsList.children.length === 0) {
        questionsList.innerHTML = `
            <div class="question-item empty">
                <p class="text-muted">No questions added yet. Click "Add Question" to start.</p>
            </div>
        `;
    }
}

/**
 * Get quiz data from the form
 */
function getQuizData() {
    const title = document.getElementById('quizTitle').value.trim();
    const passingScore = parseInt(document.getElementById('quizPassingScore').value);
    const timeLimit = parseInt(document.getElementById('quizTimeLimit').value) || null;
    
    if (!title) {
        return null;
    }
    
    const questions = [];
    const questionElements = document.querySelectorAll('#questionsList .question-item:not(.empty)');
    
    questionElements.forEach(qElement => {
        const questionText = qElement.querySelector('.question-text').value.trim();
        if (!questionText) return;
        
        const options = {};
        qElement.querySelectorAll('.option-input').forEach(input => {
            options[input.dataset.option] = input.value.trim();
        });
        
        const correctOption = qElement.querySelector('.correct-option').value;
        const skillTag = qElement.querySelector('.skill-tag').value.trim() || null;
        const difficulty = qElement.querySelector('.difficulty').value;
        
        // Validate all options
        if (!options.A || !options.B || !options.C || !options.D) {
            return;
        }
        
        questions.push({
            question_text: questionText,
            option_a: options.A,
            option_b: options.B,
            option_c: options.C,
            option_d: options.D,
            correct_option: correctOption,
            skill_tag: skillTag,
            difficulty: difficulty
        });
    });
    
    if (questions.length === 0) {
        return null;
    }
    
    return {
        title: title,
        description: `Skill assessment quiz for ${document.getElementById('newOppTitle').value.trim() || 'this opportunity'}`,
        passing_score: passingScore,
        time_limit_minutes: timeLimit,
        questions: questions
    };
}

/**
 * Reset quiz editor
 */
function resetQuizEditor() {
    document.getElementById('quizTitle').value = '';
    document.getElementById('quizPassingScore').value = '50';
    document.getElementById('quizTimeLimit').value = '';
    
    const questionsList = document.getElementById('questionsList');
    questionsList.innerHTML = `
        <div class="question-item empty">
            <p class="text-muted">No questions added yet. Click "Add Question" to start.</p>
        </div>
    `;
    
    document.getElementById('quizEditor').style.display = 'none';
}

/**
 * Load user's posted opportunities
 */
async function loadMyOpportunities(userId) {
    showLoadingOnElement('myOpportunitiesList');
    
    try {
        const response = await fetch(`${API_BASE}/api/opportunities`);
        if (!response.ok) throw new Error('Failed to load opportunities');
        
        const opportunities = await response.json();
        
        // Filter to only show user's opportunities (in real app, would filter by user)
        // For demo, show recent ones
        const userOpps = opportunities.slice(0, 5);
        
        hideLoading();
        
        // Update stat
        document.getElementById('statPostedOpps').textContent = opportunities.length;
        document.getElementById('statTotalViewers').textContent = opportunities.length;
        
        if (opportunities.length > 0) {
            document.getElementById('myOpportunitiesList').innerHTML = opportunities
                .map(opp => {
                    const typeClass = opp.opportunity_type === 'internship' ? 'internship' :
                                     opp.opportunity_type === 'job' ? 'job' :
                                     opp.opportunity_type === 'event' ? 'event' : 'skill-program';
                    
                    return `
                        <div class="opportunity-card">
                            <div class="opportunity-card-header">
                                <h4>${opp.title}</h4>
                                <span class="opportunity-type ${typeClass}">${opp.opportunity_type.replace('-', ' ')}</span>
                            </div>
                            <div class="opportunity-card-body">
                                <div class="opportunity-meta">
                                    ${opp.location ? `<span class="meta-item"><i class="fas fa-map-pin"></i> ${opp.location}</span>` : ''}
                                    ${opp.mode ? `<span class="meta-item"><i class="fas fa-laptop"></i> ${opp.mode}</span>` : ''}
                                    ${opp.stipend ? `<span class="meta-item"><i class="fas fa-indian-rupee-sign"></i> ${opp.stipend}</span>` : ''}
                                </div>
                                <div class="opportunity-skills">
                                    ${(opp.required_skills || []).map(s => `<span class="opportunity-skill">${s}</span>`).join('')}
                                </div>
                                ${opp.description ? `<p class="opportunity-description">${opp.description.substring(0, 100)}${opp.description.length > 100 ? '...' : ''}</p>` : ''}
                            </div>
                            <div class="opportunity-card-footer">
                                <span class="opportunity-deadline"><i class="fas fa-calendar"></i> ${formatDate(opp.deadline)}</span>
                                <button class="btn btn-sm btn-outline" style="color: var(--danger); border-color: var(--danger);" 
                                        onclick="deleteOpportunity(${opp.id})">
                                    <i class="fas fa-trash"></i>
                                </button>
                            </div>
                        </div>
                    `;
                }).join('');
        } else {
            document.getElementById('myOpportunitiesList').innerHTML = 
                '<p class="text-muted">No opportunities posted yet. Create your first opportunity above!</p>';
        }
        
    } catch (error) {
        console.error('Error loading opportunities:', error);
        hideLoading();
    }
}

/**
 * Delete opportunity
 */
async function deleteOpportunity(oppId) {
    if (!confirm('Are you sure you want to delete this opportunity?')) return;
    
    const userId = sessionStorage.getItem('userId');
    
    try {
        showLoading();
        
        const response = await fetch(`${API_BASE}/api/opportunities/${oppId}?user_id=${userId}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) throw new Error('Failed to delete opportunity');
        
        hideLoading();
        showSuccess('Opportunity deleted successfully!');
        await loadMyOpportunities(userId);
        
    } catch (error) {
        hideLoading();
        showError('Failed to delete opportunity');
    }
}

/**
 * Search user's opportunities
 */
async function searchMyOpps(query) {
    const userId = sessionStorage.getItem('userId');
    
    try {
        const response = await fetch(`${API_BASE}/api/opportunities`);
        if (!response.ok) throw new Error('Failed to load');
        
        const opportunities = await response.json();
        
        const filtered = opportunities.filter(opp => 
            opp.title.toLowerCase().includes(query.toLowerCase()) ||
            (opp.required_skills || []).some(s => s.toLowerCase().includes(query.toLowerCase()))
        );
        
        if (filtered.length > 0) {
            document.getElementById('myOpportunitiesList').innerHTML = filtered
                .map(opp => createOpportunityCard(opp, true))
                .join('');
        } else {
            document.getElementById('myOpportunitiesList').innerHTML = 
                '<p class="text-muted">No opportunities found matching your search</p>';
        }
        
    } catch (error) {
        console.error('Error searching:', error);
    }
}

/**
 * Talent analytics
 */
async function loadTalentAnalytics() {
    showLoadingOnElement('demandChartLoading');
    
    try {
        const response = await fetch(`${API_BASE}/api/analytics/industry/demand-analysis`);
        if (!response.ok) throw new Error('Failed to load analytics');
        
        const data = await response.json();
        hideLoading();
        
        // Update stats
        document.getElementById('statAvailableTalent').textContent = data.analysis?.total_skills_analyzed || 0;
        
        if (data.analysis?.rankings?.length > 0) {
            document.getElementById('statTopDemandSkill').textContent = data.analysis.rankings[0].skill;
        }
        
        // Display charts
        const charts = data.charts || {};
        displayChart('demandChart', 'demandChartLoading', charts['demand_chart']);
        displayChart('demandSupplyChart', 'demandSupplyChartLoading', charts['demand_supply_chart']);
        
        // High demand low supply
        const highDemandContainer = document.getElementById('highDemandLowSupply');
        const highDemandLowSupply = data.analysis?.high_demand_low_supply || [];
        
        if (highDemandLowSupply.length > 0) {
            highDemandContainer.innerHTML = highDemandLowSupply.map(skill => 
                `<span class="skill-tag" style="background: rgba(239, 68, 68, 0.1); color: #ef4444;">
                    <i class="fas fa-exclamation-circle"></i> ${skill.skill} 
                    <small>(Gap: +${skill.gap}%)</small>
                </span>`
            ).join('');
        } else {
            highDemandContainer.innerHTML = '<p class="text-muted">No high-demand low-supply skills identified</p>';
        }
        
        // Rankings table
        const rankingsBody = document.getElementById('skillRankingsBody');
        const rankings = data.analysis?.rankings || [];
        
        if (rankings.length > 0) {
            rankingsBody.innerHTML = rankings.slice(0, 10).map((rank, i) => `
                <tr>
                    <td><strong>${i + 1}</strong></td>
                    <td><i class="fas fa-star" style="color: #f59e0b; margin-right: 8px;"></i>${rank.skill}</td>
                    <td>
                        <div class="progress" style="width: 80px; height: 8px; background: #e2e8f0; border-radius: 4px; overflow: hidden;">
                            <div style="width: ${rank.demand_score}%; height: 100%; background: #ef4444; border-radius: 4px;"></div>
                        </div>
                        <small>${rank.demand_score}%</small>
                    </td>
                    <td>
                        <div class="progress" style="width: 80px; height: 8px; background: #e2e8f0; border-radius: 4px; overflow: hidden;">
                            <div style="width: ${rank.supply_score}%; height: 100%; background: #10b981; border-radius: 4px;"></div>
                        </div>
                        <small>${rank.supply_score}%</small>
                    </td>
                    <td>
                        <span class="badge ${rank.gap > 20 ? 'badge-danger' : rank.gap > 10 ? 'badge-warning' : 'badge-success'}">
                            ${rank.gap > 0 ? '+' : ''}${rank.gap}%
                        </span>
                    </td>
                    <td>
                        <span class="badge ${rank.priority === 'high' ? 'badge-danger' : rank.priority === 'medium' ? 'badge-warning' : 'badge-success'}">
                            ${rank.priority}
                        </span>
                    </td>
                </tr>
            `).join('');
        } else {
            rankingsBody.innerHTML = '<tr><td colspan="6" class="text-center text-muted">No skill ranking data available</td></tr>';
        }
        
    } catch (error) {
        console.error('Error loading talent analytics:', error);
        hideLoading();
    }
}

/**
 * Setup skill suggestions
 */
function setupSkillSuggestions() {
    const skillsInput = document.getElementById('newOppSkills');
    const suggestions = document.getElementById('skillSuggestions');
    
    const commonSkills = [
        'Python', 'Java', 'JavaScript', 'C++', 'C', 'HTML', 'CSS', 'SQL',
        'React', 'Angular', 'Vue.js', 'Node.js', 'Django', 'Flask', 'Spring Boot',
        'Machine Learning', 'Deep Learning', 'Data Analysis', 'Data Science',
        'Docker', 'Kubernetes', 'AWS', 'Azure', 'GCP', 'Linux', 'Git',
        'MongoDB', 'PostgreSQL', 'MySQL', 'Redis',
        'Communication', 'Teamwork', 'Problem Solving', 'Leadership',
        'English', 'Hindi', 'Typing', 'Excel'
    ];
    
    if (skillsInput) {
        skillsInput.addEventListener('input', function() {
            const value = this.value.toLowerCase();
            if (value.length < 2) {
                suggestions.innerHTML = '<small class="text-muted">Start typing to see suggested skills</small>';
                return;
            }
            
            const matches = commonSkills.filter(skill => 
                skill.toLowerCase().includes(value) && 
                !this.value.split(',').some(s => s.trim().toLowerCase() === skill.toLowerCase())
            ).slice(0, 5);
            
            if (matches.length > 0) {
                suggestions.innerHTML = `
                    <div style="display: flex; flex-wrap: wrap; gap: 4px;">
                        ${matches.map(skill => `
                            <button type="button" 
                                    style="background: var(--bg-secondary); border: 1px solid var(--border-color); border-radius: var(--radius-full); 
                                           padding: 4px 10px; font-size: 0.8rem; cursor: pointer; transition: var(--transition);"
                                    onmouseover="this.style.background='var(--primary-color)'; this.style.color='white'; this.style.borderColor='var(--primary-color)'"
                                    onmouseout="this.style.background='var(--bg-secondary)'; this.style.color='var(--text-primary)'; this.style.borderColor='var(--border-color)'"
                                    onclick="addSkill('${skill}', '${skillsInput.id}')">
                                ${skill}
                            </button>
                        `).join('')}
                    </div>
                `;
            } else {
                suggestions.innerHTML = '<small class="text-muted">No suggestions</small>';
            }
        });
    }
}

/**
 * Add skill to input
 */
function addSkill(skill, inputId) {
    const input = document.getElementById(inputId);
    const current = input.value;
    const skills = current.split(',').map(s => s.trim()).filter(s => s);
    
    if (!skills.includes(skill)) {
        skills.push(skill);
        input.value = skills.join(', ');
    }
    
    // Clear suggestions
    document.getElementById('skillSuggestions').innerHTML = '<small class="text-muted">Skill added!</small>';
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
 * Debounced search
 */
const debounceSearchMyOpps = debounce(function() {
    const query = document.getElementById('myOppSearch')?.value || '';
    searchMyOpps(query);
}, 300);

// Expose functions
window.postOpportunity = postOpportunity;
window.deleteOpportunity = deleteOpportunity;
window.loadMyOpportunities = loadMyOpportunities;
window.searchMyOpps = searchMyOpps;
window.debounceSearchMyOpps = debounceSearchMyOpps;
