export const runtime = "edge";
export const dynamic = "force-dynamic";

import { createApiProxy } from "@/lib/edge-api-proxy";

const proxy = createApiProxy("/api/auth/token/verify");

export const POST = proxy;
