// Global variables
let cart = [];
let quantityModal = null;
let paymentModal = null;

// Main initialization
$(document).ready(function() {
    console.log('Initializing POS system...');
    console.log('DOM ready, jQuery version:', $.fn.jquery);
    initializeModals();
    initializeUI();
    initializeEventListeners();
});

// Initialize modals
function initializeModals() {
    console.log('Initializing modals...');
    quantityModal = new bootstrap.Modal(document.getElementById('quantityModal'));
    paymentModal = new bootstrap.Modal(document.getElementById('paymentModal'));
}

// Initialize UI components
function initializeUI() {
    console.log('Initializing UI components...');
    
    // Initialize customer search functionality
    initializeCustomerSearch();

    // Initialize Select2 for filters
    $('#category-filter').select2({
        placeholder: 'All Categories',
        allowClear: true,
        width: '100%'
    });

    $('#brand-filter').select2({
        placeholder: 'All Brands',
        allowClear: true,
        width: '100%'
    });
}

// Initialize all event listeners
function initializeEventListeners() {
    console.log('Setting up event listeners...');
    
    // Search and filter events (only if elements exist)
    if ($('#product-search').length > 0) {
        $('#product-search').on('input', debounce(filterProducts, 300));
    }
    if ($('#category-filter').length > 0) {
        $('#category-filter').on('change', filterProducts);
    }
    if ($('#brand-filter').length > 0) {
        $('#brand-filter').on('change', filterProducts);
    }

    // Product selection
    $('#products-container').on('click', '.pos-product-card', function(e) {
        e.preventDefault();
        e.stopPropagation();
        const productCard = $(this);
        const productId = productCard.data('product-id');
        console.log('Product clicked:', productId);
        
        if (!productId) {
            showErrorMessage('Invalid product selection');
            return;
        }

        // Add visual feedback
        productCard.addClass('border-primary');
        setTimeout(() => productCard.removeClass('border-primary'), 200);
        
        showQuantityModal(productId);
    });

    // Complete sale button
    $('#complete-sale').on('click', function() {
        if (cart.length === 0) {
            showErrorMessage('Please add items to cart first');
            return;
        }
        showPaymentModal();
    });
}

// Filter products based on search and filters
function filterProducts() {
    console.log('Filtering products...');
    
    // Safety check - only run if product elements exist
    if ($('#product-search').length === 0 || $('.product-item').length === 0) {
        console.log('Product search elements not found, skipping filter');
        return;
    }
    
    const searchTerm = ($('#product-search').val() || '').toLowerCase();
    const categoryId = $('#category-filter').val();
    const brandId = $('#brand-filter').val();

    $('.product-item').each(function() {
        const item = $(this);
        const productName = (item.find('.card-title').text() || '').toLowerCase();
        const productCategory = item.data('category');
        const productBrand = item.data('brand');

        const matchesSearch = productName.includes(searchTerm);
        const matchesCategory = !categoryId || productCategory === parseInt(categoryId);
        const matchesBrand = !brandId || productBrand === parseInt(brandId);

        item.toggle(matchesSearch && matchesCategory && matchesBrand);
    });
}

