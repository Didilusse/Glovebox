import http from 'node:http'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const root = path.join(path.dirname(fileURLToPath(import.meta.url)), 'dist')
const backendHost = process.env.BACKEND_HOST || 'backend'
const backendPort = Number(process.env.BACKEND_PORT || 8000)
const port = Number(process.env.PORT || 8080)
const maxBodyBytes = 11 * 1024 * 1024

const contentTypes = {
  '.css': 'text/css; charset=utf-8',
  '.gif': 'image/gif',
  '.html': 'text/html; charset=utf-8',
  '.ico': 'image/x-icon',
  '.jpg': 'image/jpeg',
  '.js': 'text/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.png': 'image/png',
  '.svg': 'image/svg+xml',
  '.webp': 'image/webp',
  '.woff': 'font/woff',
  '.woff2': 'font/woff2'
}

function securityHeaders() {
  return {
    'Cache-Control': 'no-store',
    'Content-Security-Policy': "default-src 'self'; base-uri 'none'; object-src 'none'; script-src 'self'; style-src 'self'; img-src 'self' data:; font-src 'self'; connect-src 'self'; frame-src 'none'; frame-ancestors 'none'; form-action 'self'; manifest-src 'self'",
    'Cross-Origin-Opener-Policy': 'same-origin',
    'Cross-Origin-Resource-Policy': 'same-origin',
    'Permissions-Policy': 'accelerometer=(), camera=(), geolocation=(), gyroscope=(), magnetometer=(), microphone=(), payment=(), usb=()',
    'Referrer-Policy': 'same-origin',
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'DENY'
  }
}

function respond(response, status, body, headers = {}) {
  response.writeHead(status, { ...securityHeaders(), ...headers })
  response.end(body)
}

function proxyApi(request, response, url) {
  const forwardedFor = request.socket.remoteAddress || 'unknown'
  const headers = { ...request.headers }
  delete headers.connection
  headers.host = `${backendHost}:${backendPort}`
  headers['x-real-ip'] = forwardedFor
  headers['x-forwarded-for'] = forwardedFor
  headers['x-forwarded-host'] = request.headers.host || ''
  headers['x-forwarded-port'] = String(port)
  headers['x-forwarded-proto'] = 'http'
  delete headers.forwarded

  const upstream = http.request({
    hostname: backendHost,
    port: backendPort,
    method: request.method,
    path: `${url.pathname.replace(/^\/api/, '') || '/'}${url.search}`,
    headers
  }, upstreamResponse => {
    response.writeHead(upstreamResponse.statusCode || 502, {
      ...securityHeaders(),
      ...upstreamResponse.headers
    })
    upstreamResponse.pipe(response)
  })

  upstream.on('error', () => {
    if (!response.headersSent) respond(response, 502, 'Bad gateway\n', { 'Content-Type': 'text/plain; charset=utf-8' })
    else response.destroy()
  })

  let received = 0
  request.on('data', chunk => {
    received += chunk.length
    if (received > maxBodyBytes) {
      upstream.destroy()
      request.destroy()
      if (!response.headersSent) respond(response, 413, 'Request body too large\n', { 'Content-Type': 'text/plain; charset=utf-8' })
    }
  })
  request.on('aborted', () => upstream.destroy())
  request.pipe(upstream)
}

function safePath(urlPath) {
  let decoded
  try {
    decoded = decodeURIComponent(urlPath)
  } catch {
    return null
  }
  const candidate = path.resolve(root, `.${decoded}`)
  return candidate.startsWith(`${root}${path.sep}`) ? candidate : null
}

async function serveStatic(request, response, url) {
  if (!['GET', 'HEAD'].includes(request.method)) {
    respond(response, 405, 'Method not allowed\n', { Allow: 'GET, HEAD', 'Content-Type': 'text/plain; charset=utf-8' })
    return
  }
  if (url.pathname === '/healthz') {
    respond(response, 200, 'ok\n', { 'Content-Type': 'text/plain; charset=utf-8' })
    return
  }

  const requestedPath = safePath(url.pathname)
  if (!requestedPath) {
    respond(response, 400, 'Bad request\n', { 'Content-Type': 'text/plain; charset=utf-8' })
    return
  }

  let filePath = requestedPath
  try {
    if (!(await fs.promises.stat(filePath)).isFile()) throw new Error('not a file')
  } catch {
    filePath = path.join(root, 'index.html')
  }

  try {
    const file = await fs.promises.readFile(filePath)
    const headers = {
      'Content-Length': file.length,
      'Content-Type': contentTypes[path.extname(filePath).toLowerCase()] || 'application/octet-stream'
    }
    response.writeHead(200, { ...securityHeaders(), ...headers })
    if (request.method !== 'HEAD') response.end(file)
    else response.end()
  } catch {
    respond(response, 500, 'Unable to serve frontend\n', { 'Content-Type': 'text/plain; charset=utf-8' })
  }
}

const server = http.createServer((request, response) => {
  let url
  try {
    url = new URL(request.url || '/', `http://${request.headers.host || 'localhost'}`)
  } catch {
    respond(response, 400, 'Bad request\n', { 'Content-Type': 'text/plain; charset=utf-8' })
    return
  }

  const declaredLength = Number(request.headers['content-length'] || 0)
  if (declaredLength > maxBodyBytes) {
    respond(response, 413, 'Request body too large\n', { 'Content-Type': 'text/plain; charset=utf-8' })
    request.resume()
    return
  }
  if (url.pathname === '/api' || url.pathname.startsWith('/api/')) proxyApi(request, response, url)
  else serveStatic(request, response, url)
})

server.listen(port, '0.0.0.0', () => {
  console.log(`Frontend listening on HTTP port ${port}`)
})

function shutdown() {
  server.close(() => process.exit(0))
}
process.on('SIGTERM', shutdown)
process.on('SIGINT', shutdown)
