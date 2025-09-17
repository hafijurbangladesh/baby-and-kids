document.addEventListener('DOMContentLoaded', function() {
    const mainCategory = document.getElementById('main-category');
    const subcategoryContainer = document.getElementById('subcategory-container');
    const finalCategoryInput = document.getElementById('final-category');
    
    // Track current selected values for maintaining state
    let selectedCategories = [];
    
    // Initialize with any existing selection
    if (finalCategoryInput.value) {
        loadCategoryChain(finalCategoryInput.value);
    }

    // Event delegation for all category selects
    document.addEventListener('change', function(event) {
        if (event.target.classList.contains('category-select')) {
            const selectedValue = event.target.value;
            const currentLevel = parseInt(event.target.dataset.level);
            
            // Remove any subsequent category dropdowns
            removeSubsequentCategories(currentLevel);
            
            if (selectedValue) {
                // Update final category and fetch subcategories
                finalCategoryInput.value = selectedValue;
                fetchSubcategories(selectedValue, currentLevel + 1);
            } else {
                // If no value selected, clear final category if this was the last dropdown
                const nextSelect = document.querySelector(`[data-level="${currentLevel + 1}"]`);
                if (!nextSelect) {
                    finalCategoryInput.value = '';
                }
            }
        }
    });

    function loadCategoryChain(categoryId) {
        fetch(`/inventory/api/category-chain/${categoryId}/`)
            .then(response => response.json())
            .then(data => {
                // Clear existing dropdowns
                subcategoryContainer.innerHTML = '';
                selectedCategories = data;
                
                // Set main category
                if (data.length > 0) {
                    const rootCategory = data[0];
                    mainCategory.value = rootCategory.id;
                    
                    // Load subcategories if any
                    if (data.length > 1) {
                        for (let i = 1; i < data.length; i++) {
                            const parentId = data[i-1].id;
                            fetchSubcategories(parentId, i, data[i].id);
                        }
                    }
                }
            })
            .catch(error => console.error('Error loading category chain:', error));
    }

    function fetchSubcategories(parentId, level, selectedId = null) {
        fetch(`/inventory/api/subcategories/?parent_id=${parentId}`)
            .then(response => response.json())
            .then(subcategories => {
                if (subcategories.length > 0) {
                    addSubcategoryDropdown(subcategories, level, selectedId);
                }
            })
            .catch(error => console.error('Error fetching subcategories:', error));
    }

    function addSubcategoryDropdown(subcategories, level, selectedId = null) {
        const div = document.createElement('div');
        div.className = 'mb-3';
        div.dataset.level = level;

        const select = document.createElement('select');
        select.className = 'form-select category-select';
        select.dataset.level = level;

        const defaultOption = document.createElement('option');
        defaultOption.value = '';
        defaultOption.textContent = `Select Subcategory Level ${level}`;
        select.appendChild(defaultOption);

        subcategories.forEach(category => {
            const option = document.createElement('option');
            option.value = category.id;
            option.textContent = category.name;
            if (selectedId && category.id === parseInt(selectedId)) {
                option.selected = true;
            }
            select.appendChild(option);
        });

        div.appendChild(select);
        subcategoryContainer.appendChild(div);
    }

    function removeSubsequentCategories(level) {
        const subsequentCategories = document.querySelectorAll(`[data-level="${level + 1}"]`);
        subsequentCategories.forEach(el => el.remove());
    }
});
