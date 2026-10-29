export const dynamic = 'force-dynamic';
export const runtime = 'nodejs';

const BASE = process.env.EAT_API_URL || 'http://localhost:7777';

async function proxy(req, { params }) {
  const { path = [] } = await params;
  const url = new URL(req.url);
  const target = `${BASE.replace(/\/$/, '')}/ui/${path.map(encodeURIComponent).join('/')}${url.search}`;

  const headers = { accept: req.headers.get('accept') || '*/*' };
  const ct = req.headers.get('content-type');
  if (ct) headers['content-type'] = ct;
  if (process.env.OS_SECURITY_KEY) headers.authorization = `Bearer ${process.env.OS_SECURITY_KEY}`;

  let upstream;
  try {
    upstream = await fetch(target, {
      method: req.method,
      headers,
      body: req.method === 'GET' ? undefined : await req.text(),
      cache: 'no-store',
      signal: req.signal,
    });
  } catch (e) {
    return Response.json({ detail: `backend unreachable at ${BASE}: ${e.message}` }, { status: 502 });
  }

  const out = new Headers();
  out.set('content-type', upstream.headers.get('content-type') || 'application/json');
  out.set('cache-control', 'no-cache, no-transform');
  if ((upstream.headers.get('content-type') || '').includes('text/event-stream')) {
    out.set('x-accel-buffering', 'no');
    out.set('connection', 'keep-alive');
  }
  return new Response(upstream.body, { status: upstream.status, headers: out });
}

export const GET = proxy;
export const POST = proxy;
