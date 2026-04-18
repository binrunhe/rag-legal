import { verifyJwt } from "@/lib/api/auth";

const AUTH_SESSION_KEY = "legal_auth_session";

export type StoredAuthSession = {
  accessToken: string;
  userEmail: string;
  role: "user" | "admin";
  signedInAt: string;
  expiresAt: string;
};

function parseStoredSession(raw: string | null): StoredAuthSession | null {
  if (!raw) {
    return null;
  }

  try {
    const parsed = JSON.parse(raw) as Partial<StoredAuthSession>;

    if (
      typeof parsed.accessToken !== "string" ||
      typeof parsed.userEmail !== "string" ||
      (parsed.role !== "user" && parsed.role !== "admin") ||
      typeof parsed.signedInAt !== "string" ||
      typeof parsed.expiresAt !== "string"
    ) {
      return null;
    }

    return {
      accessToken: parsed.accessToken,
      userEmail: parsed.userEmail,
      role: parsed.role,
      signedInAt: parsed.signedInAt,
      expiresAt: parsed.expiresAt,
    };
  } catch {
    return null;
  }
}

export function saveAuthSession(options: {
  token: string;
  userEmail: string;
  role: "user" | "admin";
  expiresInSeconds: number;
  remember: boolean;
}): StoredAuthSession {
  const now = Date.now();
  const session: StoredAuthSession = {
    accessToken: options.token,
    userEmail: options.userEmail,
    role: options.role,
    signedInAt: new Date(now).toISOString(),
    expiresAt: new Date(now + Math.max(0, options.expiresInSeconds) * 1000).toISOString(),
  };

  const payload = JSON.stringify(session);
  if (options.remember) {
    localStorage.setItem(AUTH_SESSION_KEY, payload);
    sessionStorage.removeItem(AUTH_SESSION_KEY);
  } else {
    sessionStorage.setItem(AUTH_SESSION_KEY, payload);
    localStorage.removeItem(AUTH_SESSION_KEY);
  }

  return session;
}

export function clearAuthSession() {
  localStorage.removeItem(AUTH_SESSION_KEY);
  sessionStorage.removeItem(AUTH_SESSION_KEY);
}

export function getStoredAuthSession(): StoredAuthSession | null {
  const sessionValue = parseStoredSession(sessionStorage.getItem(AUTH_SESSION_KEY));
  if (sessionValue) {
    return sessionValue;
  }

  const localValue = parseStoredSession(localStorage.getItem(AUTH_SESSION_KEY));
  if (localValue) {
    return localValue;
  }

  return null;
}

function isSessionExpired(session: StoredAuthSession): boolean {
  const expiresAt = Date.parse(session.expiresAt);
  if (Number.isNaN(expiresAt)) {
    return true;
  }

  return Date.now() >= expiresAt;
}

export async function validateStoredAuthSession(): Promise<{
  ok: boolean;
  session: StoredAuthSession | null;
  reason?: string;
}> {
  const session = getStoredAuthSession();
  if (!session) {
    return { ok: false, session: null, reason: "missing" };
  }

  if (isSessionExpired(session)) {
    clearAuthSession();
    return { ok: false, session: null, reason: "expired" };
  }

  try {
    await verifyJwt(session.accessToken);
    return { ok: true, session };
  } catch {
    clearAuthSession();
    return { ok: false, session: null, reason: "invalid" };
  }
}
