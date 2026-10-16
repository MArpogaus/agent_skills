---
name: selfhosted
description: >
  Conventions for the user's self-hosted home server: Fedora CoreOS with
  SecureBlue, rootless Podman Quadlets deployed by Ansible, the repo
  layout, the uniform service interface, the VM-first test cycle, the
  root gate, releases, security and debugging. Use in `home-server` or
  `home-server-*` repos, and for Ansible, Quadlet, Butane, root-gate or
  SSH work on the test VM or the production host.
license: MIT
compatibility: claude-code opencode
metadata: {stack: ansible podman systemd, requires: [dev-conventions, git-conventions]}
---

# Skill: Self-hosted home server

## Hard rules

- Deploy to the production host only when the user asks for it in this
  session.
- Test every change on the test VM first.
- On the test VM, run commands yourself. On the production host, run
  only read-only commands, except a deploy the user asked for in this
  session. Say before each command that needs the user's hardware key.
- If the logind session count rises by more than 50 above the count
  before the deploy, stop and tell the user.
- Roles assume a clean install (dev-conventions, "1. Design
  principles"). Give one-off steps for the existing production host to
  the user as manual steps.

## Platform

- A host that runs Fedora CoreOS rebases to SecureBlue on first boot.
  Butane files produce the Ignition config.
- Each service runs as rootless Podman Quadlets under its own user, on
  its own Btrfs subvolume.
- Containers log to the journal (`LogDriver=passthrough`; nginx and
  php-fpm log through syslog).
- Containers do not reach the LAN. Egress rules control this.
- Ansible is the single source of truth. Image bumps, limits and
  settings change in a repo, and a redeploy applies them.

## Repositories

- `home-server` (public): the generic playbook `site.yml`, the core
  roles, the `test/` VM harness and the `examples/vm` deployment. It
  holds no host specifics and no default inventory.
- `home-server-<service>` (for example `home-server-monitoring`):
  self-contained service repos. Each ships its role, its alerts and its
  dashboards. The monitoring role knows no service.
  `home-server` pins them as submodules under `services/`.
- `<secrets repo>` (private): one directory per deployment with
  `inventory.yml`, `group_vars/all/vars.yml`, the Vault file
  `vault.yml`, `ssh/known_hosts` and `tasks/pre.yml`.
- Host and platform specifics (for example SecureBlue settings) live
  in the deployment directory and its `host_tasks_pre` hook, never in
  `home-server`.

## Service interface

- Config is separate from code. Each service takes
  `<name>_service_config` and carries sane, generic defaults.
- CPU and memory limits work the same for every container of every
  service: `<name>_service_cpu` and `<name>_service_memory` are dicts
  per container, merged over the role defaults.
- Similar features use one implementation and one variable shape in
  every service. Per-service proxy settings follow the same pattern.
- No service has a hard dependency on the notification service.

## Dashboards

Key metrics and aggregates go at the top, detail views and logs at
the bottom. The plot type fits the data. Every panel has a complete
legend and explains itself. Check a changed dashboard on the test VM
with a screenshot.

## systemd over custom code

- Use timers, `OnSuccess=`, automount units, unit dependencies and
  inhibitor locks. Write no retry loops and no edge-case handling.
- A snapshot timer per service starts the backup sync. The sync depends
  on the automount of the target. A missing target makes the unit fail,
  and the journal shows it.
- The nightly reboot waits for inhibitor locks. A long one-off job, for
  example a preview backfill, runs under `systemd-inhibit`.
- Ansible escalates with `become` and the stock
  `community.general.run0` plugin everywhere. Playbooks and scripts call
  no `run0`, `systemd-run` or `machinectl` directly. No custom become
  plugin and no pipelining.
- Each `run0` call opens a logind session. Count the sessions with
  `loginctl --no-legend list-sessions | wc -l`. Too many sessions wedge
  polkit, and only a reboot clears them. Never leave
  a `run0` call in the background.

## Deploy commands

- Write no wrapper deploy scripts. Document the exact commands:

  ```bash
  ansible-playbook -i <deployment dir>/inventory.yml site.yml -l <host>
  ./functional_test.sh <host> -i <deployment dir>/inventory.yml
  ```

- `-e '{"deploy_services": ["<service>"]}'` limits a run to the listed
  service roles.
- A temporary change on the host does not touch the role. Use a runtime
  setting, for example
  `systemctl --user set-property --runtime <unit> CPUQuota=200%`.

## Test cycle

1. `test/start_vm.py --fresh` builds a new VM; `--platform <butane
   file>` adds the platform config. After the rebase, the user shuts the
   VM down and runs `--save-base`. `--restore` resets the disk to that
   base.
2. The agent cannot start the VM. Ask the user for `--restore` or
   `--fresh`, and wait until the user says the VM is up. Autonomous:
   record it as a blocker (`dev-conventions`, "2. Asking and acting")
   and work on something else.
3. Before a release that changes a role, test on a fresh VM. A
   long-lived VM hides first-install bugs.
4. Deploy, deploy again (expect `changed=0`), then run the functional
   test.
5. A deploy reads the live working tree. During a deploy, do not edit
   files or switch submodule branches. Use `git worktree`.

## Root gate on the production host

- The SSH key is on the user's hardware key, so each new SSH connection
  needs the user's input. Reuse one connection (`ControlMaster`,
  `ControlPersist`).
