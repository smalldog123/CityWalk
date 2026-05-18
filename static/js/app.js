function navigate(page) {
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('.nav-links a').forEach(a => a.classList.remove('active'));

    document.getElementById(`page-${page}`).classList.add('active');
    document.querySelector(`.nav-links a[data-page="${page}"]`).classList.add('active');

    if (page === 'routes') {
        loadRoutes();
    }
}

document.addEventListener('DOMContentLoaded', function() {
    loadRoutes();

    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            closeModal();
        }
    });
});
