export const runtime = 'experimental-edge';

import { type NextRequest, NextResponse } from "next/server";

// 这里的函数名必须从 proxy 改为 middleware
export async function middleware(_request: NextRequest) {
  return NextResponse.next();
}

export const config = {
  matcher: [
    "/",
    "/chat/:id",
    "/api/:path*",
    "/login",
    "/register",
    "/((?!_next/static|_next/image|favicon.ico|sitemap.xml|robots.txt).*)",
  ],
};