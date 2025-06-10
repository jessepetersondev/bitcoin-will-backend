// Enhanced Will Creation JavaScript

// Will creation state
let currentWill = {
    id: null,
    title: '',
    personal_info: {},
    bitcoin_assets: { wallets: [], exchanges: [], other_crypto: [] },
    beneficiaries: [],
    instructions: {}
};

let currentStep = 1;
const totalSteps = 5;

// Initialize will creation
function initializeWillCreation() {
    // Check if user is logged in
    if (!currentUser) {
        showAuthModal();
        return;
    }
    
    // Load will template
    loadWillTemplate();
    
    // Show will creation interface
    showWillCreationInterface();
}

// Load will template from backend
async function loadWillTemplate() {
    try {
        const response = await fetch(`${API_BASE_URL}/will/template`, {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
                'Content-Type': 'application/json'
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            currentWill = { ...currentWill, ...data.template };
        }
    } catch (error) {
        console.error('Failed to load will template:', error);
    }
}

// Show will creation interface
function showWillCreationInterface() {
    const mainContent = document.getElementById('main-content');
    
    mainContent.innerHTML = `
        <div class="will-creation-container">
            <div class="will-progress">
                <div class="progress-bar">
                    <div class="progress-fill" style="width: ${(currentStep / totalSteps) * 100}%"></div>
                </div>
                <div class="step-indicators">
                    ${Array.from({length: totalSteps}, (_, i) => `
                        <div class="step-indicator ${i + 1 <= currentStep ? 'active' : ''}" data-step="${i + 1}">
                            <span>${i + 1}</span>
                            <label>${getStepLabel(i + 1)}</label>
                        </div>
                    `).join('')}
                </div>
            </div>
            
            <div class="will-form-container">
                <div id="will-step-content">
                    ${getStepContent(currentStep)}
                </div>
                
                <div class="will-navigation">
                    <button id="prev-step" onclick="previousStep()" ${currentStep === 1 ? 'disabled' : ''}>
                        Previous
                    </button>
                    <button id="next-step" onclick="nextStep()">
                        ${currentStep === totalSteps ? 'Generate Will' : 'Next'}
                    </button>
                </div>
            </div>
        </div>
    `;
}

// Get step label
function getStepLabel(step) {
    const labels = {
        1: 'Personal Info',
        2: 'Bitcoin Assets',
        3: 'Beneficiaries',
        4: 'Instructions',
        5: 'Review & Generate'
    };
    return labels[step];
}

// Get step content
function getStepContent(step) {
    switch(step) {
        case 1:
            return getPersonalInfoForm();
        case 2:
            return getBitcoinAssetsForm();
        case 3:
            return getBeneficiariesForm();
        case 4:
            return getInstructionsForm();
        case 5:
            return getReviewForm();
        default:
            return '';
    }
}

// Personal Info Form
function getPersonalInfoForm() {
    const info = currentWill.personal_info || {};
    const address = info.address || {};
    
    return `
        <div class="form-section">
            <h2>Personal Information</h2>
            <p>Please provide your personal details for the will.</p>
            
            <div class="form-grid">
                <div class="form-group">
                    <label for="full_name">Full Legal Name *</label>
                    <input type="text" id="full_name" value="${info.full_name || ''}" required>
                </div>
                
                <div class="form-group">
                    <label for="date_of_birth">Date of Birth *</label>
                    <input type="date" id="date_of_birth" value="${info.date_of_birth || ''}" required>
                </div>
                
                <div class="form-group">
                    <label for="email">Email Address *</label>
                    <input type="email" id="email" value="${info.email || ''}" required>
                </div>
                
                <div class="form-group">
                    <label for="phone">Phone Number</label>
                    <input type="tel" id="phone" value="${info.phone || ''}">
                </div>
            </div>
            
            <h3>Address</h3>
            <div class="form-grid">
                <div class="form-group full-width">
                    <label for="street">Street Address *</label>
                    <input type="text" id="street" value="${address.street || ''}" required>
                </div>
                
                <div class="form-group">
                    <label for="city">City *</label>
                    <input type="text" id="city" value="${address.city || ''}" required>
                </div>
                
                <div class="form-group">
                    <label for="state">State/Province *</label>
                    <input type="text" id="state" value="${address.state || ''}" required>
                </div>
                
                <div class="form-group">
                    <label for="zip_code">ZIP/Postal Code *</label>
                    <input type="text" id="zip_code" value="${address.zip_code || ''}" required>
                </div>
                
                <div class="form-group">
                    <label for="country">Country *</label>
                    <input type="text" id="country" value="${address.country || 'United States'}" required>
                </div>
            </div>
        </div>
    `;
}

// Bitcoin Assets Form
function getBitcoinAssetsForm() {
    const assets = currentWill.bitcoin_assets || { wallets: [], exchanges: [], other_crypto: [] };
    
    return `
        <div class="form-section">
            <h2>Bitcoin & Cryptocurrency Assets</h2>
            <p>Document your Bitcoin wallets, exchange accounts, and other cryptocurrency holdings.</p>
            
            <div class="asset-section">
                <h3>Bitcoin Wallets</h3>
                <div id="wallets-container">
                    ${assets.wallets.map((wallet, index) => getWalletForm(wallet, index)).join('')}
                </div>
                <button type="button" onclick="addWallet()" class="add-button">+ Add Wallet</button>
            </div>
            
            <div class="asset-section">
                <h3>Exchange Accounts</h3>
                <div id="exchanges-container">
                    ${assets.exchanges.map((exchange, index) => getExchangeForm(exchange, index)).join('')}
                </div>
                <button type="button" onclick="addExchange()" class="add-button">+ Add Exchange</button>
            </div>
        </div>
    `;
}

// Wallet form
function getWalletForm(wallet = {}, index = 0) {
    return `
        <div class="wallet-form" data-index="${index}">
            <div class="form-header">
                <h4>Wallet ${index + 1}</h4>
                <button type="button" onclick="removeWallet(${index})" class="remove-button">Remove</button>
            </div>
            
            <div class="form-grid">
                <div class="form-group">
                    <label>Wallet Name *</label>
                    <input type="text" name="wallet_name_${index}" value="${wallet.name || ''}" placeholder="e.g., My Ledger Nano S">
                </div>
                
                <div class="form-group">
                    <label>Wallet Type *</label>
                    <select name="wallet_type_${index}">
                        <option value="hardware" ${wallet.type === 'hardware' ? 'selected' : ''}>Hardware Wallet</option>
                        <option value="software" ${wallet.type === 'software' ? 'selected' : ''}>Software Wallet</option>
                        <option value="paper" ${wallet.type === 'paper' ? 'selected' : ''}>Paper Wallet</option>
                        <option value="exchange" ${wallet.type === 'exchange' ? 'selected' : ''}>Exchange Wallet</option>
                    </select>
                </div>
                
                <div class="form-group full-width">
                    <label>Description</label>
                    <textarea name="wallet_description_${index}" placeholder="Brief description of this wallet">${wallet.description || ''}</textarea>
                </div>
                
                <div class="form-group full-width">
                    <label>Access Method *</label>
                    <textarea name="wallet_access_${index}" placeholder="How to access this wallet (without revealing sensitive info)">${wallet.access_method || ''}</textarea>
                </div>
                
                <div class="form-group">
                    <label>Seed Phrase Location</label>
                    <input type="text" name="wallet_seed_${index}" value="${wallet.seed_phrase_location || ''}" placeholder="Where the seed phrase is stored">
                </div>
                
                <div class="form-group">
                    <label>Private Key Location</label>
                    <input type="text" name="wallet_key_${index}" value="${wallet.private_key_location || ''}" placeholder="Where private keys are stored">
                </div>
                
                <div class="form-group full-width">
                    <label>Additional Notes</label>
                    <textarea name="wallet_notes_${index}" placeholder="Any additional important information">${wallet.additional_notes || ''}</textarea>
                </div>
            </div>
        </div>
    `;
}

// Exchange form
function getExchangeForm(exchange = {}, index = 0) {
    return `
        <div class="exchange-form" data-index="${index}">
            <div class="form-header">
                <h4>Exchange ${index + 1}</h4>
                <button type="button" onclick="removeExchange(${index})" class="remove-button">Remove</button>
            </div>
            
            <div class="form-grid">
                <div class="form-group">
                    <label>Exchange Name *</label>
                    <input type="text" name="exchange_name_${index}" value="${exchange.name || ''}" placeholder="e.g., Coinbase, Binance">
                </div>
                
                <div class="form-group">
                    <label>Username/Account ID</label>
                    <input type="text" name="exchange_username_${index}" value="${exchange.username || ''}" placeholder="Your username or account ID">
                </div>
                
                <div class="form-group">
                    <label>Email Address</label>
                    <input type="email" name="exchange_email_${index}" value="${exchange.email || ''}" placeholder="Email used for this account">
                </div>
                
                <div class="form-group">
                    <label>2FA Backup Location</label>
                    <input type="text" name="exchange_2fa_${index}" value="${exchange.two_factor_backup || ''}" placeholder="Where 2FA backup codes are stored">
                </div>
                
                <div class="form-group full-width">
                    <label>Additional Notes</label>
                    <textarea name="exchange_notes_${index}" placeholder="Any additional important information">${exchange.additional_notes || ''}</textarea>
                </div>
            </div>
        </div>
    `;
}

// Beneficiaries Form
function getBeneficiariesForm() {
    const beneficiaries = currentWill.beneficiaries || [];
    
    return `
        <div class="form-section">
            <h2>Beneficiaries</h2>
            <p>Specify who will inherit your Bitcoin and cryptocurrency assets.</p>
            
            <div id="beneficiaries-container">
                ${beneficiaries.map((beneficiary, index) => getBeneficiaryForm(beneficiary, index)).join('')}
            </div>
            
            <button type="button" onclick="addBeneficiary()" class="add-button">+ Add Beneficiary</button>
            
            <div class="percentage-check">
                <p><strong>Total Percentage: <span id="total-percentage">0</span>%</strong></p>
                <p class="note">The total percentage should equal 100%</p>
            </div>
        </div>
    `;
}

// Beneficiary form
function getBeneficiaryForm(beneficiary = {}, index = 0) {
    const address = beneficiary.address || {};
    const backup = beneficiary.backup_contact || {};
    
    return `
        <div class="beneficiary-form" data-index="${index}">
            <div class="form-header">
                <h4>Beneficiary ${index + 1}</h4>
                <button type="button" onclick="removeBeneficiary(${index})" class="remove-button">Remove</button>
            </div>
            
            <div class="form-grid">
                <div class="form-group">
                    <label>Full Name *</label>
                    <input type="text" name="beneficiary_name_${index}" value="${beneficiary.name || ''}" required>
                </div>
                
                <div class="form-group">
                    <label>Relationship *</label>
                    <input type="text" name="beneficiary_relationship_${index}" value="${beneficiary.relationship || ''}" placeholder="e.g., Spouse, Child, Friend" required>
                </div>
                
                <div class="form-group">
                    <label>Percentage of Assets *</label>
                    <input type="number" name="beneficiary_percentage_${index}" value="${beneficiary.percentage || ''}" min="0" max="100" onchange="updateTotalPercentage()" required>
                </div>
                
                <div class="form-group">
                    <label>Phone Number</label>
                    <input type="tel" name="beneficiary_phone_${index}" value="${beneficiary.phone || ''}">
                </div>
                
                <div class="form-group">
                    <label>Email Address</label>
                    <input type="email" name="beneficiary_email_${index}" value="${beneficiary.email || ''}">
                </div>
                
                <div class="form-group">
                    <label>Bitcoin Address (Optional)</label>
                    <input type="text" name="beneficiary_bitcoin_${index}" value="${beneficiary.bitcoin_address || ''}" placeholder="Their Bitcoin address for direct transfers">
                </div>
            </div>
            
            <h5>Address</h5>
            <div class="form-grid">
                <div class="form-group full-width">
                    <label>Street Address</label>
                    <input type="text" name="beneficiary_street_${index}" value="${address.street || ''}">
                </div>
                
                <div class="form-group">
                    <label>City</label>
                    <input type="text" name="beneficiary_city_${index}" value="${address.city || ''}">
                </div>
                
                <div class="form-group">
                    <label>State/Province</label>
                    <input type="text" name="beneficiary_state_${index}" value="${address.state || ''}">
                </div>
                
                <div class="form-group">
                    <label>ZIP/Postal Code</label>
                    <input type="text" name="beneficiary_zip_${index}" value="${address.zip_code || ''}">
                </div>
                
                <div class="form-group">
                    <label>Country</label>
                    <input type="text" name="beneficiary_country_${index}" value="${address.country || ''}">
                </div>
            </div>
            
            <h5>Backup Contact</h5>
            <div class="form-grid">
                <div class="form-group">
                    <label>Backup Contact Name</label>
                    <input type="text" name="backup_name_${index}" value="${backup.name || ''}">
                </div>
                
                <div class="form-group">
                    <label>Backup Contact Phone</label>
                    <input type="tel" name="backup_phone_${index}" value="${backup.phone || ''}">
                </div>
                
                <div class="form-group">
                    <label>Backup Contact Email</label>
                    <input type="email" name="backup_email_${index}" value="${backup.email || ''}">
                </div>
            </div>
        </div>
    `;
}

// Instructions Form
function getInstructionsForm() {
    const instructions = currentWill.instructions || {};
    const executor = instructions.executor || {};
    const lawyer = instructions.lawyer_contact || {};
    const emergencyContacts = instructions.emergency_contacts || [];
    
    return `
        <div class="form-section">
            <h2>Instructions & Executor</h2>
            <p>Provide detailed instructions for executing your will and managing your Bitcoin assets.</p>
            
            <h3>Executor Information</h3>
            <div class="form-grid">
                <div class="form-group">
                    <label>Executor Name *</label>
                    <input type="text" id="executor_name" value="${executor.name || ''}" required>
                </div>
                
                <div class="form-group">
                    <label>Relationship *</label>
                    <input type="text" id="executor_relationship" value="${executor.relationship || ''}" required>
                </div>
                
                <div class="form-group">
                    <label>Phone Number *</label>
                    <input type="tel" id="executor_phone" value="${executor.phone || ''}" required>
                </div>
                
                <div class="form-group">
                    <label>Email Address *</label>
                    <input type="email" id="executor_email" value="${executor.email || ''}" required>
                </div>
            </div>
            
            <h3>Distribution Instructions</h3>
            <div class="form-group">
                <label>How should your Bitcoin assets be distributed?</label>
                <textarea id="distribution_instructions" rows="4" placeholder="Provide detailed instructions on how your Bitcoin should be transferred to beneficiaries...">${instructions.distribution_instructions || ''}</textarea>
            </div>
            
            <h3>Technical Instructions</h3>
            <div class="form-group">
                <label>Technical guidance for accessing your Bitcoin</label>
                <textarea id="technical_instructions" rows="4" placeholder="Provide step-by-step technical instructions for accessing wallets, exchanges, etc...">${instructions.technical_instructions || ''}</textarea>
            </div>
            
            <h3>Emergency Contacts</h3>
            <div id="emergency-contacts-container">
                ${emergencyContacts.map((contact, index) => getEmergencyContactForm(contact, index)).join('')}
            </div>
            <button type="button" onclick="addEmergencyContact()" class="add-button">+ Add Emergency Contact</button>
            
            <h3>Legal Counsel (Optional)</h3>
            <div class="form-grid">
                <div class="form-group">
                    <label>Lawyer Name</label>
                    <input type="text" id="lawyer_name" value="${lawyer.name || ''}">
                </div>
                
                <div class="form-group">
                    <label>Law Firm</label>
                    <input type="text" id="lawyer_firm" value="${lawyer.firm || ''}">
                </div>
                
                <div class="form-group">
                    <label>Phone Number</label>
                    <input type="tel" id="lawyer_phone" value="${lawyer.phone || ''}">
                </div>
                
                <div class="form-group">
                    <label>Email Address</label>
                    <input type="email" id="lawyer_email" value="${lawyer.email || ''}">
                </div>
            </div>
            
            <h3>Additional Notes</h3>
            <div class="form-group">
                <label>Any additional instructions or information</label>
                <textarea id="additional_notes" rows="4" placeholder="Any other important information for your executor or beneficiaries...">${instructions.additional_notes || ''}</textarea>
            </div>
        </div>
    `;
}

// Emergency contact form
function getEmergencyContactForm(contact = {}, index = 0) {
    return `
        <div class="emergency-contact-form" data-index="${index}">
            <div class="form-header">
                <h5>Emergency Contact ${index + 1}</h5>
                <button type="button" onclick="removeEmergencyContact(${index})" class="remove-button">Remove</button>
            </div>
            
            <div class="form-grid">
                <div class="form-group">
                    <label>Name</label>
                    <input type="text" name="emergency_name_${index}" value="${contact.name || ''}">
                </div>
                
                <div class="form-group">
                    <label>Relationship</label>
                    <input type="text" name="emergency_relationship_${index}" value="${contact.relationship || ''}">
                </div>
                
                <div class="form-group">
                    <label>Phone</label>
                    <input type="tel" name="emergency_phone_${index}" value="${contact.phone || ''}">
                </div>
                
                <div class="form-group">
                    <label>Email</label>
                    <input type="email" name="emergency_email_${index}" value="${contact.email || ''}">
                </div>
            </div>
        </div>
    `;
}

// Review Form
function getReviewForm() {
    return `
        <div class="form-section">
            <h2>Review Your Will</h2>
            <p>Please review all the information below before generating your Bitcoin will document.</p>
            
            <div id="will-review-content">
                ${generateReviewContent()}
            </div>
            
            <div class="final-actions">
                <div class="form-group">
                    <label for="will_title">Will Title</label>
                    <input type="text" id="will_title" value="${currentWill.title || 'My Bitcoin Will'}" placeholder="Enter a title for your will">
                </div>
                
                <div class="legal-notice">
                    <h4>Important Legal Notice</h4>
                    <p>This document is a comprehensive record of your Bitcoin and cryptocurrency assets for estate planning purposes. 
                    It is strongly recommended that you:</p>
                    <ul>
                        <li>Have this document reviewed by qualified legal counsel</li>
                        <li>Ensure proper execution according to your local laws</li>
                        <li>Store the document securely</li>
                        <li>Inform trusted individuals of its existence and location</li>
                        <li>Update the document regularly as your assets change</li>
                    </ul>
                </div>
                
                <div class="checkbox-group">
                    <label>
                        <input type="checkbox" id="legal_acknowledgment" required>
                        I understand that this document should be reviewed by legal counsel and properly executed according to local laws.
                    </label>
                </div>
            </div>
        </div>
    `;
}

// Generate review content
function generateReviewContent() {
    let content = '';
    
    // Personal Info Review
    if (currentWill.personal_info && currentWill.personal_info.full_name) {
        content += `
            <div class="review-section">
                <h3>Personal Information</h3>
                <p><strong>Name:</strong> ${currentWill.personal_info.full_name}</p>
                <p><strong>Email:</strong> ${currentWill.personal_info.email || 'Not provided'}</p>
                <p><strong>Phone:</strong> ${currentWill.personal_info.phone || 'Not provided'}</p>
            </div>
        `;
    }
    
    // Bitcoin Assets Review
    if (currentWill.bitcoin_assets) {
        const wallets = currentWill.bitcoin_assets.wallets || [];
        const exchanges = currentWill.bitcoin_assets.exchanges || [];
        
        content += `
            <div class="review-section">
                <h3>Bitcoin Assets</h3>
                <p><strong>Wallets:</strong> ${wallets.length} wallet(s) documented</p>
                <p><strong>Exchanges:</strong> ${exchanges.length} exchange account(s) documented</p>
            </div>
        `;
    }
    
    // Beneficiaries Review
    if (currentWill.beneficiaries && currentWill.beneficiaries.length > 0) {
        const totalPercentage = currentWill.beneficiaries.reduce((sum, b) => sum + (parseFloat(b.percentage) || 0), 0);
        content += `
            <div class="review-section">
                <h3>Beneficiaries</h3>
                <p><strong>Number of Beneficiaries:</strong> ${currentWill.beneficiaries.length}</p>
                <p><strong>Total Percentage Allocated:</strong> ${totalPercentage}%</p>
                ${totalPercentage !== 100 ? '<p class="warning">⚠️ Total percentage does not equal 100%</p>' : ''}
            </div>
        `;
    }
    
    // Instructions Review
    if (currentWill.instructions && currentWill.instructions.executor && currentWill.instructions.executor.name) {
        content += `
            <div class="review-section">
                <h3>Executor & Instructions</h3>
                <p><strong>Executor:</strong> ${currentWill.instructions.executor.name}</p>
                <p><strong>Relationship:</strong> ${currentWill.instructions.executor.relationship}</p>
            </div>
        `;
    }
    
    return content || '<p>No information has been entered yet. Please go back and fill out the previous steps.</p>';
}

// Navigation functions
function nextStep() {
    if (validateCurrentStep()) {
        saveCurrentStepData();
        
        if (currentStep === totalSteps) {
            generateWillDocument();
        } else {
            currentStep++;
            showWillCreationInterface();
        }
    }
}

function previousStep() {
    if (currentStep > 1) {
        saveCurrentStepData();
        currentStep--;
        showWillCreationInterface();
    }
}

// Validate current step
function validateCurrentStep() {
    const requiredFields = document.querySelectorAll('[required]');
    let isValid = true;
    
    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            field.classList.add('error');
            isValid = false;
        } else {
            field.classList.remove('error');
        }
    });
    
    if (!isValid) {
        showNotification('Please fill in all required fields', 'error');
    }
    
    return isValid;
}

