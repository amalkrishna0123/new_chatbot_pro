# API Integration Guide for Frontend

This guide shows how to integrate the Django backend with your existing HTML/JavaScript frontend.

## Quick Start

### 1. Start the Backend Server

```bash
python manage.py runserver
```

The API will be available at: `http://127.0.0.1:8000/`

### 2. Update Frontend JavaScript

## Authentication Flow

### Step 1: Send OTP

Replace the `sendOTP()` function in your HTML:

```javascript
async function sendOTP() {
    const email = document.getElementById('emailInput').value;
    if (!email) {
        document.getElementById('emailInput').focus();
        return;
    }
    
    try {
        const response = await fetch('http://127.0.0.1:8000/api/auth/send-otp/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ email: email })
        });
        
        const data = await response.json();
        
        if (data.success) {
            document.getElementById('login-step-1').classList.add('hidden');
            document.getElementById('login-step-2').classList.remove('hidden');
            document.getElementById('login-step-2').classList.add('fade-in');
            
            // In development, the OTP might be returned in response
            if (data.otp) {
                console.log('OTP:', data.otp); // For testing
            }
        } else {
            alert('Failed to send OTP: ' + data.message);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Failed to send OTP. Please try again.');
    }
}
```

### Step 2: Verify OTP

Replace the `verifyOTP()` function:

```javascript
async function verifyOTP() {
    const email = document.getElementById('emailInput').value;
    const otp = document.getElementById('otpInput').value;
    
    if (!otp || otp.length !== 4) {
        alert('Please enter the 4-digit OTP');
        return;
    }
    
    try {
        const response = await fetch('http://127.0.0.1:8000/api/auth/verify-otp/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'include', // Important for session cookies
            body: JSON.stringify({
                email: email,
                otp_code: otp
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            state.user = data.user;
            showView('view-landing');
        } else {
            alert(data.message || 'Invalid OTP');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Verification failed. Please try again.');
    }
}
```

### Step 3: Check Authentication Status

Add this function to check if user is already logged in:

```javascript
async function checkAuth() {
    try {
        const response = await fetch('http://127.0.0.1:8000/api/auth/check/', {
            method: 'GET',
            credentials: 'include'
        });
        
        const data = await response.json();
        
        if (data.authenticated) {
            state.user = data.user;
            showView('view-landing');
            return true;
        } else {
            showView('view-login');
            return false;
        }
    } catch (error) {
        console.error('Error:', error);
        showView('view-login');
        return false;
    }
}

// Call this on page load
window.addEventListener('DOMContentLoaded', () => {
    checkAuth();
});
```

## Insurance Flow Integration

### 1. Create Insurance Application

```javascript
async function createInsuranceApplication(applicationData) {
    try {
        const response = await fetch('http://127.0.0.1:8000/api/insurance/applications/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'include',
            body: JSON.stringify(applicationData)
        });
        
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error:', error);
        throw error;
    }
}

// Example usage in your flow
function askUpload() {
    // After collecting all data, create the application
    const applicationData = {
        language: state.insuranceData.lang,
        application_type: state.insuranceData.type,
        dependent_type: state.insuranceData.depType || '',
        salary_range: state.insuranceData.salary,
        emirates_id: state.insuranceData.eid,
        full_name: state.insuranceData.name,
        expiry_date: state.insuranceData.expiry,
        nationality: state.insuranceData.nationality,
        gender: state.insuranceData.gender,
        issuing_place: state.insuranceData.issuingPlace,
        mobile_number: state.insuranceData.mobile,
        occupation: state.insuranceData.occupation || '',
        status: 'In Progress'
    };
    
    createInsuranceApplication(applicationData)
        .then(response => {
            if (response.id) {
                state.insuranceData.applicationId = response.id;
                // Continue with document upload
            }
        })
        .catch(error => {
            console.error('Failed to create application:', error);
        });
}
```

### 2. Upload Emirates ID Document

```javascript
async function uploadEmiratesID(file, applicationId) {
    const formData = new FormData();
    formData.append('document', file);
    if (applicationId) {
        formData.append('application_id', applicationId);
    }
    
    try {
        const response = await fetch('http://127.0.0.1:8000/api/insurance/process-ocr/', {
            method: 'POST',
            credentials: 'include',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Update state with OCR extracted data
            state.insuranceData = {
                ...state.insuranceData,
                ...data.data
            };
            
            // Show review modal
            document.getElementById('view-review').classList.remove('hidden');
            renderReviewForm();
        }
        
        return data;
    } catch (error) {
        console.error('Error:', error);
        throw error;
    }
}

// Update simulateUpload function
function simulateUpload() {
    // Create file input
    const fileInput = document.createElement('input');
    fileInput.type = 'file';
    fileInput.accept = 'image/*,.pdf';
    
    fileInput.onchange = async (e) => {
        const file = e.target.files[0];
        if (file) {
            addChatBubble("Uploading ID Document...", 'user');
            hideInputOptions();
            
            showTyping();
            
            try {
                const result = await uploadEmiratesID(file, state.insuranceData.applicationId);
                addChatBubble("Document scanned successfully!", 'bot');
            } catch (error) {
                addChatBubble("Failed to process document. Please try again.", 'bot');
            }
        }
    };
    
    fileInput.click();
}
```

