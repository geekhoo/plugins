# MXC .NET SDK and policy reference

Package: `Microsoft.Mxc.Sdk` 1.0.1 on NuGet (targets net8.0; works on net10.0). Native runtime ships
inside the package; no separate install. Namespaces: `Microsoft.Mxc.Sdk`, `Microsoft.Mxc.Sdk.V1`.
Source: https://github.com/microsoft/mxc. For anything below that looks stale, shallow-clone the
repo and read `sdk/dotnet/README.md`, `sdk/dotnet/Microsoft.Mxc.Sdk/V1/ContainerRequest.cs`,
`sdk/dotnet/Microsoft.Mxc.Sdk/V1/ContainerRequestSections.cs`, and `docs/schema.md`. WebFetch of
GitHub tree pages returns partial listings; prefer the clone or raw.githubusercontent.com URLs.

## Entry points (`MxcContainer`, `MxcPlatform`)

| Call | Returns | Notes |
|---|---|---|
| `MxcPlatform.GetPlatformSupport()` | `IsSupported`, `Reason` | |
| `MxcPlatform.GetAvailableBackends()` | backend, tier, capabilities, warnings | |
| `MxcContainer.Probe(request)` | `Tier`, `NeedsDaclAugmentation`, `Warnings`, `Error`, `Probes.*` | Read-only; `Probes.BaseContainerSupportsEnumeratePaths`, `Probes.IsolationSessionAvailable` |
| `MxcContainer.RunAsync(request)` | `ExecutionResult` (`Stdout`, `Stderr`, `ExitCode`, `TimedOut`, `Warnings`) | Run to completion, captured |
| `MxcContainer.SpawnAsync(request)` | `MxcProcess` (`StandardInput/Output/Error` streams, `WaitAsync`, `Kill`) | Streaming stdio |
| `MxcContainer.SpawnWithPty(request, new SpawnWithPtyOptions { Size = new MxcPtySize(rows, cols) })` | `MxcPtyProcess` (`Input`, `Output`, `Resize`) | Windows: IsolationSession only |
| `MxcLifecycle.*` | provision / start / exec / stop / deprovision | Persisted containers (IsolationSession, WSLc) |

Errors surface as `MxcException` with `Code` and `Message`.

## `ContainerRequest`

```csharp
new ContainerRequest(commandLine)        // full Windows command line; quote per CommandLineToArgvW
{
    Containment = new Containment.Process(),              // default: ProcessContainer on Windows
    Filesystem  = new FilesystemPolicy { ReadonlyPaths = { ... }, ReadwritePaths = { ... }, DeniedPaths = { ... } },
    Network     = new NetworkPolicy { Egress = ..., Ingress = ... },
    Ui          = new UiPolicy { Disable = true },         // default true = Win32k syscalls blocked
    WorkingDirectory = @"C:\repos\x",
    Environment = new() { ["KEY"] = "value" },
    InheritDefaultEnvironment = true,                     // layer Environment over the user's profile env block
    TimeoutMs   = 30_000,                                 // null = no timeout
}
```

### Containment choices

| Class | Backend | Policy support | PTY |
|---|---|---|---|
| `Containment.Process` | ProcessContainer (Win), Bubblewrap (Linux), Seatbelt (macOS) | fs + net + ui | No on Windows |
| `Containment.ProcessContainer { Filesystem = new ProcessContainerFilesystemPolicy { EnumeratePaths = { ... } }, Capabilities, CaptureDenials, LearningMode }` | ProcessContainer, explicit | fs + net + ui + enumerate-only paths | No |
| `Containment.IsolationSession` | Separate agent account | None; must declare unrestricted network | Yes |
| `Containment.Wslc { Image, ... }` | WSL container | | |

Tiers on Windows ProcessContainer: **BaseContainer** (Tier 1, OS-enforced, no host changes) or
AppContainer (Tier 2/3; Tier 3 uses temporary DENY ACEs and needs `wxc-host-prep`).

### Filesystem

- Lists default empty; omitted cwd falls back to the first readwrite path, then readonly, then
  the drive root.
- Grant folders, not single files (single-file grants were denied on BaseContainer).
- Never grant a drive root (exposes all children on BaseContainer).
- `%LOCALAPPDATA%` is redirected inside the container: read-write grants there are not writable,
  and the child sees `LOCALAPPDATA=...\Packages\sandbox.{guid}\AC`.

### Network

```csharp
new NetworkPolicy
{
    Egress = new NetworkEgressPolicy
    {
        Default = NetworkAction.Deny,
        // Allow/To/Ports are nullable lists with no initializer: assign new lists, don't use `X = { ... }`.
        Allow = new()
        {
            new NetworkRulePolicy
            {
                To = new() { new NetworkPeerPolicy("198.51.100.0/24") },
                Ports = new() { new NetworkPortPolicy { Protocol = NetworkProtocol.Tcp, Port = 443 } },
            },
        },
    },
    Ingress = new NetworkIngressPolicy { Default = NetworkAction.Deny, HostLoopback = NetworkAction.Deny },
}
```

No hostname or domain allow-lists exist; use CIDR rules or `RuntimeConfig.NetworkProxy` (a
caller-managed proxy, which cannot be combined with direct egress rules). A CIDR allow-list for an
API also needs DNS (UDP/TCP 53 to the resolver) allowed.

### Environment

| `Environment` | `InheritDefaultEnvironment` | Child gets |
|---|---|---|
| null | ignored | backend default (user profile block) |
| `{}` | false | nothing: rejected on ProcessContainer, which requires `SYSTEMROOT` and `LOCALAPPDATA` |
| `{K=V}` | true | default plus K (caller wins) |

IsolationSession always uses the agent account's default environment; set
`InheritDefaultEnvironment = true` when adding variables.

## Debug tooling

- `wxc-exec.exe --debug config.json`: diagnostic output for a JSON request.
- `CaptureDenials = new CaptureDenialsPolicy { Mode = CaptureDenialsMode.Block }` on
  `Containment.ProcessContainer` logs blocked access attempts (see the MXC
  `run-with-logging-access-denied` sample).
- Never use `wxc-exec.exe --audit`: it disables all sandbox security for the workload.