// Save current step data
function saveCurrentStepData() {
    switch(currentStep) {
        case 1:
            savePersonalInfo();
            break;
        case 2:
            saveBitcoinAssets();
            break;
        case 3:
            saveBeneficiaries();
            break;
        case 4:
            saveInstructions();
            break;
        case 5:
            currentWill.title = document.getElementById('will_title')?.value || 'My Bitcoin Will';
            break;
    }
}

// Save personal info
function savePersonalInfo() {
    currentWill.personal_info = {
        full_name: document.getElementById('full_name')?.value || '',
        date_of_birth: document.getElementById('date_of_birth')?.value || '',
        email: document.getElementById('email')?.value || '',
        phone: document.getElementById('phone')?.value || '',
        address: {
            street: document.getElementById('street')?.value || '',
            city: document.getElementById('city')?.value || '',
            state: document.getElementById('state')?.value || '',
            zip_code: document.getElementById('zip_code')?.value || '',
            country: document.getElementById('country')?.value || ''
        }
    };
}

// Save bitcoin assets
function saveBitcoinAssets() {
    const wallets = [];
    const exchanges = [];
    
    // Save wallets
    document.querySelectorAll('.wallet-form').forEach((form, index) => {
        const wallet = {
            name: form.querySelector(`[name="wallet_name_${index}"]`)?.value || '',
            type: form.querySelector(`[name="wallet_type_${index}"]`)?.value || '',
            description: form.querySelector(`[name="wallet_description_${index}"]`)?.value || '',
            access_method: form.querySelector(`[name="wallet_access_${index}"]`)?.value || '',
            seed_phrase_location: form.querySelector(`[name="wallet_seed_${index}"]`)?.value || '',
            private_key_location: form.querySelector(`[name="wallet_key_${index}"]`)?.value || '',
            additional_notes: form.querySelector(`[name="wallet_notes_${index}"]`)?.value || ''
        };
        if (wallet.name) wallets.push(wallet);
    });
    
    // Save exchanges
    document.querySelectorAll('.exchange-form').forEach((form, index) => {
        const exchange = {
            name: form.querySelector(`[name="exchange_name_${index}"]`)?.value || '',
            username: form.querySelector(`[name="exchange_username_${index}"]`)?.value || '',
            email: form.querySelector(`[name="exchange_email_${index}"]`)?.value || '',
            two_factor_backup: form.querySelector(`[name="exchange_2fa_${index}"]`)?.value || '',
            additional_notes: form.querySelector(`[name="exchange_notes_${index}"]`)?.value || ''
        };
        if (exchange.name) exchanges.push(exchange);
    });
    
    currentWill.bitcoin_assets = { wallets, exchanges, other_crypto: [] };
}

