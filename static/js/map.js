var AMAP_KEY = '37c10a3ec8837f0cf57ef6ddb6de639c';

var routeMap = null;

function _createMap(containerOrId, centerLng, centerLat) {
    var map = new AMap.Map(containerOrId, {
        zoom: 13,
        center: [centerLng, centerLat],
        resizeEnable: true,
        viewMode: '2D',
        mapStyle: 'amap://styles/normal',
        features: ['bg', 'road', 'building', 'point'],
    });

    map.addControl(new AMap.Scale());
    map.addControl(new AMap.ToolBar({ position: { top: '10px', right: '10px' } }));

    return map;
}

function _buildPath(gpxPoints) {
    return gpxPoints.map(function (p) {
        var lng = typeof p.lng === 'number' ? p.lng : p.lon;
        var lat = p.lat;
        if (typeof lng !== 'number' || typeof lat !== 'number') return null;
        return [lng, lat];
    }).filter(Boolean);
}

function _drawRoute(gpxPoints) {
    var path = _buildPath(gpxPoints);
    if (path.length === 0) return null;

    routeMap.add(new AMap.Polyline({
        path: path,
        strokeColor: '#fff',
        strokeWeight: 14,
        strokeOpacity: 0.5,
        lineJoin: 'round',
        lineCap: 'round',
        zIndex: 99,
    }));

    routeMap.add(new AMap.Polyline({
        path: path,
        strokeColor: '#FF5722',
        strokeWeight: 8,
        strokeOpacity: 1,
        lineJoin: 'round',
        lineCap: 'round',
        showDir: true,
        zIndex: 100,
    }));

    var start = path[0];
    var end = path[path.length - 1];

    routeMap.add(new AMap.Marker({
        position: start,
        content: '<div style="position:relative;display:flex;align-items:center;gap:4px;background:#4CAF50;color:#fff;padding:4px 10px 4px 6px;border-radius:16px;font-size:12px;font-weight:700;white-space:nowrap;box-shadow:0 2px 8px rgba(0,0,0,0.4);border:2px solid #fff"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2.5"><circle cx="12" cy="12" r="3"/><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7z"/></svg>开始</div>',
        offset: new AMap.Pixel(-12, -34),
        zIndex: 120,
    }));

    routeMap.add(new AMap.Marker({
        position: end,
        content: '<div style="position:relative;display:flex;align-items:center;gap:4px;background:#F44336;color:#fff;padding:4px 10px 4px 6px;border-radius:16px;font-size:12px;font-weight:700;white-space:nowrap;box-shadow:0 2px 8px rgba(0,0,0,0.4);border:2px solid #fff"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2.5"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0118 0z"/><circle cx="12" cy="10" r="3"/></svg>结束</div>',
        offset: new AMap.Pixel(-12, -34),
        zIndex: 120,
    }));

    return { path: path, start: start, end: end };
}

function _drawRouteLabel(path, name) {
    if (!path || path.length < 2 || !name) return;
    var mid = path[Math.floor(path.length / 2)];
    routeMap.add(new AMap.Marker({
        position: mid,
        content: '<div style="background:rgba(255,87,34,0.92);color:#fff;padding:5px 14px;border-radius:6px;font-size:13px;font-weight:700;white-space:nowrap;box-shadow:0 2px 8px rgba(0,0,0,0.3);border:1px solid rgba(255,255,255,0.3)">' + name + '</div>',
        offset: new AMap.Pixel(-40, -40),
        zIndex: 120,
    }));
}

function _drawCityLabel(gpxPoints, city) {
    if (!gpxPoints || gpxPoints.length === 0 || !city) return;
    var path = _buildPath(gpxPoints);
    if (path.length < 2) return;
    var mid = path[Math.floor(path.length / 2)];
    routeMap.add(new AMap.Marker({
        position: [mid[0] + 0.008, mid[1] + 0.004],
        content: '<div style="background:rgba(0,0,0,0.55);color:#fff;padding:2px 8px;border-radius:4px;font-size:11px;white-space:nowrap;backdrop-filter:blur(2px)">' + city + '</div>',
        offset: new AMap.Pixel(-10, -20),
        zIndex: 105,
    }));
}

var _routeCenter = null;
var _poiMarkers = [];

function setRouteCenter(center) { _routeCenter = center; }
function getRouteCenter() { return _routeCenter; }

function _drawPOIs(pois, path) {
    _poiMarkers = [];
    if (!pois || pois.length === 0 || !path || path.length === 0) return;

    var step = Math.floor(path.length / (pois.length + 1));
    pois.forEach(function (poiName, idx) {
        var pathIdx = Math.min(step * (idx + 1), path.length - 1);
        var pos = path[pathIdx];

        var marker = new AMap.Marker({
            position: pos,
            content: '<div style="display:flex;align-items:center;gap:3px;background:#fff;color:#FF5722;padding:3px 10px;border-radius:12px;font-size:12px;white-space:nowrap;font-weight:600;box-shadow:0 2px 8px rgba(0,0,0,0.2);border:1.5px solid #FF5722;cursor:pointer;transition:transform 0.15s,box-shadow 0.15s" onmouseover="this.style.transform=\'scale(1.1)\';this.style.boxShadow=\'0 4px 12px rgba(255,87,34,0.4)\'" onmouseout="this.style.transform=\'scale(1)\';this.style.boxShadow=\'0 2px 8px rgba(0,0,0,0.2)\'"><svg width="12" height="12" viewBox="0 0 24 24" fill="#FF5722" stroke="none"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0118 0z"/><circle cx="12" cy="10" r="3" fill="#fff"/></svg>' + poiName + '</div>',
            offset: new AMap.Pixel(-20, -28),
            zIndex: 110,
        });

        marker.on('click', function () {
            routeMap.setZoomAndCenter(16, pos, false, 300);
        });

        routeMap.add(marker);
        _poiMarkers.push({ name: poiName, position: pos, marker: marker });
    });
}