// Show quantity selection modal
function showQuantityModal(productId) {
    console.log('Opening quantity modal for product:', productId);
    
    // Reset modal state
    const quantityInput = $('#quantity-input');
    const addToCartBtn = $('#add-to-cart');
    
    quantityInput.val(1);
    quantityInput.removeClass('is-invalid');
    $('#quantity-feedback').text('');
    addToCartBtn.prop('disabled', false);

    // Clear previous event handlers
    quantityInput.off('input');
    addToCartBtn.off('click');

    // Fetch product info
    $.get(`/sales/api/product-info/${productId}/`)
        .done(function(product) {
            console.log('Product info received:', product);
            
            if (!product || typeof product.stock === 'undefined') {
                showErrorMessage('Invalid product data received');
                return;
            }

            $('#available-stock').text(product.stock);
            quantityInput.attr('max', product.stock);

            // Show modal
            const modal = new bootstrap.Modal(document.getElementById('quantityModal'));
            modal.show();

            // Setup quantity validation
            quantityInput.on('input', function() {
                const quantity = parseInt(this.value) || 0;
                const isValid = quantity > 0 && quantity <= product.stock;
                
                addToCartBtn.prop('disabled', !isValid);
                quantityInput.toggleClass('is-invalid', !isValid);
                
                if (quantity <= 0) {
                    $('#quantity-feedback').text('Quantity must be greater than 0');
                } else if (quantity > product.stock) {
                    $('#quantity-feedback').text('Not enough stock available');
                } else {
                    $('#quantity-feedback').text('');
                }
            });

            // Setup add to cart handler
            addToCartBtn.on('click', function() {
                const quantity = parseInt(quantityInput.val());
                if (quantity > 0 && quantity <= product.stock) {
                    addToCart(product, quantity);
                    modal.hide();
                }
            });
        })
        .fail(function(xhr) {
            showErrorMessage('Failed to get product information. Please try again.');
            console.error('Product info fetch failed:', xhr);
        });
}

// Add item to cart
function addToCart(product, quantity) {
    console.log('Adding to cart:', product, quantity);
    
    const existingItem = cart.find(item => item.id === product.id);
    if (existingItem) {
        existingItem.quantity += quantity;
    } else {
        cart.push({
            id: product.id,
            name: product.name,
            price: parseFloat(product.price),
            quantity: quantity
        });
    }
    updateCartDisplay();
}

// Update cart display
function updateCartDisplay() {
    console.log('Updating cart display');
    
    const cartDiv = $('#cart-items');
    cartDiv.empty();

    cart.forEach(item => {
        const itemTotal = (item.price * item.quantity).toFixed(2);
        cartDiv.append(`
            <div class="list-group-item">
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <h6 class="mb-0">${item.name}</h6>
                        <small class="text-muted">৳${item.price.toFixed(2)} × ${item.quantity}</small>
                    </div>
                    <div class="d-flex align-items-center">
                        <div class="btn-group me-2">
                            <button class="btn btn-sm btn-outline-secondary" onclick="updateQuantity(${item.id}, -1)">
                                <i class="bi bi-dash"></i>
                            </button>
                            <button class="btn btn-sm btn-outline-secondary" onclick="updateQuantity(${item.id}, 1)">
                                <i class="bi bi-plus"></i>
                            </button>
                        </div>
                        <span class="me-3">৳${itemTotal}</span>
                        <button class="btn btn-sm btn-outline-danger" onclick="removeFromCart(${item.id})">
                            <i class="bi bi-trash"></i>
                        </button>
                    </div>
                </div>
            </div>
        `);
    });

    // Update totals with proper precision
    const subtotal = cart.reduce((sum, item) => sum + parseFloat((item.price * item.quantity).toFixed(2)), 0);
    const total = parseFloat(subtotal.toFixed(2));

    $('#subtotal').text(`৳${subtotal.toFixed(2)}`);
    $('#total').text(`৳${total.toFixed(2)}`);
    
    // Enable/disable complete sale button
    $('#complete-sale').prop('disabled', cart.length === 0);
}

    // Show payment modal
function showPaymentModal() {
    console.log('Opening payment modal');
    
    // Calculate totals with proper precision
    const subtotal = cart.reduce((sum, item) => sum + (parseFloat((item.price * item.quantity).toFixed(2))), 0);
    const total = parseFloat(subtotal.toFixed(2));
    
    $('#payment-total').text(`৳${total.toFixed(2)}`);
    $('#amount-received').val('').removeClass('is-invalid');
    $('#change-amount').text('৳0.00');
    $('#confirm-payment').prop('disabled', true);    const modal = new bootstrap.Modal(document.getElementById('paymentModal'));
    modal.show();

    // Setup amount received handler
    $('#amount-received').off('input').on('input', function() {
        const amountReceived = parseFloat(this.value) || 0;
        const change = amountReceived - total;
        
        $('#change-amount').text(`৳${Math.max(0, change).toFixed(2)}`);
        $('#confirm-payment').prop('disabled', amountReceived < total);
        
        const isValid = amountReceived >= total;
        $(this).toggleClass('is-invalid', !isValid);
        if (!isValid && this.value) {
            $('#amount-received-feedback').text('Amount received must be at least equal to the total amount');
        } else {
            $('#amount-received-feedback').text('');
        }
    });

    // Setup payment confirmation
    $('#confirm-payment').off('click').on('click', function() {
        processPayment(total);
    });
}

