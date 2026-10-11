import { clsx } from "clsx";
import EmptyState from "./EmptyState";

interface Column<T> {
  key: string;
  header: string;
  render?: (row: T) => React.ReactNode;
  className?: string;
}

interface TableProps<T> {
  columns: Column<T>[];
  data: T[];
  rowKey: (row: T) => string | number;
  onRowClick?: (row: T) => void;
  emptyMessage?: string;
}

export default function Table<T>({ columns, data, rowKey, onRowClick, emptyMessage = "No data" }: TableProps<T>) {
  return (
    <div className="overflow-x-auto">
      <table className="min-w-full text-sm">
        <thead>
          <tr className="border-b border-gray-200 bg-gray-50/80">
            {columns.map((col) => (
              <th
                key={col.key}
                className={clsx("table-header-cell whitespace-nowrap", col.className)}
              >
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {data.length === 0 ? (
            <tr>
              <td colSpan={columns.length}>
                <EmptyState title={emptyMessage} />
              </td>
            </tr>
          ) : (
            data.map((row) => (
              <tr
                key={rowKey(row)}
                className={clsx("transition-colors", onRowClick && "cursor-pointer hover:bg-gray-50")}
                onClick={() => onRowClick?.(row)}
              >
                {columns.map((col) => (
                  <td key={col.key} className={clsx("px-4 py-3 text-gray-700", col.className)}>
                    {col.render ? col.render(row) : String((row as Record<string, unknown>)[col.key] ?? "")}
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}
