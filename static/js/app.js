// app.js
// Configuration
// const MATCH_QR_STRING = "f29cZb7Q6DuaMjYkTLV3nxR9KEqV2XoBslrHcwA8d1tZ5UeqgiWTvjNpLEsQ";
// const API_BASE_URL = "http://localhost:5000";

// Script.js
// Configuration
const MATCH_QR_STRING = "f29cZb7Q6DuaMjYkTLV3nxR9KEqV2XoBslrHcwA8d1tZ5UeqgiWTvjNpLEsQ";
const API_BASE_URL = "https://qr-attendance-9jq0.onrender.com";

// State variables
let qrScanner = null;
let currentUser = null;
let scanCooldown = false;
let isUserRegistered = false;
let currentLocation = null;
let isAppInitialized = false;
let isCameraActive = false;

let qrReaderElement, userFormCard, userInfoDisplay, statusDisplay;

// ============ STEP 1: START APP & LAUNCH QR SCANNER ============
document.addEventListener('DOMContentLoaded', initializeApp);

async function initializeApp() {
    console.log('Starting QR Attendance App...');

    // Initialize DOM elements
    initDOMElements();
    disableForm();

    // Setup camera toggle button
    setupCameraToggle();

    // Request location permission early
    await requestLocationPermission();

    // Check if user data exists in temporary storage
    await primary_check()
    checkTempUserData();

    // Setup gallery upload
    setupGalleryUpload();

    // Setup form submission
    setupFormSubmission();

    // Update status
    updateStatus('Ready - Toggle camera or upload QR image');
    updateScannerStatus('inactive');

    isAppInitialized = true;
}

function initDOMElements() {
    qrReaderElement = document.getElementById('qr-reader');
    userFormCard = document.getElementById('form-card');
    userInfoDisplay = document.getElementById('user-info-display');
    statusDisplay = document.getElementById('status-text');
}

// ============ CAMERA TOGGLE FUNCTIONS ============
function setupCameraToggle() {
    // Add toggle button to the scanner container
    const scannerContainer = document.getElementById('qr-scanner-container');
    if (scannerContainer) {
        const toggleButton = document.createElement('button');
        toggleButton.id = 'camera-toggle-btn';
        toggleButton.className = 'w-full mt-4 bg-primary hover:bg-primary-dark text-white font-medium py-3 px-4 rounded-lg transition-colors focus:ring-2 focus:ring-primary focus:ring-offset-2';
        toggleButton.innerHTML = `
            <div class="flex items-center justify-center space-x-2">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0118.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z"></path>
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 13a3 3 0 11-6 0 3 3 0 016 0z"></path>
                </svg>
                <span>Start Camera</span>
            </div>
        `;
        toggleButton.addEventListener('click', toggleCamera);
        scannerContainer.appendChild(toggleButton);
    }
}

async function toggleCamera() {
    const toggleBtn = document.getElementById('camera-toggle-btn');

    if (!isCameraActive) {
        // Start camera
        await startQRScanner();
        if (qrScanner) {
            isCameraActive = true;
            toggleBtn.innerHTML = `
                <div class="flex items-center justify-center space-x-2">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 10l6 6m0-6l-6 6"></path>
                    </svg>
                    <span>Stop Camera</span>
                </div>
            `;
            toggleBtn.className = 'w-full mt-4 bg-red-600 hover:bg-red-700 text-white font-medium py-3 px-4 rounded-lg transition-colors focus:ring-2 focus:ring-red-500 focus:ring-offset-2';
            updateScannerStatus('active');
        }
    } else {
        // Stop camera
        await stopQRScanner();
        isCameraActive = false;
        toggleBtn.innerHTML = `
            <div class="flex items-center justify-center space-x-2">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0118.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z"></path>
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 13a3 3 0 11-6 0 3 3 0 016 0z"></path>
                </svg>
                <span>Start Camera</span>
            </div>
        `;
        toggleBtn.className = 'w-full mt-4 bg-primary hover:bg-primary-dark text-white font-medium py-3 px-4 rounded-lg transition-colors focus:ring-2 focus:ring-primary focus:ring-offset-2';
        updateScannerStatus('inactive');

        // Reset QR reader display
        qrReaderElement.innerHTML = `
            <div class="text-center text-gray-500">
                <svg class="w-16 h-16 mx-auto mb-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v1m6 11h2m-6 0h-2v4m0-11v3m0 0h.01M12 12h4.01M16 20h4M4 12h4m12 0h.01M5 8h2a1 1 0 001-1V5a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1zm12 0h2a1 1 0 001-1V5a1 1 0 00-1-1h-2a1 1 0 00-1 1v2a1 1 0 001 1zM5 20h2a1 1 0 001-1v-2a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1z"></path>
                </svg>
                <p class="font-medium">Click "Start Camera" to begin scanning</p>
            </div>
        `;
    }
}

