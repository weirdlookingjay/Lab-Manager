'use client';

import { Computer } from '@/types/computer';
import { useEffect, useState } from 'react';
import { ArrowLeft } from 'lucide-react';
import Link from 'next/link';
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import SystemInformation from '@/components/computers/SystemInformation';
import SystemOverview from '@/components/computers/SystemOverview';
import { ProcessesSection } from '@/components/computers/ProcessesSection';
import { ToolsSection } from '@/components/computers/ToolsSection';



interface ComputerPageClientProps {
    id: string;
    token?: string;
}

export default function ComputerPageClient({ id, token }: ComputerPageClientProps) {
    const [computer, setComputer] = useState<Computer | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchComputer = async () => {
            try {
                const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/computers/${id}/`, {
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Token ${token}`
                    }
                });

                if (!response.ok) {
                    throw new Error('Failed to fetch computer');
                }

                const data = await response.json();
                setComputer(data);
                setError(null);
            } catch (err) {
                setError(err instanceof Error ? err.message : 'An error occurred');
            } finally {
                setLoading(false);
            }
        };

        fetchComputer();
    }, [id, token]);

    if (loading) return <div>Loading...</div>;
    if (error) return <div>Error: {error}</div>;
    if (!computer) return <div>Computer not found</div>;

    const tabs = [
        { id: "overview", label: "Overview" },
        { id: "tools", label: "Tools" },
        { id: "monitoring", label: "Monitoring" },
        { id: "settings", label: "Settings" }
    ];

    return (
        <div className="space-y-4">
            <div className="flex items-center space-x-2">
                <Link href="/computers" className="text-gray-500 hover:text-gray-700">
                    <ArrowLeft className="h-4 w-4" />
                </Link>
                <h1 className="text-2xl font-bold">{computer.label || computer.hostname || computer.ip_address}</h1>
                <div className="flex items-center space-x-1">
                    <div className={`h-2 w-2 rounded-full ${computer.status === 'online' ? 'bg-green-500' : 'bg-red-500'} animate-pulse`} />
                    <span className="text-sm text-gray-500">{computer.status === 'online' ? 'Online' : 'Offline'}</span>
                </div>
                <div className="text-sm text-gray-500">
                    Last seen: {computer.last_seen}
                </div>
                {computer.last_metrics_update && (
                    <div className="text-sm text-gray-500">
                        Last metrics: {computer.last_metrics_update}
                    </div>
                )}
            </div>

            <SystemOverview computer={computer} token={token} />

            <Tabs defaultValue="overview">
                <TabsList>
                    {tabs.map((tab) => (
                        <TabsTrigger key={tab.id} value={tab.id}>
                            {tab.label}
                        </TabsTrigger>
                    ))}
                </TabsList>

                <TabsContent value="overview">
                    <div className="space-y-4">
                        <SystemInformation computer={computer} />
                        <ProcessesSection computer={computer} />
                    </div>
                </TabsContent>

                <TabsContent value="tools">
                    <ToolsSection computerId={computer.id} />
                </TabsContent>

                <TabsContent value="monitoring">
                    <div>Monitoring content</div>
                </TabsContent>

                <TabsContent value="settings">
                    <div>Settings content</div>
                </TabsContent>
            </Tabs>
        </div>
    );
}
