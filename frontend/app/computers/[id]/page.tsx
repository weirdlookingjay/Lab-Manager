import { cookies } from 'next/headers';
import { redirect } from 'next/navigation';
import ComputerPageClient from './ComputerPageClient';

interface ComputerPageProps {
    params: Promise<{
        id: string;
    }>;
}

export default async function ComputerPage({ params }: ComputerPageProps) {
    // Get token from cookies
    const cookieStore = await cookies();
    const token = cookieStore.get('token')?.value;

    if (!token) {
        redirect('/login');
    }

    // Get id from params - need to await since it's a Promise in Next.js 13+
    const { id } = await params;

    return (
        <div className="flex-1 space-y-4 p-8 pt-6">
            <ComputerPageClient id={id} token={token} />
        </div>
    );
}
