# Shared-host preparation and integration review

Continue platform deployment/integration work while T1 selects reviewed excerpts.
No shared service deployment, network exposure, source copy or database reset.

1. [x] Attempt inventory of candidate-host architecture, free disk, ports and existing private
   ingress read-only. Report unreachable hosts; do not infer readiness.
2. [x] Reproduce HTTPS origin rejection through the actual proxy/API. Configure the
   external scheme explicitly, preserve Host and trust forwarded headers only
   behind the unpublished API. Verify HTTPS cookies, same-origin writes, rejected
   foreign origins and ignored client scheme spoofing; retain test records.
3. [x] Support explicit target architecture in local image builds. Keep the default
   native behavior and reject unsupported targets. Target builds remain unproven
   until actually executed on/for the selected host.
4. [x] Review the cumulative platform diff against the fetched team baseline, run
   focused and full backend checks, and make small local commits.
5. [x] Record host prerequisites, exact staging/access commands, evidence and remaining
   approval/Orin/T1 dependencies in a reviewable preparation document. Deployment
   remains a separate explicit action. Keep teammate implementation with owners.

Source snapshots, existing application projects and every database volume remain
untouched. Use isolated fixture projects for local deployment-path verification;
fixture evidence does not establish real-model or shared-host acceptance.

Follow-up host inventory succeeded through Tailscale SSH; the LAN alias still
timed out. G14 matches AMD64 but has no Docker/Compose and no noninteractive
sudo. Runtime installation and ingress setup remain unperformed.
Local ARM64 and AMD64-under-emulation checks passed. Shared deployment, actual
front-door compatibility and real-model acceptance remain unperformed.
