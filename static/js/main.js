// main.js - Funcionalidades JavaScript para Farmacias La Guadalajara

document.addEventListener('DOMContentLoaded', function() {
    console.log('Farmacias La Guadalajara - Frontend cargado');
    
    // Inicializar tooltips de Bootstrap
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    const tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Manejar formularios con validación
    initFormValidation();
    
    // Manejar interacciones del carrito
    initCartInteractions();
    
    // Manejar galería de productos
    initProductGallery();
    
    // Configurar filtros de productos
    initProductFilters();
});

/**
 * Validación de formularios
 */
function initFormValidation() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const requiredFields = form.querySelectorAll('[required]');
            let isValid = true;
            
            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    isValid = false;
                    highlightInvalidField(field);
                } else {
                    removeInvalidHighlight(field);
                }
            });
            
            // Validación específica para contraseñas
            const password = form.querySelector('#password');
            const confirmPassword = form.querySelector('#confirm_password');
            
            if (password && confirmPassword) {
                if (password.value !== confirmPassword.value) {
                    isValid = false;
                    highlightInvalidField(confirmPassword);
                    showToast('Las contraseñas no coinciden', 'error');
                }
            }
            
            if (!isValid) {
                e.preventDefault();
                showToast('Por favor completa todos los campos requeridos', 'error');
            }
        });
    });
}

/**
 * Resaltar campo inválido
 */
function highlightInvalidField(field) {
    field.classList.add('is-invalid');
    
    // Agregar mensaje de error si no existe
    if (!field.nextElementSibling || !field.nextElementSibling.classList.contains('invalid-feedback')) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'invalid-feedback';
        errorDiv.textContent = 'Este campo es requerido';
        field.parentNode.appendChild(errorDiv);
    }
}

/**
 * Remover resaltado de campo inválido
 */
function removeInvalidHighlight(field) {
    field.classList.remove('is-invalid');
    field.classList.add('is-valid');
}

/**
 * Interacciones del carrito
 */
function initCartInteractions() {
    // Actualizar cantidad en carrito
    const quantityInputs = document.querySelectorAll('input[name="cantidad"]');
    
    quantityInputs.forEach(input => {
        input.addEventListener('change', function() {
            const form = this.closest('form');
            if (form) {
                form.submit();
            }
        });
    });
    
    // Confirmación para eliminar del carrito
    const removeButtons = document.querySelectorAll('a[href*="/cart/remove/"]');
    
    removeButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            if (!confirm('¿Estás seguro de que quieres eliminar este producto del carrito?')) {
                e.preventDefault();
            }
        });
    });
}

/**
 * Galería de productos
 */
function initProductGallery() {
    // Efecto hover en productos
    const productCards = document.querySelectorAll('.product-card');
    
    productCards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-5px)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });
}

/**
 * Filtros de productos
 */
function initProductFilters() {
    const categoryRadios = document.querySelectorAll('input[name="category"]');
    
    categoryRadios.forEach(radio => {
        radio.addEventListener('change', function() {
            // En una implementación real, aquí se filtrarían los productos
            console.log('Categoría seleccionada:', this.value);
            // showLoadingState();
            // filterProducts(this.value);
        });
    });
}

/**
 * Mostrar estado de carga
 */
function showLoadingState() {
    const mainContent = document.querySelector('main');
    const loader = document.createElement('div');
    loader.className = 'loading-overlay';
    loader.innerHTML = `
        <div class="d-flex justify-content-center align-items-center" style="height: 200px;">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Cargando...</span>
            </div>
        </div>
    `;
    mainContent.appendChild(loader);
}

/**
 * Mostrar notificación toast
 */
function showToast(message, type = 'info') {
    // Crear contenedor de toasts si no existe
    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
        document.body.appendChild(toastContainer);
    }
    
    const toastId = 'toast-' + Date.now();
    const bgClass = type === 'error' ? 'bg-danger' : type === 'success' ? 'bg-success' : 'bg-info';
    
    const toastHTML = `
        <div id="${toastId}" class="toast align-items-center text-white ${bgClass} border-0" role="alert">
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        </div>
    `;
    
    toastContainer.insertAdjacentHTML('beforeend', toastHTML);
    
    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement, { delay: 3000 });
    toast.show();
    
    // Remover el toast del DOM después de que se oculte
    toastElement.addEventListener('hidden.bs.toast', function() {
        this.remove();
    });
}

