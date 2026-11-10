const http=require('http'),fs=require('fs'),path=require('path');
const root=path.resolve(__dirname);
http.createServer((req,res)=>{let relative;try{relative=decodeURIComponent(new URL(req.url,'http://localhost').pathname)}catch{res.writeHead(400);res.end();return}const file=path.resolve(root,'.'+relative+(relative.endsWith('/')?'index.html':''));if(!file.startsWith(root+path.sep)){res.writeHead(403);res.end();return}fs.readFile(file,(err,data)=>{if(err){res.writeHead(404);res.end('Not found');return}res.writeHead(200,{'Content-Type':({'.html':'text/html; charset=utf-8','.css':'text/css; charset=utf-8','.js':'application/javascript; charset=utf-8','.png':'image/png'})[path.extname(file)]||'text/plain','Cache-Control':'no-store'});res.end(data)})}).listen(8766,'127.0.0.1',()=>console.log('http://127.0.0.1:8766/'));


