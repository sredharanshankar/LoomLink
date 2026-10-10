import { useState } from "react";
import Button from "./Button";
import ScannerModal from "./ScannerModal";

interface Props {
  onScan: (code: string) => void;
  label?: string;
  className?: string;
}

export default function ScanButton({ onScan, label = "Scan", className }: Props) {
  const [open, setOpen] = useState(false);

  function handleScan(code: string) {
    setOpen(false);
    onScan(code);
  }

  return (
    <>
      <Button variant="secondary" onClick={() => setOpen(true)} className={className}>
        📷 {label}
      </Button>
      <ScannerModal open={open} onClose={() => setOpen(false)} onScan={handleScan} />
    </>
  );
}
