export default function PulsePage() {
  return (
    <div className="min-h-screen bg-zinc-900 p-6 text-white">
      <div className="mb-6">
        <p className="text-sm text-zinc-500">Operations</p>
        <h1 className="mt-1 text-2xl font-semibold">
          System Pulse
        </h1>
        <p className="mt-1 text-sm text-zinc-500">
          Real-time overview of the AI call platform.
        </p>
      </div>

      {/* Metrics */}
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
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

        <MetricCard
          title="Avg. Latency"
          value="420 ms"
          status="Healthy"
        />

        <MetricCard
          title="Success Rate"
          value="98.7%"
          status="Healthy"
        />
      </div>

      {/* Main panels */}
      <div className="mt-6 grid gap-4 lg:grid-cols-3">
        {/* Traffic */}
        <div className="rounded-xl border border-zinc-800 bg-zinc-950 p-5 lg:col-span-2">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs uppercase tracking-wider text-zinc-500">
                Live Call Traffic
              </p>

              <p className="mt-2 text-3xl font-bold">
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

          <div className="mt-8 flex h-40 items-end gap-2 rounded-lg bg-zinc-900 p-4">
            {[30, 45, 38, 55, 48, 70, 62, 80, 68, 92, 75, 88].map(
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

          <div className="mt-6 space-y-5">
            <HealthRow name="API" />
            <HealthRow name="Voice Engine" />
            <HealthRow name="Database" />
            <HealthRow name="LLM Providers" />
            <HealthRow name="Telecom" />
          </div>
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