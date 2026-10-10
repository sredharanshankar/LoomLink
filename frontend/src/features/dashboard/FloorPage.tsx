import PageHeader from "../../components/ui/PageHeader";

export default function FloorPage() {
  return (
    <div className="p-6">
      <PageHeader title="Floor View" subtitle="Live machine status map" />
      <div className="bg-white rounded-lg border border-gray-200 p-8 text-center text-gray-400">
        Floor map — Ripple RippleFloor component mounts here
      </div>
    </div>
  );
}
