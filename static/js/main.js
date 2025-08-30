document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 DOM Cargado - Iniciando aplicación...');
    
    // Estado global para la paginación
    window.paginationState = {
        currentPage: 1,
        itemsPerPage: 20,
        totalItems: 0,
        totalPages: 0
    };

    // Inicializar aplicación
    initializeApp();
});

async function initializeApp() {
    try {
        console.log('🔧 Inicializando aplicación...');
        
        await fetchMangaList();
        await fetchPopularMangas();
        await fetchUserInfo();
        
        setupSearchInput();
        setupNavigation();
        setupRefreshButton();
        setupUI();
        
        console.log('✅ Aplicación inicializada correctamente');
    } catch (error) {
        console.error('❌ Error al inicializar aplicación:', error);
    }
}

function setupSearchInput() {
    const searchInput = document.querySelector('.search-bar input');
    if (searchInput) {
        searchInput.addEventListener('input', debounce(handleSearch, 300));
    }
}

function setupNavigation() {
    console.log('🔧 Configurando navegación...');
    
    // Configurar home link
    const homeLink = document.getElementById('home-link');
    console.log('🏠 Home link encontrado:', homeLink);
    
    if (homeLink) {
        homeLink.addEventListener('click', () => {
            console.log('🏠 Click en home');
            document.querySelectorAll('.categories li').forEach(li => li.classList.remove('active'));
            homeLink.classList.add('active');
            window.scrollTo({ top: 0, behavior: 'smooth' });
            window.paginationState.currentPage = 1;
            fetchMangaList();
        });
        homeLink.classList.add('active');
    }
    
    // Configurar settings link
    const settingsLink = document.getElementById('settings-link');
    console.log('⚙️ Settings link encontrado:', settingsLink);
    
    if (settingsLink) {
        settingsLink.addEventListener('click', () => {
            console.log('⚙️ Click en configuración');
            window.location.href = '/settings';
        });
    }
    
    // Configurar logout link
    const logoutLink = document.getElementById('logout-link');
    console.log('🚪 Logout link encontrado:', logoutLink);
    
    if (logoutLink) {
        console.log('🚪 Configurando event listener para logout');
        
        // Agregar visual feedback
        logoutLink.style.cursor = 'pointer';
        logoutLink.style.backgroundColor = 'rgba(255, 0, 0, 0.1)';
        
        // Event listener principal
        logoutLink.addEventListener('click', (e) => {
            console.log('🚪 CLICK EN LOGOUT DETECTADO!', e);
            e.preventDefault();
            e.stopPropagation();
            handleLogout();
        });
        
        // Backup onclick
        logoutLink.onclick = (e) => {
            console.log('🚪 ONCLICK EN LOGOUT!', e);
            e.preventDefault();
            handleLogout();
        };
        
        console.log('🚪 Event listeners configurados');
    } else {
        console.error('❌ No se encontró logout-link');
    }
}

function setupRefreshButton() {
    const refreshBtn = document.getElementById('refresh-library-btn');
    console.log('🔄 Refresh button encontrado:', refreshBtn);
    
    if (refreshBtn) {
        refreshBtn.addEventListener('click', () => {
            console.log('🔄 Click en refresh button');
            refreshLibrary();
        });
        console.log('🔄 Event listener para refresh configurado');
    }
}

function setupUI() {
    // Forzar modo oscuro
    document.documentElement.setAttribute('data-theme', 'dark');
    localStorage.setItem('theme', 'dark');
    
    // Inicializar menú colapsable
    initCollapsibleMenu();
    
    // Manejar menú móvil
    initMobileMenu();
}

async function handleLogout() {
    console.log('🚪 ===== FUNCIÓN HANDLELOGOUT EJECUTADA =====');
    
    try {
        const token = localStorage.getItem('token');
        console.log('🔑 Token encontrado:', token ? 'Sí' : 'No');
        
        // Llamar al backend
        if (token) {
            console.log('📡 Enviando request al backend...');
            const response = await fetch('/api/auth/logout', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });
            console.log('📡 Respuesta del backend:', response.status);
        }
        
        // Limpiar localStorage
        console.log('🧹 Limpiando localStorage...');
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        localStorage.removeItem('theme');
        
        // Mostrar notificación
        console.log('✅ Mostrando notificación...');
        showNotification('Sesión cerrada exitosamente', 'success');
        
        // Redireccionar
        console.log('🔄 Redirigiendo en 1 segundo...');
        setTimeout(() => {
            console.log('🔄 Redirigiendo ahora...');
            window.location.href = '/login';
        }, 1000);
        
    } catch (error) {
        console.error('❌ Error en logout:', error);
        localStorage.clear();
        window.location.href = '/login';
    }
}

