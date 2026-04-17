const publicApiBaseUrl =
  process.env.NEXT_PUBLIC_API_BASE_URL?.trim().replace(/\/+$/, "") ?? "";

const basePath = process.env.NEXT_PUBLIC_BASE_PATH ?? "";

export function getApiUrl(path: string) {
  if (/^https?:\/\//i.test(path)) {
    return path;
  }

  const normalizedPath = path.startsWith("/") ? path : `/${path}`;

  if (publicApiBaseUrl) {
    return `${publicApiBaseUrl}${normalizedPath}`;
  }

  return `${basePath}${normalizedPath}`;
}
