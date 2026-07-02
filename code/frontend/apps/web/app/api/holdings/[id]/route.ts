import { NextResponse } from 'next/server';
import { gatewayFetch } from '../../gateway';
import { DEMO_CLIENT_ID, DEMO_TENANT_ID } from '@/components/holdings/holdings-shared';

export const dynamic = 'force-dynamic';

interface RouteParams {
  params: { id: string };
}

export async function DELETE(_request: Request, { params }: RouteParams): Promise<NextResponse> {
  const id = params.id?.trim();
  if (!id) {
    return NextResponse.json(
      { success: false, data: null, error: 'Holding id is required' },
      { status: 400 },
    );
  }

  const query = `tenantId=${DEMO_TENANT_ID}&clientId=${DEMO_CLIENT_ID}`;
  const result = await gatewayFetch<unknown>(`/v1/holdings/${encodeURIComponent(id)}?${query}`, {
    method: 'DELETE',
  });

  if (result.status === 404) {
    return NextResponse.json(
      { success: false, data: null, error: 'Holding not found' },
      { status: 404 },
    );
  }
  if (!result.ok) {
    return NextResponse.json(
      { success: false, data: null, error: result.error ?? 'Holdings service unavailable' },
      { status: 502 },
    );
  }
  return NextResponse.json({ success: true, data: { id }, error: null });
}
