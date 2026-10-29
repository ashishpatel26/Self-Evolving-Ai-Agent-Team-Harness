async function call(path, body) {
  const res = await fetch(`/api/${path}`, {
    method: body === undefined ? 'GET' : 'POST',
    headers: body === undefined ? undefined : { 'content-type': 'application/json' },
    body: body === undefined ? undefined : JSON.stringify(body),
    cache: 'no-store',
  });
  let data = null;
  try {
    data = await res.json();
  } catch {}
  if (!res.ok) {
    const detail = data?.detail;
    throw new Error(typeof detail === 'string' ? detail : `${res.status} ${res.statusText}`);
  }
  return data;
}

export const api = {
  state: () => call('state'),
  ticket: (text, customer_id) => call('tickets', customer_id ? { text, customer_id } : { text }),
  evolve: (opts) => call('evolve', opts),
  gate: (decision, rationale) => call('gate', { decision, rationale }),
};
