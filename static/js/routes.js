const DIFFICULTY_MAP = {
    easy: { label: '简单', class: 'badge-easy' },
    moderate: { label: '中等', class: 'badge-moderate' },
    hard: { label: '困难', class: 'badge-hard' },
    expert: { label: '专家', class: 'badge-expert' },
};

const DEFAULT_COVER = 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=' + encodeURIComponent('a beautiful scenic hiking trail through lush green mountains with a winding path, morning mist, golden sunlight, photorealistic landscape photography, 4k') + '&image_size=landscape_16_9';

let searchTimer = null;
let carouselIntervals = {};

function debounceSearch() {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(loadRoutes, 400);
}

async function loadRoutes() {
    const grid = document.getElementById('routes-grid');
    const keyword = document.getElementById('route-search').value.trim();
    const city = document.getElementById('filter-city').value;
    const difficulty = document.getElementById('filter-difficulty').value;

    Object.values(carouselIntervals).forEach(function(id) { clearInterval(id); });
    carouselIntervals = {};

    grid.innerHTML = '<div style="grid-column:1/-1;text-align:center;padding:40px"><div class="loading-spinner"></div><p style="margin-top:12px;color:var(--text-secondary);font-size:14px">加载中...</p></div>';

    try {
        const data = await fetchRoutes({ keyword, city, difficulty });
        const routes = data.routes || [];

        if (routes.length === 0) {
            grid.innerHTML = `
                <div class="empty-state" style="grid-column:1/-1">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                        <path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 00-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0020 4.77 5.07 5.07 0 0019.91 1S18.73.65 16 2.48a13.38 13.38 0 00-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 005 4.77a5.44 5.44 0 00-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 009 18.13V22"/>
                    </svg>
                    <h3>暂无路线</h3>
                    <p>试试调整筛选条件</p>
                </div>`;
            return;
        }

        grid.innerHTML = routes.map(route => renderRouteCard(route)).join('');
        startCarousels();
    } catch (err) {
        grid.innerHTML = `
            <div class="empty-state" style="grid-column:1/-1">
                <h3>加载失败</h3>
                <p>${err.message}</p>
            </div>`;
    }
}

function renderRouteCard(route) {
    const diff = DIFFICULTY_MAP[route.difficulty] || { label: route.difficulty, class: '' };
    const tags = (route.tags || []).map(t => `<span class="tag">${t}</span>`).join('');
    const pois = route.pois || [];
    const images = route.images && route.images.length > 0 ? route.images : [];
    const hasImages = images.length > 0;
    const carouselId = 'carousel-' + route._id;

    let headerContent;
    if (hasImages) {
        const slides = images.map((img, idx) =>
            `<div class="carousel-slide${idx === 0 ? ' active' : ''}" style="background-image:url('${img}')"></div>`
        ).join('');
        const dots = images.length > 1 ? images.map((_, idx) =>
            `<span class="carousel-dot${idx === 0 ? ' active' : ''}" onclick="event.stopPropagation();goToSlide('${carouselId}',${idx})"></span>`
        ).join('') : '';
        const navBtns = images.length > 1 ? `
            <button class="carousel-nav carousel-prev" onclick="event.stopPropagation();prevSlide('${carouselId}')">&#10094;</button>
            <button class="carousel-nav carousel-next" onclick="event.stopPropagation();nextSlide('${carouselId}')">&#10095;</button>
        ` : '';
        headerContent = `
            <div class="route-card-carousel" id="${carouselId}" data-index="0" data-count="${images.length}">
                ${slides}
                ${navBtns}
                <div class="carousel-dots">${dots}</div>
            </div>`;
    } else {
        headerContent = `
            <div class="route-card-default-cover">
                <img src="${DEFAULT_COVER}" alt="默认封面" onerror="this.style.display='none';this.parentElement.querySelector('.fallback-icon').style.display='flex'">
                <div class="fallback-icon" style="display:none">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                        <path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z"/>
                        <polyline points="9 22 9 12 15 12 15 22"/>
                    </svg>
                </div>
            </div>`;
    }

    return `
        <div class="route-card" onclick="showRouteDetail('${route._id}')">
            <div class="route-card-header">
                ${headerContent}
                <span class="difficulty-badge badge ${diff.class}">${diff.label}</span>
                <span class="city-label">${route.city}</span>
            </div>
            <div class="route-card-body">
                <h3>${route.name}</h3>
                <p class="description">${route.description || ''}</p>
                <div class="route-card-stats">
                    <span class="stat">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/></svg>
                        ${route.distance_km}km
                    </span>
                    <span class="stat">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 19V5M5 12l7-7 7 7"/></svg>
                        ${route.elevation_gain_m || 0}m
                    </span>
                    <span class="stat">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
                        ${route.duration_hours ? route.duration_hours + 'h' : '-'}
                    </span>
                </div>
                <div class="route-card-tags">${tags}</div>
            </div>
        </div>`;
}

let currentRouteId = null;

