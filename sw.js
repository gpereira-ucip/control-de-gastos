/* Sin caché a propósito: siempre se ve la última versión publicada. Solo permite instalar la app. */
self.addEventListener('install',()=>self.skipWaiting());
self.addEventListener('activate',e=>e.waitUntil(self.clients.claim()));
self.addEventListener('fetch',()=>{});
/* v2.4: tocar una notificación de vencimientos abre (o trae al frente) la app. */
self.addEventListener('notificationclick',e=>{
  e.notification.close();
  e.waitUntil(self.clients.matchAll({type:'window',includeUncontrolled:true}).then(l=>{
    for(const c of l){ if('focus' in c) return c.focus(); }
    return self.clients.openWindow ? self.clients.openWindow((e.notification.data&&e.notification.data.url)||'./') : null;
  }));
});