/**
 * Formatear precios
 */
function formatPrice(price) {
    return new Intl.NumberFormat('es-MX', {
        style: 'currency',
        currency: 'MXN'
    }).format(price);
}

/**
 * Validar archivos antes de subir
 */
function validateFile(input, maxSize = 2 * 1024 * 1024) { // 2MB por defecto
    if (input.files.length > 0) {
        const file = input.files[0];
        const validTypes = ['image/jpeg', 'image/png', 'image/jpg', 'application/pdf'];
        
        if (!validTypes.includes(file.type)) {
            showToast('Tipo de archivo no permitido. Use JPG, PNG o PDF.', 'error');
            input.value = '';
            return false;
        }
        
        if (file.size > maxSize) {
            showToast('El archivo es demasiado grande. Máximo 2MB permitido.', 'error');
            input.value = '';
            return false;
        }
        
        return true;
    }
    
    return false;
}

// Exportar funciones para uso global
window.FarmaciaApp = {
    showToast,
    formatPrice,
    validateFile
};
/**
 * Funcionalidades específicas del perfil
 */
function initProfileFeatures() {
    // Validación de formularios de perfil
    initProfileFormValidation();
    
    // Gestión de direcciones
    initAddressManagement();
    
    // Configuración de notificaciones
    initNotificationSettings();
}

/**
 * Validación de formularios de perfil
 */
function initProfileFormValidation() {
    const profileForms = document.querySelectorAll('form[action*="/profile/"]');
    
    profileForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const passwordForm = this.querySelector('#new_password');
            if (passwordForm) {
                const currentPassword = this.querySelector('#current_password').value;
                const newPassword = this.querySelector('#new_password').value;
                const confirmPassword = this.querySelector('#confirm_password').value;
                
                if (newPassword.length < 6) {
                    e.preventDefault();
                    showToast('La contraseña debe tener al menos 6 caracteres', 'error');
                    return;
                }
                
                if (newPassword !== confirmPassword) {
                    e.preventDefault();
                    showToast('Las contraseñas no coinciden', 'error');
                    return;
                }
            }
        });
    });
}

/**
 * Gestión de direcciones
 */
function initAddressManagement() {
    // Marcar dirección como principal
    const setPrimaryButtons = document.querySelectorAll('.set-primary-address');
    
    setPrimaryButtons.forEach(button => {
        button.addEventListener('click', function() {
            const addressId = this.dataset.addressId;
            // Aquí iría la lógica para marcar como principal
            showToast('Dirección establecida como principal', 'success');
        });
    });
    
    // Eliminar dirección
    const deleteAddressButtons = document.querySelectorAll('.delete-address');
    
    deleteAddressButtons.forEach(button => {
        button.addEventListener('click', function() {
            if (confirm('¿Estás seguro de que quieres eliminar esta dirección?')) {
                const addressId = this.dataset.addressId;
                // Aquí iría la lógica para eliminar la dirección
                showToast('Dirección eliminada', 'success');
            }
        });
    });
}

/**
 * Configuración de notificaciones
 */
function initNotificationSettings() {
    const notificationToggles = document.querySelectorAll('.form-switch input');
    
    notificationToggles.forEach(toggle => {
        toggle.addEventListener('change', function() {
            const settingName = this.name;
            const isEnabled = this.checked;
            
            // Aquí podrías hacer una petición AJAX para guardar la preferencia
            console.log(`Configuración ${settingName} ${isEnabled ? 'activada' : 'desactivada'}`);
        });
    });
}

/**
 * Cargar historial de pedidos con AJAX (opcional)
 */
function loadOrderHistory() {
    // Implementación para cargar más pedidos via AJAX
}

// Inicializar funcionalidades del perfil cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    initProfileFeatures();
});