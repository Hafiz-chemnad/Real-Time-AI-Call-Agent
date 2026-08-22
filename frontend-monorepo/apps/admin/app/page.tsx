import CmdKSearch from "@/components/layout/CmdKSearch";
export default function Home() {
  return (
    <div className="min-h-screen bg-zinc-900 text-white">
      {/* Header */}
      <header className="flex h-16 items-center justify-between border-b border-zinc-800 px-6">
        <div>
          <h1 className="text-xl font-semibold">Command Center</h1>
          <p className="text-xs text-zinc-500">
            Real-Time AI Call Agent
          </p>
        </div>

        <div className="flex items-center gap-4">
          <CmdKSearch />
          {/* System status */}
          <div className="flex items-center gap-2 rounded-full border border-zinc-700 px-3 py-2">
            <span className="h-2 w-2 rounded-full bg-green-500" />
            <span className="text-xs text-zinc-300">
              All Systems Operational
            </span>
          </div>

          {/* Admin */}
          <div className="flex h-9 w-9 items-center justify-center rounded-full bg-zinc-800 text-sm font-semibold">
            A
          </div>
        </div>
      </header>

      {/* Main dashboard */}
      <main className="p-6">
        <div className="mb-6">
          <p className="text-sm text-zinc-500">Overview</p>

          <h2 className="mt-1 text-2xl font-semibold">
            System Pulse
          </h2>
        </div>

        {/* Financial cards */}
        <div className="grid gap-4 md:grid-cols-3">
          <MetricCard
            label="Live MRR"
            value="$24,820"
            change="+12.4%"
          />

          <MetricCard
            label="Twilio Charges"
            value="$4,280"
            change="+4.8%"
          />

          <MetricCard
            label="LLM Token Expenses"
            value="$1,940"
            change="-8.2%"
          />
        </div>

        {/* Traffic + Health */}
        <div className="mt-6 grid gap-4 lg:grid-cols-3">
          {/* Live Traffic */}
          <div className="rounded-xl border border-zinc-800 bg-zinc-950 p-5 lg:col-span-2">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs uppercase tracking-wider text-zinc-500">
                  Live Traffic
                </p>

                <p className="mt-2 text-4xl font-bold">
                  128
                </p>

                <p className="mt-1 text-sm text-zinc-500">
                  active calls right now
                </p>
              </div>

              <div className="flex items-center gap-2 rounded-full border border-green-900 bg-green-950 px-3 py-2">
                <span className="h-2 w-2 rounded-full bg-green-500" />

                <span className="text-xs text-green-400">
                  Healthy
                </span>
              </div>
            </div>

            {/* Simple traffic chart */}
            <div className="mt-8 flex h-32 items-end gap-2 rounded-lg bg-zinc-900 p-4">
              {[35, 50, 42, 65, 55, 75, 60, 85, 70, 92, 78, 88].map(
                (height, index) => (
                  <div
                    key={index}
                    className="flex-1 rounded-t bg-zinc-700"
                    style={{ height: `${height}%` }}
                  />
                )
              )}
            </div>
          </div>

          {/* Platform Health */}
          <div className="rounded-xl border border-zinc-800 bg-zinc-950 p-5">
            <p className="text-xs uppercase tracking-wider text-zinc-500">
              Platform Health
            </p>

            <div className="mt-5 space-y-5">
              <HealthRow name="API" />
              <HealthRow name="Voice Engine" />
              <HealthRow name="Database" />
              <HealthRow name="LLM Providers" />
              <HealthRow name="Telecom" />
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

/* Financial metric card */
function MetricCard({
  label,
  value,
  change,
}: {
  label: string;
  value: string;
  change: string;
}) {
  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-950 p-5">
      <p className="text-xs uppercase tracking-wider text-zinc-500">
        {label}
      </p>

      <div className="mt-3 flex items-end justify-between">
        <p className="text-3xl font-bold">{value}</p>

        <span className="text-xs text-zinc-400">
          {change}
        </span>
      </div>
    </div>
  );
}

/* Health status row */
function HealthRow({ name }: { name: string }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-sm text-zinc-300">
        {name}
      </span>

      <div className="flex items-center gap-2">
        <span className="h-2 w-2 rounded-full bg-green-500" />

        <span className="text-xs text-green-400">
          Healthy
        </span>
      </div>
    </div>
  );
}