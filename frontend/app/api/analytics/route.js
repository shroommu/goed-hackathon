import { NextResponse } from "next/server";

export async function POST(request) {
  try {
    const payload = await request.json();

    console.info("landing_cta_click", {
      ctaId: payload?.ctaId,
      mode: payload?.mode,
      destination: payload?.destination,
      timestamp: payload?.timestamp,
      path: payload?.path,
    });

    return new NextResponse(null, { status: 204 });
  } catch {
    return NextResponse.json(
      { error: "Invalid analytics payload" },
      { status: 400 },
    );
  }
}
