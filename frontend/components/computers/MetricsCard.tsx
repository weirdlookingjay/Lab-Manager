import React from 'react';
import { Card, CardContent, Typography, Grid } from '@mui/material';
import { Computer } from '@/lib/types';
import { formatBytes } from '@/lib/utils';
import { Cpu, CircuitBoard, HardDrive } from 'lucide-react';

interface MetricsCardProps {
  computer: Computer;
}

const MetricsCard: React.FC<MetricsCardProps> = ({ computer }) => {
  const metrics = computer.metrics;
  
  const items = [
    {
      icon: <Cpu className="h-4 w-4" />,
      label: 'CPU',
      value: metrics.cpu.model || 'Unknown',
      details: metrics.cpu.cores ? `${metrics.cpu.cores} cores @ ${metrics.cpu.speed}GHz` : 'Unknown'
    },
    {
      icon: <CircuitBoard className="h-4 w-4" />,
      label: 'Memory',
      value: metrics.memory.total_gb,
      details: `${metrics.memory.used ? formatBytes(metrics.memory.used) : '0 GB'} used`
    },
    {
      icon: <HardDrive className="h-4 w-4" />,
      label: 'Disk',
      value: metrics.disk.total_gb,
      details: `${metrics.disk.percent}% used`
    }
  ];

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          System Metrics
        </Typography>
        <Grid container spacing={2}>
          {items.map((item, index) => (
            <Grid item xs={12} sm={4} key={index}>
              <div className="flex items-center space-x-2">
                {item.icon}
                <div>
                  <Typography variant="subtitle2">{item.label}</Typography>
                  <Typography variant="body2" color="textSecondary">
                    {item.value}
                  </Typography>
                  <Typography variant="caption" color="textSecondary">
                    {item.details}
                  </Typography>
                </div>
              </div>
            </Grid>
          ))}
        </Grid>
      </CardContent>
    </Card>
  );
};

export default MetricsCard;
