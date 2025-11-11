// Voice2Note JavaScript

// Utility function to show/hide elements
function show(element) {
    if (typeof element === 'string') {
        element = document.getElementById(element);
    }
    if (element) element.style.display = 'block';
}

function hide(element) {
    if (typeof element === 'string') {
        element = document.getElementById(element);
    }
    if (element) element.style.display = 'none';
}

// Format duration in seconds to human-readable format
function formatDuration(seconds) {
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);

    if (hours > 0) {
        return `${hours}h ${minutes % 60}m`;
    }
    return `${minutes}m`;
}

// Format date to readable string
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

// Debounce function for search
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

// Add event listener when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('Voice2Note app loaded');

    // Add any global event listeners here

    // Handle drag and drop for file upload
    const fileLabel = document.querySelector('.file-label');
    if (fileLabel) {
        fileLabel.addEventListener('dragover', (e) => {
            e.preventDefault();
            fileLabel.style.borderColor = 'var(--primary-color)';
            fileLabel.style.background = '#f1f5f9';
        });

        fileLabel.addEventListener('dragleave', (e) => {
            e.preventDefault();
            fileLabel.style.borderColor = 'var(--border-color)';
            fileLabel.style.background = 'var(--bg-color)';
        });

        fileLabel.addEventListener('drop', (e) => {
            e.preventDefault();
            fileLabel.style.borderColor = 'var(--border-color)';
            fileLabel.style.background = 'var(--bg-color)';

            const files = e.dataTransfer.files;
            if (files.length > 0) {
                const fileInput = document.getElementById('video_file');
                fileInput.files = files;
                document.getElementById('fileName').textContent = files[0].name;
            }
        });
    }
});

// Export utility functions for use in templates
window.Voice2Note = {
    show,
    hide,
    formatDuration,
    formatDate,
    debounce
};
