import Button from "./Button";

interface Props {
  onScan: (code: string) => void;
  label?: string;
}

export default function ScanButton({ onScan, label = "Scan" }: Props) {
  return (
    <Button
      variant="secondary"
      onClick={() => {
        const code = prompt("Enter or scan code:");
        if (code) onScan(code.trim());
      }}
    >
      📷 {label}
    </Button>
  );
}
