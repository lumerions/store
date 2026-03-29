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

export function logout() {
    const logoutBtn = document.getElementById('logout-btn') || document.querySelector('.login-btn')
    if (!logoutBtn) return

    logoutBtn.addEventListener('click', async function(event) {
        event.preventDefault(); 
        if (document.querySelector('button.login-btn').innerText === "Logout") {
            try {
                await fetch("/logout", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    credentials: "include"
                })
                window.location.reload()
            } catch {
                window.location.href = "/internalerror"
            }
        } else {
            window.location.href = "/login"
        }
    })
}