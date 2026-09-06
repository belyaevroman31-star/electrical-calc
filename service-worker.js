const CACHE_NAME='electrik-v2';
const BASE=self.location.pathname.replace(/\/[^/]*$/,'/');
const ASSETS=[BASE,BASE+'calculator-house.html',BASE+'manifest.json',BASE+'icons/icon-192x192.svg',BASE+'icons/icon-512x512.svg'];

self.addEventListener('install',e=>{e.waitUntil(caches.open(CACHE_NAME).then(c=>c.addAll(ASSETS)));self.skipWaiting()});
self.addEventListener('activate',e=>{e.waitUntil(caches.keys().then(k=>Promise.all(k.filter(n=>n!==CACHE_NAME).map(n=>caches.delete(n)))));self.clients.claim()});
self.addEventListener('fetch',e=>{e.respondWith(caches.match(e.request).then(r=>r||fetch(e.request).then(res=>{if(res&&res.status===200){const clone=res.clone();caches.open(CACHE_NAME).then(c=>c.put(e.request,clone))}return res}).catch(()=>caches.match(BASE+'calculator-house.html')))});
