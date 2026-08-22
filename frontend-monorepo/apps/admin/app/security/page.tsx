export default function SecurityPage() {
  return (
    <div className="min-h-screen bg-zinc-900 p-6 text-white">
      {/* Header */}
      <div className="mb-6">
        <p className="text-sm text-zinc-500">Administration</p>

        <h1 className="mt-1 text-2xl font-semibold">
          Security
        </h1>

        <p className="mt-1 text-sm text-zinc-500">
          Monitor access, authentication, and platform security.
        </p>
      </div>

      {/* Security overview */}
      <div className="grid gap-4 md:grid-cols-3">
        <SecurityCard
          title="Security Status"
          value="Protected"
          description="No active threats detected"
        />

        <SecurityCard
          title="Admin Sessions"
          value="12"
          description="Active administrator sessions"
        />

        <SecurityCard
          title="Failed Attempts"
          value="3"
          description="In the last 24 hours"
        />
      </div>

      {/* Authentication */}
      <div className="mt-6 grid gap-4 lg:grid-cols-2">
        <div className="rounded-xl border border-zinc-800 bg-zinc-950 p-5">
          <p className="text-xs uppercase tracking-wider text-zinc-500">
            Authentication
          </p>

          <div className="mt-6 space-y-5">
            <SecurityRow
              name="Supabase Authentication"
              status="Enabled"
            />

            <SecurityRow
              name="JWT Verification"
              status="Enabled"
            />

            <SecurityRow
              name="Role Based Access"
              status="Enabled"
            />

            <SecurityRow
              name="Bearer Token Protection"
              status="Enabled"
            />
          </div>
        </div>

        {/* Access control */}
        <div className="rounded-xl border border-zinc-800 bg-zinc-950 p-5">
          <p className="text-xs uppercase tracking-wider text-zinc-500">
            Access Control
          </p>

          <div className="mt-6 space-y-5">
            <AccessRow
              role="Super Admin"
              access="Full Access"
            />

            <AccessRow
              role="Admin"
              access="Management"
            />

            <AccessRow
              role="Support"
              access="Read Only"
            />
          </div>
        </div>
      </div>

      {/* Recent security events */}
      <div className="mt-6 overflow-hidden rounded-xl border border-zinc-800 bg-zinc-950">
        <div className="border-b border-zinc-800 p-5">
          <h2 className="font-semibold">
            Recent Security Events
          </h2>

          <p className="mt-1 text-xs text-zinc-500">
            Latest authentication and access activity.
          </p>
        </div>

        <div className="divide-y divide-zinc-800">
          <SecurityEvent
            event="Admin login"
            user="admin@call.ai"
            time="2 minutes ago"
            type="Success"
          />

          <SecurityEvent
            event="Role updated"
            user="support@call.ai"
            time="18 minutes ago"
            type="Success"
          />

          <SecurityEvent
            event="Failed login attempt"
            user="unknown"
            time="42 minutes ago"
            type="Warning"
          />

          <SecurityEvent
            event="Session revoked"
            user="admin@call.ai"
            time="1 hour ago"
            type="Success"
          />
        </div>
      </div>

      {/* Warning */}
      <div className="mt-6 rounded-xl border border-yellow-900 bg-yellow-950/30 p-5">
        <div className="flex gap-3">
          <span className="text-yellow-400">⚠</span>

          <div>
            <p className="font-medium text-yellow-300">
              Sensitive operations
            </p>

            <p className="mt-1 text-sm text-yellow-500/80">
              Destructive administrative actions require
              additional confirmation.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

function SecurityCard({
  title,
  value,
  description,
}: {
  title: string;
  value: string;
  description: string;
}) {
  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-950 p-5">
      <p className="text-xs uppercase tracking-wider text-zinc-500">
        {title}
      </p>

      <p className="mt-3 text-2xl font-bold">
        {value}
      </p>

      <p className="mt-2 text-xs text-zinc-500">
        {description}
      </p>
    </div>
  );
}

function SecurityRow({
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

function AccessRow({
  role,
  access,
}: {
  role: string;
  access: string;
}) {
  return (
    <div className="flex items-center justify-between border-b border-zinc-800 pb-4 last:border-0 last:pb-0">
      <span className="text-sm text-zinc-300">
        {role}
      </span>

      <span className="rounded-full border border-zinc-700 px-3 py-1 text-xs text-zinc-400">
        {access}
      </span>
    </div>
  );
}

function SecurityEvent({
  event,
  user,
  time,
  type,
}: {
  event: string;
  user: string;
  time: string;
  type: "Success" | "Warning";
}) {
  const isWarning = type === "Warning";

  return (
    <div className="flex items-center justify-between gap-4 px-5 py-4">
      <div className="flex items-center gap-3">
        <span
          className={`h-2 w-2 rounded-full ${
            isWarning ? "bg-yellow-500" : "bg-green-500"
          }`}
        />

        <div>
          <p className="text-sm text-white">
            {event}
          </p>

          <p className="mt-1 text-xs text-zinc-500">
            {user}
          </p>
        </div>
      </div>

      <div className="text-right">
        <p
          className={`text-xs ${
            isWarning ? "text-yellow-400" : "text-green-400"
          }`}
        >
          {type}
        </p>

        <p className="mt-1 text-[10px] text-zinc-600">
          {time}
        </p>
      </div>
    </div>
  );
}