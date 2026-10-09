/**
 * SIH Platform - Authentication JavaScript
 * Handles login, signup, and session management
 */

document.addEventListener('DOMContentLoaded', function() {
    // Set up auth modal
    document.querySelector('.hero-actions .btn-primary')?.addEventListener('click', showAuthModal);
    
    // Set up auth forms
    setupAuthForms();
    
    // Check if returning from API redirect
    checkAuthState();
});

/**
 * Show authentication modal
 */
function showAuthModal() {
    const modal = document.getElementById('authModal');
    if (modal) {
        modal.classList.add('active');
        // Default to login tab
        switchAuthTab('login');
    }
}

/**
 * Close authentication modal
 */
function closeAuthModal() {
    const modal = document.getElementById('authModal');
    if (modal) {
        modal.classList.remove('active');
    }
}

/**
 * Switch between login and signup tabs
 */
function switchAuthTab(tab) {
    const loginForm = document.getElementById('loginForm');
    const signupForm = document.getElementById('signupForm');
    const loginTabs = document.querySelectorAll('.auth-tab');
    
    if (tab === 'login') {
        loginForm.style.display = 'block';
        signupForm.style.display = 'none';
        loginTabs[0].classList.add('active');
        loginTabs[1].classList.remove('active');
    } else {
        loginForm.style.display = 'none';
        signupForm.style.display = 'block';
        loginTabs[0].classList.remove('active');
        loginTabs[1].classList.add('active');
        toggleInstituteField();
    }
}

/**
 * Toggle institute name field based on role
 */
function toggleInstituteField() {
    const selectedRole = document.querySelector('input[name="signupRole"]:checked');
    const instituteGroup = document.getElementById('instituteNameGroup');
    
    if (selectedRole && selectedRole.value === 'institute') {
        instituteGroup.style.display = 'block';
    } else {
        instituteGroup.style.display = 'none';
    }
}

/**
 * Set up auth forms
 */
function setupAuthForms() {
    // Login form
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', handleLogin);
    }
    
    // Signup form
    const signupForm = document.getElementById('signupForm');
    if (signupForm) {
        signupForm.addEventListener('submit', handleSignup);
    }
    
    // Role selection change
    document.querySelectorAll('input[name="signupRole"]').forEach(radio => {
        radio.addEventListener('change', toggleInstituteField);
    });
    
    // Close modal on outside click
    const modal = document.getElementById('authModal');
    if (modal) {
        modal.addEventListener('click', function(e) {
            if (e.target === modal) {
                closeAuthModal();
            }
        });
    }
    
    // ESC to close
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            closeAuthModal();
        }
    });
}

/**
 * Handle login form submission
 */