function focusPOI(poiName) {
    var found = _poiMarkers.find(function (p) { return p.name === poiName; });
    if (found && routeMap) {
        routeMap.setZoomAndCenter(16, found.position, false, 300);
    }
}

function _addOverlays(gpxPoints, routeData) {
    var info = _drawRoute(gpxPoints);
    var path = info ? info.path : null;

    if (routeData) {
        if (path && routeData.name) _drawRouteLabel(path, routeData.name);
        if (routeData.pois && path) _drawPOIs(routeData.pois, path);
        if (routeData.city) _drawCityLabel(gpxPoints, routeData.city);
    }

    return info;
}

function initRouteMap(containerId, gpxPoints, routeData) {
    destroyMap();

    var container = document.getElementById(containerId);
    if (!container) return;

    container.innerHTML = '';

    if (!gpxPoints || gpxPoints.length === 0) {
        container.innerHTML = '<div class="map-empty"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0118 0z"/><circle cx="12" cy="10" r="3"/></svg><span>暂无轨迹数据</span></div>';
        return;
    }

    container.innerHTML = '<div id="map-canvas" class="map-container"></div>';

    var first = gpxPoints[0];
    var lng = (typeof first.lng === 'number') ? first.lng : (first.lon || 116.397428);
    var lat = first.lat || 39.90923;
    setRouteCenter({ lng: lng, lat: lat });

    routeMap = _createMap('map-canvas', lng, lat);

    _addOverlays(gpxPoints, routeData);

    setTimeout(function () {
        if (routeMap) {
            routeMap.setFitView(null, false, [80, 80, 80, 80]);
        }
    }, 300);
}

function destroyMap() {
    if (routeMap) {
        routeMap.destroy();
        routeMap = null;
    }
    _routeCenter = null;
    _poiMarkers = [];
}

function initFullMap(containerId, gpxPoints, routeData) {
    destroyMap();

    var container = document.getElementById(containerId);
    if (!container) return;

    if (!gpxPoints || gpxPoints.length === 0) {
        container.innerHTML = '<div class="map-empty" style="height:100%"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0118 0z"/><circle cx="12" cy="10" r="3"/></svg><span>暂无轨迹数据</span></div>';
        return;
    }

    var first = gpxPoints[0];
    var lng = (typeof first.lng === 'number') ? first.lng : (first.lon || 116.397428);
    var lat = first.lat || 39.90923;
    setRouteCenter({ lng: lng, lat: lat });

    routeMap = _createMap(containerId, lng, lat);

    _addOverlays(gpxPoints, routeData);

    setTimeout(function () {
        if (routeMap) {
            routeMap.setFitView(null, false, [100, 100, 100, 100]);
        }
    }, 300);
}

function parseGPXContent(xmlString) {
    var parser = new DOMParser();
    var xmlDoc = parser.parseFromString(xmlString, 'text/xml');

    if (xmlDoc.querySelector('parsererror')) {
        throw new Error('GPX 文件格式无效，无法解析');
    }

    var nameEl = xmlDoc.getElementsByTagName('name')[0];
    var trackName = nameEl ? nameEl.textContent.trim() : '未命名路线';

    var trkpts = xmlDoc.getElementsByTagName('trkpt');
    if (trkpts.length === 0) {
        throw new Error('GPX 文件中未找到轨迹点 (trkpt)');
    }

    var gpxPoints = [];
    for (var i = 0; i < trkpts.length; i++) {
        var pt = trkpts[i];
        var ele = pt.getElementsByTagName('ele')[0];
        var time = pt.getElementsByTagName('time')[0];
        gpxPoints.push({
            lat: parseFloat(pt.getAttribute('lat')),
            lng: parseFloat(pt.getAttribute('lon')),
            elevation: ele ? parseFloat(ele.textContent) : null,
            timestamp: time ? time.textContent : null,
        });
    }

    var cmt = xmlDoc.getElementsByTagName('cmt')[0];
    var desc = xmlDoc.getElementsByTagName('desc')[0];
    var parts = [];
    if (cmt) parts.push(cmt.textContent.trim());
    if (desc) parts.push(desc.textContent.trim());
    var description = parts.length > 0 ? parts.join('；') : null;

    return { name: trackName, gpxPoints: gpxPoints, description: description };
}

async function handleGPXUpload(event) {
    var file = event.target.files[0];
    if (!file) return;

    var progress = document.getElementById('upload-progress');
    var status = document.getElementById('upload-status');

    progress.classList.add('show');
    status.textContent = '解析文件中...';

    try {
        var text = await file.text();
        var parsed = parseGPXContent(text);
        status.textContent = '上传中...';

        await apiPost('/routes/upload-gpx', {
            name: file.name.replace(/\.gpx$/i, ''),
            parsed_name: parsed.name,
            description: parsed.description,
            gpx_points: parsed.gpxPoints,
        });

        status.textContent = '上传成功！';
        setTimeout(function () {
            progress.classList.remove('show');
            status.textContent = '上传中...';
        }, 1500);

        event.target.value = '';
        loadRoutes();
    } catch (err) {
        status.textContent = '上传失败: ' + err.message;
        setTimeout(function () {
            progress.classList.remove('show');
            status.textContent = '上传中...';
        }, 3000);
    }
}
