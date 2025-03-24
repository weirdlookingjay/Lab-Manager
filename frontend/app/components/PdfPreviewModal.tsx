import { Dialog, DialogContent } from "@/components/ui/dialog";

interface PdfPreviewModalProps {
  isOpen: boolean;
  onClose: () => void;
  pdfUrl: string;
  fileName: string;
}

export default function PdfPreviewModal({
  isOpen,
  onClose,
  pdfUrl,
  fileName,
}: PdfPreviewModalProps) {
  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] flex flex-col p-0">
        <div className="p-4 border-b">
          <h2 className="text-lg font-semibold">{fileName}</h2>
        </div>
        <div className="flex-1 min-h-0">
          <iframe
            src={pdfUrl}
            className="w-full h-[80vh]"
            title={`Preview of ${fileName}`}
          />
        </div>
      </DialogContent>
    </Dialog>
  );
}
