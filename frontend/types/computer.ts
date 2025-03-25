export interface Process {
    pid: number;
    name: string;
    cpu_percent: number;
    memory_percent: number;
    status: string;
    create_time: string;
    username: string;
}

export interface MetricsData {
    cpu: {
        manufacturer: string;
        architecture: string;
        model: string;
        cores: number;
        threads: number;
        usage: number;
        temperature?: number;
    };
    memory: {
        total: number;
        used: number;
        free: number;
        usage: number;
    };
    disk: {
        total: number;
        used: number;
        free: number;
        usage: number;
        device: string;
        mountpoint: string;
        filesystem: string;
    }[];
    network: {
        interfaces: {
            name: string;
            ip: string;
            mac: string;
            speed: number;
        }[];
    };
    system: {
        device_class: string;
        os_version: string;
        logged_in_user: string;
        uptime: string;
    };
}

export interface Computer {
  id: string;
  label: string;
  hostname: string;
  ip_address: string;
  status: 'online' | 'offline';
  os_version?: string;
  last_seen?: string;
  last_metrics_update?: string;
  manufacturer?: string;
  cpu_model?: string;
  cpu_cores?: number;
  cpu_threads?: number;
  cpu_percent?: number;
  cpu_speed?: string;
  memory_total?: number;
  memory_usage?: number;
  memory_gb?: string;
  memory_percent?: number;
  total_disk?: number;
  disk_usage?: number;
  disk_gb?: string;
  disk_percent?: number;
  device_class?: string;
  boot_time?: string;
  system_uptime?: number;
  uptime?: string;
  logged_in_user?: string;
  metrics?: {
    metrics?: {
      cpu?: {
        model?: string;
        speed?: string;
        cores?: number;
        threads?: number;
        architecture?: string;
        manufacturer?: string;
        percent?: number;
      };
      memory?: {
        total?: number;
        used?: number;
        free?: number;
        percent?: number;
      };
      disk?: {
        total?: number;
        used?: number;
        free?: number;
        percent?: number;
      };
      system?: {
        status?: string;
        uptime?: string;
        boot_time?: number;
        os_version?: string;
        device_class?: string;
        logged_in_user?: string;
      };
    };
  };
}
