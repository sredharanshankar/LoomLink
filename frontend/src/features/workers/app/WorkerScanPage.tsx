import { useNavigate } from "react-router-dom";
import PageHeader from "../../../components/ui/PageHeader";
import ScannerModal from "../../../components/ui/ScannerModal";

export default function WorkerScanPage() {
  const navigate = useNavigate();

  function handleScan(code: string) {
    navigate(`/s/${encodeURIComponent(code)}`);
  }

  return (
    <div className="p-4">
      <PageHeader title="Scan" />
      <ScannerModal
        open={true}
        onClose={() => navigate(-1)}
        onScan={handleScan}
      />
    </div>
  );
}
