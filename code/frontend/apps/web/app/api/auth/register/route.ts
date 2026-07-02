import { NextResponse } from 'next/server';
import { registerUser } from '@/lib/users-store';

export async function POST(req: Request) {
  try {
    const body = (await req.json()) as {
      name?: string;
      email?: string;
      phone?: string;
      age?: number;
      password?: string;
    };
    const { name, email, phone, age, password } = body;
    if (!name || !email || !phone || !age || !password) {
      return NextResponse.json({ error: 'All fields are required' }, { status: 400 });
    }
    if (String(age).length < 1 || Number(age) < 18) {
      return NextResponse.json({ error: 'Must be 18 or older' }, { status: 400 });
    }
    const user = registerUser({ name, email, phone, age: Number(age), password });
    return NextResponse.json({ id: user.id, name: user.name, email: user.email });
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : 'Registration failed';
    return NextResponse.json({ error: message }, { status: 400 });
  }
}