### 3. Get Product Recommendations

```javascript
async function getProductRecommendations(salaryRange, issuingPlace) {
    try {
        const response = await fetch('http://127.0.0.1:8000/api/insurance/recommendations/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'include',
            body: JSON.stringify({
                salary_range: salaryRange,
                issuing_place: issuingPlace
            })
        });
        
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error:', error);
        throw error;
    }
}

// Update calculateAndShowProducts function
async function calculateAndShowProducts() {
    const place = state.insuranceData.issuingPlace;
    const salary = state.insuranceData.salary;
    
    try {
        const result = await getProductRecommendations(salary, place);
        
        if (result.success && result.count > 0) {
            addChatBubble(`I found ${result.count} eligible plan(s) for you.`, 'bot');
            
            // Display products (use result.products instead of mock data)
            const plans = result.products;
            
            setTimeout(() => {
                const container = document.getElementById('chat-stream');
                const cardsContainer = document.createElement('div');
                cardsContainer.className = 'flex flex-col md:flex-row gap-4 mt-2 fade-in mb-4 w-full md:w-auto';
                
                plans.forEach((plan) => {
                    const card = document.createElement('div');
                    card.className = 'bg-white border border-slate-200 p-5 rounded-[20px] shadow-sm hover:shadow-md hover:border-brand-500 transition-all cursor-pointer flex-1 md:min-w-[260px] group';
                    card.onclick = () => selectProduct(plan);
                    
                    card.innerHTML = `
                        <div class="flex justify-between items-start mb-4">
                            <div>
                                <h4 class="font-bold text-lg text-slate-800">${plan.plan_name}</h4>
                                <span class="text-[10px] font-bold bg-slate-100 text-slate-500 px-2 py-1 rounded mt-1 inline-block group-hover:bg-brand-50 group-hover:text-brand-600 transition-colors">${plan.plan_type}</span>
                            </div>
                            <div class="w-8 h-8 rounded-full bg-slate-50 flex items-center justify-center group-hover:bg-brand-500 transition-colors">
                                <i data-lucide="arrow-right" class="w-4 h-4 text-slate-400 group-hover:text-white"></i>
                            </div>
                        </div>
                        <div class="text-2xl font-bold text-slate-900 mb-1"><span class="text-sm font-medium text-slate-400">AED</span> ${plan.premium_amount}</div>
                        <div class="text-[10px] text-green-600 font-bold uppercase tracking-wide flex items-center gap-1">
                            <i data-lucide="check" class="w-3 h-3"></i> Eligible
                        </div>
                    `;
                    cardsContainer.appendChild(card);
                });
                
                container.appendChild(cardsContainer);
                lucide.createIcons();
                cardsContainer.scrollIntoView({ behavior: 'smooth', block: 'end' });
            }, 800);
        } else {
            addChatBubble("I apologize, but no eligible products are available for your profile.", 'bot');
        }
    } catch (error) {
        console.error('Error fetching recommendations:', error);
        addChatBubble("Failed to fetch product recommendations. Please try again.", 'bot');
    }
}
```

### 4. Create Policy

