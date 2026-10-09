/**
 * SIH Platform - Institute Dashboard JavaScript
 * Handles institute analytics and charts
 */

document.addEventListener('DOMContentLoaded', function() {
    initializeInstituteDashboard();
});

/**
 * Initialize institute dashboard
 */
async function initializeInstituteDashboard() {
    const userId = sessionStorage.getItem('userId');
    const role = sessionStorage.getItem('role');
    
    if (!userId || role !== 'institute') {
        window.location.href = 'index.html';
        return;
    }
    
    const userName = localStorage.getItem('sih_user');
    if (userName) {
        const user = JSON.parse(userName);
        document.getElementById('instituteUserName').textContent = user.name;
    }
    
    // Load all analytics data
    await Promise.all([
        loadInstituteProfile(userId),
        loadInstituteAnalytics(userId),
        loadInstituteCharts(userId)
    ]);
}

/**
 * Load institute profile
 */
async function loadInstituteProfile(userId) {
    try {
        const response = await fetch(`${API_BASE}/api/auth/me/${userId}`);
        if (!response.ok) throw new Error('Failed to load user');
        
        const user = await response.json();
        
        if (user.institute_id) {
            const instituteResponse = await fetch(`${API_BASE}/api/institute/${user.institute_id}`);
            if (instituteResponse.ok) {
                const institute = await instituteResponse.json();
                document.getElementById('instituteNameDisplay').textContent = 
                    `Analytics for ${institute.name}`;
            }
        }
    } catch (error) {
        console.error('Error loading institute profile:', error);
    }
}

/**
 * Load institute analytics
 */
async function loadInstituteAnalytics(userId) {
    showLoadingOnElement('totalStudents');
    
    try {
        // Get institute ID from user
        const userResponse = await fetch(`${API_BASE}/api/auth/me/${userId}`);
        const user = await userResponse.json();
        
        if (!user.institute_id) {
            throw new Error('No institute associated');
        }
        
        const response = await fetch(`${API_BASE}/api/analytics/institute/analytics/${user.institute_id}`);
        if (!response.ok) throw new Error('Failed to load analytics');
        
        const data = await response.json();
        hideLoading();
        
        // Update stats
        document.getElementById('totalStudents').textContent = data.total_students;
        document.getElementById('totalSkillsCount').textContent = 
            data.skill_distribution.reduce((sum, s) => sum + s.count, 0);
        document.getElementById('internshipCount').textContent = data.internship_participation;
        document.getElementById('eventCount').textContent = data.skill_development_participation;
        
        // Update tables
        updateBranchTable(data.students_by_branch);
        updateBatchTable(data.students_by_batch);
        
        // Update skills list
        const skillsContainer = document.getElementById('commonSkillsList');
        if (data.most_common_skills.length > 0) {
            skillsContainer.innerHTML = data.most_common_skills.map(skill => 
                `<span class="skill-tag"><i class="fas fa-check"></i> ${skill.skill} <small>(${skill.count})</small></span>`
            ).join('');
        } else {
            skillsContainer.innerHTML = '<p class="text-muted">No skill data available</p>';
        }
        
        // Update career interests
        const careerContainer = document.getElementById('careerInterestsList');
        if (data.career_interests.length > 0) {
            careerContainer.innerHTML = data.career_interests.map(interest => 
                `<div class="insight-item">
                    <i class="fas fa-bullseye"></i>
                    <div class="insight-content">
                        <span class="insight-title">${interest.industry}</span>
                        <span class="insight-meta">${interest.count} students (${interest.percentage}%)</span>
                    </div>
                </div>
            `).join('');
        } else {
            careerContainer.innerHTML = '<p class="text-muted">No career interest data available</p>';
        }
        
        // Update outcome summary
        document.getElementById('outcomeInternships').textContent = data.internship_participation;
        document.getElementById('outcomeJobs').textContent = data.job_participation;
        document.getElementById('outcomeEvents').textContent = data.skill_development_participation;
        document.getElementById('outcomeSkillPrograms').textContent = data.skill_development_participation;
        
        // Load skill distribution data for charts
        await loadSkillDistributionCharts(user.institute_id);
        
        // Load internship analytics
        await loadInternshipAnalytics(user.institute_id);
        
        // Store analytics for charts
        window.instituteAnalytics = data;
        
    } catch (error) {
        console.error('Error loading analytics:', error);
        hideLoading();
    }
}

/**
 * Load skill distribution charts from new endpoint
 */
