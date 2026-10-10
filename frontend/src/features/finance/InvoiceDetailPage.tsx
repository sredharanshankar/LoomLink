import { useParams } from "react-router-dom";
import PageHeader from "../../components/ui/PageHeader";

export default function InvoiceDetailPage() {
  const params = useParams();
  return (
    <div className="p-6">
      <PageHeader title="Invoice" subtitle={params.id} />
      <div className="bg-white rounded-lg border border-gray-200 p-8 text-center text-gray-400">Invoice detail — C-M1</div>
    </div>
  );
}

