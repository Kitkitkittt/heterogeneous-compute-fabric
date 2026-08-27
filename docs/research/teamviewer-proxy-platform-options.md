# Managed proxy options for blocked TeamViewer client networks

Status: decision evidence

Evidence date: 2026-08-27

Scope: an authorized Windows TeamViewer client on a network that blocks direct TeamViewer traffic and may also block overlay-network clients. This note compares ways to expose a standard authenticated HTTP `CONNECT` forward proxy without publishing Private Operations Overlay data.

## Decision

Keep the **existing cloud-node forward proxy** as the first bounded pilot when its public listener can be restricted to one approved source address and protected with proxy authentication. It is the smallest change and the only already-available option that accepts TeamViewer's normal proxy configuration without extra client software.

If a separate managed host is preferable, **Fly.io with a dedicated IPv4 address and raw TCP pass-through** is the practical self-service alternative. It can expose an authenticated proxy on TCP 443 without a client helper, but it adds another public service, billable compute, and application ownership.

Use **Cloudflare Tunnel plus Access** only when installing and supervising `cloudflared` or the Cloudflare One Client on the blocked computer is acceptable. It avoids opening an origin port, but it is not clientless and Cloudflare warns that the WebSocket-based `cloudflared access` path can close unexpectedly. This makes it a weaker fit for unattended TeamViewer.

Do not build this as a Vercel Function, Vercel Edge Function, or Cloudflare Worker. Cloudflare Spectrum is technically suitable but commercially disproportionate: generic TCP is an Enterprise paid add-on.

No option should be deployed unless the network owner authorizes this remote-access path.

## Required transport contract

TeamViewer exposes manual proxy fields for a proxy address, port, username, and password. Its current network documentation says TeamViewer attempts outbound TCP/UDP 5938 first, TCP 443 second, and TCP 80 last, and that its server addresses are dynamic under `*.teamviewer.com`. A forward proxy therefore needs to accept the client's proxy connection, process HTTP `CONNECT`, and open allowed outbound TCP connections to the TeamViewer destinations. [TeamViewer proxy settings](https://dl.teamviewer.com/docs/en/v15/TeamViewer-Manual-Remote-Control-en.pdf) and [TeamViewer ports and URLs](https://www.teamviewer.com/en-us/global/support/knowledge-base/teamviewer-remote/troubleshooting/ports-used-by-teamviewer/)

For this comparison, an option is **clientless** only when TeamViewer can point directly at the proxy host and port. A custom WebSocket, VPN, tunnel, or local-port helper does not satisfy that contract even if it can carry the same bytes after additional software is installed.

## Evidence matrix

| Option | Ordinary inbound `CONNECT` / raw TCP | Client helper | TCP 443 viability | Authentication boundary | Plan and cost shape | Assessment |
| --- | --- | --- | --- | --- | --- | --- |
| Existing cloud-node public proxy | Yes; the proxy daemon owns the public listener | None | Yes if 443 is free on that public address; otherwise use a separate address or a tested permitted port | Proxy username/password, one-source CIDR allowlist, destination and CONNECT-port ACLs | Existing node cost plus its normal egress; operator owns patching, logs, availability, and abuse response | **Recommended bounded pilot** |
| Vercel Functions / Edge runtime | No documented raw inbound socket listener or TCP pass-through; ingress is routed as HTTP requests through Vercel's CDN | A custom WebSocket tunnel would require a new client and would not be TeamViewer's standard proxy | 443 reaches Vercel's HTTP/TLS edge, not a user-owned raw TCP listener | Custom application auth only | Hobby is $0 for personal use; Pro starts at $20/month, but neither plan changes the transport mismatch | **Reject** |
| Cloudflare Workers TCP sockets | No. Workers `connect()` creates outbound sockets; Cloudflare explicitly says inbound TCP, including HTTP `CONNECT`, is not currently possible | A custom WebSocket client would be required | 443 reaches the Worker HTTP endpoint; it does not expose raw TCP `CONNECT` ingress | Custom Worker auth, if a custom protocol were built | Free plan exists; Workers Paid starts at $5/month, but pricing does not remove the ingress limitation | **Reject** |
| Cloudflare Tunnel + Access | Yes only through the non-HTTP Tunnel path, which streams TCP over WebSockets | **Required:** `cloudflared` on origin and client, or Cloudflare One Client for client-to-Tunnel routing | The client-side helper uses the Cloudflare hostname over web-allowed connectivity; the local TeamViewer proxy target is a loopback port | Access SSO for interactive users; service credentials require lifecycle and secret handling | Tunnel is available on all plans; Access has a free plan for teams under 50, then published per-user or contract pricing | **Conditional diagnostic option; weak unattended fit** |
| Cloudflare Spectrum | Yes. Spectrum is Cloudflare's Layer 4 TCP/UDP reverse proxy | None | Yes; Spectrum supports all TCP ports and can relay TCP 443 to an origin | Origin proxy authentication plus Spectrum/IP access controls as entitled | Generic TCP is an Enterprise paid add-on; pricing is contractual rather than a low-cost self-service proxy | **Technically valid, commercially reject for this scope** |
| Fly.io Machine + dedicated IPv4 | Yes. Fly Proxy can pass TCP through unchanged when no protocol handler is configured | None | Yes on a dedicated IPv4 with raw TCP pass-through | Authentication and destination ACLs in the proxy application; Fly services are default-deny until exposed | Usage-based Machine, $2/month dedicated IPv4, and egress; no permanent free tier | **Best self-service managed-host alternative** |