```javascript
async function createPolicy(applicationId, planData) {
    try {
        const response = await fetch('http://127.0.0.1:8000/api/insurance/create-policy/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'include',
            body: JSON.stringify({
                application_id: applicationId,
                plan_name: planData.plan_name,
                plan_type: planData.plan_type,
                premium_amount: planData.premium_amount
            })
        });
        
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error:', error);
        throw error;
    }
}

// Update selectProduct and finalizeInsurance
async function selectProduct(plan) {
    addChatBubble(`I'll take the ${plan.plan_name} (${plan.plan_type}) plan.`, 'user');
    showTyping();
    
    try {
        const result = await createPolicy(state.insuranceData.applicationId, plan);
        
        if (result.success) {
            const policy = result.policy;
            
            const successHtml = `
                <div class="bg-gradient-to-br from-green-500 to-emerald-600 rounded-[24px] p-6 text-white shadow-lg w-full md:min-w-[320px]">
                    <div class="flex items-center gap-3 mb-4">
                        <div class="w-10 h-10 bg-white/20 rounded-full flex items-center justify-center backdrop-blur-sm">
                            <i data-lucide="check" class="w-6 h-6 text-white"></i>
                        </div>
                        <div>
                            <h3 class="font-bold text-lg">Success!</h3>
                            <p class="text-xs text-white/80">Policy Active</p>
                        </div>
                    </div>
                    <div class="bg-white/10 rounded-xl p-4 backdrop-blur-sm mb-4">
                        <div class="flex justify-between text-sm mb-1"><span>Policy No:</span> <span class="font-mono font-bold">${policy.policy_number}</span></div>
                        <div class="flex justify-between text-sm"><span>Premium:</span> <span class="font-bold">AED ${policy.premium_amount}</span></div>
                    </div>
                    <button onclick="window.location.href='https://google.com'" class="w-full bg-white text-emerald-600 font-bold py-3 rounded-xl text-xs uppercase tracking-wider hover:bg-emerald-50 transition-colors">
                        Continue
                    </button>
                </div>
            `;
            
            addChatBubble(successHtml, 'bot', true);
            setTimeout(() => lucide.createIcons(), 100);
        } else {
            addChatBubble(result.message || "Failed to create policy.", 'bot');
        }
    } catch (error) {
        console.error('Error creating policy:', error);
        addChatBubble("Failed to create policy. Please try again.", 'bot');
    }
}
```

### 5. Get User Policies

```javascript
async function getUserPolicies() {
    try {
        const response = await fetch('http://127.0.0.1:8000/api/insurance/policies/active/', {
            method: 'GET',
            credentials: 'include'
        });
        
        const data = await response.json();
        
        if (data.success) {
            return data.policies;
        }
        
        return [];
    } catch (error) {
        console.error('Error:', error);
        return [];
    }
}

// Update showDetails function
async function showDetails() {
    showView('view-details');
    const list = document.getElementById('policies-list');
    list.innerHTML = '';
    
    const policies = await getUserPolicies();
    
    if (policies.length === 0) {
        document.getElementById('no-policies').classList.remove('hidden');
        return;
    } else {
        document.getElementById('no-policies').classList.add('hidden');
    }
    
    policies.forEach(p => {
        const card = document.createElement('div');
        card.className = 'bg-white p-6 md:p-8 rounded-[24px] shadow-sm border border-slate-100 flex flex-col md:flex-row md:items-center justify-between gap-4 hover:shadow-md transition-all';
        card.innerHTML = `
            <div class="flex gap-4 items-start">
                <div class="w-12 h-12 bg-blue-50 rounded-2xl flex items-center justify-center flex-none text-blue-600">
                    <i data-lucide="shield" class="w-6 h-6"></i>
                </div>
                <div>
                    <div class="text-[10px] text-slate-400 font-bold font-mono uppercase tracking-widest mb-1">${p.policy_number}</div>
                    <h3 class="text-base font-bold text-slate-900">${p.plan_name} <span class="text-xs font-normal text-slate-500 bg-slate-100 px-2 py-0.5 rounded ml-2">${p.plan_type}</span></h3>
                    <p class="text-sm text-slate-500 mt-1 font-medium">Insured: ${p.insured_name}</p>
                </div>
            </div>
            <div class="flex items-center justify-between md:flex-col md:items-end md:justify-center border-t md:border-0 border-slate-100 pt-4 md:pt-0">
                <div class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-green-50 text-green-700 text-[10px] font-bold uppercase tracking-wide border border-green-100">
                    <div class="w-2 h-2 rounded-full bg-green-500"></div> ${p.status}
                </div>
                <div class="text-xs text-slate-400 mt-0 md:mt-2 font-medium">${new Date(p.issue_date).toLocaleDateString()}</div>
            </div>
        `;
        list.appendChild(card);
    });
    
    lucide.createIcons();
}
```

## Testing the Integration

### 1. Test Authentication
1. Open the page in browser: `http://127.0.0.1:8000/`
2. Enter your email
3. Check console for OTP (in development mode)
4. Enter OTP and verify login

### 2. Test Insurance Flow
1. Click "Get Medical Insurance"
2. Follow the chat flow
3. Upload an Emirates ID (any image for testing)
4. Review and confirm details
5. Select a product
6. Verify policy creation

### 3. Check Admin Panel
1. Create superuser: `python manage.py createsuperuser`
2. Login at: `http://127.0.0.1:8000/admin/`
3. View all created records

## Important Notes

- Always include `credentials: 'include'` in fetch requests for session handling
- CSRF tokens are handled automatically by Django sessions
- In production, update CORS settings to match your frontend domain
- All API responses follow the format: `{success: true/false, ...data}`

## Error Handling

Add global error handler:

```javascript
async function apiCall(url, options = {}) {
    try {
        const response = await fetch(url, {
            ...options,
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

// Usage
const data = await apiCall('http://127.0.0.1:8000/api/auth/send-otp/', {
    method: 'POST',
    body: JSON.stringify({ email: 'user@example.com' })
});
```