- Root needs an open gate. A root gate script that the deployment repo
  provides controls it. The gate is closed by default. The user opens
  it as `<admin user>` on the host, with or without a timer.
- Before a command that needs root, assert that the gate is open. If it
  is closed, stop and ask the user to open it. Autonomous: record it as
  a blocker (`dev-conventions`, "2. Asking and acting") and work on
  something else.
- The gate closes on its timer, or when the user closes it.
- "gate open", "key unlocked" or "timer extended" from the user means:
  continue at once.
- When done, tell the user, who closes the gate.

## Releases and CI

- Pin actions as git-conventions, "CI workflows" says.
- Dependabot updates actions, and pre-commit hooks follow
  git-conventions, "Pre-commit hooks". In service repos, Renovate
  (`.github/renovate.json`, a regex manager over the `*_image`
  defaults) opens image update PRs against `dev`.
- The agent tags no service repo. The user tags them by hand. A repo
  that packages one upstream application uses the upstream version (for
  example `35`, then `35.1`). The others use `v1.0.0`.
- The production host runs tagged releases only. For a change deployed
  there, ask the user to tag a patch release of each changed service
  repo, so the tags match the host.

## Security

- Keep the WAF rules strict. Raise a limit for one path
  instead of adding an exception or disabling a rule.
- Secrets live in Ansible Vault. Machine secrets are 48 alphanumeric
  characters: `openssl rand -base64 48 | tr -d '/+=' | cut -c1-48`.
- Give each container the minimum capabilities. Make each remaining gap
  visible in the docs or the functional test.
- Rotate secrets by hand. Write no rotation automation.
- Never print a secret. Pass tokens through stdin.
- If a credential appears in the chat or in tool output, tell the user
  and suggest rotating it.

## Debugging

- When something worked before, suspect the most recent change first.
- No workarounds. Trace the error to its cause. Question a new rule or
  exception that seems necessary all of a sudden.
- For a hard bug, give fresh subagents the bug report only, not your
  findings.
- If probes of a device fail 3 times in a row, stop and ask the user.
- Confirm an upstream defect (for example in SecureBlue) before you
  draft an issue. The user posts it.

---

## Required skills

This skill assumes the following prerequisite skills are loaded.
Use the `skill` tool to load them before using this one:

- **dev-conventions**: design principles, review loop, autonomous
  sessions, code and documentation style.
- **git-conventions**: two-branch flow, conventional commits, tagging,
  releases, no AI attribution.
