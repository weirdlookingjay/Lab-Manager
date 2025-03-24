import { Checkbox } from "@/components/ui/checkbox";

interface DocumentCheckboxProps {
  checked: boolean;
  onCheckedChange: (checked: boolean) => void;
  className?: string;
}

export function DocumentCheckbox({
  checked,
  onCheckedChange,
  className = ''
}: DocumentCheckboxProps) {
  return (
    <div className={`flex items-center ${className}`}
      onClick={(e) => {
        e.stopPropagation();
      }}
    >
      <Checkbox
        checked={checked}
        onCheckedChange={(checked) => onCheckedChange(checked as boolean)}
        className="data-[state=checked]:bg-blue-600"
      />
    </div>
  );
}
