import { getApiUrl } from "@/lib/api-url";

export type AuthEnvelope<TData> = {
  status: "success" | "error";
  data: TData;
  msg: string;
};

export class AuthApiError extends Error {
  statusCode: number;
  data: unknown;

  constructor(message: string, statusCode = 400, data: unknown = null) {
    super(message);
    this.name = "AuthApiError";
    this.statusCode = statusCode;
    this.data = data;
  }
}

export type AuthUser = {
  id: string;
  email: string;
  full_name: string;
  role: "user" | "admin";
};

export type AuthToken = {
  access_token: string;
  token_type: "bearer";
  expires_in: number;
};

export type SendCodeResponse = AuthEnvelope<null>;

export type RegisterResponse = AuthEnvelope<{
  user_id: string;
  role: "user" | "admin";
}>;

export type LoginResponse = AuthEnvelope<{
  token: AuthToken;
  user: AuthUser;
}>;

export type ResetPasswordResponse = AuthEnvelope<null>;

export type VerifyTokenResponse = AuthEnvelope<{
  payload: Record<string, unknown>;
}>;

export type RegisterUserParams = {
  email: string;
  password: string;
  full_name: string;
  code: string;
  invite_code?: string;
};

export type SendCodePurpose = "register" | "reset";

export type LoginParams = {
  email: string;
  password: string;
};

export type ResetPasswordParams = {
  email: string;
  code: string;
  new_password: string;
};

function translateAuthError(message: string) {
  const normalizedMessage = message.toLowerCase();

  if (normalizedMessage.includes("password cannot be longer than 72 bytes")) {
    return "密码过长，当前系统最多支持 72 个字节，请缩短后重试";
  }

  if (normalizedMessage.includes("bcrypt") && normalizedMessage.includes("72 bytes")) {
    return "密码过长，当前系统最多支持 72 个字节，请缩短后重试";
  }

  return message;
}

async function requestJson<TResponse>(path: string, init: RequestInit): Promise<TResponse> {
  let response: Response;

  try {
    response = await fetch(getApiUrl(path), {
      ...init,
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
        ...(init.headers ?? {}),
      },
    });
  } catch (error) {
    const message = error instanceof Error && /failed to fetch|networkerror|load failed/i.test(error.message)
      ? "无法连接到后端服务，请确认后端已启动并检查接口地址"
      : error instanceof Error
        ? translateAuthError(error.message)
        : "请求失败，请稍后重试";

    throw new AuthApiError(message, 0);
  }

  let payload: AuthEnvelope<unknown> | null = null;
  try {
    payload = (await response.json()) as AuthEnvelope<unknown>;
  } catch {
    throw new AuthApiError("服务器返回了无效的响应", response.status);
  }

  if (!response.ok || !payload || payload.status === "error") {
    const rawMessage = payload?.msg || response.statusText || "请求失败";
    throw new AuthApiError(translateAuthError(rawMessage), response.status, payload?.data);
  }

  return payload as TResponse;
}

export function sendCode(params: { email: string; purpose?: SendCodePurpose }) {
  return requestJson<SendCodeResponse>("/api/auth/send-code", {
    method: "POST",
    body: JSON.stringify(params),
  });
}

export function register(params: RegisterUserParams) {
  return requestJson<RegisterResponse>("/api/auth/register", {
    method: "POST",
    body: JSON.stringify(params),
  });
}

export function login(params: LoginParams) {
  return requestJson<LoginResponse>("/api/auth/login", {
    method: "POST",
    body: JSON.stringify(params),
  });
}

export function resetPassword(params: ResetPasswordParams) {
  return requestJson<ResetPasswordResponse>("/api/auth/reset-password", {
    method: "POST",
    body: JSON.stringify(params),
  });
}

export function verifyJwt(token: string) {
  return requestJson<VerifyTokenResponse>("/api/auth/token/verify", {
    method: "POST",
    body: JSON.stringify({ token }),
  });
}

export const registerUser = register;
export const sendAuthCode = sendCode;
export const loginUser = login;