async function loadSkillDistributionCharts(instituteId) {
    try {
        const response = await fetch(`${API_BASE}/api/institute/${instituteId}/skill-distribution`);
        if (!response.ok) throw new Error('Failed to load skill distribution');
        
        const data = await response.json();
        
        // Update skill distribution stats
        const topSkills = data.skill_distribution.slice(0, 10);
        
        // Create a simple bar chart using CSS (lightweight, no library needed)
        const chartContainer = document.getElementById('skillsChart');
        if (chartContainer && topSkills.length > 0) {
            const maxCount = Math.max(...topSkills.map(s => s.count));
            
            let chartHtml = '<div class="simple-bar-chart">';
            topSkills.forEach(skill => {
                const barWidth = (skill.count / maxCount * 100).toFixed(0);
                chartHtml += `
                    <div class="bar-row">
                        <span class="bar-label">${skill.skill}</span>
                        <div class="bar-container">
                            <div class="bar-fill" style="width: ${barWidth}%; ${barWidth > 60 ? 'background: linear-gradient(90deg, #1a56db, #3b82f6);' : 'background: #3b82f6;'}"></div>
                        </div>
                        <span class="bar-value">${skill.count}</span>
                    </div>
                `;
            });
            chartHtml += '</div>';
            chartContainer.innerHTML = chartHtml;
            chartContainer.style.display = 'block';
            document.getElementById('skillsChartLoading').style.display = 'none';
        }
        
        // Store for other uses
        window.skillDistribution = data.skill_distribution;
        
    } catch (error) {
        console.error('Error loading skill distribution:', error);
    }
}

/**
 * Load internship analytics
 */
async function loadInternshipAnalytics(instituteId) {
    try {
        const response = await fetch(`${API_BASE}/api/institute/${instituteId}/internships`);
        if (!response.ok) throw new Error('Failed to load internship analytics');
        
        const data = await response.json();
        
        // Update internship-related stats
        document.getElementById('internshipCount').textContent = data.internship_opportunities;
        document.getElementById('eventCount').textContent = data.event_opportunities + data.skill_program_opportunities;
        
        // Add internship-specific stats to the dashboard if there's space
        // For now, store for potential future use
        window.internshipAnalytics = data;
        
    } catch (error) {
        console.error('Error loading internship analytics:', error);
    }
}

/**
 * Update branch table
 */
function updateBranchTable(branchData) {
    const tbody = document.getElementById('branchTableBody');
    
    if (branchData.length > 0) {
        tbody.innerHTML = branchData.map(branch => `
            <tr>
                <td><i class="fas fa-code-branch" style="color: #3b82f6; margin-right: 8px;"></i>${branch.branch}</td>
                <td><strong>${branch.count}</strong></td>
                <td>
                    <div class="progress" style="width: 100px; height: 8px; background: #e2e8f0; border-radius: 4px; overflow: hidden;">
                        <div style="width: ${branch.percentage}%; height: 100%; background: #3b82f6; border-radius: 4px;"></div>
                    </div>
                    <small>${branch.percentage}%</small>
                </td>
            </tr>
        `).join('');
    } else {
        tbody.innerHTML = '<tr><td colspan="3" class="text-center text-muted">No data available</td></tr>';
    }
}

/**
 * Update batch table
 */
function updateBatchTable(batchData) {
    const tbody = document.getElementById('batchTableBody');
    
    if (batchData.length > 0) {
        tbody.innerHTML = batchData.map(batch => `
            <tr>
                <td><i class="fas fa-calendar" style="color: #3b82f6; margin-right: 8px;"></i>${batch.batch}</td>
                <td><strong>${batch.count}</strong></td>
                <td>
                    <div class="progress" style="width: 100px; height: 8px; background: #e2e8f0; border-radius: 4px; overflow: hidden;">
                        <div style="width: ${batch.percentage}%; height: 100%; background: #10b981; border-radius: 4px;"></div>
                    </div>
                    <small>${batch.percentage}%</small>
                </td>
            </tr>
        `).join('');
    } else {
        tbody.innerHTML = '<tr><td colspan="3" class="text-center text-muted">No data available</td></tr>';
    }
}

/**
 * Load institute charts
 */