async function showRouteDetail(routeId) {
    const modal = document.getElementById('route-modal');
    const title = document.getElementById('modal-title');
    const body = document.getElementById('modal-body');
    const mapArea = document.getElementById('modal-map');

    currentRouteId = routeId;
    body.innerHTML = '<div style="text-align:center;padding:40px"><div class="loading-spinner"></div></div>';
    mapArea.innerHTML = '';
    modal.classList.add('show');

    try {
        const route = await fetchRouteDetail(routeId);
        const diff = DIFFICULTY_MAP[route.difficulty] || { label: route.difficulty, class: '' };
        const tags = (route.tags || []).map(t => `<span class="tag">${t}</span>`).join('');
        const pois = (route.pois || []).map(p => `
            <span class="poi-item" style="cursor:pointer;transition:all 0.15s" onclick="event.stopPropagation();focusPOI('${p.replace(/'/g, "\\'")}')" onmouseover="this.style.background='#FF5722';this.style.color='#fff'" onmouseout="this.style.background='';this.style.color=''">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0118 0z"/><circle cx="12" cy="10" r="3"/></svg>
                ${p}
            </span>`).join('');

        const hasGpx = route.gpx_points && route.gpx_points.length > 0;
        const gpxCount = hasGpx ? route.gpx_points.length : 0;

        title.textContent = route.name;
        body.innerHTML = `
            <div class="route-detail">
                <div class="detail-header">
                    <span class="badge ${diff.class}">${diff.label}</span>
                    <span class="detail-city">${route.city}</span>
                </div>
                <div class="detail-stats">
                    <div class="detail-stat">
                        <div class="value">${route.distance_km}</div>
                        <div class="label">距离 (km)</div>
                    </div>
                    <div class="detail-stat">
                        <div class="value">${route.elevation_gain_m || 0}</div>
                        <div class="label">爬升 (m)</div>
                    </div>
                    <div class="detail-stat">
                        <div class="value">${route.duration_hours || '-'}</div>
                        <div class="label">时长 (h)</div>
                    </div>
                </div>
                ${hasGpx ? `
                <div class="detail-map-preview">
                    <h4>路线概览 <span style="color:var(--text-light);font-weight:400;font-size:12px">${gpxCount} 个轨迹点</span></h4>
                    <div id="modal-map-inner" class="map-preview-container"></div>
                    <button class="btn btn-outline btn-sm" style="margin-top:12px;width:100%;background:#FF5722;color:#fff;border-color:#FF5722;font-weight:600;font-size:14px;padding:10px 16px" onclick="openFullMap()">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M15 3v18"/></svg>
                        查看详情
                    </button>
                </div>` : `
                <div class="map-empty">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0118 0z"/><circle cx="12" cy="10" r="3"/></svg>
                    <span>暂无轨迹数据</span>
                </div>`}
                <div class="detail-description" style="margin-top:${hasGpx ? '16px' : '0'}">
                    <h4>路线描述</h4>
                    <p>${route.description || '暂无描述'}</p>
                </div>
                ${pois ? `
                <div class="detail-pois">
                    <h4>沿途景点</h4>
                    <div class="poi-list">${pois}</div>
                </div>` : ''}
                ${tags ? `
                <div style="margin-top:16px">
                    <h4 style="font-size:14px;font-weight:600;margin-bottom:8px">标签</h4>
                    <div class="detail-tags">${tags}</div>
                </div>` : ''}
            </div>`;
        mapArea.innerHTML = '';

        if (hasGpx) {
            window._gpxPoints = route.gpx_points;
            window._routeName = route.name;
            window._routeCity = route.city;
            window._routeStats = {
                distance_km: route.distance_km,
                elevation_gain_m: route.elevation_gain_m || 0,
                duration_hours: route.duration_hours || '-',
                difficulty: route.difficulty,
            };
            setTimeout(() => initRouteMap('modal-map-inner', route.gpx_points, {
                name: route.name,
                city: route.city,
                pois: route.pois,
            }), 150);
        }
    } catch (err) {
        body.innerHTML = `<div class="empty-state"><h3>加载失败</h3><p>${err.message}</p></div>`;
    }
}

function openFullMap() {
    if (!currentRouteId) return;
    window.open('/map/' + currentRouteId, '_blank');
}

function closeModal() {
    document.getElementById('route-modal').classList.remove('show');
    destroyMap();
}

document.getElementById('route-modal').addEventListener('click', function(e) {
    if (e.target === this) closeModal();
});

function goToSlide(carouselId, index) {
    var el = document.getElementById(carouselId);
    if (!el) return;
    var count = parseInt(el.dataset.count);
    var current = parseInt(el.dataset.index);
    if (index < 0) index = count - 1;
    if (index >= count) index = 0;
    el.dataset.index = index;
    var slides = el.querySelectorAll('.carousel-slide');
    var dots = el.querySelectorAll('.carousel-dot');
    slides.forEach(function(s, i) { s.classList.toggle('active', i === index); });
    dots.forEach(function(d, i) { d.classList.toggle('active', i === index); });
}

function nextSlide(carouselId) {
    var el = document.getElementById(carouselId);
    if (!el) return;
    goToSlide(carouselId, parseInt(el.dataset.index) + 1);
}

function prevSlide(carouselId) {
    var el = document.getElementById(carouselId);
    if (!el) return;
    goToSlide(carouselId, parseInt(el.dataset.index) - 1);
}

function startCarousels() {
    Object.values(carouselIntervals).forEach(function(id) { clearInterval(id); });
    carouselIntervals = {};
    document.querySelectorAll('.route-card-carousel').forEach(function(el) {
        var count = parseInt(el.dataset.count);
        if (count <= 1) return;
        var id = el.id;
        carouselIntervals[id] = setInterval(function() {
            nextSlide(id);
        }, 4000);
    });
}
