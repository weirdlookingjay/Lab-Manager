import { SystemInfoCard } from "@/components/computers/SystemInfoCard";
import MetricsCard from "@/components/computers/MetricsCard";
import { getComputerById } from "@/lib/api";
import { Computer } from "@/lib/types";
import { notFound } from "next/navigation";

interface OverviewPageProps {
  params: { id: string };
}

export default async function OverviewPage({ params }: OverviewPageProps) {
  const computer: Computer | null = await getComputerById(params.id);
  
  if (!computer) {
    notFound();
  }

  return (
    <div className="space-y-4 p-4 md:p-8 pt-6">
      <MetricsCard computer={computer} />
      <SystemInfoCard computer={computer} />
    </div>
  );
}
