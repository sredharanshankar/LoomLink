import { useQuery } from "@tanstack/react-query";
import { api } from "../../lib/api";
import PageHeader from "../../components/ui/PageHeader";
import Skeleton from "../../components/ui/Skeleton";
import Badge from "../../components/ui/Badge";
import Table from "../../components/ui/Table";

interface User {
  id: string;
  employee_code: string;
  name: string;
  role: string;
  is_active: boolean;
}

interface UsersResponse {
  items: User[];
  total: number;
}

const ROLE_COLOR: Record<string, "purple" | "blue" | "green" | "gray"> = {
  admin: "purple",
  manager: "blue",
  supervisor: "green",
  operator: "gray",
};

const columns = [
  { key: "employee_code", header: "Code" },
  { key: "name", header: "Name" },
  {
    key: "role",
    header: "Role",
    render: (r: User) => <Badge color={ROLE_COLOR[r.role] ?? "gray"}>{r.role}</Badge>,
  },
  {
    key: "is_active",
    header: "Active",
    render: (r: User) => <Badge color={r.is_active ? "green" : "red"}>{r.is_active ? "Active" : "Inactive"}</Badge>,
  },
];

export default function UsersPage() {
  const { data, isLoading } = useQuery({
    queryKey: ["users"],
    queryFn: () => api.get<UsersResponse>("/users?page=1&size=50"),
  });

  return (
    <div className="p-6">
      <PageHeader title="Users" subtitle={data ? `${data.total} users` : undefined} />
      {isLoading ? (
        <Skeleton rows={8} />
      ) : (
        <div className="bg-white rounded-lg border border-gray-200 shadow-sm">
          <Table columns={columns} data={data?.items ?? []} rowKey={(r) => r.id} />
        </div>
      )}
    </div>
  );
}