async function loadInstituteCharts(userId) {
    try {
        const userResponse = await fetch(`${API_BASE}/api/auth/me/${userId}`);
        const user = await userResponse.json();
        
        if (!user.institute_id) {
            console.error('No institute_id found for user');
            return;
        }
        
        console.log('Loading charts for institute_id:', user.institute_id);
        
        const response = await fetch(`${API_BASE}/api/analytics/institute/charts/${user.institute_id}`);
        if (!response.ok) {
            const errorText = await response.text();
            console.error('Failed to load charts, status:', response.status, 'body:', errorText);
            throw new Error('Failed to load charts');
        }
        
        const data = await response.json();
        console.log('Charts data received:', Object.keys(data.charts || {}));
        
        const charts = data.charts || {};
        
        // Display charts - skip skillsChart since we have our own CSS-based chart
        displayChart('branchChart', 'branchChartLoading', charts['branch_chart']);
        displayChart('batchChart', 'batchChartLoading', charts['batch_chart']);
        displayChart('careerChart', 'careerChartLoading', charts['career_chart']);
        displayChart('participationChart', 'participationChartLoading', charts['participation_chart']);
        // Don't display skillsChart from matplotlib - we'll use our CSS chart
        
    } catch (error) {
        console.error('Error loading charts:', error);
    }
}

/**
 * Display chart image
 */
function displayChart(chartId, loadingId, base64Data) {
    const chartImg = document.getElementById(chartId);
    const loadingEl = document.getElementById(loadingId);
    
    if (base64Data) {
        chartImg.src = `data:image/png;base64,${base64Data}`;
        chartImg.style.display = 'block';
        if (loadingEl) loadingEl.style.display = 'none';
    } else {
        if (loadingEl) loadingEl.style.display = 'block';
    }
}

/**
 * Load skill gap analysis
 */
async function loadSkillGaps() {
    const userId = sessionStorage.getItem('userId');
    
    try {
        const userResponse = await fetch(`${API_BASE}/api/auth/me/${userId}`);
        const user = await userResponse.json();
        
        if (!user.institute_id) return;
        
        const response = await fetch(`${API_BASE}/api/analytics/industry/demand-analysis`);
        if (!response.ok) throw new Error('Failed to load demand analysis');
        
        const data = await response.json();
        
        // Update skill gaps list
        const gapsContainer = document.getElementById('skillGapsList');
        const highDemandLowSupply = data.analysis?.high_demand_low_supply || [];
        
        if (highDemandLowSupply.length > 0) {
            gapsContainer.innerHTML = highDemandLowSupply.map(skill => 
                `<div class="insight-item" style="border-left-color: #f59e0b;">
                    <i class="fas fa-exclamation-triangle" style="color: #f59e0b;"></i>
                    <div class="insight-content">
                        <span class="insight-title">${skill.skill}</span>
                        <span class="insight-meta">
                            Demand: ${skill.demand_score}% | Supply: ${skill.supply_score}% | 
                            Gap: ${skill.gap > 0 ? '+' : ''}${skill.gap}%
                        </span>
                    </div>
                </div>
            `).join('');
        } else {
            gapsContainer.innerHTML = '<p class="text-muted">No significant skill gaps identified</p>';
        }
        
        // Update demand chart
        const demandChart = data.charts?.['demand_chart'];
        if (demandChart) {
            displayChart('demandChart', 'demandChartLoading', demandChart);
        }
        
        // Update demand vs supply chart
        const demandSupplyChart = data.charts?.['demand_supply_chart'];
        if (demandSupplyChart) {
            displayChart('demandSupplyChart', 'demandSupplyChartLoading', demandSupplyChart);
        }
        
        // Update high demand low supply section
        const highDemandContainer = document.getElementById('highDemandLowSupply');
        if (highDemandLowSupply.length > 0) {
            highDemandContainer.innerHTML = highDemandLowSupply.map(skill => 
                `<span class="skill-tag" style="background: rgba(245, 158, 11, 0.1); color: #f59e0b;">
                    <i class="fas fa-exclamation-circle"></i> ${skill.skill} 
                    <small>(Gap: ${skill.gap}%)</small>
                </span>`
            ).join('');
        } else {
            highDemandContainer.innerHTML = '<p class="text-muted">No high-demand low-supply skills identified</p>';
        }
        
        // Update rankings table
        const rankingsBody = document.getElementById('skillRankingsBody');
        const rankings = data.analysis?.rankings || [];
        
        if (rankings.length > 0) {
            rankingsBody.innerHTML = rankings.slice(0, 10).map((rank, i) => `
                <tr>
                    <td><strong>${i + 1}</strong></td>
                    <td>${rank.skill}</td>
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
        console.error('Error loading skill gaps:', error);
    }
}

// Expose function for section switching
window.loadSkillGaps = loadSkillGaps;
