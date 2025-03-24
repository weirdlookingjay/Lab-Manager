import { useState } from 'react';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { fetchWithAuth } from '@/app/utils/api';


interface RemoteCommandPromptProps {
    computerId: string;
}

export function RemoteCommandPrompt({ computerId }: RemoteCommandPromptProps) {
    const [command, setCommand] = useState('');
    const [output, setOutput] = useState<string[]>([]);
    const [isLoading, setIsLoading] = useState(false);

    const executeCommand = async () => {
        if (!command.trim()) return;

        setIsLoading(true);
        setOutput(prev => [...prev, `> ${command}`]); // Show command immediately

        try {
            // Add timeout to the fetch request
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 second timeout

            const response = await fetchWithAuth(`/api/computers/${computerId}/execute_remote_command/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ command }),
                signal: controller.signal
            });

            clearTimeout(timeoutId);

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            if (data.error) {
                setOutput(prev => [...prev, `Error: ${data.error}`]);
            } else {
                setOutput(prev => [...prev, data.output || 'No output received']);
            }
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
        } catch (error: any) {
            if (error.name === 'AbortError') {
                setOutput(prev => [...prev, 'Command timed out after 30 seconds']);
            } else {
                setOutput(prev => [...prev, `Error: ${error.message}`]);
            }
        } finally {
            setIsLoading(false);
            setCommand('');
        }
    };

    return (
        <div className="flex flex-col space-y-4">
            <ScrollArea className="h-[300px] w-full rounded-md border p-4 bg-black text-white font-mono">
                {output.map((line, i) => (
                    <div key={i} className="whitespace-pre-wrap">{line}</div>
                ))}
                {isLoading && <div className="text-gray-500">Executing command...</div>}
            </ScrollArea>

            <div className="flex space-x-2">
                <Input
                    value={command}
                    onChange={(e) => setCommand(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && !isLoading && executeCommand()}
                    placeholder="Enter command..."
                    disabled={isLoading}
                    className="font-mono"
                />
                <Button
                    onClick={executeCommand}
                    disabled={isLoading}
                    className={isLoading ? "opacity-50" : ""}
                >
                    {isLoading ? "Executing..." : "Execute"}
                </Button>
            </div>
        </div>
    );
}