// Save beneficiaries
function saveBeneficiaries() {
    const beneficiaries = [];
    
    document.querySelectorAll('.beneficiary-form').forEach((form, index) => {
        const beneficiary = {
            name: form.querySelector(`[name="beneficiary_name_${index}"]`)?.value || '',
            relationship: form.querySelector(`[name="beneficiary_relationship_${index}"]`)?.value || '',
            percentage: parseFloat(form.querySelector(`[name="beneficiary_percentage_${index}"]`)?.value) || 0,
            phone: form.querySelector(`[name="beneficiary_phone_${index}"]`)?.value || '',
            email: form.querySelector(`[name="beneficiary_email_${index}"]`)?.value || '',
            bitcoin_address: form.querySelector(`[name="beneficiary_bitcoin_${index}"]`)?.value || '',
            address: {
                street: form.querySelector(`[name="beneficiary_street_${index}"]`)?.value || '',
                city: form.querySelector(`[name="beneficiary_city_${index}"]`)?.value || '',
                state: form.querySelector(`[name="beneficiary_state_${index}"]`)?.value || '',
                zip_code: form.querySelector(`[name="beneficiary_zip_${index}"]`)?.value || '',
                country: form.querySelector(`[name="beneficiary_country_${index}"]`)?.value || ''
            },
            backup_contact: {
                name: form.querySelector(`[name="backup_name_${index}"]`)?.value || '',
                phone: form.querySelector(`[name="backup_phone_${index}"]`)?.value || '',
                email: form.querySelector(`[name="backup_email_${index}"]`)?.value || ''
            }
        };
        if (beneficiary.name) beneficiaries.push(beneficiary);
    });
    
    currentWill.beneficiaries = beneficiaries;
}

