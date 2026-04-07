// middleware.ts — Vercel Edge Middleware for Pa se App
//
// Runs at the CDN edge before any file is served.
// Protects the app with a shared password stored in the APP_PASSWORD
// environment variable (set in Vercel dashboard → Settings → Environment Variables).
//
// Family members log in once; a cookie persists for 1 year.
// To rotate the password, change APP_PASSWORD in the Vercel dashboard —
// no code change or redeploy needed.

import { NextRequest, NextResponse } from 'next/server';

const COOKIE_NAME = 'pa-se-app-auth';
const COOKIE_MAX_AGE = 60 * 60 * 24 * 365; // 1 year in seconds

export function middleware(request: NextRequest) {
  const password = process.env.APP_PASSWORD;

  // If no password is configured, allow all requests through.
  // Set APP_PASSWORD in Vercel dashboard before going live.
  if (!password) {
    return NextResponse.next();
  }

  // Check for valid auth cookie.
  const cookie = request.cookies.get(COOKIE_NAME);
  if (cookie?.value === password) {
    return NextResponse.next();
  }

  // Check password submitted via query param (from the login form GET).
  const url = request.nextUrl;
  const submitted = url.searchParams.get('pw');
  if (submitted === password) {
    // Correct password — set cookie and redirect to clean URL (remove ?pw=).
    const cleanUrl = new URL(url.pathname, request.url);
    const response = NextResponse.redirect(cleanUrl);
    response.cookies.set(COOKIE_NAME, password, {
      maxAge: COOKIE_MAX_AGE,
      httpOnly: true,
      secure: true,
      sameSite: 'strict',
      path: '/',
    });
    return response;
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

  return new NextResponse(loginHtml, {
    status: 401,
    headers: { 'Content-Type': 'text/html; charset=utf-8' },
  });
}

export const config = {
  // Match all paths except Vercel internals and the favicon.
  matcher: ['/((?!_next/static|_next/image|favicon.ico).*)'],
};