// ============ GALLERY UPLOAD FUNCTIONS ============
function setupGalleryUpload() {
    const uploadInput = document.getElementById('qr-image-upload');
    if (uploadInput) {
        uploadInput.addEventListener('change', handleGalleryUpload);
    }
}

async function handleGalleryUpload(event) {
    const file = event.target.files[0];
    if (!file) return;

    // Validate file type
    if (!file.type.startsWith('image/')) {
        showMessage('Please select a valid image file.', 'error');
        return;
    }

    updateStatus('Processing uploaded image...');
    updateScannerStatus('processing');

    const reader = new FileReader();
    reader.onload = function(e) {
        const img = new Image();
        img.onload = function() {
            try {
                // Create canvas to process image
                const canvas = document.createElement('canvas');
                const ctx = canvas.getContext('2d');

                canvas.width = img.width;
                canvas.height = img.height;
                ctx.drawImage(img, 0, 0);

                // Get image data for QR detection
                const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);

                // Use jsQR library to detect QR code
                const code = jsQR(imageData.data, canvas.width, canvas.height);

                if (code) {
                    console.log('QR code detected from gallery:', code.data);
                    showMessage('QR code detected from image!', 'success');
                    updateStatus('QR code found in image');

                    // Process the QR code using the same handler
                    handleQRCodeScan(code.data);
                } else {
                    showMessage('No QR code found in the image. Please try another image.', 'error');
                    updateStatus('No QR code found in image');
                    updateScannerStatus('inactive');
                }
            } catch (error) {
                console.error('Error processing image:', error);
                showMessage('Error processing image. Please try again.', 'error');
                updateStatus('Error processing image');
                updateScannerStatus('inactive');
            }
        };

        img.onerror = function() {
            showMessage('Error loading image. Please try another file.', 'error');
            updateStatus('Error loading image');
            updateScannerStatus('inactive');
        };

        img.src = e.target.result;
    };

    reader.onerror = function() {
        showMessage('Error reading file. Please try again.', 'error');
        updateStatus('Error reading file');
        updateScannerStatus('inactive');
    };

    reader.readAsDataURL(file);

    // Clear the input
    event.target.value = '';
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

        updateStatus('Camera active - Please scan QR code');
        updateScannerStatus('active');

    } catch (error) {
        console.error('Error starting QR scanner:', error);
        updateStatus('Camera Error - Please check permissions or try gallery upload');
        updateScannerStatus('error');
        isCameraActive = false;

        // Reset button state
        const toggleBtn = document.getElementById('camera-toggle-btn');
        if (toggleBtn) {
            toggleBtn.innerHTML = `
                <div class="flex items-center justify-center space-x-2">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0118.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z"></path>
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 13a3 3 0 11-6 0 3 3 0 016 0z"></path>
                    </svg>
                    <span>Start Camera</span>
                </div>
            `;
            toggleBtn.className = 'w-full mt-4 bg-primary hover:bg-primary-dark text-white font-medium py-3 px-4 rounded-lg transition-colors focus:ring-2 focus:ring-primary focus:ring-offset-2';
        }
    }
}