// Save instructions
function saveInstructions() {
    const emergencyContacts = [];
    
    document.querySelectorAll('.emergency-contact-form').forEach((form, index) => {
        const contact = {
            name: form.querySelector(`[name="emergency_name_${index}"]`)?.value || '',
            relationship: form.querySelector(`[name="emergency_relationship_${index}"]`)?.value || '',
            phone: form.querySelector(`[name="emergency_phone_${index}"]`)?.value || '',
            email: form.querySelector(`[name="emergency_email_${index}"]`)?.value || ''
        };
        if (contact.name) emergencyContacts.push(contact);
    });
    
    currentWill.instructions = {
        executor: {
            name: document.getElementById('executor_name')?.value || '',
            relationship: document.getElementById('executor_relationship')?.value || '',
            phone: document.getElementById('executor_phone')?.value || '',
            email: document.getElementById('executor_email')?.value || ''
        },
        distribution_instructions: document.getElementById('distribution_instructions')?.value || '',
        technical_instructions: document.getElementById('technical_instructions')?.value || '',
        emergency_contacts: emergencyContacts,
        additional_notes: document.getElementById('additional_notes')?.value || '',
        lawyer_contact: {
            name: document.getElementById('lawyer_name')?.value || '',
            firm: document.getElementById('lawyer_firm')?.value || '',
            phone: document.getElementById('lawyer_phone')?.value || '',
            email: document.getElementById('lawyer_email')?.value || ''
        }
    };
}

