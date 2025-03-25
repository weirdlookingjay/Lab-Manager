import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Computer } from "@/types/computer";
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";

interface ProcessesSectionProps {
    computer: Computer;
}

export function ProcessesSection({ computer }: ProcessesSectionProps) {
    const processes = computer.processes || [];

    return (
        <Card>
            <CardHeader>
                <CardTitle>Processes</CardTitle>
            </CardHeader>
            <CardContent>
                <Table>
                    <TableHeader>
                        <TableRow>
                            <TableHead>PID</TableHead>
                            <TableHead>Name</TableHead>
                            <TableHead>CPU %</TableHead>
                            <TableHead>Memory %</TableHead>
                            <TableHead>Status</TableHead>
                            <TableHead>User</TableHead>
                            <TableHead>Started</TableHead>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        {processes.map((process) => (
                            <TableRow key={process.pid}>
                                <TableCell>{process.pid}</TableCell>
                                <TableCell>{process.name}</TableCell>
                                <TableCell>{process.cpu_percent.toFixed(1)}%</TableCell>
                                <TableCell>{process.memory_percent.toFixed(1)}%</TableCell>
                                <TableCell>{process.status}</TableCell>
                                <TableCell>{process.username}</TableCell>
                                <TableCell>{new Date(process.create_time).toLocaleString()}</TableCell>
                            </TableRow>
                        ))}
                        {processes.length === 0 && (
                            <TableRow>
                                <TableCell colSpan={7} className="text-center">
                                    No processes found
                                </TableCell>
                            </TableRow>
                        )}
                    </TableBody>
                </Table>
            </CardContent>
        </Card>
    );
}
