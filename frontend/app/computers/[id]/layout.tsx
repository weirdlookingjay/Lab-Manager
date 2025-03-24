import { getComputerFromServer } from "@/lib/api";
import { notFound, redirect } from "next/navigation";
import { cookies } from 'next/headers';

interface ComputerLayoutProps {
  children: React.ReactNode;
  params: {
    id: string;
  };
}

export default async function ComputerLayout({ children, params }: ComputerLayoutProps) {
  const cookieStore = await cookies();
  const token = cookieStore.get('token');

  if (!token) {
    redirect('/login');
  }

  const resolvedParams = await Promise.resolve(params);
  const computer = await getComputerFromServer(resolvedParams.id, token.value);
  
  if (!computer) {
    notFound();
  }

  return children;
}
