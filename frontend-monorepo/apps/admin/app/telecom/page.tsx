export default function TelecomPage() {
  return (
    <div className="min-h-screen bg-zinc-900 p-6 text-white">
      {/* Header */}
      <div className="mb-6">
        <p className="text-sm text-zinc-500">Infrastructure</p>

        <h1 className="mt-1 text-2xl font-semibold">
          Telecom
        </h1>

        <p className="mt-1 text-sm text-zinc-500">
          Monitor phone numbers, calls, and telecom infrastructure.
        </p>
      </div>

      {/* Metrics */}
      <div className="grid gap-4 md:grid-cols-3">
        <MetricCard
          title="Active Numbers"
          value="248"
          status="Healthy"
        />

        <MetricCard
          title="Active Calls"
          value="128"
          status="Live"
        />

        <MetricCard
          title="Calls Today"
          value="2,481"
          status="+12.4%"
        />
      </div>

      {/* Telecom status */}
      <div className="mt-6 grid gap-4 lg:grid-cols-2">
        <div className="rounded-xl border border-zinc-800 bg-zinc-950 p-5">
          <p className="text-xs uppercase tracking-wider text-zinc-500">
            Voice Infrastructure
          </p>

          <div className="mt-6 space-y-5">
            <StatusRow name="Twilio" status="Operational" />
            <StatusRow name="Voice Gateway" status="Operational" />
            <StatusRow name="Call Routing" status="Operational" />
            <StatusRow name="WebSocket Voice" status="Operational" />
          </div>
        </div>

        {/* Call activity */}
        <div className="rounded-xl border border-zinc-800 bg-zinc-950 p-5">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs uppercase tracking-wider text-zinc-500">
                Current Call Activity
              </p>

              <p className="mt-3 text-4xl font-bold">
                128
              </p>

              <p className="mt-1 text-sm text-zinc-500">
                active calls
              </p>
            </div>

            <div className="flex items-center gap-2 rounded-full border border-green-900 bg-green-950 px-3 py-2">
              <span className="h-2 w-2 rounded-full bg-green-500" />

              <span className="text-xs text-green-400">
                Live
              </span>
            </div>
          </div>

          <div className="mt-8 space-y-4">
            <ProgressRow
              label="Inbound"
              value="72"
              percentage={56}
            />

            <ProgressRow
              label="Outbound"
              value="56"
              percentage={44}
            />
          </div>
        </div>
      </div>

      {/* Phone numbers */}
      <div className="mt-6 overflow-hidden rounded-xl border border-zinc-800 bg-zinc-950">
        <div className="border-b border-zinc-800 p-5">
          <h2 className="font-semibold">
            Phone Numbers
          </h2>

          <p className="mt-1 text-xs text-zinc-500">
            Recently active telecom numbers.
          </p>
        </div>

        <div className="divide-y divide-zinc-800">
          <NumberRow
            number="+1 (415) 555-0124"
            customer="Acme Corporation"
            calls="342"
          />

          <NumberRow
            number="+1 (415) 555-0188"
            customer="TechFlow"
            calls="218"
          />

          <NumberRow
            number="+1 (415) 555-0231"
            customer="Nova Solutions"
            calls="156"
          />
        </div>
      </div>
    </div>
  );
}

function MetricCard({
  title,
  value,
  status,
}: {
  title: string;
  value: string;
  status: string;
}) {
  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-950 p-5">
      <p className="text-xs uppercase tracking-wider text-zinc-500">
        {title}
      </p>

      <div className="mt-3 flex items-end justify-between">
        <p className="text-2xl font-bold">{value}</p>

        <span className="text-xs text-zinc-400">
          {status}
        </span>
      </div>
    </div>
  );
}

function StatusRow({
  name,
  status,
}: {
  name: string;
  status: string;
}) {
  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-3">
        <span className="h-2.5 w-2.5 rounded-full bg-green-500" />

        <span className="text-sm text-zinc-300">
          {name}
        </span>
      </div>

      <span className="text-xs text-green-400">
        {status}
      </span>
    </div>
  );
}

function ProgressRow({
  label,
  value,
  percentage,
}: {
  label: string;
  value: string;
  percentage: number;
}) {
  return (
    <div>
      <div className="mb-2 flex justify-between text-xs">
        <span className="text-zinc-400">{label}</span>

        <span className="text-zinc-500">
          {value} calls
        </span>
      </div>

      <div className="h-2 overflow-hidden rounded-full bg-zinc-800">
        <div
          className="h-full rounded-full bg-zinc-500"
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
}

function NumberRow({
  number,
  customer,
  calls,
}: {
  number: string;
  customer: string;
  calls: string;
}) {
  return (
    <div className="flex items-center justify-between px-5 py-4">
      <div>
        <p className="font-mono text-sm text-white">
          {number}
        </p>

        <p className="mt-1 text-xs text-zinc-500">
          {customer}
        </p>
      </div>

      <div className="text-right">
        <p className="text-sm text-zinc-300">
          {calls}
        </p>

        <p className="text-[10px] uppercase text-zinc-600">
          calls
        </p>
      </div>
    </div>
  );
}