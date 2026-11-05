'use strict';
document.querySelectorAll('form[method="post"]').forEach(form=>form.addEventListener('submit',()=>{if(form.checkValidity())form.querySelectorAll('button[type="submit"],button:not([type])').forEach(b=>{b.disabled=true;b.textContent='Working…';});}));
if(window.L){
 const list=document.getElementById('issue-map');
 if(list){const map=L.map(list).setView([37.7749,-122.4194],12);L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{attribution:'© OpenStreetMap contributors',maxZoom:19}).addTo(map);const points=JSON.parse(list.dataset.points);for(const i of points){const link=document.createElement('a');link.href='/issues/'+encodeURIComponent(i.issue_id);link.textContent=i.summary+' · '+i.report_count+' reports';L.marker([i.location.lat,i.location.lon]).addTo(map).bindPopup(link);} }
 const picker=document.getElementById('location-map');
 if(picker){const map=L.map(picker).setView([37.7749,-122.4194],13);L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{attribution:'© OpenStreetMap contributors',maxZoom:19}).addTo(map);let pin;map.on('click',e=>{document.getElementById('lat').value=e.latlng.lat.toFixed(6);document.getElementById('lon').value=e.latlng.lng.toFixed(6);if(pin)pin.remove();pin=L.marker(e.latlng).addTo(map);});}
}
