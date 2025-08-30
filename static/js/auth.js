document.addEventListener('DOMContentLoaded', () => {
    const forms = {
        login: document.getElementById('login-form'),
        register: document.getElementById('register-form')
    };
    
    // Configurar formularios
    if (forms.login) {
        setupLoginForm(forms.login);
    }
    
    if (forms.register) {
        setupRegisterForm(forms.register);
    }
    
    // Configurar toggle de contraseña
    setupPasswordToggle();
    
    // Configurar tema
    setupTheme();
});

function setupLoginForm(form) {
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const formData = new FormData(form);
        const data = {
            username: formData.get('username'),
            password: formData.get('password')
        };
        
        if (!data.username || !data.password) {
            showAlert('Por favor, completa todos los campos', 'error');
            return;
        }
        
        await handleLogin(data, form);
    });
}

function setupRegisterForm(form) {
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const formData = new FormData(form);
        const data = {
            username: formData.get('username'),
            email: formData.get('email'),
            password: formData.get('password'),
            confirmPassword: formData.get('confirm-password')
        };
        
        // Validaciones
        if (!data.username || !data.email || !data.password || !data.confirmPassword) {
            showAlert('Por favor, completa todos los campos', 'error');
            return;
        }
        
        if (data.username.length < 3) {
            showAlert('El nombre de usuario debe tener al menos 3 caracteres', 'error');
            return;
        }
        
        if (data.password.length < 6) {
            showAlert('La contraseña debe tener al menos 6 caracteres', 'error');
            return;
        }
        
        if (data.password !== data.confirmPassword) {
            showAlert('Las contraseñas no coinciden', 'error');
            return;
        }
        
        if (!isValidEmail(data.email)) {
            showAlert('Por favor, ingresa un email válido', 'error');
            return;
        }
        
        await handleRegister(data, form);
    });
}

async function handleLogin(data, form) {
    const button = form.querySelector('.auth-button');
    setButtonLoading(button, true);
    
    try {
        const response = await fetch('/api/auth/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showAlert('¡Inicio de sesión exitoso!', 'success');
            setTimeout(() => {
                window.location.href = '/';
            }, 1000);
        } else {
            showAlert(result.message || 'Error en el inicio de sesión', 'error');
        }
    } catch (error) {
        console.error('Error en login:', error);
        showAlert('Error de conexión. Inténtalo de nuevo.', 'error');
    } finally {
        setButtonLoading(button, false);
    }
}

async function handleRegister(data, form) {
    const button = form.querySelector('.auth-button');
    setButtonLoading(button, true);
    
    try {
        const response = await fetch('/api/auth/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                username: data.username,
                email: data.email,
                password: data.password
            })
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showAlert('¡Registro exitoso! Redirigiendo al inicio de sesión...', 'success');
            setTimeout(() => {
                window.location.href = '/login';
            }, 2000);
        } else {
            showAlert(result.message || 'Error en el registro', 'error');
        }
    } catch (error) {
        console.error('Error en registro:', error);
        showAlert('Error de conexión. Inténtalo de nuevo.', 'error');
    } finally {
        setButtonLoading(button, false);
    }
}

function setupPasswordToggle() {
    const toggleButtons = document.querySelectorAll('.toggle-password');
    
    toggleButtons.forEach(button => {
        button.addEventListener('click', () => {
            const input = button.parentElement.querySelector('input[type="password"], input[type="text"]');
            const icon = button.querySelector('.material-icons');
            
            if (input.type === 'password') {
                input.type = 'text';
                icon.textContent = 'visibility_off';
            } else {
                input.type = 'password';
                icon.textContent = 'visibility';
            }
        });
    });
}

function setButtonLoading(button, loading) {
    const buttonText = button.querySelector('.button-text');
    const loadingSpinner = button.querySelector('.loading-spinner');
    
    if (loading) {
        button.classList.add('loading');
        button.disabled = true;
        buttonText.style.display = 'none';
        loadingSpinner.style.display = 'flex';
    } else {
        button.classList.remove('loading');
        button.disabled = false;
        buttonText.style.display = 'block';
        loadingSpinner.style.display = 'none';
    }
}

function showAlert(message, type = 'info') {
    const alertElement = document.getElementById('alert');
    const alertMessage = alertElement.querySelector('.alert-message');
    const alertIcon = alertElement.querySelector('.alert-icon');
    
    // Limpiar clases anteriores
    alertElement.className = 'alert';
    alertElement.classList.add(type);
    
    // Configurar icono según el tipo
    switch (type) {
        case 'success':
            alertIcon.textContent = 'check_circle';
            break;
        case 'error':
            alertIcon.textContent = 'error';
            break;
        case 'info':
        default:
            alertIcon.textContent = 'info';
            break;
    }
    
    alertMessage.textContent = message;
    alertElement.style.display = 'flex';
    
    // Auto-hide después de 5 segundos
    setTimeout(() => {
        alertElement.style.display = 'none';
    }, 5000);
}

function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

// Función para manejar Enter en los campos de formulario
document.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        const form = e.target.closest('form');
        if (form) {
            const submitButton = form.querySelector('button[type="submit"], .auth-button');
            if (submitButton && !submitButton.disabled) {
                submitButton.click();
            }
        }
    }
});

// Validación en tiempo real para el registro
document.addEventListener('input', (e) => {
    if (e.target.name === 'confirm-password') {
        const password = document.getElementById('password').value;
        const confirmPassword = e.target.value;
        
        if (confirmPassword && password !== confirmPassword) {
            e.target.setCustomValidity('Las contraseñas no coinciden');
        } else {
            e.target.setCustomValidity('');
        }
    }
});

// Función para limpiar mensajes de error al cambiar campos
document.addEventListener('input', () => {
    const alertElement = document.getElementById('alert');
    if (alertElement && alertElement.style.display !== 'none') {
        alertElement.style.display = 'none';
    }
});

// Función para configurar el tema
function setupTheme() {
    // Forzar modo oscuro
    document.documentElement.setAttribute('data-theme', 'dark');
    localStorage.setItem('theme', 'dark');
}
