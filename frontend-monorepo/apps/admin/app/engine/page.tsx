export default function EnginePage() {
  return (
    <div className="min-h-screen bg-zinc-900 p-6 text-white">
      {/* Header */}
      <div className="mb-6">
        <p className="text-sm text-zinc-500">Operations</p>

        <h1 className="mt-1 text-2xl font-semibold">
          AI Engine
        </h1>

        <p className="mt-1 text-sm text-zinc-500">
          Monitor AI providers, models, and engine performance.
        </p>
      </div>

      {/* Provider summary */}
      <div className="grid gap-4 md:grid-cols-3">
        <MetricCard
          title="Active Providers"
          value="4"
          status="Online"
        />

        <MetricCard
          title="Requests / Min"
          value="1,842"
          status="+8.4%"
        />

        <MetricCard
          title="Avg. Latency"
          value="382 ms"
          status="Healthy"
        />
      </div>

      {/* Providers */}
      <div className="mt-6 rounded-xl border border-zinc-800 bg-zinc-950">
        <div className="border-b border-zinc-800 p-5">
          <h2 className="font-semibold">AI Providers</h2>

          <p className="mt-1 text-xs text-zinc-500">
            Current provider status and usage.
          </p>
        </div>

        <div className="divide-y divide-zinc-800">
          <ProviderRow
            name="OpenAI"
            model="GPT"
            requests="842"
            latency="320 ms"
          />

          <ProviderRow
            name="Google Gemini"
            model="Gemini"
            requests="516"
            latency="365 ms"
          />

          <ProviderRow
            name="Anthropic"
            model="Claude"
            requests="318"
            latency="410 ms"
          />

          <ProviderRow
            name="Local Engine"
            model="Kokoro"
            requests="166"
            latency="285 ms"
          />
        </div>
      </div>

      {/* Engine health */}
      <div className="mt-6 grid gap-4 md:grid-cols-2">
        <div className="rounded-xl border border-zinc-800 bg-zinc-950 p-5">
          <p className="text-xs uppercase tracking-wider text-zinc-500">
            Engine Status
          </p>

          <div className="mt-5">
            <div className="flex items-center gap-3">
              <span className="h-3 w-3 rounded-full bg-green-500" />

              <span className="font-medium">
                All engines operational
              </span>
            </div>

            <p className="mt-3 text-sm text-zinc-500">
              No provider failures detected.
            </p>
          </div>
        </div>

        <div className="rounded-xl border border-zinc-800 bg-zinc-950 p-5">
          <p className="text-xs uppercase tracking-wider text-zinc-500">
            Failover
          </p>

          <div className="mt-5 flex items-center justify-between">
            <div>
              <p className="font-medium">
                Automatic failover
              </p>

              <p className="mt-1 text-xs text-zinc-500">
                Backup provider routing enabled
              </p>
            </div>

            <span className="rounded-full border border-green-900 bg-green-950 px-3 py-1 text-xs text-green-400">
              Enabled
            </span>
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

function ProviderRow({
  name,
  model,
  requests,
  latency,
}: {
  name: string;
  model: string;
  requests: string;
  latency: string;
}) {
  return (
    <div className="flex flex-col gap-4 px-5 py-5 sm:flex-row sm:items-center sm:justify-between">
      <div className="flex items-center gap-3">
        <span className="h-2.5 w-2.5 rounded-full bg-green-500" />

        <div>
          <p className="font-medium">{name}</p>

          <p className="mt-1 text-xs text-zinc-500">
            {model}
          </p>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-8 sm:flex sm:items-center">
        <div>
          <p className="text-[10px] uppercase tracking-wider text-zinc-600">
            Requests
          </p>

          <p className="mt-1 text-sm text-zinc-300">
            {requests}
          </p>
        </div>

        <div>
          <p className="text-[10px] uppercase tracking-wider text-zinc-600">
            Latency
          </p>

          <p className="mt-1 text-sm text-zinc-300">
            {latency}
          </p>
        </div>

        <span className="hidden rounded-full border border-green-900 bg-green-950 px-3 py-1 text-xs text-green-400 sm:inline-block">
          Online
        </span>
      </div>
    </div>
  );
}