async function stopQRScanner() {
    if (qrScanner) {
        try {
            await qrScanner.stop();
            qrScanner = null;
            updateScannerStatus('inactive');
        } catch (error) {
            console.error('Error stopping QR scanner:', error);
        }
    }
}

// ============ UNIFIED QR CODE HANDLER ============
async function handleQRCodeScan(qrCode) {
    // Prevent duplicate scans
    if (scanCooldown) {
        console.log('Scan cooldown active, ignoring scan');
        return;
    }

    scanCooldown = true;
    setTimeout(() => { scanCooldown = false; }, 2000);
    // Check if it's an authorized QR code
    if (qrCode === MATCH_QR_STRING) {
        updateStatus('Authorized QR code detected!');
        updateScannerStatus('success');
        showMessage('Authorized QR code detected!', 'success');
        await handleAuthorizedUser();
    } else {
        updateStatus('Invalid QR code. Please scan the correct QR code.');
        updateScannerStatus('error');
        showMessage('Invalid QR code. Please scan the authorized QR code.', 'error');
    }
}

// ============ STATUS UPDATE FUNCTIONS ============
function updateScannerStatus(status) {
    const scannerDot = document.getElementById('scanner-dot');
    const scannerText = document.getElementById('scanner-text');

    if (scannerDot && scannerText) {
        scannerDot.className = 'w-2 h-2 rounded-full';

        switch (status) {
            case 'active':
                scannerDot.classList.add('status-active');
                scannerText.textContent = 'Active';
                break;
            case 'inactive':
                scannerDot.classList.add('status-inactive');
                scannerText.textContent = 'Inactive';
                break;
            case 'processing':
                scannerDot.classList.add('status-warning');
                scannerText.textContent = 'Processing';
                break;
            case 'success':
                scannerDot.classList.add('status-success');
                scannerText.textContent = 'Success';
                break;
            case 'error':
                scannerDot.classList.add('status-error');
                scannerText.textContent = 'Error';
                break;
            default:
                scannerDot.classList.add('status-inactive');
                scannerText.textContent = 'Inactive';
        }
    }
}

// ============ STEP 2: IF AUTHORIZED - CHECK TEMP STORAGE ============
async function handleAuthorizedUser() {
    console.log('Authorized user detected');

    // Check temp storage for existing user data
    const tempUserData = checkTempUserData();

    if (tempUserData && tempUserData.id) {
        // User data exists in temp storage, proceed with attendance
        // disableForm();
        currentUser = tempUserData;
        isUserRegistered = true;
        await processAttendance();
    } else {
        // No user data in temp storage, enable registration form
        await handleUnregisteredUser();
    }
}

function primary_check(){
    const tempData = localStorage.getItem('tempUserData');
    console.log('Temporary user data:', tempData);
    if (!tempData) {
        console.log('No temporary user data found');
        showMessage("No user data found. Scan the Qr to activate the form.", 'warning');
        // Update the heading dynamically
        const heading = document.getElementById("main-heading");
        if (heading) {
            heading.textContent = "Scan the QR to activate the form";
            // heading.textContent = "Smart QR Attendance";
        }
        // Disable the form until QR is scanned
        disableForm();
        return null;
    }

}

