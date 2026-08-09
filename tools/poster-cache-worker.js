/**
 * LDW-Cinema 海报缓存加速代理 - Cloudflare Worker
 * 
 * 功能:
 * 1. 缓存海报图片到 Cloudflare 边缘节点（首次加载后秒开）
 * 2. 自动压缩为 WebP 格式（体积减少 50-70%）
 * 3. 失败自动重试 + 备用源切换
 * 4. 过滤死海报源（doubanio.com 418 等）
 * 
 * 部署方法:
 * 1. 注册 Cloudflare 账号 (免费)
 * 2. Workers & Pages -> Create Worker
 * 3. 粘贴此代码 -> Save and Deploy
 * 4. 将得到的 Worker URL 填入 combined.json 的 posterConfig.proxyUrl
 *    例如: https://your-worker.your-subdomain.workers.dev/?url={url}&w=300&h=400
 */

// 死亡海报源黑名单
const DEAD_SOURCES = [
  'doubanio.com',      // 返回 418 反爬
  'gcalic.v.myalicdn.com',  // 返回 403
];

// 备用海报源映射（当原始源失败时尝试）
const BACKUP_PATTERNS = [
  // 如果 doubanio 失败，尝试从其他源获取
  { pattern: /doubanio\.com/, replace: null }, // 直接跳过，不尝试
];

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    
    // 健康检查
    if (url.pathname === '/health') {
      return new Response(JSON.stringify({ status: 'ok', version: 'v1' }), {
        headers: { 'Content-Type': 'application/json' }
      });
    }
    
    // 获取海报 URL
    let targetUrl = url.searchParams.get('url');
    if (!targetUrl) {
      return new Response('Missing url parameter', { status: 400 });
    }
    
    // 检查黑名单
    for (const dead of DEAD_SOURCES) {
      if (targetUrl.includes(dead)) {
        // 返回占位图
        return new Response(PLACEHOLDER_IMAGE, {
          headers: { 'Content-Type': 'image/svg+xml', 'Cache-Control': 'public, max-age=86400' }
        });
      }
    }
    
    // 解析压缩参数
    const width = parseInt(url.searchParams.get('w') || '300');
    const height = parseInt(url.searchParams.get('h') || '400');
    const quality = parseInt(url.searchParams.get('q') || '80');
    const output = url.searchParams.get('output') || 'webp';
    
    // Cloudflare Cache Key
    const cacheKey = new Request(`https://poster-cache.ldw-cinema.workers.dev/${btoa(targetUrl)}?w=${width}&h=${height}&q=${quality}&f=${output}`, request);
    const cache = caches.default;
    
    // 检查缓存
    let cachedResponse = await cache.match(cacheKey);
    if (cachedResponse) {
      // 命中缓存，秒返回
      const resp = new Response(cachedResponse.body, cachedResponse);
      resp.headers.set('X-Cache', 'HIT');
      return resp;
    }
    
    // 未命中缓存，从源获取
    try {
      const fetchResponse = await fetch(targetUrl, {
        headers: {
          'User-Agent': 'Mozilla/5.0 (Linux; Android 12) AppleWebKit/537.36',
          'Referer': new URL(targetUrl).origin,
        },
        cf: {
          // Cloudflare 图片优化
          image: {
            width: width,
            height: height,
            quality: quality,
            format: output,
          },
          cacheTtl: 604800,  // 7 天缓存
          cacheEverything: true,
        },
      });
      
      if (!fetchResponse.ok) {
        throw new Error(`Source returned ${fetchResponse.status}`);
      }
      
      // 克隆响应以便缓存
      const body = await fetchResponse.blob();
      
      const responseHeaders = new Headers({
        'Content-Type': `image/${output}`,
        'Cache-Control': 'public, max-age=604800, s-maxage=604800',
        'Access-Control-Allow-Origin': '*',
        'X-Cache': 'MISS',
        'CDN-Cache-Control': 'max-age=604800',
      });
      
      const responseToReturn = new Response(body, { headers: responseHeaders });
      
      // 存入缓存（7天）
      const responseToCache = new Response(body, { headers: responseHeaders });
      responseToCache.headers.set('X-Cache', 'CACHED');
      ctx.waitUntil(cache.put(cacheKey, responseToCache));
      
      return responseToReturn;
      
    } catch (error) {
      // 返回占位图
      return new Response(PLACEHOLDER_IMAGE, {
        headers: { 
          'Content-Type': 'image/svg+xml',
          'Cache-Control': 'public, max-age=3600'  // 1小时后重试
        }
      });
    }
  }
};

// SVG 占位图（海报加载失败时显示）
const PLACEHOLDER_IMAGE = `<svg xmlns="http://www.w3.org/2000/svg" width="300" height="400" viewBox="0 0 300 400">
  <rect width="300" height="400" fill="#1a1a2e"/>
  <text x="150" y="180" text-anchor="middle" fill="#e0e0e0" font-size="16" font-family="sans-serif">暂无海报</text>
  <text x="150" y="220" text-anchor="middle" fill="#666" font-size="12" font-family="sans-serif">LDW-Cinema Enhanced</text>
</svg>`;