// Add/Remove functions
function addWallet() {
    const container = document.getElementById('wallets-container');
    const index = container.children.length;
    container.insertAdjacentHTML('beforeend', getWalletForm({}, index));
}

function removeWallet(index) {
    const wallet = document.querySelector(`.wallet-form[data-index="${index}"]`);
    if (wallet) wallet.remove();
}

function addExchange() {
    const container = document.getElementById('exchanges-container');
    const index = container.children.length;
    container.insertAdjacentHTML('beforeend', getExchangeForm({}, index));
}

function removeExchange(index) {
    const exchange = document.querySelector(`.exchange-form[data-index="${index}"]`);
    if (exchange) exchange.remove();
}

function addBeneficiary() {
    const container = document.getElementById('beneficiaries-container');
    const index = container.children.length;
    container.insertAdjacentHTML('beforeend', getBeneficiaryForm({}, index));
}

function removeBeneficiary(index) {
    const beneficiary = document.querySelector(`.beneficiary-form[data-index="${index}"]`);
    if (beneficiary) beneficiary.remove();
    updateTotalPercentage();
}

function addEmergencyContact() {
    const container = document.getElementById('emergency-contacts-container');
    const index = container.children.length;
    container.insertAdjacentHTML('beforeend', getEmergencyContactForm({}, index));
}

