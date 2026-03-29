export function showNotification(text, type = 'error') {
    let container = document.getElementById('notification-toast');
    
    if (!container) {
        container = document.createElement('div');
        container.id = 'notification-toast';
        container.className = 'toast-left';
        document.body.appendChild(container);
    }
    
    const toast = document.createElement('div');
    toast.className = `toast-card toast-${type}`;
    toast.innerText = text;

    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(-20px)';
        toast.style.transition = 'all 0.4s ease';
        
        setTimeout(() => toast.remove(), 400);
    }, 3000);
}