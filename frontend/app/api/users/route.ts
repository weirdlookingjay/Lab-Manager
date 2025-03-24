import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export const GET = async (request: NextRequest) => {
  try {
    const response = await fetch('http://localhost:8000/api/users/', {
      headers: {
        'Content-Type': 'application/json',
      },
    });
    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    return NextResponse.json({ error: 'Failed to fetch users' }, { status: 500 });
  }
};

export const POST = async (request: NextRequest) => {
  try {
    const body = await request.json();
    const response = await fetch('http://localhost:8000/api/users/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });
    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    return NextResponse.json({ error: 'Failed to create user' }, { status: 500 });
  }
};

export const PUT = async (request: NextRequest) => {
  try {
    const body = await request.json();
    const response = await fetch('http://localhost:8000/api/users/', {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });
    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    return NextResponse.json({ error: 'Failed to update user' }, { status: 500 });
  }
};

export const DELETE = async (request: NextRequest) => {
  try {
    const { searchParams } = new URL(request.url);
    const id = searchParams.get('id');
    
    if (!id) {
      return NextResponse.json({ error: 'User ID is required' }, { status: 400 });
    }

    const response = await fetch(`http://localhost:8000/api/users/${id}/`, {
      method: 'DELETE',
    });

    if (response.ok) {
      return new NextResponse(null, { status: 204 });
    } else {
      return NextResponse.json({ error: 'Failed to delete user' }, { status: response.status });
    }
  } catch (error) {
    return NextResponse.json({ error: 'Failed to delete user' }, { status: 500 });
  }
};