const http = require('http');
const fs = require('fs');
const path = require('path');
const handleAnalytics = require('./api/analytics');
const ROOT = __dirname;
const PUBLIC = path.join(ROOT,'public');
const MIME = {'.html':'text/html; charset=utf-8','.css':'text/css; charset=utf-8','.js':'application/javascript; charset=utf-8','.json':'application/json; charset=utf-8','.svg':'image/svg+xml','.png':'image/png','.pdf':'application/pdf','.md':'text/markdown; charset=utf-8'};
const server = http.createServer((req,res)=>{
  const pathname = new URL(req.url, 'http://localhost').pathname;
  if (pathname.startsWith('/api/')) return handleAnalytics(req,res);
  let requested = pathname === '/' ? '/index.html' : decodeURIComponent(pathname);
  const file = path.resolve(PUBLIC, '.' + requested);
  if (!file.startsWith(PUBLIC + path.sep) && file !== path.join(PUBLIC,'index.html')) { res.statusCode=403; res.end('Forbidden'); return; }
  fs.readFile(file,(err,data)=>{
    if (err) { res.statusCode=404; res.end('Not found'); return; }
    res.statusCode=200; res.setHeader('Content-Type',MIME[path.extname(file)]||'application/octet-stream');
    if (path.extname(file)==='.json') res.setHeader('Cache-Control','public, max-age=300');
    res.end(data);
  });
});
const port = Number(process.env.PORT || 3000);
server.listen(port,()=>console.log(`SupeRR Pressure Lab running at http://localhost:${port}`));
