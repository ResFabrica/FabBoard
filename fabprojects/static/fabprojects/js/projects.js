document.addEventListener('DOMContentLoaded', function() {
    // Gestionnaire pour la complétion des tâches
    document.querySelectorAll('.task-complete-checkbox').forEach(function(checkbox) {
        checkbox.addEventListener('change', function() {
            const taskId = this.dataset.taskId;
            const url = `/projects/tasks/${taskId}/complete/`;
            
            fetch(url, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                    'Content-Type': 'application/json'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    const taskElement = this.closest('.task-item');
                    if (data.is_completed) {
                        taskElement.classList.add('completed');
                    } else {
                        taskElement.classList.remove('completed');
                    }
                }
            })
            .catch(error => console.error('Error:', error));
        });
    });

    // Fonction pour récupérer le cookie CSRF
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // Gestionnaire pour le tri des sections
    if (typeof Sortable !== 'undefined') {
        document.querySelectorAll('.sortable-section').forEach(function(section) {
            new Sortable(section, {
                group: 'tasks',
                animation: 150,
                distance: 7,
                onEnd: function(evt) {
                    const taskId = evt.item.dataset.taskId;
                    const newSectionId = evt.to.dataset.sectionId;
                    const newIndex = evt.newIndex;
                    
                    // Mettre à jour l'ordre des tâches via l'API
                    updateTaskOrder(taskId, newSectionId, newIndex);
                }
            });
        });
    }

    // Fonction pour mettre à jour l'ordre des tâches
    function updateTaskOrder(taskId, sectionId, newIndex) {
        const url = `/projects/tasks/${taskId}/reorder/`;
        
        fetch(url, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                section_id: sectionId,
                new_index: newIndex
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.status !== 'success') {
                console.error('Error updating task order');
            }
        })
        .catch(error => console.error('Error:', error));
    }

    // Gestionnaire pour les dates limites
    document.querySelectorAll('.datepicker').forEach(function(input) {
        if (typeof flatpickr !== 'undefined') {
            flatpickr(input, {
                enableTime: true,
                dateFormat: "Y-m-d H:i",
                time_24hr: true
            });
        }
    });

    // Gestionnaire pour les tags
    document.querySelectorAll('.tag-select').forEach(function(select) {
        if (typeof Choices !== 'undefined') {
            new Choices(select, {
                removeItemButton: true,
                maxItemCount: 5,
                searchResultLimit: 5,
                renderChoiceLimit: 5
            });
        }
    });
}); 