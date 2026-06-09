/**
 * Next 16 proxy (ex middleware). Protege /onboarding y /settings cuando
 * AUTH_ENABLED=true. Las páginas de datos (feed, dashboard, search, dnu) son
 * públicas — datos legislativos abiertos. En modo demo, passthrough total.
 */
import { NextResponse } from 'next/server';
import { AUTH_ENABLED, auth } from '@/auth';

const PROTECTED_PREFIXES = ['/onboarding', '/settings'];

const passthrough = () => NextResponse.next();

const gated = auth((req) => {
  const path = req.nextUrl.pathname;
  const isLoggedIn = !!req.auth;
  const isProtected = PROTECTED_PREFIXES.some((p) => path === p || path.startsWith(`${p}/`));
  if (isProtected && !isLoggedIn) {
    const signin = new URL('/auth/signin', req.url);
    signin.searchParams.set('callbackUrl', path);
    return NextResponse.redirect(signin);
  }
  return NextResponse.next();
});

export default AUTH_ENABLED ? gated : passthrough;

export const config = {
  matcher: ['/((?!api|_next/static|_next/image|favicon.ico|.*\\..*).*)'],
};
