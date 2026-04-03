import { showNotification } from "./functions.js";
import { logout } from "./functions.js";
let cart = JSON.parse(localStorage.getItem("store_cart")) || [];
const loginBtn = document.querySelector(".login-btn"); 
const loginBtnText = document.querySelector("button.login-btn"); 
const SUPPORTED_COINS = {
    "btc": "Bitcoin", "eth": "Ethereum", "sol": "Solana",
    "usdc": "USD Coin", "usdt": "Tether", "pyusd": "PayPal USD",
    "busd": "Binance USD", "ltc": "Litecoin", "xrp": "Ripple",
    "doge": "Dogecoin", "trx": "Tron", "bch": "Bitcoin Cash",
    "xlm": "Stellar", "matic": "Polygon", "ada": "Cardano",
    "shib": "Shiba Inu", "avax": "Avalanche", "link": "Chainlink",
    "dot": "Polkadot", "near": "Near Protocol", "atom": "Cosmos",
    "algo": "Algorand", "ftm": "Fantom", "hbar": "Hedera",
    "vet": "VeChain", "pepe": "Pepe", "uni": "Uniswap",
    "kas": "Kaspa", "xmr": "Monero", "zec": "Zcash"
};

function initializeCoinSelect() {
    const select = document.getElementById("coin-select");
    if (!select) return;

    select.innerHTML = "";

    Object.entries(SUPPORTED_COINS).forEach(([symbol, name]) => {
        const option = document.createElement("option");
        option.value = symbol;
        option.textContent = `${name} (${symbol.toUpperCase()})`;
        
        if (symbol === "sol") option.selected = true;

        select.appendChild(option);
    });
}

function toggleCart() {
    const panel = document.getElementById("cart-panel");
    const overlay = document.getElementById("cart-overlay");
    
    panel.classList.toggle("open");
    overlay.style.display = panel.classList.contains("open") ? "block" : "none";
    
    renderCart();
}

function addToCart(name, price,image) {
    const item = {
        id: Date.now(), 
        name: name,
        price: price,
        image: image || "https://via.placeholder.com/60"
    };
    
    cart.push(item);
    showNotification(`Success! Added ${name} to cart.`, "success");
    saveAndRefresh();
}

function removeItem(id) {
    cart = cart.filter(item => item.id !== id);
    saveAndRefresh();
}

function saveAndRefresh() {
    localStorage.setItem("store_cart", JSON.stringify(cart));
    updateCountBadge();
    renderCart();
}

function updateCountBadge() {
    const badge = document.getElementById("cart-count");
    if(badge) badge.innerText = cart.length;
}

function renderCart() {
    const container = document.getElementById("cart-items");
    const totalEl = document.getElementById("cart-total");
    
    container.innerHTML = "";
    let total = 0;

    if (cart.length === 0) {
        container.innerHTML = `
            <div class="empty-cart-state">
                <p>Your cart is empty.</p>
            </div>`;
    } else {
        cart.forEach((item, index) => {
            const numPrice = parseFloat(item.price.replace("$", ""));
            total += numPrice;

            container.innerHTML += `
                <div class="cart-item-row">
                    <div class="cart-item-info">
                        <div class="cart-item-details">
                            <h4 class="cart-item-name">${item.name}</h4>
                            <p class="cart-item-price">${item.price}</p>
                        </div>
                        <div class="cart-item-img-container">
                            <img src="${item.image}" alt="${item.name}" class="cart-item-thumb">
                        </div>
                    </div>
                    
                    <button class="cart-item-remove" onclick="removeItem(${item.id})" title="Remove Item">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <polyline points="3 6 5 6 21 6"></polyline>
                            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                            <line x1="10" y1="11" x2="10" y2="17"></line>
                            <line x1="14" y1="11" x2="14" y2="17"></line>
                        </svg>
                    </button>
                </div>
            `;
        });
    }
    
    totalEl.innerText = `$${total.toFixed(2)}`;
}

function openCheckout() {
    if (cart.length === 0) {
        showNotification("Add some items first!")
        return;
    }

    document.getElementById("cart-panel").classList.remove("open");
    document.getElementById("cart-overlay").style.display = "none";
    const total = cart.reduce((sum, item) => sum + parseFloat(item.price.replace("$", "")), 0);
    document.getElementById("modal-total-display").innerText = `$${total.toFixed(2)}`;
    document.getElementById("checkout-modal").style.display = "block";
    document.getElementById("modal-overlay").style.display = "block";
}

function closeCheckout() {
    document.getElementById("checkout-modal").style.display = "none";
    document.getElementById("modal-overlay").style.display = "none";
}

function processPayment(method) {    
    saveAndRefresh();
    closeCheckout();
    if (method == "Crypto") {
        createInvoice()
    }
}

function showCryptoOptions() {
    document.getElementById("method-selection").style.display = "none";
    document.getElementById("modal-title").innerText = "Select Crypto";
    document.getElementById("crypto-selection").style.display = "flex";
}

function backToMethods() {
    document.getElementById("method-selection").style.display = "block";
    document.getElementById("modal-title").innerText = "Checkout";
    document.getElementById("crypto-selection").style.display = "none";
}

async function createInvoice() {
    const itemNames = cart.map(item => item.name);
    const coinDropdown = document.getElementById("coin-select");
    const selectedCoin = coinDropdown.value;

    if (cart.length === 0) {
        showNotification("Add some items first!")
        return;
    }

    const response = await fetch("/api/createcryptoinvoice",{
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            itemnames: itemNames, 
            coin: selectedCoin
        })
    })

    const data = await response.json();

    console.log(data)
    
    if (data.invoice_url) {
        window.location.href = data.invoice_url;
    } else {
        showNotification("Something went wrong with creating crypto invoice.")
    }
}

updateCountBadge()

async function CheckIfUserLoggedIn() {
    try {
        const response = await fetch("/userloggedin", {
            method: "GET",
            credentials: "include"
        })

        if (!response) {
            throw new Error("GET request was not okay. " + response.statusText)
        }

        const data = await response.json()

        if (!loginBtnText || !loginBtn) {
            return
        }

        if (!data.loggedin) {
            loginBtnText.innerText = "Login"
            loginBtn.style.display = "flex"
        } else {
            loginBtnText.innerText = "Logout"
            loginBtn.style.display = "flex"
        }

        if (data.isadmin) {
            const adminBtn = document.getElementById("admin-btn");
            adminBtn.style.display = "flex"
        }

    } catch(error) { 
        console.log(error)
        window.location.href = "/internalerror"
    }
}

CheckIfUserLoggedIn()
logout()
initializeCoinSelect()

window.toggleCart = toggleCart
window.addToCart = addToCart
window.removeItem = removeItem
window.openCheckout = openCheckout
window.closeCheckout = closeCheckout
window.processPayment = processPayment
window.showCryptoOptions = showCryptoOptions
window.backToMethods = backToMethods
window.createInvoice = createInvoice