async function fetchMangaList() {
    try {
        const response = await fetch('/api/mangas/list');
        if (!response.ok) throw new Error('Error al cargar mangas');
        
        const mangas = await response.json();
        window.allMangas = mangas;
        window.paginationState.totalItems = mangas.length;
        window.paginationState.totalPages = Math.ceil(mangas.length / window.paginationState.itemsPerPage);
        updateMangaList(mangas);
        updateMangaCount(mangas.length);
    } catch (error) {
        console.error('Error al cargar mangas:', error);
        showError('Error al cargar la lista de mangas');
    }
}

async function fetchPopularMangas() {
    // Usar la misma lista por ahora
    if (window.allMangas) {
        updatePopularMangasList(window.allMangas);
    }
}

async function fetchUserInfo() {
    try {
        const response = await fetch('/api/auth/user');
        if (!response.ok) throw new Error('Error al cargar información del usuario');
        
        const data = await response.json();
        console.log('Usuario logueado:', data.user?.username || 'Anónimo');
    } catch (error) {
        console.error('Error al cargar información del usuario:', error);
    }
}

function updatePopularMangasList(mangas) {
    const popularGrid = document.getElementById('popular-grid');
    if (!popularGrid) return;
    
    popularGrid.innerHTML = '';
    
    mangas.slice(0, 10).forEach(manga => {
        const mangaCard = createMangaCard(manga);
        popularGrid.appendChild(mangaCard);
    });
}

function updateMangaList(mangas) {
    const booksGrid = document.getElementById('books-grid');
    if (!booksGrid) return;
    
    booksGrid.innerHTML = '';
    
    const startIndex = (window.paginationState.currentPage - 1) * window.paginationState.itemsPerPage;
    const endIndex = startIndex + window.paginationState.itemsPerPage;
    const paginatedMangas = mangas.slice(startIndex, endIndex);
    
    paginatedMangas.forEach(manga => {
        const mangaCard = createMangaCard(manga);
        booksGrid.appendChild(mangaCard);
    });
    
    updatePagination();
}

function createMangaCard(manga) {
    const card = document.createElement('div');
    card.className = 'book-card';
    card.onclick = () => openMangaDetail(manga.id);
    
    card.innerHTML = `
        <div class="book-cover">
            <img src="${manga.cover_image}" alt="${manga.title}" loading="lazy">
        </div>
        <div class="book-info">
            <h3 class="book-title">${manga.title}</h3>
            <p class="book-author">${manga.artist || 'Desconocido'}</p>
            <div class="book-meta">
                <div class="book-views">
                    <span class="material-icons">visibility</span>
                    <span>${manga.views || 0}</span>
                </div>
                <div class="book-pages">
                    <span class="material-icons">collections</span>
                    <span>${manga.page_count || 0}</span>
                </div>
            </div>
        </div>
    `;
    
    return card;
}

function openMangaDetail(mangaId) {
    window.location.href = `/manga/${mangaId}`;
}

function updateMangaCount(count) {
    const mangaCountElement = document.getElementById('manga-count');
    if (mangaCountElement) {
        mangaCountElement.textContent = count;
    }
}

function updatePagination() {
    const paginationContainer = document.getElementById('pagination');
    if (!paginationContainer) return;
    
    paginationContainer.innerHTML = '';
    
    if (window.paginationState.totalPages <= 1) return;
    
    // Botón anterior
    const prevBtn = document.createElement('button');
    prevBtn.textContent = 'Anterior';
    prevBtn.disabled = window.paginationState.currentPage === 1;
    prevBtn.onclick = () => changePage(window.paginationState.currentPage - 1);
    paginationContainer.appendChild(prevBtn);
    
    // Números de página
    const maxVisible = 5;
    const start = Math.max(1, window.paginationState.currentPage - Math.floor(maxVisible / 2));
    const end = Math.min(window.paginationState.totalPages, start + maxVisible - 1);
    
    for (let i = start; i <= end; i++) {
        const pageBtn = document.createElement('button');
        pageBtn.textContent = i;
        pageBtn.className = i === window.paginationState.currentPage ? 'active' : '';
        pageBtn.onclick = () => changePage(i);
        paginationContainer.appendChild(pageBtn);
    }
    
    // Botón siguiente
    const nextBtn = document.createElement('button');
    nextBtn.textContent = 'Siguiente';
    nextBtn.disabled = window.paginationState.currentPage === window.paginationState.totalPages;
    nextBtn.onclick = () => changePage(window.paginationState.currentPage + 1);
    paginationContainer.appendChild(nextBtn);
}