function checkTempUserData() {
    const tempData = localStorage.getItem('tempUserData');
    console.log('Temporary user data:', tempData);
    disableForm()
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

// ============ FORM DISABLE/ENABLE FUNCTIONS ============
function disableForm() {
    if (!userFormCard) return;

    userFormCard.style.display = 'none';
}

// new function:
function enableForm() {
    if (!userFormCard) return;

    console.log('Enabling form...');

    // Make the form card visible again
    userFormCard.style.display = 'block'; // Show the element if it was hidden using display:none
    // userFormCard.classList.remove('hidden'); // If you used Tailwind's 'hidden' class instead

    // Enable all form inputs
    const formInputs = userFormCard.querySelectorAll('input, button, select');
    formInputs.forEach(input => {
        input.disabled = false;
        input.classList.remove('opacity-50', 'cursor-not-allowed');
    });

    // Restore form title
    const formTitle = userFormCard.querySelector('h2');
    if (formTitle) {
        formTitle.textContent = 'Employee Registration';
        formTitle.classList.remove('text-gray-500');
        formTitle.classList.add('text-gray-900');
    }

    // Re-enable the entire form
    const form = userFormCard.querySelector('form');
    if (form) {
        form.style.pointerEvents = 'auto';
        form.classList.remove('opacity-50');
    }

    // Make sure the form card is fully interactive and visible
    userFormCard.style.pointerEvents = 'auto';
    userFormCard.classList.remove('opacity-50');

    // Update the main heading
    const heading = document.getElementById("main-heading");
    if (heading) {
        heading.textContent = "Form Activated";
    }
}


// ============ STEP 3: IF NOT REGISTERED - COLLECT USER DETAILS ============
async function handleUnregisteredUser() {
    console.log('User not registered, enabling registration form');

    // Stop QR scanner temporarily
    await stopQRScanner();
    isCameraActive = false;

    // Reset camera button
    const toggleBtn = document.getElementById('camera-toggle-btn');
    if (toggleBtn) {
        toggleBtn.innerHTML = `
            <div class="flex items-center justify-center space-x-2">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0118.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z"></path>
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 13a3 3 0 11-6 0 3 3 0 016 0z"></path>
                </svg>
                <span>Start Camera</span>
            </div>
        `;
        toggleBtn.className = 'w-full mt-4 bg-primary hover:bg-primary-dark text-white font-medium py-3 px-4 rounded-lg transition-colors focus:ring-2 focus:ring-primary focus:ring-offset-2';
    }

    // Enable and show registration form
    enableForm();
    showUserRegistrationForm();

    updateStatus('Please fill in your details to register');
    updateScannerStatus('inactive');
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

    // Update heading to "QR Scanner" when form is submitted
    const heading = document.getElementById("main-heading");
    if (heading) {
        heading.textContent = "Scan the QR to mark attendance";
    }

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

        // Try to register user (Flask backend will handle existing users)
        const response = await fetch('/api/register', {
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
            disableForm();
            if (result.existing_user) {
                showMessage('User already registered! Please scan the QR code again.', 'info');
            } else {
                showMessage('Registration successful! Please scan the QR code again.', 'success');
            }

            // Update form status
            updateFormStatus('success');

            updateStatus('Registration complete - Ready to scan QR code');

        } else {
            showMessage(result.error || 'Registration failed', 'error');
            updateFormStatus('error');
        }

    } catch (error) {
        console.error('Registration error:', error);
        showMessage('Registration failed. Please try again.', 'error');
        updateFormStatus('error');
    }
}

function updateFormStatus(status) {
    const formDot = document.getElementById('form-dot');
    const formText = document.getElementById('form-text');

    if (formDot && formText) {
        formDot.className = 'w-2 h-2 rounded-full';

        switch (status) {
            case 'success':
                formDot.classList.add('status-success');
                formText.textContent = 'Complete';
                break;
            case 'error':
                formDot.classList.add('status-error');
                formText.textContent = 'Error';
                break;
            default:
                formDot.classList.add('bg-red-400');
                formText.textContent = 'Required';
        }
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
    isCameraActive = false;

    // Show user info
    showUserInfo();

    // Check current attendance status
    const attendanceStatus = await checkAttendanceStatus();


    // Require location before proceeding
    const locationGranted = await captureLocationAndTime();
    if (!locationGranted) {
        showMessage('Location access is required for attendance. Please enable location permissions and try again.', 'error');
        updateStatus('Location permission required');
        
        // Reset camera button
        const toggleBtn = document.getElementById('camera-toggle-btn');
        if (toggleBtn) {
            toggleBtn.innerHTML = `
                <div class="flex items-center justify-center space-x-2">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0118.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z"></path>
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 13a3 3 0 11-6 0 3 3 0 016 0z"></path>
                    </svg>
                    <span>Start Camera</span>
                </div>
            `;
            toggleBtn.className = 'w-full mt-4 bg-primary hover:bg-primary-dark text-white font-medium py-3 px-4 rounded-lg transition-colors focus:ring-2 focus:ring-primary focus:ring-offset-2';
        }
        return;  // Stop here if location not allowed
    }

    // Process check-in or check-out based on current status
    if (attendanceStatus === 'not_checked_in') {
        await performCheckIn();
        await updateStatusCard();  // After check-in, check-out, or registration

    } else if (attendanceStatus === 'checked_in') {
        await performCheckOut();
        await updateStatusCard();  // After check-in, check-out, or registration

    } else {
        showMessage('Attendance already completed for today.', 'info');
        await updateStatusCard();  // After check-in, check-out, or registration

    }

    // Reset camera button after attendance
    const toggleBtn = document.getElementById('camera-toggle-btn');
    if (toggleBtn) {
        toggleBtn.innerHTML = `
            <div class="flex items-center justify-center space-x-2">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0118.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z"></path>
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 13a3 3 0 11-6 0 3 3 0 016 0z"></path>
            </svg>
            <span>Start Camera</span>
        </div>
        `;
        toggleBtn.className = 'w-full mt-4 bg-primary hover:bg-primary-dark text-white font-medium py-3 px-4 rounded-lg transition-colors focus:ring-2 focus:ring-primary focus:ring-offset-2';
    }

    // Allow user to scan again after 3 seconds
    setTimeout(() => {
        updateStatus('Ready for next QR scan');
        updateScannerStatus('inactive');
    }, 3000);
}

async function checkAttendanceStatus() {
    try {
        const response = await fetch('/api/check-status', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ user_id: currentUser.id })
        });

        if (response.ok) {
            const result = await response.json();
            return result.status;
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
        const locationGranted = await requestLocationPermission();
        if (!locationGranted) {
            updateStatus('Location permission denied');
            return false;
        }
    }

    if (currentLocation) {
        console.log('Location captured:', currentLocation);
        updateStatus('Location captured successfully');
        return true;
    } else {
        updateStatus('Location not available');
        return false;
    }
}