function removeEmergencyContact(index) {
    const contact = document.querySelector(`.emergency-contact-form[data-index="${index}"]`);
    if (contact) contact.remove();
}

// Update total percentage
function updateTotalPercentage() {
    const percentageInputs = document.querySelectorAll('[name^="beneficiary_percentage_"]');
    let total = 0;
    
    percentageInputs.forEach(input => {
        total += parseFloat(input.value) || 0;
    });
    
    const totalElement = document.getElementById('total-percentage');
    if (totalElement) {
        totalElement.textContent = total;
        totalElement.style.color = total === 100 ? 'green' : total > 100 ? 'red' : 'orange';
    }
}

// Generate will document
async function generateWillDocument() {
    try {
        // Validate legal acknowledgment
        const acknowledgment = document.getElementById('legal_acknowledgment');
        if (!acknowledgment || !acknowledgment.checked) {
            showNotification('Please acknowledge the legal notice before generating your will', 'error');
            return;
        }
        
        showNotification('Generating your Bitcoin will document...', 'info');
        
        // Save or update will
        let response;
        if (currentWill.id) {
            response = await fetch(`${API_BASE_URL}/will/${currentWill.id}`, {
                method: 'PUT',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(currentWill)
            });
        } else {
            response = await fetch(`${API_BASE_URL}/will/create`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(currentWill)
            });
        }
        
        if (response.ok) {
            const data = await response.json();
            currentWill.id = data.will.id;
            
            // Generate PDF document
            const generateResponse = await fetch(`${API_BASE_URL}/will/${currentWill.id}/generate`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
                    'Content-Type': 'application/json'
                }
            });
            
            if (generateResponse.ok) {
                const generateData = await generateResponse.json();
                showWillCompletionPage(generateData);
            } else {
                throw new Error('Failed to generate will document');
            }
        } else {
            throw new Error('Failed to save will');
        }
        
    } catch (error) {
        console.error('Generate will error:', error);
        showNotification('Failed to generate will document. Please try again.', 'error');
    }
}

