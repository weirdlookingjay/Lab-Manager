import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Computer } from "@/types/computer";
import { formatBytes } from "@/lib/utils";

interface SystemInfoCardProps {
    computer: Computer;
}

export function SystemInfoCard({ computer }: SystemInfoCardProps) {
    return (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">CPU Usage</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="text-2xl font-bold">{computer.cpu_percent.toFixed(1)}%</div>
                    <p className="text-xs text-muted-foreground">
                        {computer.cpu_model} ({computer.cpu_count} cores)
                    </p>
                </CardContent>
            </Card>

            <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Memory Usage</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="text-2xl font-bold">{computer.memory_usage.toFixed(1)}%</div>
                    <p className="text-xs text-muted-foreground">
                        {formatBytes(computer.memory_used)} / {formatBytes(computer.memory_total)}
                    </p>
                </CardContent>
            </Card>

            <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Disk Usage</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="text-2xl font-bold">{computer.disk_usage.toFixed(1)}%</div>
                    <p className="text-xs text-muted-foreground">
                        {formatBytes(computer.disk_used)} / {formatBytes(computer.disk_total)}
                    </p>
                </CardContent>
            </Card>

            <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Network</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="text-2xl font-bold">{computer.network_interfaces.length}</div>
                    <p className="text-xs text-muted-foreground">Active Interfaces</p>
                </CardContent>
            </Card>
        </div>
    );
}