async function performCheckIn() {
    try {
        updateStatus('Checking in...');

        const response = await fetch('/api/check-in', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                user_id: currentUser.id,
                location: currentLocation
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

        const response = await fetch('/api/check-out', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                user_id: currentUser.id,
                location: currentLocation
            })
        });

        const result = await response.json();

        if (response.ok) {
            showMessage('Check-out successfull!', 'success');
            updateStatus('Checked out successfully');
        } else {
            showMessage(result.error || 'Check-out failed', 'error');
        }

    } catch (error) {
        console.error('Check-out error:', error);
        showMessage('Check-out failed. Please try again.', 'error');
    }
}

async function updateStatusCard() {
    const container = document.getElementById('attendance-status');
    if (!container || !currentUser) return;

    try {
        const response = await fetch('/api/check-status', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: currentUser.id })
        });

        if (!response.ok) throw new Error('Failed to fetch status');
        const data = await response.json();
        const status = data.status;
        const checkIn = data.check_in_time;
        const checkOut = data.check_out_time;

        // Create status HTML
        let html = '';
        if (status === 'not_checked_in') {
            html = `
                <div class="text-center">
                    <div class="w-16 h-16 bg-yellow-100 rounded-full flex items-center justify-center mx-auto mb-4">
                        <svg class="w-8 h-8 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                  d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                        </svg>
                    </div>
                    <p class="text-lg font-medium text-gray-900">Ready to Check In</p>
                    <p class="text-sm text-gray-600">Scan QR code to mark your attendance</p>
                </div>
            `;
        } else if (status === 'checked_in') {
            html = `
                <div class="text-center">
                    <div class="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                        <svg class="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                  d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                        </svg>
                    </div>
                    <p class="text-lg font-medium text-gray-900">Checked In</p>
                    <p class="text-sm text-gray-600">Check-in: ${checkIn}</p>
                    <p class="text-xs text-gray-500 mt-1">Scan QR code to check out</p>
                </div>
            `;
        } else if (status === 'completed') {
            html = `
                <div class="text-center">
                    <div class="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                        <svg class="w-8 h-8 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                  d="M5 13l4 4L19 7"></path>
                        </svg>
                    </div>
                    <p class="text-lg font-medium text-gray-900">Attendance Complete</p>
                    <div class="text-sm text-gray-600 space-y-1">
                        <p>Check-in: ${checkIn}</p>
                        <p>Check-out: ${checkOut}</p>
                    </div>
                </div>
            `;
        } else {
            html = `
                <div class="text-center text-gray-500">
                    <p>Save your information to view status</p>
                </div>
            `;
        }

        container.innerHTML = html;

    } catch (error) {
        console.error('Error updating status card:', error);
        document.getElementById('attendance-status').innerHTML = `
            <div class="text-center text-gray-500">
                <p>Unable to load status. Try again later.</p>
            </div>
        `;
    }
}


