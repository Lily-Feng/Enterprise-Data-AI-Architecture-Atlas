---
title: DNS across the on-prem/cloud boundary
description: Making on-prem resolvers answer for cloud private names and cloud resolvers answer for on-prem names, in both directions.
tags: [dns, hybrid, private-endpoint, routing]
---

# DNS across the on-prem/cloud boundary

The circuit is up. BGP is established. You can ping the private IP. The application still cannot reach the database, because the name resolved to a public address — or to nothing at all.

DNS is the most common cause of "hybrid connectivity is broken" reports that are not connectivity problems. It is a seam because each side has a complete, self-consistent DNS system that knows nothing about the other, and joining them means pointing each at the other for a specific set of zones without creating a loop.

## Topology

Resolution has to work in **both** directions, and they are separate mechanisms with separate failure modes.

```text
        ON-PREM                    │              CLOUD
                                   │
  ┌──────────────────┐             │       ┌────────────────────────┐
  │ Corporate DNS    │             │       │ Cloud private zone     │
  │ (AD DS / BIND)   │             │       │ db.internal.example    │
  │ corp.example.com │             │       │ → 10.20.4.15           │
  └────────┬─────────┘             │       └───────────┬────────────┘
           │                       │                   │
           │ conditional forwarder │                   │ associated to VPC
           │ internal.example      │                   │
           │        ─────────────► │ ┌───────────────┐ │
           │                       │ │  INBOUND      │ │
           │                       │ │  endpoint     ├─┘
           │                       │ │  10.20.1.10   │
           │                       │ └───────────────┘
           │                       │
           │ ◄───────────────────  │ ┌───────────────┐
           │  forwarding rule      │ │  OUTBOUND     │
           │  corp.example.com     │ │  endpoint     │
           │                       │ │  10.20.1.20   │
           │                       │ └───────┬───────┘
           │                       │         │
  ┌────────▼─────────┐             │   ┌─────▼──────────┐
  │ on-prem hosts    │             │   │ cloud workloads│
  │ 172.16.0.0/12    │             │   │ 10.20.0.0/16   │
  └──────────────────┘             │   └────────────────┘
                              boundary
```

| Element | What it is | Which side |
|---|---|---|
| Conditional forwarder | On-prem rule: "for `internal.example`, ask 10.20.1.10" | On-prem |
| Inbound endpoint | ENIs in the VPC that accept queries from on-prem | Cloud |
| Outbound endpoint | ENIs that send queries out to on-prem resolvers | Cloud |
| Forwarding rule | Cloud rule: "for `corp.example.com`, ask the on-prem resolver" | Cloud |
| Private hosted zone | Names resolvable only from associated VPCs | Cloud |

The two arrows are independent. Configuring one and assuming the other works is the single most common version of this mistake.

## Wiring

**Cloud → on-prem** (outbound endpoint plus a forwarding rule):

```bash
aws route53resolver create-resolver-endpoint \
  --name outbound-to-corp --direction OUTBOUND \
  --security-group-ids sg-0abc123 \
  --ip-addresses SubnetId=subnet-0a1,SubnetId=subnet-0b2

aws route53resolver create-resolver-rule \
  --name corp-forward --rule-type FORWARD \
  --domain-name corp.example.com \
  --resolver-endpoint-id rslvr-out-0abc \
  --target-ips Ip=172.16.10.53,Port=53 Ip=172.16.11.53,Port=53
```

**On-prem → cloud** is configured on the corporate resolver, pointed at the inbound endpoint IPs. On Windows DNS:

```powershell
Add-DnsServerConditionalForwarderZone `
  -Name "internal.example" `
  -MasterServers 10.20.1.10,10.20.2.10
```

Deploy endpoints in **at least two subnets in different AZs**. A single-AZ resolver endpoint is a single-AZ dependency for every name in the zone.

| Concern | AWS | Azure | GCP |
|---|---|---|---|
| Cloud-private names | Route 53 private hosted zone | Private DNS zone + VNet link | Cloud DNS private zone |
| Accept queries from on-prem | Resolver **inbound** endpoint | DNS Private Resolver **inbound** endpoint | Inbound server policy |
| Query on-prem from cloud | Resolver **outbound** endpoint + rule | DNS Private Resolver **outbound** + ruleset | Outbound forwarding zone |
| Auto-registration of records | — | Private zone auto-registration | Cloud DNS managed zone |

