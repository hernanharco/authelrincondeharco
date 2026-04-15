export const GET = ({ request, url }: { request: Request, url: URL }) => {
  return new Response(JSON.stringify({
    url_origin: url.origin,
    url_href: url.href,
    headers: {
      host: request.headers.get("host"),
      x_forwarded_host: request.headers.get("x-forwarded-host"),
      x_forwarded_proto: request.headers.get("x-forwarded-proto"),
    }
  }, null, 2), { headers: { "content-type": "application/json" } });
};
