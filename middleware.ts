// middleware.ts — Vercel Edge Middleware for Pa se App
//
// Uses only Web Platform APIs (no next/server import) so it works on
// plain static Vercel projects without a package.json or Next.js.
//
// Password is stored in the APP_PASSWORD environment variable.
// Set it in: Vercel dashboard → project → Settings → Environment Variables.
// Family members log in once; cookie persists 1 year.
// To rotate the password, update APP_PASSWORD in the dashboard — no redeploy needed.

export const config = {
  runtime: 'edge',
  // Match all paths. The edge function checks auth before serving any file.
  matcher: '/(.*)',
};

const COOKIE_NAME = 'pa-se-app-auth';
const COOKIE_MAX_AGE = 60 * 60 * 24 * 365; // 1 year

// env() avoids a missing @types/node tsconfig error while remaining valid at runtime.
const env = (key: string): string =>
  ((globalThis as Record<string, unknown>)['process'] as { env: Record<string, string> } | undefined)
    ?.env?.[key] ?? '';

export default function middleware(request: Request): Response {
  const password = env('APP_PASSWORD').trim();

  // If APP_PASSWORD is not set, allow all requests through.
  if (!password) {
    return new Response(null, { status: 200, headers: { 'x-middleware-next': '1' } });
  }

  const url = new URL(request.url);

  // Check for valid auth cookie.
  const cookieHeader = request.headers.get('cookie') ?? '';
  const authCookie = parseCookie(cookieHeader, COOKIE_NAME);
  if (authCookie === password) {
    return new Response(null, { status: 200, headers: { 'x-middleware-next': '1' } });
  }

  // Check password submitted via query param.
  const submitted = url.searchParams.get('pw');
  if (submitted === password) {
    const cleanUrl = url.origin + url.pathname;
    const headers = new Headers({ Location: cleanUrl });
    headers.append(
      'Set-Cookie',
      `${COOKIE_NAME}=${password}; Max-Age=${COOKIE_MAX_AGE}; Path=/; HttpOnly; Secure; SameSite=Strict`
    );
    return new Response(null, { status: 302, headers });
  }

  // Not authenticated — serve a minimal Afrikaans login page.
  const loginHtml = `<!DOCTYPE html>
<html lang="af">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Pa se App — Teken in</title>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background: #212121;
      color: #fff;
      font-family: 'Segoe UI', Arial, sans-serif;
      display: flex;
      align-items: center;
      justify-content: center;
      height: 100vh;
    }
    form { display: flex; flex-direction: column; gap: 16px; width: 280px; }
    input {
      padding: 14px;
      font-size: 20px;
      border-radius: 8px;
      border: none;
      background: #333;
      color: #fff;
    }
    button {
      padding: 16px;
      font-size: 22px;
      background: #1565c0;
      color: #fff;
      border: none;
      border-radius: 8px;
      cursor: pointer;
      font-weight: 600;
    }
    button:active { background: #0d47a1; }
  </style>
</head>
<body>
  <form method="GET" action="/">
    <input type="password" name="pw" placeholder="Wagwoord" autofocus autocomplete="current-password">
    <button type="submit">Teken in</button>
  </form>
</body>
</html>`;

  return new Response(loginHtml, {
    status: 401,
    headers: { 'Content-Type': 'text/html; charset=utf-8' },
  });
}

function parseCookie(cookieHeader: string, name: string): string | undefined {
  for (const part of cookieHeader.split(';')) {
    const [k, ...v] = part.trim().split('=');
    if (k.trim() === name) return v.join('=').trim();
  }
  return undefined;
}
