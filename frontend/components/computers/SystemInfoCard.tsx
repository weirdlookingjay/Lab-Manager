import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { formatDistanceToNow } from 'date-fns';
import { Computer } from "@/lib/types";
import { Monitor } from 'lucide-react';

interface SystemInfoProps {
  computer: Computer;
}

export function SystemInfoCard({ computer }: SystemInfoProps) {
  const lastSeen = computer.last_seen
    ? formatDistanceToNow(new Date(computer.last_seen), { addSuffix: true })
    : 'Never';

  return (
    <Card className="col-span-2">
      <CardHeader>
        <div className="flex items-center gap-2">
          <Monitor className="h-5 w-5" />
          <CardTitle>SYSTEM INFORMATION</CardTitle>
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <div>
              <div className="text-sm text-muted-foreground">LAST SEEN</div>
              <div>{lastSeen}</div>
            </div>
            <div>
              <div className="text-sm text-muted-foreground">DEVICE CLASS</div>
              <div>{computer.metrics.system.device_class || 'Unknown'}</div>
            </div>
            <div>
              <div className="text-sm text-muted-foreground">OS VERSION</div>
              <div>{computer.metrics.system.os_version || 'Unknown'}</div>
            </div>
            <div>
              <div className="text-sm text-muted-foreground">CPU MODEL</div>
              <div>{computer.metrics.cpu.model || 'Unknown'}</div>
            </div>
          </div>
          <div className="space-y-2">
            <div>
              <div className="text-sm text-muted-foreground">LOGGED IN USER</div>
              <div>{computer.metrics.system.logged_in_user || 'None'}</div>
            </div>
            <div>
              <div className="text-sm text-muted-foreground">HOSTNAME</div>
              <div>{computer.hostname || 'Unknown'}</div>
            </div>
            <div>
              <div className="text-sm text-muted-foreground">MANUFACTURER</div>
              <div>{computer.model?.split(' ')[0] || 'Unknown'}</div>
            </div>
            <div>
              <div className="text-sm text-muted-foreground">UPTIME</div>
              <div>{computer.metrics.system.uptime || 'Unknown'}</div>
            </div>
            <div>
              <div className="text-sm text-muted-foreground">TOTAL MEMORY</div>
              <div>{computer.metrics.memory.total_gb || 'Unknown'} GB</div>
            </div>
            <div>
              <div className="text-sm text-muted-foreground">TOTAL DISK SPACE</div>
              <div>{computer.metrics.disk.total_gb || 'Unknown'} GB</div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
