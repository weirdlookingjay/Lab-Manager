import { FileSystemExplorer } from "@/components/computers/FileSystemExplorer";
import { Computer, getComputerById } from "@/lib/api";

import { notFound } from "next/navigation";

interface FilesPageProps {
  params: {
    id: string;
  };
}

export default async function FilesPage({ params }: FilesPageProps) {
  const computer: Computer | null = await getComputerById(params.id);
  
  if (!computer) {
    notFound();
  }

  return (
    <div className="flex-1 space-y-4 p-4 md:p-8 pt-6">
      <FileSystemExplorer computer={computer} />
    </div>
  );
}
