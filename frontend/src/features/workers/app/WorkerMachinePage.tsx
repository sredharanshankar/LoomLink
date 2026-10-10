import { useParams } from "react-router-dom";
import PageHeader from "../../../components/ui/PageHeader";

export default function WorkerMachinePage() {
  const params = useParams();
  return (
    <div className="p-4">
      <PageHeader title="Machine" subtitle={params.id} />
      <div className="bg-white rounded-lg border border-gray-200 p-6 text-center text-gray-400">Machine</div>
    </div>
  );
}