// Show will completion page
function showWillCompletionPage(data) {
    const mainContent = document.getElementById('main-content');
    
    mainContent.innerHTML = `
        <div class="completion-container">
            <div class="completion-content">
                <div class="success-icon">✅</div>
                <h1>Your Bitcoin Will Has Been Generated!</h1>
                <p>Your comprehensive Bitcoin will document has been successfully created and is ready for download.</p>
                
                <div class="completion-actions">
                    <a href="${data.download_url}" class="download-button" target="_blank">
                        📄 Download Your Will (PDF)
                    </a>
                    
                    <button onclick="showDashboard()" class="secondary-button">
                        View My Wills
                    </button>
                </div>
                
                <div class="next-steps">
                    <h3>Important Next Steps:</h3>
                    <ol>
                        <li><strong>Review the Document:</strong> Carefully review the generated will document for accuracy</li>
                        <li><strong>Legal Review:</strong> Have the document reviewed by qualified legal counsel</li>
                        <li><strong>Proper Execution:</strong> Execute the will according to your local laws (signatures, witnesses, notarization)</li>
                        <li><strong>Secure Storage:</strong> Store the executed will in a secure location</li>
                        <li><strong>Inform Trusted Parties:</strong> Let your executor and trusted individuals know about the will's existence and location</li>
                        <li><strong>Regular Updates:</strong> Update your will as your Bitcoin holdings change</li>
                    </ol>
                </div>
                
                <div class="legal-reminder">
                    <h4>⚠️ Legal Reminder</h4>
                    <p>This document serves as a comprehensive record for estate planning purposes. 
                    It must be properly executed with legal counsel to become a legally binding will.</p>
                </div>
            </div>
        </div>
    `;
}