// Process payment
function processPayment(total) {
    console.log('Processing payment...');
    
    const customerId = $('#customer-id').val();
    const paymentMethod = $('#payment-method').val();
    const amountPaid = parseFloat($('#amount-received').val());

    if (amountPaid < total) {
        showErrorMessage('Insufficient payment amount');
        return;
    }

    // Prepare order data
    const shopAssistantId = $('#shop-assistant-select').val();
    const orderData = {
        customer: customerId || null,
        shop_assistant: shopAssistantId || null,
        payment_method: paymentMethod,
        amount_paid: amountPaid,
        items: cart.map(item => ({
            id: item.id,
            quantity: item.quantity,
            price: item.price
        }))
    };

    // Show loading state
    const confirmBtn = $('#confirm-payment');
    const originalText = confirmBtn.html();
    confirmBtn.prop('disabled', true).html('<span class="spinner-border spinner-border-sm"></span> Processing...');

    // Send to server
    $.ajax({
        url: '/sales/api/complete-sale/',
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify(orderData),
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        },
        success: function(response) {
            if (response.success) {
                // Show success message first
                showSuccessMessage('Sale completed successfully!', function() {
                    // Clear cart and reset form
                    cart = [];
                    updateCartDisplay();
                    // Reset customer search
                    $('#customer-search').val('');
                    $('#customer-id').val('');
                    $('#selected-customer').text('Walk-in Customer');
                    $('#shop-assistant-select').val('');
                    $('#payment-method').val('cash');

                    // Close modal
                    const modal = bootstrap.Modal.getInstance(document.getElementById('paymentModal'));
                    modal.hide();

                    // Redirect to order detail page
                    if (response.redirect_url) {
                        window.location.href = response.redirect_url;
                    } else if (response.order_id) {
                        window.location.href = `/sales/order/${response.order_id}/`;
                    }
                });
            } else {
                showErrorMessage(response.error || 'Failed to complete sale');
            }
        },
        error: function(xhr) {
            let errorMessage = 'An error occurred while processing the sale.';
            if (xhr.responseJSON && xhr.responseJSON.error) {
                errorMessage = xhr.responseJSON.error;
            }
            showErrorMessage(errorMessage);
        },
        complete: function() {
            // Restore button state
            confirmBtn.prop('disabled', false).html(originalText);
        }
    });
}

// Update item quantity in cart
window.updateQuantity = function(productId, delta) {
    const item = cart.find(item => item.id === productId);
    if (!item) return;

    $.get(`/sales/api/product-info/${productId}/`)
        .done(function(product) {
            const newQuantity = item.quantity + delta;
            if (newQuantity > 0 && newQuantity <= product.stock) {
                item.quantity = newQuantity;
                updateCartDisplay();
            } else {
                showErrorMessage(newQuantity <= 0 ? 'Quantity cannot be less than 1' : 'Not enough stock available');
            }
        })
        .fail(function() {
            showErrorMessage('Failed to verify stock availability');
        });
};

// Remove item from cart
window.removeFromCart = function(productId) {
    cart = cart.filter(item => item.id !== productId);
    updateCartDisplay();
};

// Utility function to get CSRF token
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

// Utility function to show success message
function showSuccessMessage(message, callback) {
    console.log('Success:', message);
    if (typeof Swal !== 'undefined') {
        Swal.fire({
            title: 'Success!',
            text: message,
            icon: 'success',
            timer: 2000,
            showConfirmButton: false
        }).then(() => {
            if (callback) callback();
        });
    } else {
        alert(message);
        if (callback) callback();
    }
}

// Utility function to show error message
function showErrorMessage(message) {
    console.error('Error:', message);
    if (typeof Swal !== 'undefined') {
        Swal.fire({
            title: 'Error!',
            text: message,
            icon: 'error',
            confirmButtonText: 'OK'
        });
    } else {
        alert(message);
    }
}

