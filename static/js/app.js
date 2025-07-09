// app.js
// Configuration
const MATCH_QR_STRING = "f29cZb7Q6DuaMjYkTLV3nxR9KEqV2XoBslrHcwA8d1tZ5UeqgiWTvjNpLEsQ";
const API_BASE_URL = "https://qr-attendance-2xfa.onrender.com";

// State variables
let qrScanner = null;
let currentUser = null;
let scanCooldown = false;
let isUserRegistered = false;
let currentLocation = null;
let isAppInitialized = false;

let qrReaderElement, userFormCard, userInfoDisplay, statusDisplay;

// ============ STEP 1: START APP & LAUNCH QR SCANNER ============
document.addEventListener('DOMContentLoaded', initializeApp);

async function initializeApp() {
    console.log('Starting QR Attendance App...');
    
    // Initialize DOM elements
    initDOMElements();
    
    // Request location permission early
    await requestLocationPermission();
    
    // Check if user data exists in temporary storage
    checkTempUserData();
    
    // Start QR scanner immediately as per workflow
    await startQRScanner();
    
    isAppInitialized = true;
    updateStatus('Scanning for QR code...');
}

function initDOMElements() {
    qrReaderElement = document.getElementById('qr-reader');
    userFormCard = document.getElementById('user-form-card');
    userInfoDisplay = document.getElementById('user-info-display');
    statusDisplay = document.getElementById('status-display');
}

// ============ QR SCANNER FUNCTIONS ============
async function startQRScanner() {
    try {
        if (qrScanner) {
            await stopQRScanner();
        }
        
        qrReaderElement.innerHTML = '';
        qrScanner = new Html5Qrcode("qr-reader");
        
        const config = {
            fps: 10,
            qrbox: { width: 250, height: 250 },
            aspectRatio: 1.0
        };

        await qrScanner.start(
            { facingMode: "environment" },
            config,
            handleQRCodeScan,
            (errorMessage) => {
                console.debug('QR scan error:', errorMessage);
            }
        );

        updateStatus('Ready - Please scan QR code');
        
    } catch (error) {
        console.error('Error starting QR scanner:', error);
        updateStatus('Camera Error - Please check permissions');
    }
}

async function stopQRScanner() {
    if (qrScanner) {
        try {
            await qrScanner.stop();
            qrScanner = null;
        } catch (error) {
            console.error('Error stopping QR scanner:', error);
        }
    }
}

// ============ STEP 1: HANDLE QR CODE SCAN ============
async function handleQRCodeScan(qrCode) {
    // Prevent duplicate scans
    if (scanCooldown) {
        return;
    }
    
    scanCooldown = true;
    setTimeout(() => { scanCooldown = false; }, 2000);
    
    console.log('QR Code scanned:', qrCode);
    
    // Check if it's an authorized QR code
    if (qrCode === MATCH_QR_STRING) {
        updateStatus('Authorized QR code detected!');
        await handleAuthorizedUser();
    } else {
        updateStatus('Invalid QR code. Please scan the correct QR code.');
        showMessage('Invalid QR code. Please scan the authorized QR code.', 'error');
    }
}

// ============ STEP 2: IF AUTHORIZED - CHECK TEMP STORAGE ============
async function handleAuthorizedUser() {
    console.log('Authorized user detected');
    
    // Check temp storage for existing user data
    const tempUserData = checkTempUserData();
    
    if (tempUserData && tempUserData.id) {
        // User data exists in temp storage, proceed with attendance
        currentUser = tempUserData;
        isUserRegistered = true;
        await processAttendance();
    } else {
        // No user data in temp storage, show registration form
        await handleUnregisteredUser();
    }
}

function checkTempUserData() {
    const tempData = localStorage.getItem('tempUserData');
    console.log('Temporary user data:', tempData);
    if (tempData) {
        try {
            const userData = JSON.parse(tempData);
            if (userData.fullName && userData.mobile && userData.employeeId && userData.department && userData.id) {
                return userData;
            }
        } catch (error) {
            console.error('Error parsing temp user data:', error);
        }
    }
    return null;
}