// Load user's existing wills
async function loadUserWills() {
    try {
        const response = await fetch(`${API_BASE_URL}/will/list`, {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
                'Content-Type': 'application/json'
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            return data.wills;
        }
    } catch (error) {
        console.error('Failed to load wills:', error);
    }
    
    return [];
}

// Show user dashboard with existing wills
async function showDashboard() {
    const wills = await loadUserWills();
    const mainContent = document.getElementById('main-content');
    
    mainContent.innerHTML = `
        <div class="dashboard-container">
            <div class="dashboard-header">
                <h1>My Bitcoin Wills</h1>
                <button onclick="initializeWillCreation()" class="create-button">
                    + Create New Will
                </button>
            </div>
            
            <div class="wills-grid">
                ${wills.length > 0 ? wills.map(will => `
                    <div class="will-card">
                        <h3>${will.title}</h3>
                        <p>Created: ${new Date(will.created_at).toLocaleDateString()}</p>
                        <p>Last Updated: ${new Date(will.updated_at).toLocaleDateString()}</p>
                        
                        <div class="will-actions">
                            <button onclick="editWill(${will.id})" class="edit-button">Edit</button>
                            <button onclick="downloadWill(${will.id})" class="download-button">Download</button>
                            <button onclick="deleteWill(${will.id})" class="delete-button">Delete</button>
                        </div>
                    </div>
                `).join('') : `
                    <div class="empty-state">
                        <h3>No Wills Created Yet</h3>
                        <p>Create your first Bitcoin will to get started with securing your digital assets for your beneficiaries.</p>
                        <button onclick="initializeWillCreation()" class="create-button">
                            Create Your First Will
                        </button>
                    </div>
                `}
            </div>
        </div>
    `;
}

// Edit existing will
async function editWill(willId) {
    try {
        const response = await fetch(`${API_BASE_URL}/will/${willId}`, {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
                'Content-Type': 'application/json'
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            currentWill = data.will;
            currentStep = 1;
            showWillCreationInterface();
        }
    } catch (error) {
        console.error('Failed to load will:', error);
        showNotification('Failed to load will for editing', 'error');
    }
}

// Download will
async function downloadWill(willId) {
    try {
        const response = await fetch(`${API_BASE_URL}/will/${willId}/download`, {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            }
        });
        
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `bitcoin_will_${willId}.pdf`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        } else {
            throw new Error('Download failed');
        }
    } catch (error) {
        console.error('Download error:', error);
        showNotification('Failed to download will', 'error');
    }
}

// Delete will
async function deleteWill(willId) {
    if (!confirm('Are you sure you want to delete this will? This action cannot be undone.')) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/will/${willId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            }
        });
        
        if (response.ok) {
            showNotification('Will deleted successfully', 'success');
            showDashboard(); // Refresh dashboard
        } else {
            throw new Error('Delete failed');
        }
    } catch (error) {
        console.error('Delete error:', error);
        showNotification('Failed to delete will', 'error');
    }
}

