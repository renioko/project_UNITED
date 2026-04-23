// communities/static/communities/js/community_picker.js

/**
 * Community Picker Widget
 * Reużywalny widget do wyboru wspólnoty z wyszukiwarką
 * 
 * Użycie:
 * CommunityPicker.open((community) => {
 *     console.log('Wybrano:', community);
 * });
 */

const CommunityPicker = (function() {
    let modal = null;
    let searchInput = null;
    let resultsContainer = null;
    let loadingIndicator = null;
    let callback = null;
    let searchTimeout = null;

    // Inicjalizacja widgetu
    function init() {
        modal = document.getElementById('communityPickerModal');
        searchInput = document.getElementById('community-picker-search');
        resultsContainer = document.getElementById('community-picker-results');
        loadingIndicator = document.getElementById('community-picker-loading');

        if (!modal || !searchInput || !resultsContainer) {
            console.error('Community Picker: Nie znaleziono wymaganych elementów DOM');
            return;
        }

        // Event listener dla wyszukiwania
        searchInput.addEventListener('input', handleSearchInput);

        // Reset po zamknięciu modala
        modal.addEventListener('hidden.bs.modal', handleModalClose);

        console.log('Community Picker: Zainicjalizowany');
    }

    // Obsługa wpisywania w pole wyszukiwania (debounce)
    function handleSearchInput(e) {
        const query = e.target.value.trim();

        // Wyczyść poprzedni timeout
        if (searchTimeout) {
            clearTimeout(searchTimeout);
        }

        // Jeśli puste pole, wyczyść wyniki
        if (query.length === 0) {
            showEmptyState();
            return;
        }

        // Czekaj 300ms przed wyszukiwaniem (debounce)
        searchTimeout = setTimeout(() => {
            performSearch(query);
        }, 300);
    }

    // Wykonaj wyszukiwanie
    function performSearch(query) {
        console.log('Szukam:', query);

        // Pokaż loading
        showLoading(true);

        const url = `/api/search/?q=${encodeURIComponent(query)}`;

        fetch(url)
            .then(res => {
                if (!res.ok) {
                    throw new Error(`HTTP ${res.status}`);
                }
                return res.json();
            })
            .then(data => {
                console.log('Wyniki:', data);
                displayResults(data);
            })
            .catch(err => {
                console.error('Błąd wyszukiwania:', err);
                showError('Wystąpił błąd podczas wyszukiwania. Spróbuj ponownie.');
            })
            .finally(() => {
                showLoading(false);
            });
    }

    // Wyświetl wyniki
    function displayResults(communities) {
        resultsContainer.innerHTML = '';

        if (communities.length === 0) {
            resultsContainer.innerHTML = `
                <div class="text-center text-muted py-4">
                    <p class="mb-0">Brak wyników</p>
                    <small>Spróbuj wpisać inną frazę</small>
                </div>
            `;
            return;
        }

        communities.forEach(community => {
            const item = document.createElement('button');
            item.type = 'button';
            item.className = 'list-group-item list-group-item-action text-start';
            item.innerHTML = `
                <div class="d-flex justify-content-between align-items-start">
                    <div>
                        <strong>${escapeHtml(community.name)}</strong>
                        <br>
                        <small class="text-muted">
                            ${escapeHtml(community.city || '—')}, ${escapeHtml(community.country || '—')}
                        </small>
                    </div>
                    <span class="badge bg-primary">Wybierz</span>
                </div>
            `;

            item.addEventListener('click', () => {
                selectCommunity(community);
            });

            resultsContainer.appendChild(item);
        });
    }

    // Wybrano wspólnotę
    function selectCommunity(community) {
        console.log('Wybrano wspólnotę:', community);

        if (callback && typeof callback === 'function') {
            callback(community);
        }

        // Zamknij modal
        const bsModal = bootstrap.Modal.getInstance(modal);
        if (bsModal) {
            bsModal.hide();
        }
    }

    // Pokaż/ukryj loading
    function showLoading(show) {
        if (show) {
            loadingIndicator.classList.remove('d-none');
            resultsContainer.classList.add('d-none');
        } else {
            loadingIndicator.classList.add('d-none');
            resultsContainer.classList.remove('d-none');
        }
    }

    // Pokaż pusty stan
    function showEmptyState() {
        resultsContainer.innerHTML = `
            <div class="text-center text-muted py-4">
                Wpisz frazę, aby rozpocząć wyszukiwanie
            </div>
        `;
    }

    // Pokaż błąd
    function showError(message) {
        resultsContainer.innerHTML = `
            <div class="alert alert-danger mb-0" role="alert">
                ${escapeHtml(message)}
            </div>
        `;
    }

    // Reset po zamknięciu modala
    function handleModalClose() {
        searchInput.value = '';
        showEmptyState();
        callback = null;
    }

    // Escape HTML (bezpieczeństwo)
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // API publiczne
    return {
        /**
         * Inicjalizuj widget (wywołaj raz przy ładowaniu strony)
         */
        init: init,

        /**
         * Otwórz modal wyboru wspólnoty
         * @param {Function} onSelect - Callback wywoływany po wyborze (otrzymuje obiekt community)
         */
        open: function(onSelect) {
            if (!modal) {
                console.error('Community Picker: Widget nie został zainicjalizowany. Wywołaj CommunityPicker.init()');
                return;
            }

            callback = onSelect;
            
            // Otwórz modal
            const bsModal = new bootstrap.Modal(modal);
            bsModal.show();

            // Focus na pole wyszukiwania
            setTimeout(() => {
                searchInput.focus();
            }, 300);
        }
    };
})();

// Auto-inicjalizacja po załadowaniu DOM
document.addEventListener('DOMContentLoaded', () => {
    CommunityPicker.init();
});