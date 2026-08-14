/**
 * Shared names for the prototype gallery.
 *
 * GET  /names   returns { "<id>": "<naam>", ... }   public, no key needed
 * PUT  /names   replaces the whole map                 requires x-edit-key
 *
 * The gallery reads this on load and writes on every rename, so a name typed by
 * one person is what the next visitor sees. Only names live here; everything
 * else about a prototype stays in prototypes.json.
 */

const KEY = "names";
const MAX_ENTRIES = 500;
const MAX_LEN = 120;

function cors(env) {
  return {
    "Access-Control-Allow-Origin": env.ALLOW_ORIGIN || "*",
    "Access-Control-Allow-Methods": "GET, PUT, OPTIONS",
    "Access-Control-Allow-Headers": "content-type, x-edit-key",
    "Access-Control-Max-Age": "86400",
  };
}

function json(body, status, env) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { ...cors(env), "content-type": "application/json", "cache-control": "no-store" },
  });
}

/** Keep only sane id/name string pairs, so a bad client cannot fill the store. */
function clean(input) {
  if (!input || typeof input !== "object" || Array.isArray(input)) return null;
  const out = {};
  for (const [id, name] of Object.entries(input).slice(0, MAX_ENTRIES)) {
    if (typeof id !== "string" || typeof name !== "string") continue;
    const k = id.trim(), v = name.trim();
    if (!k || !v || k.length > MAX_LEN || v.length > MAX_LEN) continue;
    out[k] = v;
  }
  return out;
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (request.method === "OPTIONS") {
      return new Response(null, { headers: cors(env) });
    }
    if (url.pathname !== "/names") {
      return json({ error: "not_found" }, 404, env);
    }

    if (request.method === "GET") {
      const stored = await env.NAMES.get(KEY);
      return new Response(stored || "{}", {
        headers: { ...cors(env), "content-type": "application/json", "cache-control": "no-store" },
      });
    }

    if (request.method === "PUT") {
      if (!env.EDIT_KEY) return json({ error: "no_edit_key_configured" }, 500, env);
      if (request.headers.get("x-edit-key") !== env.EDIT_KEY) {
        return json({ error: "unauthorized" }, 401, env);
      }
      let body;
      try {
        body = await request.json();
      } catch (e) {
        return json({ error: "invalid_json" }, 400, env);
      }
      const names = clean(body);
      if (!names) return json({ error: "expected_object" }, 400, env);

      await env.NAMES.put(KEY, JSON.stringify(names));
      return json({ ok: true, count: Object.keys(names).length }, 200, env);
    }

    return json({ error: "method_not_allowed" }, 405, env);
  },
};
