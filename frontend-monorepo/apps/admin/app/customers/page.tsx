export default function CustomersPage() {
  return (
    <div className="min-h-screen bg-zinc-900 p-6 text-white">
      {/* Header */}
      <div className="mb-6">
        <p className="text-sm text-zinc-500">Operations</p>

        <h1 className="mt-1 text-2xl font-semibold">
          Customers
        </h1>

        <p className="mt-1 text-sm text-zinc-500">
          Manage customer accounts and call activity.
        </p>
      </div>

      {/* Search and actions */}
      <div className="mb-5 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <input
          type="text"
          placeholder="Search customers..."
          className="h-10 rounded-lg border border-zinc-800 bg-zinc-950 px-4 text-sm text-white outline-none placeholder:text-zinc-600 focus:border-zinc-600"
        />

        <button
          type="button"
          className="h-10 rounded-lg bg-white px-4 text-sm font-medium text-black hover:bg-zinc-200"
        >
          Add Customer
        </button>
      </div>

      {/* Customer table */}
      <div className="overflow-hidden rounded-xl border border-zinc-800 bg-zinc-950">
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead className="border-b border-zinc-800 bg-zinc-900">
              <tr>
                <th className="px-5 py-4 text-xs font-medium uppercase tracking-wider text-zinc-500">
                  Customer
                </th>

                <th className="px-5 py-4 text-xs font-medium uppercase tracking-wider text-zinc-500">
                  Plan
                </th>

                <th className="px-5 py-4 text-xs font-medium uppercase tracking-wider text-zinc-500">
                  Calls
                </th>

                <th className="px-5 py-4 text-xs font-medium uppercase tracking-wider text-zinc-500">
                  Status
                </th>

                <th className="px-5 py-4 text-xs font-medium uppercase tracking-wider text-zinc-500">
                  Action
                </th>
              </tr>
            </thead>

            <tbody className="divide-y divide-zinc-800">
              <CustomerRow
                name="Acme Corporation"
                email="admin@acme.com"
                plan="Enterprise"
                calls="1,248"
                status="Active"
              />

              <CustomerRow
                name="TechFlow"
                email="hello@techflow.com"
                plan="Pro"
                calls="842"
                status="Active"
              />

              <CustomerRow
                name="Nova Solutions"
                email="contact@nova.com"
                plan="Starter"
                calls="326"
                status="Active"
              />

              <CustomerRow
                name="Bright Labs"
                email="admin@brightlabs.com"
                plan="Pro"
                calls="591"
                status="Suspended"
              />
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function CustomerRow({
  name,
  email,
  plan,
  calls,
  status,
}: {
  name: string;
  email: string;
  plan: string;
  calls: string;
  status: string;
}) {
  const active = status === "Active";

  return (
    <tr className="hover:bg-zinc-900">
      <td className="px-5 py-4">
        <div className="font-medium text-white">{name}</div>
        <div className="mt-1 text-xs text-zinc-500">{email}</div>
      </td>

      <td className="px-5 py-4 text-sm text-zinc-300">
        {plan}
      </td>

      <td className="px-5 py-4 text-sm text-zinc-300">
        {calls}
      </td>

      <td className="px-5 py-4">
        <div className="flex items-center gap-2">
          <span
            className={`h-2 w-2 rounded-full ${
              active ? "bg-green-500" : "bg-yellow-500"
            }`}
          />

          <span
            className={`text-xs ${
              active ? "text-green-400" : "text-yellow-400"
            }`}
          >
            {status}
          </span>
        </div>
      </td>

      <td className="px-5 py-4">
        <button
          type="button"
          className="text-xs text-zinc-400 hover:text-white"
        >
          View
        </button>
      </td>
    </tr>
  );
}