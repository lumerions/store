let cart = JSON.parse(localStorage.getItem('store_cart')) || [];

function toggleCart() {
    const panel = document.getElementById('cart-panel');
    const overlay = document.getElementById('cart-overlay');
    
    panel.classList.toggle('open');
    overlay.style.display = panel.classList.contains('open') ? 'block' : 'none';
    
    renderCart();
}

function addToCart(name, price) {
    const item = {
        id: Date.now(), 
        name: name,
        price: price
    };
    
    cart.push(item);
    saveAndRefresh();
}

function removeItem(id) {
    cart = cart.filter(item => item.id !== id);
    saveAndRefresh();
}

function saveAndRefresh() {
    localStorage.setItem('store_cart', JSON.stringify(cart));
    updateCountBadge();
    renderCart();
}

function updateCountBadge() {
    const badge = document.getElementById('cart-count');
    if(badge) badge.innerText = cart.length;
}

function renderCart() {
    const container = document.getElementById('cart-items');
    const totalEl = document.getElementById('cart-total');
    
    container.innerHTML = '';
    let total = 0;

    if (cart.length === 0) {
        container.innerHTML = '<p style="text-align:center; color:#999; margin-top:50px;">Your cart is empty.</p>';
    } else {
        cart.forEach(item => {
            const numPrice = parseFloat(item.price.replace('$', ''));
            total += numPrice;

            container.innerHTML += `
                <div class="cart-item">
                    <div>
                        <h4 style="font-size:0.95rem;">${item.name}</h4>
                        <p style="font-size:0.85rem; color:#666;">${item.price}</p>
                        <button class="remove-btn" onclick="removeItem(${item.id})">Remove</button>
                    </div>
                </div>
            `;
        });
    }
    
    totalEl.innerText = `$${total.toFixed(2)}`;
}


function openCheckout() {
    if (cart.length === 0) {
        alert("Add some items first!");
        return;
    }

    document.getElementById('cart-panel').classList.remove('open');
    document.getElementById('cart-overlay').style.display = 'none';
    const total = cart.reduce((sum, item) => sum + parseFloat(item.price.replace('$', '')), 0);
    document.getElementById('modal-total-display').innerText = `$${total.toFixed(2)}`;
    document.getElementById('checkout-modal').style.display = 'block';
    document.getElementById('modal-overlay').style.display = 'block';
}

function closeCheckout() {
    document.getElementById('checkout-modal').style.display = 'none';
    document.getElementById('modal-overlay').style.display = 'none';
}

function processPayment(method) {
    alert(`Redirecting to ${method} secure gateway...`);
    
    cart = [];
    saveAndRefresh();
    closeCheckout();
    alert("Success! Your order has been placed.");
}

updateCountBadge();