"""Rebuild index.html keeping the PAINTINGS data intact."""

content = open('index.html', encoding='utf-8').read()
idx = content.find('\nconst PAINTINGS = [')
nl  = content.find('\n', idx + 1)
paintings_line = content[idx : nl + 1]
tail = content[content.rfind('</script>'):]

# ── New HTML (before PAINTINGS) ───────────────────────────────────────────────
PRE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Art Map — Most Referenced Paintings</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.css"/>
<link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.Default.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script src="https://unpkg.com/leaflet.markercluster@1.5.3/dist/leaflet.markercluster.js"></script>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: 'Georgia', serif; background: #1a1a1a; color: #f0ead6; height: 100vh; display: flex; flex-direction: column; }

  /* Tabs */
  #tabs { display: flex; gap: 2px; padding: 0 20px; background: #111; border-bottom: 1px solid #333; flex-shrink: 0; }
  .tab-btn { padding: 8px 18px; font-size: 0.75rem; letter-spacing: 0.05em; color: #888; background: none; border: none; border-bottom: 2px solid transparent; cursor: pointer; font-family: 'Georgia', serif; transition: color 0.15s; }
  .tab-btn:hover { color: #c9a84c; }
  .tab-btn.active { color: #c9a84c; border-bottom-color: #c9a84c; }

  /* Panels */
  #panel-map      { flex: 1; display: none; flex-direction: column; overflow: hidden; }
  #panel-period   { flex: 1; display: none; flex-direction: column; overflow: hidden; }
  #panel-timeline { flex: 1; display: none; flex-direction: column; overflow: hidden; }
  #panel-map.active, #panel-period.active, #panel-timeline.active { display: flex; }

  /* Header */
  #header { padding: 12px 20px; background: #111; border-bottom: 1px solid #333; display: flex; align-items: center; flex-shrink: 0; gap: 20px; }
  #header h1 { font-size: 1.1rem; font-weight: normal; letter-spacing: 0.05em; color: #c9a84c; }
  #header p  { font-size: 0.75rem; color: #888; margin-top: 3px; }

  /* Search */
  #search-wrap { position: relative; margin-left: auto; flex-shrink: 0; }
  #search-input { background: #1e1e1e; border: 1px solid #333; color: #f0ead6; padding: 6px 12px 6px 30px; font-size: 0.74rem; font-family: 'Georgia', serif; border-radius: 3px; width: 230px; outline: none; }
  #search-input:focus { border-color: #c9a84c; }
  #search-input::placeholder { color: #555; }
  #search-icon { position: absolute; left: 9px; top: 50%; transform: translateY(-50%); color: #555; pointer-events: none; font-size: 13px; }
  #search-drop { position: absolute; top: calc(100% + 5px); right: 0; background: #1e1e1e; border: 1px solid #333; border-radius: 3px; width: 300px; max-height: 340px; overflow-y: auto; z-index: 10000; display: none; box-shadow: 0 6px 20px rgba(0,0,0,0.6); scrollbar-width: thin; scrollbar-color: #444 #1e1e1e; }
  #search-drop::-webkit-scrollbar { width: 4px; }
  #search-drop::-webkit-scrollbar-thumb { background: #444; border-radius: 2px; }
  .search-item { padding: 8px 12px; cursor: pointer; border-bottom: 1px solid #252525; }
  .search-item:last-child { border-bottom: none; }
  .search-item:hover, .search-item.si-active { background: #2a2a2a; }
  .search-item-title { font-size: 0.75rem; color: #e0d8c0; }
  .search-item-sub { font-size: 0.65rem; color: #666; margin-top: 2px; }
  .search-no-result { padding: 10px 12px; font-size: 0.72rem; color: #555; }

  /* Century filter bar (map tab) */
  #century-bar { display: flex; gap: 6px; padding: 7px 14px; background: #141414; border-bottom: 1px solid #2a2a2a; flex-shrink: 0; align-items: center; }
  #century-bar > span { font-size: 0.7rem; color: #555; margin-right: 4px; flex-shrink: 0; }
  .century-btn { padding: 3px 11px; font-size: 0.7rem; background: #1e1e1e; border: 1px solid #2e2e2e; color: #666; cursor: pointer; border-radius: 3px; font-family: 'Georgia', serif; transition: all 0.15s; }
  .century-btn:hover { border-color: rgba(201,168,76,0.5); color: #bbb; }
  .century-btn.active { background: rgba(201,168,76,0.1); border-color: #c9a84c; color: #c9a84c; }

  /* Map */
  #map { flex: 1; }

  /* Art dots */
  .art-dot { border-radius: 50%; background: #c9a84c; border: 1px solid #8a6f2e; cursor: pointer; transition: transform 0.15s; }
  .art-dot:hover { transform: scale(1.4); }

  /* Cluster bubbles */
  .art-cluster { border-radius: 50%; background: radial-gradient(circle at 35% 35%, #e8c96a, #9a6f1e); border: 2px solid #c9a84c; box-shadow: 0 0 10px rgba(201,168,76,0.5); display: flex; align-items: center; justify-content: center; font-family: 'Georgia', serif; font-weight: bold; color: #111; cursor: pointer; transition: transform 0.15s; }
  .art-cluster:hover { transform: scale(1.08); }
  .art-cluster.small  { font-size: 0.75rem; }
  .art-cluster.medium { font-size: 0.85rem; }
  .art-cluster.large  { font-size: 1rem; }
  .leaflet-cluster-anim .leaflet-marker-icon,
  .leaflet-cluster-anim .leaflet-marker-shadow { transition: left 0.3s ease-out, top 0.3s ease-out, opacity 0.3s; }

  /* Popup */
  .leaflet-popup-content-wrapper { background: #1e1e1e; border: 1px solid #333; border-radius: 4px; color: #f0ead6; box-shadow: 0 4px 20px rgba(0,0,0,0.6); }
  .leaflet-popup-tip { background: #1e1e1e; }
  .leaflet-popup-content { margin: 0; width: 280px !important; }
  .popup-inner { padding: 14px; }
  .popup-img { width: 100%; height: 160px; object-fit: cover; display: block; background: #111; }
  .search-popup .leaflet-popup-content { width: 340px !important; }
  .search-popup .popup-img { height: auto; max-height: 340px; object-fit: contain; }
  .popup-title { font-size: 1rem; margin-bottom: 4px; color: #c9a84c; }
  .popup-meta { font-size: 0.75rem; color: #aaa; margin-bottom: 8px; }
  .popup-location { font-size: 0.75rem; color: #888; margin-bottom: 10px; }
  .popup-score-row { display: flex; gap: 12px; font-size: 0.72rem; }
  .score-badge { background: #c9a84c; color: #111; font-weight: bold; padding: 3px 8px; border-radius: 2px; }
  .stat { color: #999; }
  .stat span { color: #ccc; }
  .popup-link { display: block; margin-top: 10px; font-size: 0.72rem; color: #c9a84c; text-decoration: none; }
  .popup-link:hover { text-decoration: underline; }

  /* Gallery cluster popup */
  .gallery-popup .leaflet-popup-content-wrapper { padding: 0; width: 300px; }
  .gallery-popup .leaflet-popup-content { margin: 0; width: 300px !important; }
  .gallery-header { padding: 10px 14px 8px; background: #111; border-bottom: 1px solid #333; font-size: 0.8rem; color: #c9a84c; letter-spacing: 0.04em; }
  .gallery-list { max-height: 420px; overflow-y: auto; scrollbar-width: thin; scrollbar-color: #444 #1e1e1e; }
  .gallery-list::-webkit-scrollbar { width: 5px; }
  .gallery-list::-webkit-scrollbar-track { background: #1e1e1e; }
  .gallery-list::-webkit-scrollbar-thumb { background: #444; border-radius: 3px; }
  .gallery-card { display: flex; gap: 10px; padding: 10px 14px; border-bottom: 1px solid #2a2a2a; align-items: flex-start; }
  .gallery-card:last-child { border-bottom: none; }
  .gallery-card:hover { background: #252525; }
  .gallery-thumb { width: 56px; height: 56px; object-fit: cover; flex-shrink: 0; background: #111; border-radius: 2px; }
  .gallery-thumb-placeholder { width: 56px; height: 56px; flex-shrink: 0; background: #222; border-radius: 2px; }
  .gallery-card-info { flex: 1; min-width: 0; }
  .gallery-card-title { font-size: 0.8rem; color: #c9a84c; margin-bottom: 2px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .gallery-card-artist { font-size: 0.7rem; color: #aaa; margin-bottom: 5px; }
  .gallery-card-row { display: flex; gap: 8px; align-items: center; }
  .gallery-card-score { background: #c9a84c; color: #111; font-weight: bold; font-size: 0.65rem; padding: 2px 6px; border-radius: 2px; }
  .gallery-card-stat { font-size: 0.65rem; color: #777; }
  .gallery-card-link { font-size: 0.65rem; color: #c9a84c; text-decoration: none; margin-left: auto; }
  .gallery-card-link:hover { text-decoration: underline; }
  .gallery-group-header { padding: 7px 14px 5px; font-size: 0.72rem; color: #f0ead6; background: #252525; border-bottom: 1px solid #333; display: flex; justify-content: space-between; align-items: center; letter-spacing: 0.02em; }
  .gallery-group-count { background: #333; color: #aaa; font-size: 0.65rem; padding: 1px 6px; border-radius: 10px; }

  /* By Period */
  #period-scroll { flex: 1; overflow: auto; padding: 16px 20px 10px; }
  #period-grid { display: flex; gap: 14px; min-width: max-content; }
  .period-col { width: 188px; flex-shrink: 0; display: flex; flex-direction: column; }
  .period-heading { font-size: 0.82rem; color: #c9a84c; text-align: center; padding-bottom: 7px; border-bottom: 1px solid #333; margin-bottom: 10px; letter-spacing: 0.04em; }
  .period-bar-area { height: 260px; display: flex; align-items: flex-end; margin-bottom: 3px; }
  .period-bar { display: flex; flex-direction: column; width: 100%; border-radius: 2px 2px 0 0; overflow: hidden; border-bottom: 1px solid #444; }
  .period-bar-seg { flex-shrink: 0; cursor: default; }
  .period-count { font-size: 0.62rem; color: #555; text-align: center; margin-bottom: 10px; }
  .period-top5 { display: flex; flex-direction: column; gap: 7px; }
  .period-card { border: 1px solid #2a2a2a; border-radius: 3px; overflow: hidden; transition: border-color 0.15s; text-decoration: none; display: block; color: inherit; }
  .period-card:hover { border-color: #c9a84c; }
  .period-card-img { width: 100%; height: 80px; object-fit: cover; background: #111; display: block; }
  .period-card-ph  { width: 100%; height: 80px; background: #1a1a1a; display: block; }
  .period-card-body { padding: 5px 7px 7px; background: #1e1e1e; }
  .period-card-score { display: inline-block; background: #c9a84c; color: #111; font-size: 0.6rem; font-weight: bold; padding: 1px 5px; border-radius: 2px; margin-bottom: 4px; }
  .period-card-title  { font-size: 0.68rem; color: #e0d8c0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; margin-bottom: 2px; }
  .period-card-artist { font-size: 0.61rem; color: #888;    white-space: nowrap; overflow: hidden; text-overflow: ellipsis; margin-bottom: 2px; }
  .period-card-loc    { font-size: 0.59rem; color: #666;    white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

  /* Bar segment tooltip */
  #bar-tooltip { position: fixed; background: #1e1e1e; border: 1px solid #444; padding: 5px 10px; font-size: 0.72rem; color: #f0ead6; pointer-events: none; display: none; z-index: 9999; border-radius: 3px; white-space: nowrap; }

  /* Search popup — appears to the right of the pin, no tip */
  .search-popup .leaflet-popup-tip-container { display: none; }
  .search-popup .leaflet-popup-content-wrapper { border-left: 2px solid #c9a84c; }

  /* Shared geo legend */
  .geo-legend { flex-shrink: 0; display: flex; flex-wrap: wrap; gap: 8px 16px; padding: 8px 20px; border-top: 1px solid #222; }
  .geo-leg-item { display: flex; align-items: center; gap: 5px; font-size: 0.62rem; color: #888; }
  .geo-leg-dot { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }
  .geo-leg-flag { width: 18px; height: 18px; border-radius: 50%; object-fit: cover; flex-shrink: 0; }

  /* Timeline */
  #tl-scroll { flex: 1; overflow: auto; position: relative; min-height: 0; }
  #tl-scroll::-webkit-scrollbar { width: 5px; height: 5px; }
  #tl-scroll::-webkit-scrollbar-track { background: #1a1a1a; }
  #tl-scroll::-webkit-scrollbar-thumb { background: #444; border-radius: 3px; }
  #tl-spacer { display: block; }
  #tl-canvas { position: absolute; top: 0; left: 0; display: block; pointer-events: none; }
  #tl-cards  { position: absolute; top: 0; left: 0; }
  .tl-card   { position: absolute; }

  /* ── Mobile ───────────────────────────────────────────────────────────────── */
  @media (max-width: 600px) {
    /* Header: stack title above search */
    #header { flex-direction: column; align-items: flex-start; gap: 8px; padding: 10px 14px; }
    #header h1 { font-size: 0.95rem; }
    #header p  { font-size: 0.68rem; }
    #search-wrap { margin-left: 0; width: 100%; }
    #search-input { width: 100%; font-size: 0.78rem; }
    #search-drop { width: 100%; right: auto; left: 0; }

    /* Tabs */
    #tabs { padding: 0 10px; }
    .tab-btn { padding: 8px 12px; font-size: 0.78rem; }

    /* Period filter bar: allow horizontal scroll instead of wrapping */
    #century-bar { overflow-x: auto; flex-wrap: nowrap; gap: 5px; padding: 6px 10px; -webkit-overflow-scrolling: touch; scrollbar-width: none; }
    #century-bar::-webkit-scrollbar { display: none; }
    .century-btn { padding: 4px 10px; font-size: 0.72rem; white-space: nowrap; }
    #century-bar > span { display: none; }

    /* By Period: narrower columns */
    #period-scroll { padding: 10px 10px 6px; }
    #period-grid { gap: 10px; }
    .period-col { width: 150px; }
    .period-card-img, .period-card-ph { height: 65px; }

    /* Geo legend: smaller */
    .geo-legend { gap: 5px 10px; padding: 6px 10px; }
    .geo-leg-item { font-size: 0.6rem; }
    .geo-leg-flag { width: 14px; height: 14px; }
    .geo-leg-dot  { width: 8px; height: 8px; }

    /* Search popup: constrain width on narrow screens */
    .search-popup .leaflet-popup-content { width: 260px !important; }
    .search-popup .popup-img { max-height: 240px; }
  }
</style>
</head>
<body>

<div id="header">
  <div>
    <h1>Art Map — Most Referenced Paintings</h1>
    <p>1,000 publicly displayed works ranked by Wikipedia reach &amp; global cultural footprint</p>
  </div>
  <div id="search-wrap">
    <span id="search-icon">&#9906;</span>
    <input type="text" id="search-input" placeholder="Search painting or artist…" autocomplete="off" spellcheck="false">
    <div id="search-drop"></div>
  </div>
</div>

<div id="tabs">
  <button class="tab-btn active" data-tab="map">Map</button>
  <button class="tab-btn" data-tab="period">By Period</button>
  <button class="tab-btn" data-tab="timeline">Timeline</button>
</div>

<div id="panel-map" class="active">
  <div id="century-bar">
    <span>Period</span>
  </div>
  <div id="map"></div>
</div>

<div id="panel-period">
  <div id="period-scroll">
    <div id="period-grid"></div>
  </div>
  <div id="period-geo-legend" class="geo-legend"></div>
</div>

<div id="panel-timeline">
  <div id="tl-scroll">
    <div id="tl-spacer"></div>
    <canvas id="tl-canvas"></canvas>
    <div id="tl-cards"></div>
  </div>
  <div id="tl-legend" class="geo-legend"></div>
</div>

<div id="bar-tooltip"></div>

<script>
"""

# ── New JS (after PAINTINGS line) ─────────────────────────────────────────────
POST_JS = r"""
// ── Shared constants ──────────────────────────────────────────────────────────
const CENTURY_BINS = [
  { label: 'to 1500', fn: y => y < 1500 },
  { label: '1500s',   fn: y => y >= 1500 && y < 1600 },
  { label: '1600s',   fn: y => y >= 1600 && y < 1700 },
  { label: '1700s',   fn: y => y >= 1700 && y < 1800 },
  { label: '1800s',   fn: y => y >= 1800 && y < 1900 },
  { label: '1900+',   fn: y => y >= 1900 },
];

const OTHER_EU = new Set(['Netherlands','Belgium','Russia','Switzerland','Europe other']);
const ROW_DEFS = [
  { label: 'France',        color: '#4e8abf', flag: 'fr', match: p => p.geo_tag === 'France' },
  { label: 'Italy',         color: '#c0513a', flag: 'it', match: p => p.geo_tag === 'Italy' },
  { label: 'UK',            color: '#3aab6f', flag: 'gb', match: p => p.geo_tag === 'United Kingdom' },
  { label: 'United States', color: '#9b6bbf', flag: 'us', match: p => p.geo_tag === 'United States' },
  { label: 'Spain',         color: '#d4a017', flag: 'es', match: p => p.geo_tag === 'Spain' },
  { label: 'Germany',       color: '#5b8fa8', flag: 'de', match: p => p.geo_tag === 'Germany' },
  { label: 'Austria',       color: '#8a5c2e', flag: 'at', match: p => p.geo_tag === 'Austria' },
  { label: 'Other Europe',  color: '#7a9e60', flag: 'eu', match: p => OTHER_EU.has(p.geo_tag) },
  { label: 'Rest of World', color: '#a08030', flag: null, match: p => false },
];
ROW_DEFS[8].match = p => !ROW_DEFS.slice(0, 8).some(r => r.match(p));

function geoOf(p) { return ROW_DEFS.find(r => r.match(p)); }

// ── Leaflet map ────────────────────────────────────────────────────────────────
const map = L.map('map', { center: [48, 10], zoom: 4, zoomControl: true });
L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
  attribution: '&copy; <a href="https://carto.com/">CartoDB</a> | Data: Wikidata/Wikipedia',
  maxZoom: 18,
}).addTo(map);

let allMarkers = [];
let markerLayer = null;

function thumbUrl(imageUrl, width) {
  if (!imageUrl) return null;
  // For en.wikipedia Special:FilePath (fair-use images like Persistence of Memory)
  // keep the ?width= approach as thumb.php is Commons-only
  if (imageUrl.includes('en.wikipedia.org')) {
    const base = imageUrl.replace(/^http:/, 'https:');
    return base.includes('?') ? `${base}&width=${width}` : `${base}?width=${width}`;
  }
  // For Wikimedia Commons: use thumb.php directly (no redirect chain, more reliable on mobile)
  const m = imageUrl.match(/Special:FilePath\/(.+)$/);
  if (m) {
    const filename = m[1].split('?')[0]; // strip any existing query params
    return `https://commons.wikimedia.org/w/thumb.php?width=${width}&f=${filename}`;
  }
  // Fallback: original ?width= approach
  const base = imageUrl.replace(/^http:/, 'https:');
  return base.includes('?') ? `${base}&width=${width}` : `${base}?width=${width}`;
}

function preloadThumbnails(paintings) {
  paintings.forEach(p => {
    if (!p.image) return;
    const img = new Image();
    img.src = thumbUrl(p.image, 100);
  });
}

function galleryCard(p) {
  const url = thumbUrl(p.image, 100);
  const thumb = url
    ? `<img class="gallery-thumb" src="${url}" alt="">`
    : `<div class="gallery-thumb-placeholder"></div>`;
  const link = p.en_article
    ? `<a class="gallery-card-link" href="https://en.wikipedia.org/wiki/${encodeURIComponent(p.en_article)}" target="_blank">Wiki →</a>`
    : '';
  return `<div class="gallery-card">
    ${thumb}
    <div class="gallery-card-info">
      <div class="gallery-card-title" title="${p.label}">${p.label}</div>
      <div class="gallery-card-artist">${p.creator || ''}</div>
      <div class="gallery-card-row">
        <span class="gallery-card-score">${p.score}</span>
        <span class="gallery-card-stat">${fmt(p.pageviews_12mo)} views</span>
        ${link}
      </div>
    </div>
  </div>`;
}

function showClusterPopup(latlng, paintings) {
  const groups = {};
  paintings.forEach(p => {
    const key = p.collection || p.location_label || 'Unknown location';
    (groups[key] = groups[key] || []).push(p);
  });
  const sorted = Object.entries(groups).sort((a, b) =>
    Math.max(...b[1].map(p => p.score)) - Math.max(...a[1].map(p => p.score))
  );
  const totalCount = paintings.length;
  const groupCount = sorted.length;
  const headerText = groupCount === 1
    ? `${sorted[0][0]} — ${totalCount} work${totalCount > 1 ? 's' : ''}`
    : `${groupCount} venues — ${totalCount} works`;
  const content = sorted.map(([name, works]) => {
    const groupHeader = groupCount > 1
      ? `<div class="gallery-group-header">${name} <span class="gallery-group-count">${works.length}</span></div>`
      : '';
    return groupHeader + works.slice().sort((a, b) => b.score - a.score).map(galleryCard).join('');
  }).join('');
  L.popup({ className: 'gallery-popup', maxWidth: 300 })
    .setLatLng(latlng)
    .setContent(`<div class="gallery-header">${headerText}</div><div class="gallery-list">${content}</div>`)
    .openOn(map);
}

function makeClusterGroup() {
  const group = L.markerClusterGroup({
    maxClusterRadius: 50,
    spiderfyOnMaxZoom: false,
    showCoverageOnHover: false,
    zoomToBoundsOnClick: false,
    iconCreateFunction(cluster) {
      const count = cluster.getChildCount();
      const size = count < 5 ? 34 : count < 15 ? 44 : count < 40 ? 56 : 68;
      const cls  = count < 5 ? 'small' : count < 15 ? 'medium' : 'large';
      return L.divIcon({
        html: `<div class="art-cluster ${cls}" style="width:${size}px;height:${size}px">${count}</div>`,
        className: '', iconSize: [size, size], iconAnchor: [size/2, size/2],
      });
    },
  });
  group.on('clusterclick', function(e) {
    const paintings = e.layer.getAllChildMarkers().map(m => m._paintingData).filter(Boolean);
    showClusterPopup(e.layer.getLatLng(), paintings);
  });
  return group;
}

function fmt(n) {
  if (n >= 1000000) return (n/1000000).toFixed(1) + 'M';
  if (n >= 1000) return Math.round(n/1000) + 'k';
  return n.toString();
}

function buildMarker(p) {
  const sz = Math.round(7 + (p.score / 100) * 13);
  const icon = L.divIcon({
    html: `<div class="art-dot" style="width:${sz}px;height:${sz}px;"></div>`,
    className: '', iconSize: [sz, sz], iconAnchor: [sz/2, sz/2],
  });
  const marker = L.marker([p.lat, p.lon], { icon });
  marker._paintingData = p;
  const imgHtml  = p.image    ? `<img class="popup-img" src="${thumbUrl(p.image, 280)}" alt="${p.label}">` : '';
  const wikiLink = p.en_article ? `<a class="popup-link" href="https://en.wikipedia.org/wiki/${encodeURIComponent(p.en_article)}" target="_blank">Wikipedia →</a>` : '';
  const loc = p.collection || p.location_label || '';
  marker.bindPopup(`<div>${imgHtml}<div class="popup-inner">
    <div class="popup-title">${p.label}</div>
    <div class="popup-meta">${p.creator || ''}</div>
    <div class="popup-location">${loc}</div>
    <div class="popup-score-row">
      <span class="score-badge">${p.score}</span>
      <span class="stat">Views: <span>${fmt(p.pageviews_12mo)}</span></span>
      <span class="stat">Langs: <span>${p.sitelinks}</span></span>
    </div>${wikiLink}</div></div>`, { maxWidth: 300 });
  return marker;
}

// Rescale scores: lowest = 0, highest = 100
(function() {
  const lo = PAINTINGS.reduce((a, p) => Math.min(a, p.score), Infinity);
  const hi = PAINTINGS.reduce((a, p) => Math.max(a, p.score), -Infinity);
  const range = hi - lo;
  PAINTINGS.forEach(p => { p.score = Math.round((p.score - lo) / range * 1000) / 10; });
})();

// Build all markers once (after rescaling)
(function() {
  const mapped = PAINTINGS.filter(p => p.lat != null && p.lon != null);
  allMarkers = mapped.map(p => ({ data: p, marker: buildMarker(p) }));
  setTimeout(() => preloadThumbnails(PAINTINGS), 2000);
})();

// ── Century filter (map tab) ───────────────────────────────────────────────────
const activeCenturies = new Set(CENTURY_BINS.map(b => b.label));

(function() {
  const bar = document.getElementById('century-bar');
  CENTURY_BINS.forEach(bin => {
    const btn = document.createElement('button');
    btn.className = 'century-btn active';
    btn.textContent = bin.label;
    btn.addEventListener('click', () => {
      if (activeCenturies.has(bin.label)) {
        if (activeCenturies.size > 1) {
          activeCenturies.delete(bin.label);
          btn.classList.remove('active');
        }
      } else {
        activeCenturies.add(bin.label);
        btn.classList.add('active');
      }
      applyFilter();
    });
    bar.appendChild(btn);
  });
})();

function applyFilter() {
  if (markerLayer) map.removeLayer(markerLayer);
  markerLayer = makeClusterGroup();
  const visible = allMarkers.filter(m => {
    const p = m.data;
    if (p.year != null) {
      if (!CENTURY_BINS.some(b => activeCenturies.has(b.label) && b.fn(p.year))) return false;
    }
    return true;
  });
  visible.forEach(m => markerLayer.addLayer(m.marker));
  map.addLayer(markerLayer);
}

applyFilter();

// ── Tab switching ─────────────────────────────────────────────────────────────
let prBuilt = false, tlBuilt = false;

document.querySelectorAll('.tab-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    const tab = btn.dataset.tab;
    document.getElementById('panel-map').classList.toggle('active',      tab === 'map');
    document.getElementById('panel-period').classList.toggle('active',   tab === 'period');
    document.getElementById('panel-timeline').classList.toggle('active', tab === 'timeline');
    if (tab === 'period'   && !prBuilt) buildPeriodTab();
    if (tab === 'timeline' && !tlBuilt) buildTimelineTab();
    if (tab === 'map') map.invalidateSize();
  });
});

// ── Shared geo legend builder ─────────────────────────────────────────────────
function buildGeoLegend(container) {
  ROW_DEFS.forEach(rd => {
    const item = document.createElement('div');
    item.className = 'geo-leg-item';
    const dot  = `<div class="geo-leg-dot" style="background:${rd.color}"></div>`;
    const flag = rd.flag
      ? `<img class="geo-leg-flag" src="https://hatscripts.github.io/circle-flags/flags/${rd.flag}.svg" alt="${rd.label}">`
      : '';
    item.innerHTML = `${dot}${flag}<span>${rd.label}</span>`;
    container.appendChild(item);
  });
}

// ── Bar segment tooltip ───────────────────────────────────────────────────────
const barTooltip = document.getElementById('bar-tooltip');

function attachSegTooltip(seg, label, count, total) {
  const pct = total > 0 ? Math.round(count / total * 100) : 0;
  seg.addEventListener('mouseenter', e => {
    barTooltip.textContent = `${label}: ${count} (${pct}%)`;
    barTooltip.style.display = 'block';
    barTooltip.style.left = (e.clientX + 14) + 'px';
    barTooltip.style.top  = (e.clientY - 32) + 'px';
  });
  seg.addEventListener('mousemove', e => {
    barTooltip.style.left = (e.clientX + 14) + 'px';
    barTooltip.style.top  = (e.clientY - 32) + 'px';
  });
  seg.addEventListener('mouseleave', () => { barTooltip.style.display = 'none'; });
}

// ── By Period tab ─────────────────────────────────────────────────────────────
function buildPeriodTab() {
  prBuilt = true;
  const withYear = PAINTINGS.filter(p => p.year != null);
  const grid = document.getElementById('period-grid');

  const allCells = CENTURY_BINS.map(cb =>
    withYear.filter(p => cb.fn(p.year)).sort((a, b) => b.score - a.score)
  );
  const maxTotal  = Math.max(...allCells.map(c => c.length));
  const MAX_BAR_PX = 260;

  CENTURY_BINS.forEach((cb, idx) => {
    const cell  = allCells[idx];
    const total = cell.length;
    const top5  = cell.slice(0, 5);
    const barPx = maxTotal > 0 ? Math.round((total / maxTotal) * MAX_BAR_PX) : 0;

    const segs = ROW_DEFS.map(rd => ({
      rd,
      count: cell.filter(p => rd.match(p)).length,
    })).filter(s => s.count > 0);

    const col = document.createElement('div');
    col.className = 'period-col';
    col.innerHTML = `<div class="period-heading">${cb.label}</div>`;

    const barArea = document.createElement('div');
    barArea.className = 'period-bar-area';

    const bar = document.createElement('div');
    bar.className = 'period-bar';
    bar.style.height = barPx + 'px';

    segs.forEach(({ rd, count }) => {
      const seg = document.createElement('div');
      seg.className = 'period-bar-seg';
      const pct = total > 0 ? (count / total * 100).toFixed(2) : 0;
      seg.style.cssText = `height:${pct}%;background:${rd.color};`;
      attachSegTooltip(seg, rd.label, count, total);
      bar.appendChild(seg);
    });

    barArea.appendChild(bar);
    col.appendChild(barArea);

    const countEl = document.createElement('div');
    countEl.className = 'period-count';
    countEl.textContent = `${total} painting${total !== 1 ? 's' : ''}`;
    col.appendChild(countEl);

    const cardsWrap = document.createElement('div');
    cardsWrap.className = 'period-top5';
    top5.forEach(p => {
      const imgUrl = thumbUrl(p.image, 190);
      const href = p.en_article ? `https://en.wikipedia.org/wiki/${encodeURIComponent(p.en_article)}` : null;
      const card = document.createElement(href ? 'a' : 'div');
      card.className = 'period-card';
      if (href) { card.href = href; card.target = '_blank'; }
      const loc = p.collection || p.location_label || '';
      card.innerHTML =
        (imgUrl ? `<img class="period-card-img" src="${imgUrl}" alt="" loading="lazy">` : `<div class="period-card-ph"></div>`) +
        `<div class="period-card-body">
          <div class="period-card-score">${p.score}</div>
          <div class="period-card-title"  title="${p.label}">${p.label}</div>
          <div class="period-card-artist" title="${p.creator || ''}">${p.creator || ''}</div>
          <div class="period-card-loc"    title="${loc}">${loc}</div>
        </div>`;
      cardsWrap.appendChild(card);
    });
    col.appendChild(cardsWrap);
    grid.appendChild(col);
  });

  buildGeoLegend(document.getElementById('period-geo-legend'));
}

// ── Timeline tab ──────────────────────────────────────────────────────────────
function buildTimelineTab() {
  tlBuilt = true;

  const BIN_SIZE = 10, BIN_START = 1500;
  const allYear   = PAINTINGS.filter(p => p.year != null);
  const pre1500   = allYear.filter(p => p.year < BIN_START).sort((a, b) => b.score - a.score);
  const withYear  = allYear.filter(p => p.year >= BIN_START);
  const maxYear   = withYear.reduce((a, p) => Math.max(a, p.year), BIN_START + BIN_SIZE);
  const numDecade = Math.ceil((maxYear + 1 - BIN_START) / BIN_SIZE);
  // bin index 0 = pre-1500 (special); indices 1…numDecade+1 = decade bins
  const numBins   = 1 + numDecade;
  const GAP_PX    = 14; // extra horizontal gap between pre-1500 col and first decade col

  // Bin arrays sorted by score descending; index 0 is pre-1500
  const bins = [pre1500, ...Array.from({ length: numDecade }, (_, i) => {
    const y0 = BIN_START + i * BIN_SIZE;
    return withYear
      .filter(p => p.year >= y0 && p.year < y0 + BIN_SIZE)
      .sort((a, b) => b.score - a.score);
  })];

  // Top 10 paintings across all years
  const top10 = allYear.slice().sort((a, b) => b.score - a.score).slice(0, 10);

  const canvas  = document.getElementById('tl-canvas');
  const scroll  = document.getElementById('tl-scroll');
  const spacer  = document.getElementById('tl-spacer');
  const cardsEl = document.getElementById('tl-cards');

  // Layout constants
  const BIN_PX  = 22;
  const PAD_L   = 20, PAD_R = 24, PAD_T = 14;
  const AXIS_H  = 36;   // space below axis line for tick labels
  const BUBBLE_H = 220; // height for bubbles above axis
  const axisY   = PAD_T + BUBBLE_H;
  const CHART_H = axisY + AXIS_H;
  const MAX_R   = 9, MIN_R = 2;

  const W_CARD  = 158;  // callout card width
  const H_CARD  = 155;  // approximate card height (img 80 + body ~75)
  const LEAD_H  = 28;   // vertical gap: axis bottom to first card row
  const ROW_GAP = 10;   // gap between card rows

  // cx of bin i accounting for extra gap after bin 0
  function binCx(i, padL, binPx) {
    if (i === 0) return padL + binPx * 0.5;
    return padL + binPx * 0.5 + GAP_PX + i * binPx;
  }

  // Assign each top-10 card to a row (greedy left-to-right, no horizontal overlap)
  const cardItems = top10.map(p => {
    let binIdx;
    if (p.year < BIN_START) {
      binIdx = 0;
    } else {
      binIdx = 1 + Math.min(numDecade - 1, Math.max(0, Math.floor((p.year - BIN_START) / BIN_SIZE)));
    }
    return { p, binIdx };
  }).sort((a, b) => a.binIdx - b.binIdx);

  const rowSlots = []; // rowSlots[row] = array of occupied cx ranges
  const laid = cardItems.map(item => {
    let rowIdx = 0;
    while (true) {
      if (!rowSlots[rowIdx]) rowSlots[rowIdx] = [];
      // cx is tentative; we'll clamp later once we know canvasW
      const occupied = rowSlots[rowIdx].some(slot => slot === item.binIdx);
      // Use bin index spacing to check for conflicts (cards within 7 bins of each other conflict)
      const conflicts = rowSlots[rowIdx].some(slot => Math.abs(slot - item.binIdx) * BIN_PX < W_CARD + 4);
      if (!conflicts) {
        rowSlots[rowIdx].push(item.binIdx);
        return { ...item, rowIdx };
      }
      rowIdx++;
    }
  });

  const maxRow  = laid.reduce((m, c) => Math.max(m, c.rowIdx), 0);
  const TOTAL_H = CHART_H + LEAD_H + (maxRow + 1) * (H_CARD + ROW_GAP) + 16;

  function render(viewW) {
    const canvasW = Math.max(viewW, PAD_L + GAP_PX + numBins * BIN_PX + PAD_R);

    // Set spacer to define scroll area
    spacer.style.width  = canvasW + 'px';
    spacer.style.height = TOTAL_H + 'px';

    canvas.width  = canvasW;
    canvas.height = TOTAL_H;

    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvasW, TOTAL_H);

    // ── Axis line ──
    ctx.strokeStyle = '#444'; ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(PAD_L, axisY);
    ctx.lineTo(canvasW - PAD_R, axisY);
    ctx.stroke();

    // ── Vertical separator between pre-1500 and decade bins ──
    const sepX = PAD_L + BIN_PX + GAP_PX / 2;
    ctx.strokeStyle = '#555'; ctx.lineWidth = 1;
    ctx.setLineDash([3, 3]);
    ctx.beginPath();
    ctx.moveTo(sepX, PAD_T);
    ctx.lineTo(sepX, axisY);
    ctx.stroke();
    ctx.setLineDash([]);

    // ── Tick marks and labels ──
    ctx.font = '9px Georgia,serif'; ctx.textAlign = 'center'; ctx.textBaseline = 'top';
    for (let i = 0; i < numBins; i++) {
      const cx = binCx(i, PAD_L, BIN_PX);
      ctx.strokeStyle = '#333'; ctx.lineWidth = 1;
      ctx.beginPath(); ctx.moveTo(cx, axisY); ctx.lineTo(cx, axisY + 4); ctx.stroke();
      ctx.fillStyle = '#666';
      if (i === 0) {
        ctx.fillText('< 1500', cx, axisY + 8);
      } else {
        // decade bins: label every other one (every 20 years)
        const di = i - 1; // decade index
        if (di % 2 === 0) {
          ctx.fillText(String(BIN_START + di * BIN_SIZE), cx, axisY + 8);
        }
      }
    }

    // ── Bubbles ──
    bins.forEach((cell, i) => {
      const cx      = binCx(i, PAD_L, BIN_PX);
      let   bottomY = axisY - 1;
      for (const p of cell) {
        const r  = Math.max(MIN_R, (p.score / 100) * MAX_R);
        const cy = bottomY - r;
        if (cy - r < PAD_T) break;
        const rd = geoOf(p);
        ctx.beginPath();
        ctx.arc(cx, cy, r, 0, Math.PI * 2);
        ctx.fillStyle = rd.color + 'bb';
        ctx.fill();
        ctx.strokeStyle = rd.color;
        ctx.lineWidth = 0.6;
        ctx.stroke();
        bottomY = cy - r - 1;
      }
    });

    // ── Leader lines and callout cards ──
    cardsEl.innerHTML = '';

    laid.forEach(({ p, binIdx, rowIdx }) => {
      const bCx     = binCx(binIdx, PAD_L, BIN_PX);
      // Clamp card position so it stays within canvas bounds
      const rawLeft = Math.round(bCx - W_CARD / 2);
      const cardLeft = Math.max(0, Math.min(canvasW - W_CARD, rawLeft));
      const cardCx   = cardLeft + W_CARD / 2;
      const cardTop  = CHART_H + LEAD_H + rowIdx * (H_CARD + ROW_GAP);

      // Dashed leader line from axis to card top
      ctx.strokeStyle = '#555';
      ctx.lineWidth = 1;
      ctx.setLineDash([3, 4]);
      ctx.beginPath();
      ctx.moveTo(bCx, axisY + 5);
      // Elbow: go down to midpoint then across to card center
      const midY = CHART_H + LEAD_H / 2;
      ctx.lineTo(bCx, midY);
      ctx.lineTo(cardCx, midY);
      ctx.lineTo(cardCx, cardTop - 2);
      ctx.stroke();
      ctx.setLineDash([]);

      // Dot on axis
      ctx.beginPath();
      ctx.arc(bCx, axisY + 5, 3, 0, Math.PI * 2);
      ctx.fillStyle = '#666';
      ctx.fill();

      // Arrowhead pointing into card top
      ctx.fillStyle = '#555';
      ctx.beginPath();
      ctx.moveTo(cardCx, cardTop + 2);
      ctx.lineTo(cardCx - 4, cardTop - 5);
      ctx.lineTo(cardCx + 4, cardTop - 5);
      ctx.closePath();
      ctx.fill();

      // HTML card
      const imgUrl = thumbUrl(p.image, 190);
      const href = p.en_article
        ? `https://en.wikipedia.org/wiki/${encodeURIComponent(p.en_article)}`
        : null;
      const card = document.createElement(href ? 'a' : 'div');
      card.className = 'period-card tl-card';
      card.style.cssText = `left:${cardLeft}px; top:${cardTop}px; width:${W_CARD}px; z-index:2;`;
      if (href) { card.href = href; card.target = '_blank'; }
      const loc = p.collection || p.location_label || '';
      const rd  = geoOf(p);
      card.innerHTML =
        (imgUrl
          ? `<img class="period-card-img" src="${imgUrl}" alt="" loading="lazy" style="border-top:3px solid ${rd.color}">`
          : `<div class="period-card-ph" style="border-top:3px solid ${rd.color}"></div>`) +
        `<div class="period-card-body">
          <div class="period-card-score">${p.score}</div>
          <div class="period-card-title"  title="${p.label}">${p.label}</div>
          <div class="period-card-artist" title="${p.creator || ''}">${p.creator || ''}</div>
          <div class="period-card-loc"    title="${loc}">${loc}</div>
        </div>`;
      cardsEl.appendChild(card);
    });
  }

  let lastW = 0;
  function draw(entries) {
    let w;
    if (entries && entries[0]) {
      w = Math.round(entries[0].contentRect.width);
    } else {
      w = scroll.clientWidth || scroll.offsetWidth;
    }
    if (!w) return;
    if (w !== lastW) { lastW = w; render(w); }
  }

  requestAnimationFrame(draw);
  setTimeout(draw, 80);  // fallback if rAF fires before layout
  new ResizeObserver(draw).observe(scroll);

  buildGeoLegend(document.getElementById('tl-legend'));
}

// ── Search ────────────────────────────────────────────────────────────────────
let searchPopup  = null;
let searchMarker = null;

const SEARCH_PIN_ICON = L.divIcon({
  html: `<svg width="30" height="42" viewBox="0 0 30 42" xmlns="http://www.w3.org/2000/svg">
    <path d="M15 1 C7.3 1 1 7.3 1 15 C1 26 15 41 15 41 C15 41 29 26 29 15 C29 7.3 22.7 1 15 1 Z"
          fill="#d93025" stroke="white" stroke-width="2"/>
    <circle cx="15" cy="14" r="6" fill="white"/>
  </svg>`,
  className: '',
  iconSize: [30, 42],
  iconAnchor: [15, 41],
});

function selectPainting(p) {
  document.getElementById('search-input').value = '';
  document.getElementById('search-drop').style.display = 'none';

  if (p.lat == null || p.lon == null) return;

  // Switch to map tab if not already there
  if (!document.getElementById('panel-map').classList.contains('active')) {
    document.querySelector('[data-tab="map"]').click();
  }

  // Remove previous search pin and popup
  if (searchMarker) { searchMarker.remove(); searchMarker = null; }
  if (searchPopup)  { searchPopup.remove();  searchPopup  = null; }

  // Drop red pin and centre map (keep current zoom)
  searchMarker = L.marker([p.lat, p.lon], { icon: SEARCH_PIN_ICON, zIndexOffset: 1000 }).addTo(map);
  map.panTo([p.lat, p.lon]);

  // Open popup to the right of the pin
  const imgHtml  = p.image ? `<img class="popup-img" src="${thumbUrl(p.image, 400)}" alt="${p.label}">` : '';
  const wikiLink = p.en_article ? `<a class="popup-link" href="https://en.wikipedia.org/wiki/${encodeURIComponent(p.en_article)}" target="_blank">Wikipedia →</a>` : '';
  const loc = p.collection || p.location_label || '';

  searchPopup = L.popup({ maxWidth: 360, autoClose: false, closeOnClick: false, autoPan: false, className: 'search-popup', offset: L.point(165, 100) })
    .setLatLng([p.lat, p.lon])
    .setContent(`<div>${imgHtml}<div class="popup-inner">
      <div class="popup-title">${p.label}</div>
      <div class="popup-meta">${p.creator || ''}</div>
      <div class="popup-location">${loc}</div>
      <div class="popup-score-row">
        <span class="score-badge">${p.score}</span>
        <span class="stat">Views: <span>${fmt(p.pageviews_12mo)}</span></span>
        <span class="stat">Langs: <span>${p.sitelinks}</span></span>
      </div>${wikiLink}</div></div>`)
    .openOn(map);

  // Remove pin when popup is closed
  searchPopup.on('remove', () => {
    if (searchMarker) { searchMarker.remove(); searchMarker = null; }
    searchPopup = null;
  });
}

(function() {
  const input = document.getElementById('search-input');
  const drop  = document.getElementById('search-drop');
  let results = [], activeIdx = -1;

  function norm(s) { return (s || '').toLowerCase(); }

  function highlight(text, q) {
    const i = norm(text).indexOf(q);
    if (i < 0) return text;
    return text.slice(0, i) + '<mark style="background:rgba(201,168,76,0.35);color:inherit;border-radius:1px">' + text.slice(i, i + q.length) + '</mark>' + text.slice(i + q.length);
  }

  function renderDrop(q) {
    activeIdx = -1;
    if (!results.length) {
      drop.innerHTML = '<div class="search-no-result">No results</div>';
    } else {
      drop.innerHTML = results.map((p, i) => {
        const loc = p.year ? ` · ${p.year}` : '';
        return `<div class="search-item" data-idx="${i}">
          <div class="search-item-title">${highlight(p.label || '', q)}</div>
          <div class="search-item-sub">${highlight(p.creator || '', q)}${loc}</div>
        </div>`;
      }).join('');
      drop.querySelectorAll('.search-item').forEach(el => {
        el.addEventListener('mousedown', e => {
          e.preventDefault();
          selectPainting(results[+el.dataset.idx]);
        });
      });
    }
    drop.style.display = 'block';
  }

  function setActive(idx) {
    const items = drop.querySelectorAll('.search-item');
    items.forEach(el => el.classList.remove('si-active'));
    activeIdx = Math.max(0, Math.min(idx, items.length - 1));
    if (items[activeIdx]) {
      items[activeIdx].classList.add('si-active');
      items[activeIdx].scrollIntoView({ block: 'nearest' });
    }
  }

  input.addEventListener('input', () => {
    const q = norm(input.value.trim());
    if (q.length < 2) { drop.style.display = 'none'; return; }
    results = PAINTINGS
      .filter(p => norm(p.label).includes(q) || norm(p.creator).includes(q))
      .sort((a, b) => b.score - a.score)
      .slice(0, 12);
    renderDrop(q);
  });

  input.addEventListener('keydown', e => {
    if (!drop.style.display || drop.style.display === 'none') return;
    if (e.key === 'ArrowDown') { e.preventDefault(); setActive(activeIdx + 1); }
    else if (e.key === 'ArrowUp') { e.preventDefault(); setActive(activeIdx - 1); }
    else if (e.key === 'Enter') {
      const pick = activeIdx >= 0 ? results[activeIdx] : results[0];
      if (pick) selectPainting(pick);
      input.value = ''; drop.style.display = 'none';
    }
    else if (e.key === 'Escape') { drop.style.display = 'none'; input.blur(); }
  });

  document.addEventListener('click', e => {
    if (!e.target.closest('#search-wrap')) drop.style.display = 'none';
  });
})();
"""

# Assemble
new_content = PRE + paintings_line + POST_JS + tail
open('index.html', 'w', encoding='utf-8').write(new_content)
print(f'Done. New file size: {len(new_content):,} bytes')
print(f'Lines: {new_content.count(chr(10))}')
