/**
 * SIH Platform - Main JavaScript
 * Core utilities, navigation, and common functions
 */

// Base API URL
const API_BASE = 'http://127.0.0.1:8000';

// Current user state
let currentUser = {
    id: null,
    name: null,
    email: null,
    role: null
};

// Navigation
document.addEventListener('DOMContentLoaded', function() {
    // Set up navigation links
    setupNavigation();
    
    // Handle auth modal events
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('show-auth-modal')) {
            showAuthModal();
        }
    });
});

/**
 * Set up navigation for current page
 */
function setupNavigation() {
    const navLinks = document.querySelectorAll('.nav-link');
    const sections = document.querySelectorAll('.section');
    
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const section = this.dataset.section;
            
            // Update nav links
            navLinks.forEach(l => l.classList.remove('active'));
            this.classList.add('active');
            
            // Show corresponding section
            sections.forEach(s => {
                s.classList.remove('active');
                if (s.id === `section-${section}`) {
                    s.classList.add('active');
                }
            });
        });
    });
}

/**
 * Switch to a different section
 */
function switchSection(sectionName) {
    const navLinks = document.querySelectorAll('.nav-link');
    const sections = document.querySelectorAll('.section');
    
    navLinks.forEach(link => {
        link.classList.remove('active');
        if (link.dataset.section === sectionName) {
            link.classList.add('active');
        }
    });
    
    sections.forEach(section => {
        section.classList.remove('active');
        if (section.id === `section-${sectionName}`) {
            section.classList.add('active');
        }
    });
}

/**
 * Show loading overlay
 */
function showLoading() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        overlay.style.display = 'flex';
    }
}

/**
 * Hide loading overlay
 */
function hideLoading() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        overlay.style.display = 'none';
    }
}

/**
 * Show error message
 */
function showError(message) {
    alert('Error: ' + message);
}

/**
 * Show success message
 */
function showSuccess(message) {
    alert('Success: ' + message);
}

/**
 * Format date for display
 */
function formatDate(dateStr) {
    if (!dateStr) return '-';
    try {
        const date = new Date(dateStr);
        return date.toLocaleDateString('en-IN', {
            day: '2-digit',
            month: 'short',
            year: 'numeric'
        });
    } catch {
        return dateStr;
    }
}

/**
 * Check if deadline is urgent (less than 14 days)
 */
function isUrgent(deadlineStr) {
    if (!deadlineStr) return false;
    try {
        const deadline = new Date(deadlineStr);
        const now = new Date();
        const diffTime = deadline - now;
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
        return diffDays <= 14 && diffDays > 0;
    } catch {
        return false;
    }
}

/**
 * Show loading on element
 */
function showLoadingOnElement(elementId, message = 'Loading...') {
    const el = document.getElementById(elementId);
    if (el) {
        el.innerHTML = `
            <div class="text-center">
                <i class="fas fa-spinner fa-spin"></i>
                <p>${message}</p>
            </div>
        `;
    }
}

/**
 * Format number with commas
 */
function formatNumber(num) {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}

/**
 * Shared opportunity card renderer.
 *
 * Loaded on every page via main.js. The student dashboard defines its own
 * richer version in student.js (with quiz buttons) which overrides this one on
 * that page; faculty and industry rely on this shared version.
 */
function createOpportunityCard(opp, isOwn = false) {
    const skillsHtml = (opp.required_skills || []).slice(0, 5).map(skill =>
        `<span class="opportunity-skill">${skill}</span>`
    ).join('');

    const typeClass = opp.opportunity_type === 'internship' ? 'internship' :
                      opp.opportunity_type === 'job' ? 'job' :
                      opp.opportunity_type === 'event' ? 'event' : 'skill-program';

    const deadlineUrgent = isUrgent(opp.deadline);

    const actionsHtml = isOwn ? `
        <button class="btn btn-sm btn-outline" style="color: var(--danger); border-color: var(--danger);"
                onclick="deleteOpportunity(${opp.id})">
            <i class="fas fa-trash"></i>
        </button>
    ` : '';

    return `
        <div class="opportunity-card">
            <div class="opportunity-card-header">
                <h4>${opp.title}</h4>
                <span class="opportunity-type ${typeClass}">${(opp.opportunity_type || '').replace('-', ' ')}</span>
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
                <span class="company-name"><i class="fas fa-building"></i> ${opp.company_name || 'Organisation'}</span>
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

// Export functions for use in other scripts
window.createOpportunityCard = createOpportunityCard;
window.showLoading = showLoading;
window.hideLoading = hideLoading;
window.showError = showError;
window.showSuccess = showSuccess;
window.formatDate = formatDate;
window.isUrgent = isUrgent;
window.showLoadingOnElement = showLoadingOnElement;
window.formatNumber = formatNumber;
window.switchSection = switchSection;