## Knobs

| Knob | Controls | Default | When the default hurts | Set to |
|---|---|---|---|---|
| Resolver endpoint IP count | Query throughput and AZ resilience | 2 IPs (minimum) | High query volume; an AZ event | 3+ across AZs |
| Per-IP query rate | Hard cap per endpoint IP | ~10,000 qps per IP `[verify: 2026-08-29]` | Chatty workloads with low TTLs | Add IPs, not endpoints |
| Negative-cache TTL (SOA minimum) | How long `NXDOMAIN` is remembered | Often 3600s on legacy zones | A record is created and clients cache the failure for an hour | 60–300s |
| Record TTL on private zones | Failover and change speed | 300s | Cutovers, endpoint IP changes | 60s before a migration, back after |
| Forwarder ordering / timeout | Which resolver is tried first | First-listed, ~3s timeout | The first resolver is reachable but wrong | Health-check the order |
| VPC `enableDnsHostnames` / `enableDnsSupport` | Whether private zones resolve at all | **`enableDnsHostnames` is off** on VPCs created by API/IaC | Private endpoint names do not resolve, with no error explaining why | Both `true` |

That last row is worth stating plainly, because it produces a support ticket almost every time: the console default and the API default differ. A VPC created by Terraform without explicit settings can silently fail to resolve every private name in it.

**The negative-cache knob is the one people miss.** Resolvers cache failures using the zone's SOA minimum field, not the record TTL. Create a record after a client has already asked for it, and that client keeps failing for the full negative TTL while the record demonstrably exists. This presents as "DNS is broken on some machines and fine on others," which sends people looking at the network.

## Seams

### Split-horizon: the name resolves, to the wrong address

**Presents as:** connection timeouts, or traffic that works but egresses to the internet and back. TLS may still succeed, which removes the most obvious clue.

**Cause:** the same name exists in both a public zone and a cloud private zone. On-prem asks its corporate resolver, which has no forwarder for that zone, falls through to the internet root, and gets the public A record. The private IP was never consulted.

**Confirm:** query both sides for the same name and compare.

```bash
dig +short db.internal.example @172.16.10.53   # on-prem resolver
dig +short db.internal.example @10.20.1.10     # cloud inbound endpoint
```

Different answers means split-horizon. Same answer means look elsewhere.

### Private endpoint names resolve only from inside the VPC

**Presents as:** the service is reachable from cloud workloads and unreachable from on-prem, with the circuit healthy.

**Cause:** private endpoint DNS names are published in a zone associated with the VPC. On-prem has no path to that zone unless a conditional forwarder exists for it specifically. The public name still resolves globally — to a public endpoint your firewall may block, or worse, may not.

**Confirm:** `dig` the endpoint name from on-prem. A public IP in the answer means the forwarder is missing for that zone.

### The forwarding loop

**Presents as:** `SERVFAIL` under load, or resolver CPU saturation, often intermittently.

**Cause:** on-prem forwards a zone to the cloud, and the cloud has a rule forwarding the same zone (or a parent of it) back to on-prem. Each side believes the other is authoritative. Wildcard and parent-zone rules cause this more often than exact-match rules, because the overlap is not visible in either config alone.

**Confirm:** trace the delegation on both sides for the *most specific* rule that matches. Compare rule domains for parent/child overlap — this cannot be seen from one side.

### DNS succeeds and the connection still hangs

**Presents as:** name resolves to the right private IP; TCP connects; the session stalls on the first large payload.

**Cause:** not DNS at all — MTU. Tunnel encapsulation over the circuit lowers the effective path MTU, and if ICMP fragmentation-needed is filtered by an enterprise firewall, path MTU discovery fails silently. Small packets pass, large ones vanish.

**Confirm:** send progressively larger packets with DF set.

```bash
ping -M do -s 1472 10.20.4.15   # 1500-byte path
ping -M do -s 1372 10.20.4.15   # 1400-byte path
```

If the small one passes and the large one does not, clamp MSS on the boundary device rather than continuing to investigate DNS. This is in a DNS page deliberately: it is the failure most often misfiled as one.