function changePage(page) {
    if (page < 1 || page > window.paginationState.totalPages) return;
    
    window.paginationState.currentPage = page;
    updateMangaList(window.allMangas);
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function handleSearch(event) {
    const searchTerm = event.target.value.toLowerCase().trim();
    
    if (!window.allMangas) return;
    
    let filteredMangas;
    if (searchTerm === '') {
        filteredMangas = window.allMangas;
    } else {
        filteredMangas = window.allMangas.filter(manga =>
            manga.title.toLowerCase().includes(searchTerm) ||
            (manga.artist && manga.artist.toLowerCase().includes(searchTerm)) ||
            (manga.genres && manga.genres.some(genre => genre.toLowerCase().includes(searchTerm)))
        );
    }
    
    window.paginationState.currentPage = 1;
    window.paginationState.totalItems = filteredMangas.length;
    window.paginationState.totalPages = Math.ceil(filteredMangas.length / window.paginationState.itemsPerPage);
    
    updateMangaList(filteredMangas);
    updateMangaCount(filteredMangas.length);
}

async function refreshLibrary() {
    console.log('🔄 ===== FUNCIÓN REFRESH LIBRARY EJECUTADA =====');
    
    const refreshBtn = document.getElementById('refresh-library-btn');
    const btnIcon = refreshBtn?.querySelector('.material-icons');
    const btnText = refreshBtn?.querySelector('.btn-text');
    
    try {
        // Mostrar estado de carga
        if (refreshBtn) {
            refreshBtn.classList.add('loading');
            refreshBtn.disabled = true;
            if (btnText) btnText.textContent = 'Actualizando...';
        }
        
        const token = localStorage.getItem('token');
        const response = await fetch('/api/refresh-library', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
        
        const result = await response.json();
        
        if (result.success) {
            showNotification(result.message, 'success');
            await fetchMangaList();
        } else {
            showNotification(result.error || 'Error al actualizar la biblioteca', 'error');
        }
        
    } catch (error) {
        console.error('Error al actualizar biblioteca:', error);
        showNotification('Error de conexión al actualizar la biblioteca', 'error');
    } finally {
        // Restaurar estado del botón
        if (refreshBtn) {
            refreshBtn.classList.remove('loading');
            refreshBtn.disabled = false;
            if (btnText) btnText.textContent = 'Actualizar';
        }
    }
}

function initCollapsibleMenu() {
    const collapseBtn = document.getElementById('collapse-menu');
    const sidebar = document.getElementById('sidebar');
    
    if (collapseBtn && sidebar) {
        collapseBtn.addEventListener('click', () => {
            sidebar.classList.toggle('collapsed');
        });
    }
}

function initMobileMenu() {
    const mobileToggle = document.getElementById('mobile-menu-toggle');
    const sidebar = document.getElementById('sidebar');
    
    if (mobileToggle && sidebar) {
        mobileToggle.addEventListener('click', () => {
            sidebar.classList.toggle('open');
        });
        
        // Cerrar menú al hacer clic fuera
        document.addEventListener('click', (e) => {
            if (!sidebar.contains(e.target) && !mobileToggle.contains(e.target)) {
                sidebar.classList.remove('open');
            }
        });
    }
}

function showError(message) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-notification';
    errorDiv.textContent = message;
    errorDiv.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: #ef4444;
        color: white;
        padding: 12px 20px;
        border-radius: 8px;
        z-index: 10000;
        animation: slideIn 0.3s ease;
    `;
    
    document.body.appendChild(errorDiv);
    
    setTimeout(() => {
        errorDiv.remove();
    }, 5000);
}

function showNotification(message, type = 'success') {
    // Remover notificación anterior si existe
    const existingNotification = document.querySelector('.notification');
    if (existingNotification) {
        existingNotification.remove();
    }
    
    // Crear nueva notificación
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 12px 20px;
        border-radius: 8px;
        z-index: 10000;
        font-weight: 500;
        opacity: 0;
        transform: translateX(100%);
        transition: all 0.3s ease;
        ${type === 'success' ? 'background: #10b981; color: white;' : 
          type === 'warning' ? 'background: #f59e0b; color: white;' : 
          'background: #ef4444; color: white;'}
    `;
    
    document.body.appendChild(notification);
    
    // Mostrar notificación
    setTimeout(() => {
        notification.style.opacity = '1';
        notification.style.transform = 'translateX(0)';
    }, 100);
    
    // Ocultar después de 5 segundos
    setTimeout(() => {
        notification.style.opacity = '0';
        notification.style.transform = 'translateX(100%)';
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 300);
    }, 5000);
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}
