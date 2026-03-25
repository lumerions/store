let cart = JSON.parse(localStorage.getItem('store_cart')) || [];

function toggleCart() {
    const panel = document.getElementById('cart-panel');
    const overlay = document.getElementById('cart-overlay');
    panel.classList.toggle('open');
    overlay.style.display = panel.classList.contains('open') ? 'block' : 'none';
    renderCart();
}

function addToCart(name, price) {
    cart.push({ id: Date.now(), name, price });
    localStorage.setItem('store_cart', JSON.stringify(cart));
    updateCount();
}

function removeItem(id) {
    cart = cart.filter(item => item.id !== id);
    localStorage.setItem('store_cart', JSON.stringify(cart));
    renderCart();
    updateCount();
}

function updateCount() {
    document.getElementById('cart-count').innerText = cart.length;
}

function renderCart() {
    const container = document.getElementById('cart-items');
    const totalEl = document.getElementById('cart-total');
    container.innerHTML = '';
    
    let total = 0;
    cart.forEach(item => {
        total += parseFloat(item.price.replace('$', ''));
        container.innerHTML += `
            <div class="cart-item">
                <div class="cart-item-info">
                    <h4>${item.name}</h4>
                    <p>${item.price}</p>
                    <button class="remove-btn" onclick="removeItem(${item.id})">Remove</button>
                </div>
            </div>
        `;
    });
    totalEl.innerText = `$${total.toFixed(2)}`;
    if (cart.length === 0) container.innerHTML = '<p style="color:#999; text-align:center;">Your cart is empty.</p>';
}

updateCount();