// ============ UTILITY FUNCTIONS ============
function showUserInfo() {
    if (userInfoDisplay && currentUser) {
        userInfoDisplay.innerHTML = `
            <div class="bg-white rounded-lg shadow-lg border border-gray-200 p-6">
                <h3 class="text-xl font-semibold text-gray-900 mb-4">Welcome, ${currentUser.fullName}!</h3>
                <div class="space-y-2">
                    <p><span class="font-medium">Employee ID:</span> ${currentUser.employeeId}</p>
                    <p><span class="font-medium">Department:</span> ${currentUser.department}</p>
                    <p><span class="font-medium">Mobile:</span> ${currentUser.mobile}</p>
                </div>
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

function showMessage(message, type) {
    console.log(`${type.toUpperCase()}: ${message}`);

    const messageContainer = document.getElementById('message-container');
    if (messageContainer) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `p-4 rounded-lg mb-4 ${getMessageClass(type)}`;
        messageDiv.textContent = message;

        messageContainer.appendChild(messageDiv);

        // Auto-remove message after 5 seconds
        setTimeout(() => {
            if (messageDiv.parentNode) {
                messageDiv.parentNode.removeChild(messageDiv);
            }
        }, 5000);
    }
}

function getMessageClass(type) {
    switch (type) {
        case 'success':
            return 'bg-green-100 text-green-800 border border-green-200';
        case 'error':
            return 'bg-red-100 text-red-800 border border-red-200';
        case 'warning':
            return 'bg-yellow-100 text-yellow-800 border border-yellow-200';
        case 'info':
            return 'bg-blue-100 text-blue-800 border border-blue-200';
        default:
            return 'bg-gray-100 text-gray-800 border border-gray-200';
    }
}

// Location permission request
async function requestLocationPermission() {
    try {
        if (navigator.geolocation) {
            const position = await new Promise((resolve, reject) => {
                navigator.geolocation.getCurrentPosition(resolve, reject, {
                    enableHighAccuracy: true,
                    timeout: 10000,
                    maximumAge: 60000
                });
            });

            currentLocation = {
                latitude: position.coords.latitude,
                longitude: position.coords.longitude,
                accuracy: position.coords.accuracy
            };

            console.log('Location permission granted');
            return true;
        } else {
            console.log('Geolocation not supported');
            return false;
        }
    } catch (error) {
        console.error('Location permission error:', error);
        return false;
    }
}

// Form submission setup
function setupFormSubmission() {
    const form = document.getElementById('user-form');
    if (form) {
        form.addEventListener('submit', handleUserRegistration);
    }
}