// Debounce function for search input
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const context = this;
        const later = () => {
            clearTimeout(timeout);
            func.apply(context, args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Initialize customer search functionality
function initializeCustomerSearch() {
    console.log('Initializing customer search...');
    
    const customerSearch = $('#customer-search');
    const customerDropdown = $('#customer-dropdown');
    const customerIdInput = $('#customer-id');
    const selectedCustomerSpan = $('#selected-customer');
    
    console.log('Customer search elements:', {
        searchInput: customerSearch.length,
        dropdown: customerDropdown.length,
        hiddenInput: customerIdInput.length,
        selectedSpan: selectedCustomerSpan.length
    });
    
    // Check if elements exist before adding event listeners
    if (customerSearch.length === 0) {
        console.error('Customer search input not found! ID: #customer-search');
        return;
    }
    
    // Search customers with debounce
    customerSearch.on('input', debounce(function() {
        const query = ($(this).val() || '').trim();
        console.log('Customer search input:', query);
        
        if (query.length < 2) {
            customerDropdown.hide().empty();
            return;
        }
        
        console.log('Making AJAX request for customer search...');
        // Make AJAX request to search customers
        $.ajax({
            url: '/sales/api/search-customers/',
            type: 'GET',
            data: { q: query },
            success: function(response) {
                console.log('Customer search success:', response);
                displayCustomerResults(response.customers);
            },
            error: function(xhr, status, error) {
                console.error('Customer search failed:', error, xhr.responseText);
                
                if (xhr.status === 302 || xhr.status === 401) {
                    // Authentication required
                    customerDropdown.html('<div class="dropdown-item-text text-warning">Please log in to search customers</div>');
                } else {
                    customerDropdown.html('<div class="dropdown-item-text text-danger">Search failed. Check console for details.</div>');
                }
                customerDropdown.show();
            }
        });
    }, 300));
    
    // Handle input focus
    customerSearch.on('focus', function() {
        const query = ($(this).val() || '').trim();
        if (query.length >= 2) {
            customerDropdown.show();
        }
    });
    
    // Handle clicking outside to hide dropdown
    $(document).on('click', function(e) {
        if (!$(e.target).closest('#customer-search, #customer-dropdown').length) {
            customerDropdown.hide();
        }
    });
    
    // Clear customer selection
    customerSearch.on('keydown', function(e) {
        // Clear selection if user starts typing again
        if (e.key !== 'ArrowUp' && e.key !== 'ArrowDown' && e.key !== 'Enter') {
            customerIdInput.val('');
            selectedCustomerSpan.text('Walk-in Customer');
        }
    });
}

// Display customer search results
function displayCustomerResults(customers) {
    const customerDropdown = $('#customer-dropdown');
    
    if (customers.length === 0) {
        customerDropdown.html('<div class="dropdown-item-text text-muted">No customers found</div>');
        customerDropdown.show();
        return;
    }
    
    let html = '';
    customers.forEach(function(customer) {
        html += `
            <a class="dropdown-item customer-result" 
               href="#" 
               data-customer-id="${customer.id}"
               data-customer-name="${customer.name}"
               data-customer-phone="${customer.phone_number}">
                <div class="d-flex justify-content-between">
                    <span class="fw-bold">${customer.name}</span>
                    <small class="text-muted">${customer.phone_number}</small>
                </div>
            </a>
        `;
    });
    
    customerDropdown.html(html).show();
    
    // Handle customer selection
    $('.customer-result').on('click', function(e) {
        e.preventDefault();
        
        const customerId = $(this).data('customer-id');
        const customerName = $(this).data('customer-name');
        const customerPhone = $(this).data('customer-phone');
        
        // Update form values
        $('#customer-id').val(customerId);
        $('#customer-search').val(`${customerName} - ${customerPhone}`);
        $('#selected-customer').text(`${customerName} (${customerPhone})`);
        
        // Hide dropdown
        customerDropdown.hide();
        
        console.log('Customer selected:', customerName, customerId);
    });
}
