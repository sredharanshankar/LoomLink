import { useParams } from "react-router-dom";
import PageHeader from "../../components/ui/PageHeader";

export default function BatchDetailPage() {
  const params = useParams();
  return (
    <div className="p-6">
      <PageHeader title="Yarn Batch" subtitle={params.id} />
      <div className="bg-white rounded-lg border border-gray-200 p-8 text-center text-gray-400">Yarn Batch detail — C-M1</div>
    </div>
  );
}

