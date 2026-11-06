// Cloudflare Pages Function: GET /geo
// Edge geolocation for the live business-day countdown.
export async function onRequestGet(context) {
  const { request } = context;
  const cf = request.cf || {};
  return new Response(
    JSON.stringify({
      country: (cf.country || "").toUpperCase(),
      timezone: cf.timezone || "",
      city: cf.city || "",
      region: cf.region || "",
    }),
    {
      headers: {
        "content-type": "application/json; charset=utf-8",
        "cache-control": "no-store",
        "access-control-allow-origin": "*",
      },
    }
  );
}
