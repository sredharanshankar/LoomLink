import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../../lib/api";
import PageHeader from "../../components/ui/PageHeader";
import Skeleton from "../../components/ui/Skeleton";
import Badge from "../../components/ui/Badge";

interface User {
  id: string;
  employee_code: string;
  name: string;
  role: string;
  is_active: boolean;
  buyer_id: string | null;
  worker_id: string | null;
}

interface UsersResponse {
  items: User[];
  total: number;
}

interface Buyer {
  id: string;
  code: string;
  name: string;
}

interface BuyersResponse {
  items: Buyer[];
}

const ROLE_COLOR: Record<string, "purple" | "blue" | "green" | "gray" | "yellow"> = {
  admin: "purple",
  manager: "blue",
  owner: "blue",
  accounts: "yellow",
  supervisor: "green",
  operator: "gray",
  buyer: "yellow",
  dispatch: "gray",
  quality: "green",
};

function LinkBuyerModal({
  user,
  buyers,
  onClose,
}: {
  user: User;
  buyers: Buyer[];
  onClose: () => void;
}) {
  const qc = useQueryClient();
  const [selectedBuyerId, setSelectedBuyerId] = useState(user.buyer_id ?? "");
  const [error, setError] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: (buyerId: string | null) =>
      api.patch(`/users/${user.id}`, { buyer_id: buyerId }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["users"] });
      onClose();
    },
    onError: (e: Error) => setError(e.message),
  });

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-md p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-1">Link Buyer Account</h2>
        <p className="text-sm text-gray-500 mb-4">
          Linking <span className="font-medium">{user.name}</span> ({user.employee_code}) to a
          buyer entity allows them to place orders via the buyer portal.
        </p>

        <label className="block text-sm font-medium text-gray-700 mb-1">
          Buyer Entity
        </label>
        <select
          className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          value={selectedBuyerId}
          onChange={(e) => setSelectedBuyerId(e.target.value)}
        >
          <option value="">— unlink (no buyer) —</option>
          {buyers.map((b) => (
            <option key={b.id} value={b.id}>
              {b.code} — {b.name}
            </option>
          ))}
        </select>

        {error && (
          <p className="mt-2 text-sm text-red-600">{error}</p>
        )}

        <div className="mt-5 flex gap-3 justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm rounded-lg border border-gray-300 text-gray-700 hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            onClick={() => mutation.mutate(selectedBuyerId || null)}
            disabled={mutation.isPending}
            className="px-4 py-2 text-sm rounded-lg bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50"
          >
            {mutation.isPending ? "Saving…" : "Save"}
          </button>
        </div>
      </div>
    </div>
  );
}

export default function UsersPage() {
  const [linkingUser, setLinkingUser] = useState<User | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ["users"],
    queryFn: () => api.get<UsersResponse>("/users?page=1&size=100&active_only=false"),
  });

  const { data: buyersData } = useQuery({
    queryKey: ["buyers-for-link"],
    queryFn: () => api.get<BuyersResponse>("/buyers?page=1&size=200"),
  });

  const buyers = buyersData?.items ?? [];

  return (
    <div className="p-6">
      <PageHeader title="Users" subtitle={data ? `${data.total} users` : undefined} />

      {isLoading ? (
        <Skeleton rows={8} />
      ) : (
        <div className="bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Code</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Name</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Role</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Status</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Buyer Link</th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {(data?.items ?? []).map((u) => {
                const linkedBuyer = buyers.find((b) => b.id === u.buyer_id);
                return (
                  <tr key={u.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-sm font-mono text-gray-700">{u.employee_code}</td>
                    <td className="px-4 py-3 text-sm text-gray-900">{u.name}</td>
                    <td className="px-4 py-3 text-sm">
                      <Badge color={ROLE_COLOR[u.role] ?? "gray"}>{u.role}</Badge>
                    </td>
                    <td className="px-4 py-3 text-sm">
                      <Badge color={u.is_active ? "green" : "red"}>
                        {u.is_active ? "Active" : "Inactive"}
                      </Badge>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600">
                      {u.role === "buyer" ? (
                        linkedBuyer ? (
                          <span className="text-green-700 font-medium">
                            {linkedBuyer.code} — {linkedBuyer.name}
                          </span>
                        ) : (
                          <span className="text-red-500 italic">Not linked</span>
                        )
                      ) : (
                        <span className="text-gray-300">—</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-right">
                      {u.role === "buyer" && (
                        <button
                          onClick={() => setLinkingUser(u)}
                          className="text-xs px-3 py-1 rounded-md border border-blue-300 text-blue-700 hover:bg-blue-50"
                        >
                          {u.buyer_id ? "Change" : "Link Buyer"}
                        </button>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {linkingUser && (
        <LinkBuyerModal
          user={linkingUser}
          buyers={buyers}
          onClose={() => setLinkingUser(null)}
        />
      )}
    </div>
  );
}
