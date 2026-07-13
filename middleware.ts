import { clerkMiddleware, createRouteMatcher } from "@clerk/nextjs/server";
import { NextResponse } from "next/server";

const isProtected = createRouteMatcher([
  "/worker(.*)",
  "/orders(.*)",
  "/proposal(.*)",
  "/scope(.*)",
  "/start(.*)",
  "/account(.*)",
  "/admin(.*)",
]);

const clerkEnabled = Boolean(process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY);

export default clerkEnabled
  ? clerkMiddleware(async (auth, req) => {
      if (isProtected(req)) {
        await auth.protect();
      }
    })
  : function middleware() {
      return NextResponse.next();
    };

export const config = {
  matcher: [
    "/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)",
    "/(api|trpc)(.*)",
  ],
};
