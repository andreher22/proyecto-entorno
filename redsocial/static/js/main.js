// GraphNet - JavaScript Principal

document.addEventListener('DOMContentLoaded', function () {
    // Auto-cerrar alertas después de 5 segundos
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.opacity = '0';
            alert.style.transform = 'translateY(-10px)';
            setTimeout(() => alert.remove(), 300);
        }, 5000);
    });

    // Animación de entrada para cards
    const cards = document.querySelectorAll('.card, .user-card, .stat-card');
    cards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        setTimeout(() => {
            card.style.transition = 'all 0.5s ease';
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, index * 100);
    });

    // Confirmación para eliminar amigo
    const deleteButtons = document.querySelectorAll('a[href*="eliminar"]');
    deleteButtons.forEach(btn => {
        btn.addEventListener('click', function (e) {
            if (!confirm('¿Estás seguro de que quieres eliminar a este amigo?')) {
                e.preventDefault();
            }
        });
    });

    // Preview de imagen de perfil
    const fotoInput = document.querySelector('input[type="file"][name="foto"]');
    if (fotoInput) {
        fotoInput.addEventListener('change', function () {
            const file = this.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function (e) {
                    const preview = document.querySelector('.profile-avatar img, .user-avatar img');
                    if (preview) {
                        preview.src = e.target.result;
                    }
                };
                reader.readAsDataURL(file);
            }
        });
    }

    // Tooltip para puntuación de recomendación
    const scoreBadges = document.querySelectorAll('.score-badge');
    scoreBadges.forEach(badge => {
        badge.title = 'Puntuación basada en amigos en común y cercanía en el grafo social';
    });
});
