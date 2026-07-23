// 更新静态资源后需要修改 CACHE_NAME 版本号，强制用户刷新缓存
// 当前版本：v2，最后更新：2026-06-29
const CACHE_NAME = 'alz-v2';
const STATIC_ASSETS = [
  '/static/style.css', '/static/script.js', '/static/voice.js',
  '/static/manifest.json',
  '/static/icon-192.png', '/static/icon-512.png',
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(STATIC_ASSETS))
  );
  self.skipWaiting();
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys => Promise.all(
      keys.filter(key => key !== CACHE_NAME).map(key => caches.delete(key))
    ))
  );
  self.clients.claim();
});

self.addEventListener('fetch', event => {
  if (event.request.method !== 'GET') {
    return;
  }

  if (event.request.mode === 'navigate' || event.request.url.includes('/api/')) {
    // 页面导航和 API 请求不缓存，直接走网络，避免旧缓存导致页面打不开或状态错乱
    return;
  }

  if (!event.request.url.includes('/static/')) {
    return;
  }

  event.respondWith(
    caches.match(event.request).then(cached => cached || fetch(event.request))
  );
});