// ============ STEP 3: IF NOT REGISTERED - COLLECT USER DETAILS ============
async function handleUnregisteredUser() {
    console.log('User not registered, showing registration form');
    
    // Stop QR scanner temporarily
    await stopQRScanner();
    
    // Show registration form
    showUserRegistrationForm();
    
    updateStatus('Please fill in your details to register');
}

function showUserRegistrationForm() {
    if (userFormCard) {
        userFormCard.style.display = 'block';
    }
    
    if (userInfoDisplay) {
        userInfoDisplay.style.display = 'none';
    }
    
    // Setup form submission
    const form = document.getElementById('user-form');
    if (form) {
        form.removeEventListener('submit', handleUserRegistration);
        form.addEventListener('submit', handleUserRegistration);
    }
}

async function handleUserRegistration(event) {
    event.preventDefault();
    
    const formData = {
        fullName: document.getElementById('fullName').value.trim(),
        mobile: document.getElementById('mobile').value.trim(),
        employeeId: document.getElementById('employeeId').value.trim(),
        department: document.getElementById('department').value.trim()
    };
    
    // Validate form data
    if (!validateUserData(formData)) {
        return;
    }
    
    try {
        updateStatus('Checking/Registering user...');
        
        // Try to register user (backend will handle existing users)
        const response = await fetch(`${API_BASE_URL}/api/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData)
        });
        
        const result = await response.json();
        
        if (response.ok) {
            // Registration successful or user already exists
            const userData = {
                ...formData,
                id: result.user_id
            };
            
            // If user already existed, use the returned user data
            if (result.existing_user && result.user_data) {
                userData.fullName = result.user_data.fullName;
                userData.mobile = result.user_data.mobile;
                userData.employeeId = result.user_data.employeeId;
                userData.department = result.user_data.department;
            }
            
            // Save to temp storage
            localStorage.setItem('tempUserData', JSON.stringify(userData));
            
            isUserRegistered = true;
            currentUser = userData;
            
            if (result.existing_user) {
                showMessage('User already registered! Please scan the QR code again.', 'info');
            } else {
                showMessage('Registration successful! Please scan the QR code again.', 'success');
            }
            
            // Hide form and restart QR scanner
            hideUserRegistrationForm();
            await startQRScanner();
            
        } else {
            showMessage(result.error || 'Registration failed', 'error');
        }
        
    } catch (error) {
        console.error('Registration error:', error);
        showMessage('Registration failed. Please try again.', 'error');
    }
}

function hideUserRegistrationForm() {
    if (userFormCard) {
        userFormCard.style.display = 'none';
    }
}

function validateUserData(data) {
    if (!data.fullName || !data.mobile || !data.employeeId || !data.department) {
        showMessage('Please fill in all required fields.', 'error');
        return false;
    }
    
    const mobileRegex = /^[0-9]{10}$/;
    if (!mobileRegex.test(data.mobile)) {
        showMessage('Please enter a valid 10-digit mobile number.', 'error');
        return false;
    }
    
    return true;
}

// ============ STEP 2: PROCESS ATTENDANCE ============
async function processAttendance() {
    console.log('Processing attendance for registered user');
    
    // Stop QR scanner during attendance process
    await stopQRScanner();
    
    // Show user info
    showUserInfo();
    
    // Check current attendance status
    const attendanceStatus = await checkAttendanceStatus();
    
    // Ask for location and capture time
    await captureLocationAndTime();
    
    // Process check-in or check-out based on current status
    if (attendanceStatus === 'not_checked_in') {
        await performCheckIn();
    } else if (attendanceStatus === 'checked_in') {
        await performCheckOut();
    } else {
        showMessage('Attendance already completed for today.', 'info');
    }
    
}

async function checkAttendanceStatus() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/check-status`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ user_id: currentUser.id })
        });
        
        if (response.ok) {
            const status = await response.json();
            return status.status;
        }
        
    } catch (error) {
        console.error('Error checking attendance status:', error);
    }
    
    return 'not_checked_in';
}

async function captureLocationAndTime() {
    updateStatus('Capturing location and time...');
    
    // Use previously captured location or get new one
    if (!currentLocation) {
        await requestLocationPermission();
    }
    
    if (currentLocation) {
        console.log('Location captured:', currentLocation);
        updateStatus('Location captured successfully');
    } else {
        updateStatus('Warning: Location not available');
    }
}