## Platform findings

### Vercel Functions and Edge runtime

Vercel documents Functions as HTTP request handlers served through its CDN. The Edge runtime exposes `fetch`, `Request`, `Response`, and streams, but not a raw TCP listener API; it must begin a response within 25 seconds and can stream for up to 300 seconds. Node Functions have broader outbound API coverage, but each inbound request is still a Function invocation and has a maximum duration. [Vercel Functions](https://vercel.com/docs/functions), [Vercel runtimes](https://vercel.com/docs/functions/runtimes), [Vercel Edge runtime](https://vercel.com/docs/functions/runtimes/edge), and [Vercel Function limits](https://vercel.com/docs/functions/limitations)

Vercel added inbound WebSocket support in public beta in June 2026, but a WebSocket endpoint is not an HTTP forward-proxy endpoint. TeamViewer would need a separate local program to translate its proxy traffic into that custom WebSocket protocol, and the connection remains pinned to a Function and closes at the Function's maximum duration. [Vercel WebSocket public beta](https://vercel.com/changelog/websocket-support-is-now-in-public-beta) and [Vercel WebSocket guide](https://vercel.com/kb/guide/real-time-chat-websockets)

**Inference from the documented ingress model:** Vercel does not offer a supported, clientless way to bind a raw TCP port or preserve a `CONNECT` tunnel as an ordinary forward proxy. Hobby at $0 and Pro at $20/month do not change that. [Vercel pricing](https://vercel.com/pricing)

### Cloudflare Workers TCP sockets

Cloudflare Workers exposes `connect()` for **outbound** TCP connections. The current runtime documentation is explicit that a Worker cannot accept an inbound TCP connection and names HTTP `CONNECT` as an unsupported example. [Cloudflare Workers TCP sockets](https://developers.cloudflare.com/workers/runtime-apis/tcp-sockets/)

A Worker can receive HTTP or WebSocket traffic on 443, but TeamViewer is not a custom Worker WebSocket client. Building a loopback translator on Windows would reintroduce the client-helper dependency and a custom protocol, with no advantage over the supported Tunnel client. Workers Free permits 100,000 requests/day; Workers Paid has a $5/month minimum, but the plan limits do not add inbound TCP. [Cloudflare Workers limits](https://developers.cloudflare.com/workers/platform/limits/) and [Cloudflare Workers pricing](https://developers.cloudflare.com/workers/platform/pricing/)

### Cloudflare Tunnel plus Access

Cloudflare Tunnel is attractive on the origin side because `cloudflared` makes outbound connections and requires no public origin listener. Tunnel is available on all plans. [Cloudflare Tunnel](https://developers.cloudflare.com/tunnel/)

The important limitation is on the client side. Cloudflare's published-application protocol table says non-HTTP services require client-side `cloudflared`; arbitrary TCP is streamed over a WebSocket. The documented flow runs `cloudflared access tcp` on the user device, opens a local port, and points the application at that port. [Tunnel published-application protocols](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/routing-to-tunnel/protocols/) and [Access arbitrary TCP](https://developers.cloudflare.com/cloudflare-one/access-controls/applications/non-http/cloudflared-authentication/arbitrary-tcp/)

Publishing the proxy as an ordinary HTTP Tunnel application does not avoid that helper: Cloudflare's normal HTTP reverse proxy restricts the `CONNECT` method, so a forward-proxy tunnel cannot be treated like a regular website route. [Cloudflare traffic flow and restricted HTTP methods](https://developers.cloudflare.com/fundamentals/concepts/traffic-flow-cloudflare/)

The Access flow gives useful identity controls, and the free plan is positioned for teams under 50 users. However, the default client flow opens a browser for SSO. Cloudflare also states that `cloudflared` authentication relies on WebSockets, that persistent connections may close unexpectedly, and that automated/long-lived use should prefer service authentication or WARP-to-Tunnel routing. That makes this path useful for a controlled diagnostic session but a poor default for an unattended TeamViewer service unless the helper, credentials, restart behavior, and token rotation are deliberately operated. [Cloudflare client-side `cloudflared`](https://developers.cloudflare.com/cloudflare-one/access-controls/applications/non-http/cloudflared-authentication/), [Cloudflare service tokens](https://developers.cloudflare.com/cloudflare-one/access-controls/service-credentials/service-tokens/), and [Cloudflare Access pricing](https://www.cloudflare.com/sase/products/access/)

### Cloudflare Spectrum

Spectrum is the Cloudflare product that actually matches the transport: it is a global Layer 4 TCP/UDP proxy, supports all TCP ports, and can relay TCP 443 to an origin proxy. It does not require a TeamViewer-side helper. [Spectrum configuration options](https://developers.cloudflare.com/spectrum/reference/configuration-options/)

The commercial boundary rules it out here. Cloudflare's current plan table marks generic TCP as unavailable on Free, Pro, and Business and as a paid add-on on Enterprise. Pro and Business only include selected named protocols, not arbitrary forward-proxy TCP. [Spectrum protocols by plan](https://developers.cloudflare.com/spectrum/protocols-per-plan/) and [Spectrum getting started](https://developers.cloudflare.com/spectrum/get-started/)

Spectrum also does not eliminate the origin proxy. Authentication still belongs at the proxy application, with IP access controls as an additional layer where entitled. It is reasonable only if an existing Enterprise agreement already includes Spectrum and the organization wants Cloudflare DDoS protection and edge ingress for a broader service.

### Fly.io raw TCP service

Fly.io documents handler-free TCP pass-through: when a service port has no handler, Fly Proxy forwards the TCP connection to the application unchanged. It also documents dedicated IPv4 as the choice for non-HTTP protocols and raw TCP, because shared IPv4 routing depends on HTTP `Host` or TLS SNI. A plaintext forward-proxy `CONNECT` stream must therefore use a dedicated IPv4 rather than assuming that shared IPv4 plus port 443 is sufficient. [Fly.io public network services](https://fly.io/docs/networking/services/) and [Fly.io TCP troubleshooting](https://fly.io/docs/getting-started/troubleshooting/)

A small Machine can run Tinyproxy, Squid, or another maintained forward proxy. Configure TCP 443 with no Fly TLS/HTTP handlers so the application receives the client's proxy protocol unchanged. Authentication and destination restrictions remain application responsibilities; the Fly service declaration is default-deny until a service port is exposed, but once exposed it is a public endpoint. [Fly.io app configuration](https://fly.io/docs/reference/configuration/) and [Fly.io default-deny service model](https://fly.io/docs/networking/services/)

Fly.io charges usage rather than offering a permanent free tier. Its published table currently puts the smallest 256 MB shared-CPU Machine at roughly $1.94-$3.14/month depending on region, a dedicated IPv4 at $2/month, and Asia-Pacific public egress at $0.04/GB. All regular organizations require a card on file. This makes an always-on one-Machine proxy a low-single-digit monthly service before egress, not a free endpoint. [Fly.io resource pricing](https://fly.io/docs/about/pricing/) and [Fly.io cost management](https://fly.io/docs/about/cost-management/)

## Security and operational guardrails

A forward proxy must never be deployed as an unauthenticated open relay. For either the existing cloud node or Fly.io:

1. require a unique proxy username and high-entropy password; store it in the approved credential store, not Git;
2. restrict ingress to the approved source `/32` when the client egress address is stable;
3. restrict `CONNECT` destination ports to the TeamViewer-required set and restrict destinations to the TeamViewer domains and any separately verified UI/SSO dependencies;
4. rate-limit connection attempts and retain bounded connection metadata without payload capture;
5. bind no administrative interface to the public listener;
6. use a dedicated public address for TCP 443 if another service already owns 443; do not replace or multiplex a production service without a separate design and test;
7. set an expiry date for the exception and rotate or revoke proxy credentials immediately after the pilot;
8. verify the organization's remote-access and acceptable-use policy before activation.

Source-IP allowlisting alone is insufficient when the address can change or is shared by many users. Authentication alone is also insufficient for a public proxy because leaked credentials can turn it into an abuse relay. Use both where possible.

## Bounded pilot

No live change is authorized by this research note. If the network owner approves a pilot, use the following gates:

1. **Confirm the block and authority.** Record the approved client, source egress address, owner, test window, and rollback owner. Confirm that ordinary outbound HTTPS to the candidate endpoint is permitted.
2. **Choose one path.** Start with the existing cloud node. Use Fly.io only if separating the endpoint materially reduces operational risk. Do not run multiple public proxies during the first test.
3. **Deploy fail-closed.** Require proxy authentication, one-source ingress where stable, TeamViewer destination restrictions, bounded logs, and an automatic expiry.
4. **Test transport before TeamViewer.** From the approved client, verify that an authenticated `CONNECT` to an allowed TeamViewer destination succeeds, while no credentials, a wrong source, a non-TeamViewer destination, and a disallowed destination port all fail.
5. **Test the real client.** Configure TeamViewer's manual proxy fields and verify login, device-list visibility, one short remote-control session, reconnect behavior, and service behavior after a Windows restart.
6. **Observe and stop.** Review proxy connection logs and cloud spend during the test. Revoke credentials and close ingress immediately on unexpected destinations, excessive traffic, policy concern, or inability to attribute use.
7. **Promote deliberately.** Keep the endpoint only after the owner accepts availability, credential rotation, monitoring, patching, cost, and incident-response responsibilities. Otherwise remove the listener and rules.

## Revalidation rule

Re-check this note before deployment if it is more than 30 days old. Vercel WebSocket support, Cloudflare Workers inbound TCP status, Spectrum entitlements, Access behavior, Fly.io pricing, and TeamViewer network requirements are all time-sensitive.
