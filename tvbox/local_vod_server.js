const http = require('http');
const fs = require('fs');
const path = require('path');

const movies = [
  {vod_id:'sintel',vod_name:'Sintel',vod_pic:'https://upload.wikimedia.org/wikipedia/commons/thumb/8/8f/Sintel_poster.jpg/480px-Sintel_poster.jpg',vod_remarks:'开源电影',vod_content:'Blender 基金会发布的开放电影。',vod_play_from:'公开线路',vod_play_url:'正片$https://media.w3.org/2010/05/sintel/trailer.mp4'},
  {vod_id:'bunny',vod_name:'Big Buck Bunny',vod_pic:'https://upload.wikimedia.org/wikipedia/commons/thumb/c/c5/Big_buck_bunny_poster_big.jpg/480px-Big_buck_bunny_poster_big.jpg',vod_remarks:'开源电影',vod_content:'Blender 基金会发布的开放动画电影。',vod_play_from:'公开线路',vod_play_url:'正片$https://media.w3.org/2010/05/bunny/trailer.mp4'},
  {vod_id:'flower',vod_name:'Flower',vod_pic:'https://peach.blender.org/wp-content/uploads/title_anouncement.jpg',vod_remarks:'公开测试',vod_content:'用于验证 TVBox 点播播放链路。',vod_play_from:'公开线路',vod_play_url:'正片$https://interactive-examples.mdn.mozilla.net/media/cc0-videos/flower.mp4'}
];

http.createServer((req, res) => {
  const url = new URL(req.url, 'http://localhost');
  if (url.pathname === '/local-config.json') {
    const body = fs.readFileSync(path.join(__dirname, 'local-config.json'));
    res.writeHead(200, {'Content-Type':'application/json; charset=utf-8'}).end(body);
    return;
  }
  if (url.pathname === '/live.txt') {
    res.writeHead(200, {'Content-Type':'text/plain; charset=utf-8'}).end('公开测试,#genre#\nSintel,https://media.w3.org/2010/05/sintel/trailer.mp4\n');
    return;
  }
  const ids = (url.searchParams.get('ids') || '').split(',').filter(Boolean);
  const list = ids.length ? movies.filter(movie => ids.includes(movie.vod_id)) : movies;
  const payload = ids.length ? {code:1,list} : {code:1,page:1,pagecount:1,limit:20,total:movies.length,class:[{type_id:'movie',type_name:'开源电影'}],list};
  const body = Buffer.from(JSON.stringify(payload));
  res.writeHead(200, {'Content-Type':'application/json; charset=utf-8','Content-Length':body.length}).end(body);
}).listen(18080, '0.0.0.0');