async function performCheckIn() {
    try {
        updateStatus('Checking in...');
        
        const response = await fetch(`${API_BASE_URL}/api/check-in`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                user_id: currentUser.id,
                location: currentLocation
                // Removed qr_code from request
            })
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showMessage('Check-in successful!', 'success');
            updateStatus('Checked in successfully');
        } else {
            showMessage(result.error || 'Check-in failed', 'error');
        }
        
    } catch (error) {
        console.error('Check-in error:', error);
        showMessage('Check-in failed. Please try again.', 'error');
    }
}

async function performCheckOut() {
    try {
        updateStatus('Checking out...');
        
        const response = await fetch(`${API_BASE_URL}/api/check-out`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                user_id: currentUser.id,
                location: currentLocation
                // Removed qr_code from request
            })
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showMessage('Check-out successful!', 'success');
            updateStatus('Checked out successfully');
        } else {
            showMessage(result.error || 'Check-out failed', 'error');
        }
        
    } catch (error) {
        console.error('Check-out error:', error);
        showMessage('Check-out failed. Please try again.', 'error');
    }
}

// ============ UTILITY FUNCTIONS ============
async function requestLocationPermission() {
    try {
        if ('geolocation' in navigator) {
            const position = await new Promise((resolve, reject) => {
                navigator.geolocation.getCurrentPosition(resolve, reject, {
                    enableHighAccuracy: true,
                    timeout: 10000,
                    maximumAge: 300000
                });
            });
            
            currentLocation = {
                latitude: position.coords.latitude,
                longitude: position.coords.longitude,
                accuracy: position.coords.accuracy,
                timestamp: new Date().toISOString()
            };
            
            console.log('Location permission granted');
        }
    } catch (error) {
        console.warn('Location permission denied:', error);
        currentLocation = null;
    }
}

function showUserInfo() {
    if (userInfoDisplay && currentUser) {
        userInfoDisplay.innerHTML = `
            <div class="user-info">
                <h3>Welcome, ${currentUser.fullName}</h3>
                <p><strong>Employee ID:</strong> ${currentUser.employeeId}</p>
                <p><strong>Department:</strong> ${currentUser.department}</p>
                <p><strong>Mobile:</strong> ${currentUser.mobile}</p>
            </div>
        `;
        userInfoDisplay.style.display = 'block';
    }
}

function updateStatus(message) {
    console.log('Status:', message);
    if (statusDisplay) {
        statusDisplay.textContent = message;
    }
}

function showMessage(message, type = 'info') {
    console.log(`${type.toUpperCase()}: ${message}`);
    
    // Create or update message display
    let messageElement = document.getElementById('message-display');
    if (!messageElement) {
        messageElement = document.createElement('div');
        messageElement.id = 'message-display';
        messageElement.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 10px 20px;
            border-radius: 5px;
            z-index: 1000;
            max-width: 300px;
            font-weight: bold;
        `;
        document.body.appendChild(messageElement);
    }
    
    messageElement.textContent = message;
    messageElement.className = `message ${type}`;
    
    // Set colors based on type
    switch(type) {
        case 'success':
            messageElement.style.backgroundColor = '#d4edda';
            messageElement.style.color = '#155724';
            messageElement.style.border = '1px solid #c3e6cb';
            break;
        case 'error':
            messageElement.style.backgroundColor = '#f8d7da';
            messageElement.style.color = '#721c24';
            messageElement.style.border = '1px solid #f5c6cb';
            break;
        case 'info':
            messageElement.style.backgroundColor = '#d1ecf1';
            messageElement.style.color = '#0c5460';
            messageElement.style.border = '1px solid #bee5eb';
            break;
        default:
            messageElement.style.backgroundColor = '#f8f9fa';
            messageElement.style.color = '#212529';
            messageElement.style.border = '1px solid #dee2e6';
    }
    
    // Auto-hide after 2 seconds
    setTimeout(() => {
        messageElement.textContent = '';
        messageElement.style.display = 'none';
    }, 2000);
    
    messageElement.style.display = 'block';
}

// ============ CLEANUP ============
window.addEventListener('beforeunload', async () => {
    if (qrScanner) {
        await stopQRScanner();
    }
});
