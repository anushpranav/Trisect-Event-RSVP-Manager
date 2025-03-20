// Form validation
function validateForm(form) {
    const requiredFields = form.querySelectorAll('[required]');
    let isValid = true;
    
    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            isValid = false;
            field.classList.add('error');
            showError(field, 'This field is required');
        } else {
            field.classList.remove('error');
            clearError(field);
        }
    });
    
    return isValid;
}

// Show error message
function showError(field, message) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.textContent = message;
    
    const parent = field.parentElement;
    const existing = parent.querySelector('.error-message');
    if (!existing) {
        parent.appendChild(errorDiv);
    }
}

// Clear error message
function clearError(field) {
    const parent = field.parentElement;
    const error = parent.querySelector('.error-message');
    if (error) {
        parent.removeChild(error);
    }
}

// Date validation
function validateEventDate(dateInput) {
    const selectedDate = new Date(dateInput.value);
    const now = new Date();
    
    if (selectedDate < now) {
        showError(dateInput, 'Please select a future date');
        return false;
    }
    
    clearError(dateInput);
    return true;
}

// Copy to clipboard utility
function copyToClipboard(text) {
    navigator.clipboard.writeText(text)
        .then(() => {
            showToast('Copied to clipboard!');
        })
        .catch(err => {
            console.error('Failed to copy:', err);
            showToast('Failed to copy to clipboard', 'error');
        });
}

// Toast notification
function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.classList.add('show');
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => {
                document.body.removeChild(toast);
            }, 300);
        }, 3000);
    }, 100);
}

// Initialize all forms
document.addEventListener('DOMContentLoaded', function() {
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!validateForm(this)) {
                e.preventDefault();
            }
        });
    });
    
    // Initialize date inputs
    const dateInputs = document.querySelectorAll('input[type="datetime-local"]');
    dateInputs.forEach(input => {
        input.addEventListener('change', function() {
            validateEventDate(this);
        });
    });
});