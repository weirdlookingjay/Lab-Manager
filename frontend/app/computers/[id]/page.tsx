import { notFound, redirect } from "next/navigation";
import { cookies } from 'next/headers';
import ComputerPageClient from "./ComputerPageClient";

interface ComputerPageProps {
  params: {
    id: string;
  };
}

async function getComputerData(id: string) {
  const cookieStore = cookies();
  const token = cookieStore.get('token');

  if (!token) {
    redirect('/login');
  }

  const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/computers/${id}/`, {
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Token ${token.value}`
    },
    cache: 'no-store'
  });

  if (!response.ok) {
    if (response.status === 404) {
      notFound();
    }
    if (response.status === 401) {
      redirect('/login');
    }
    throw new Error('Failed to fetch computer');
  }

  const data = await response.json();
  console.log('Computer Detail Data:', JSON.stringify(data, null, 2));
  return data;
}

export default async function ComputerPage({ params }: ComputerPageProps) {
  const computer = await getComputerData(params.id);
  return <ComputerPageClient computer={computer} />;
}