async function handleLogin(e) {
    console.log("LOGIN: handleLogin started");
    e.preventDefault();
    
    const email = document.getElementById('loginEmail').value;
    const password = document.getElementById('loginPassword').value;
    
    try {
        console.log("4. LOADING SHOWN");
        showLoading();
        
        const response = await fetch(`${API_BASE}/api/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ email, password })
        });
        
        console.log("5. FETCH RESPONSE:", response.status);
        const data = await response.json();
        console.log("LOGIN: about to fetch");
        hideLoading();
        
        if (data.success) {
            // Store user session
            currentUser = {
                id: data.user_id,
                name: data.name,
                email: email,
                role: data.role
            };
            
            // Save to localStorage
            localStorage.setItem('sih_user', JSON.stringify(currentUser));
            
            // Redirect to appropriate dashboard
            redirectToDashboard(data.role, data.user_id);
        } else {
            showError(data.message || 'Login failed');
        }
    } catch (error) {
        hideLoading();
        showError('Network error. Please try again.');
        console.error('Login error:', error);
    }
}

/**
 * Handle signup form submission
 */
async function handleSignup(e) {
    e.preventDefault();
    
    const name = document.getElementById('signupName').value;
    const email = document.getElementById('signupEmail').value;
    const password = document.getElementById('signupPassword').value;
    const role = document.querySelector('input[name="signupRole"]:checked').value;
    const instituteName = document.getElementById('signupInstitute').value;
    
    try {
        showLoading();
        
        const response = await fetch(`${API_BASE}/api/auth/signup`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 
                name, 
                email, 
                password, 
                role,
                institute_name: role === 'institute' ? instituteName : null
            })
        });
        
        const data = await response.json();
        hideLoading();
        
        if (data.success) {
            showSuccess('Account created! Please complete your profile.');
            closeAuthModal();
            
            // Store user session
            currentUser = {
                id: data.user_id,
                name: data.name,
                email: email,
                role: data.role
            };
            
            localStorage.setItem('sih_user', JSON.stringify(currentUser));
            
            // Redirect based on role
            redirectToDashboard(data.role, data.user_id);
        } else {
            showError(data.message || 'Signup failed');
        }
    } catch (error) {
        hideLoading();
        showError('Network error. Please try again.');
        console.error('Signup error:', error);
    }
}

/**
 * Redirect to appropriate dashboard based on role
 */
function redirectToDashboard(role, userId) {
    // Store user ID in session
    sessionStorage.setItem('userId', userId);
    sessionStorage.setItem('role', role);
    
    switch(role) {
        case 'student':
            window.location.href = 'student.html';
            break;
        case 'faculty':
            window.location.href = 'faculty.html';
            break;
        case 'institute':
            window.location.href = 'institute.html';
            break;
        case 'industry':
            window.location.href = 'industry.html';
            break;
        default:
            window.location.href = 'index.html';
    }
}

/**
 * Use sample student credentials
 */
function useSampleStudent() {
    document.getElementById('loginEmail').value = 'arjun.sharma@student.demoayush.edu';
    document.getElementById('loginPassword').value = 'student123';
    handleLogin(new Event('submit'));
}

/**
 * Use sample faculty credentials
 */
function useSampleFaculty() {
    document.getElementById('loginEmail').value = 'vikram.singh@demoayush.edu';
    document.getElementById('loginPassword').value = 'faculty123';
    handleLogin(new Event('submit'));
}

/**
 * Use sample industry credentials
 */
function useSampleIndustry() {
    document.getElementById('loginEmail').value = 'hr@demoayushpharma.example.com';
    document.getElementById('loginPassword').value = 'industry123';
    handleLogin(new Event('submit'));
}

/**
 * Use sample institute credentials
 */
function useSampleInstitute() {
    document.getElementById('loginEmail').value = 'registrar@demoayush.edu';
    document.getElementById('loginPassword').value = 'institute123';
    handleLogin(new Event('submit'));
}

/**
 * Logout user
 */
function logout() {
    if (confirm('Are you sure you want to logout?')) {
        localStorage.removeItem('sih_user');
        sessionStorage.removeItem('userId');
        sessionStorage.removeItem('role');
        window.location.href = 'index.html';
    }
}

/**
 * Check authentication state on page load
 */
function checkAuthState() {
    const storedUser = localStorage.getItem('sih_user');
    if (storedUser) {
        currentUser = JSON.parse(storedUser);
        // User is logged in, they should be on their dashboard
    }
}

/**
 * Select role for onboarding
 */
function selectRole(role) {
    closeAuthModal();
    document.getElementById('authModalTitle').textContent = 'Create Your Account';
    
    // Show signup with role pre-selected
    switchAuthTab('signup');
    
    // Set role
    const roleRadio = document.querySelector(`input[name="signupRole"][value="${role}"]`);
    if (roleRadio) {
        roleRadio.checked = true;
        toggleInstituteField();
    }
}

// Make functions available globally
window.showAuthModal = showAuthModal;
window.closeAuthModal = closeAuthModal;
window.switchAuthTab = switchAuthTab;
window.selectRole = selectRole;
window.useSampleStudent = useSampleStudent;
window.useSampleFaculty = useSampleFaculty;
window.useSampleInstitute = useSampleInstitute;
window.useSampleIndustry = useSampleIndustry;
window.logout = logout;
