import NextAuth from 'next-auth';
import Google from 'next-auth/providers/google';

/**
 * NextAuth v5 + Google OAuth + sync server-to-server contra la API de Vigía.
 *
 * Flujo: signIn('google') → callback jwt hace POST {API}/auth/sync con AUTH_SECRET
 * → la API upserta app_user, garantiza workspace default y devuelve un JWT propio
 * → guardamos apiJwt + workspace en el token y lo exponemos en la session.
 *
 * Si no hay credenciales Google, AUTH_ENABLED=false y la app corre en modo demo
 * (datos públicos sin login).
 */
export const AUTH_ENABLED = Boolean(process.env.AUTH_GOOGLE_ID || process.env.GOOGLE_CLIENT_ID);

const INTERNAL_API_URL =
  process.env.INTERNAL_API_URL ?? process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';
const AUTH_SECRET = process.env.AUTH_SECRET ?? '';

async function syncUserWithApi(profile) {
  if (!AUTH_SECRET) {
    console.warn('[auth] AUTH_SECRET not set; skipping API sync');
    return null;
  }
  try {
    const res = await fetch(`${INTERNAL_API_URL}/auth/sync`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${AUTH_SECRET}` },
      body: JSON.stringify({
        email: profile.email,
        name: profile.name ?? undefined,
        image_url: profile.picture ?? undefined,
        provider: 'google',
        provider_id: profile.sub ?? undefined,
      }),
    });
    if (!res.ok) {
      console.error(`[auth] /auth/sync failed: ${res.status} ${await res.text()}`);
      return null;
    }
    return await res.json();
  } catch (e) {
    console.error('[auth] /auth/sync threw:', e);
    return null;
  }
}

const NEXTAUTH_SECRET =
  process.env.AUTH_SECRET ?? (AUTH_ENABLED ? undefined : 'demo-mode-placeholder-not-used');

export const { handlers, auth, signIn, signOut } = NextAuth({
  trustHost: true,
  secret: NEXTAUTH_SECRET,
  session: { strategy: 'jwt' },
  providers: AUTH_ENABLED
    ? [
        Google({
          clientId: process.env.AUTH_GOOGLE_ID ?? process.env.GOOGLE_CLIENT_ID,
          clientSecret: process.env.AUTH_GOOGLE_SECRET ?? process.env.GOOGLE_CLIENT_SECRET,
        }),
      ]
    : [],
  pages: { signIn: '/auth/signin' },
  callbacks: {
    async jwt({ token, account, profile }) {
      if (account && profile && profile.email) {
        const sync = await syncUserWithApi({
          email: profile.email,
          name: profile.name,
          picture: profile.picture,
          sub: profile.sub,
        });
        if (sync) {
          token.apiJwt = sync.jwt;
          token.userId = sync.user_id;
          token.workspaceId = sync.workspace_id;
          token.workspaceSlug = sync.workspace_slug;
          token.workspaceName = sync.workspace_name;
          token.role = sync.role;
          token.plan = sync.plan;
          token.trialEndsAt = sync.trial_ends_at;
          token.onboarded = sync.onboarded;
        }
      }
      return token;
    },
    async session({ session, token }) {
      session.apiJwt = token.apiJwt;
      if (token.workspaceId) {
        session.workspace = {
          id: token.workspaceId,
          slug: token.workspaceSlug ?? '',
          name: token.workspaceName ?? '',
          role: token.role ?? 'viewer',
          plan: token.plan ?? 'free',
          trialEndsAt: token.trialEndsAt ?? null,
          onboarded: Boolean(token.onboarded),
        };
      }
      return session;
    },
  },
});
