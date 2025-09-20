document.addEventListener('DOMContentLoaded', function() {
    // Preview image before upload
    document.getElementById('id_image').addEventListener('change', function(e) {
        if (e.target.files && e.target.files[0]) {
            const reader = new FileReader();
            reader.onload = function(e) {
                const preview = document.createElement('img');
                preview.src = e.target.result;
                preview.className = 'img-thumbnail mt-2';
                preview.style.maxHeight = '150px';
                
                const container = document.getElementById('id_image').parentNode;
                const existingPreview = container.querySelector('img');
                if (existingPreview) {
                    container.removeChild(existingPreview);
                }
                container.appendChild(preview);
            }
            reader.readAsDataURL(e.target.files[0]);
        }
    });
});
