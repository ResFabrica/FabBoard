// Configuration par défaut pour EasyMDE
const defaultEasyMDEConfig = {
    spellChecker: false,
    status: ['lines', 'words'],
    toolbar: [
        'bold', 'italic', 'heading', '|',
        'quote', 'unordered-list', 'ordered-list', '|',
        'link', 'image', '|',
        'preview', 'side-by-side', 'fullscreen'
    ],
    minHeight: '200px',
    maxHeight: '400px',
    autofocus: false
};

/**
 * Initialise un éditeur Markdown sur un élément donné
 * @param {HTMLElement} element - L'élément textarea sur lequel initialiser l'éditeur
 * @param {Object} customConfig - Configuration personnalisée à fusionner avec la configuration par défaut
 * @returns {EasyMDE} Instance de l'éditeur
 */
function initializeMarkdownEditor(element, customConfig = {}) {
    // Récupérer le placeholder depuis l'attribut de l'élément
    const placeholder = element.getAttribute('placeholder') || 'Écrivez votre texte en Markdown...';

    // Fusionner les configurations
    const config = {
        ...defaultEasyMDEConfig,
        element,
        placeholder,
        ...customConfig
    };

    // Créer et retourner l'instance d'EasyMDE
    return new EasyMDE(config);
}

// Initialiser tous les éditeurs Markdown au chargement de la page
document.addEventListener('DOMContentLoaded', function() {
    // Sélectionner tous les champs avec l'attribut data-editor="markdown"
    const markdownFields = document.querySelectorAll('[data-editor="markdown"]');
    
    markdownFields.forEach(field => {
        initializeMarkdownEditor(field);
    });
}); 