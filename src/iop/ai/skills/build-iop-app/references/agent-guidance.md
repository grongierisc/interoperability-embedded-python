# IoP Agent Guidance And Skills

IoP ships version-matched project guidance, Agent Skills, and offline copies of
the IoP cookbooks. Install them in any IoP application repository, including a
project that was not created from the IoP template:

```bash
iop --install-agent-guidance
```

The command configures Codex, Claude Code, and Gemini CLI by default. It adds a
small IoP-managed block to existing root instruction files without replacing
other project rules, installs canonical guidance in `.config/AGENTS`, and adds
the `build-iop-app` and `validate-iop-app` skills for each agent.

## Select Agents

Use one or more `--agent` options when the project only needs specific clients:

```bash
iop --install-agent-guidance --agent codex
iop --install-agent-guidance --agent claude --agent gemini
```

Pass a project directory to configure a repository other than the current one:

```bash
iop --install-agent-guidance /path/to/iop-application
```

The installer is idempotent. If an IoP-managed file was changed locally, it
stops before writing anything. Review the conflict, then replace only the
IoP-managed snapshot when appropriate:

```bash
iop --install-agent-guidance --force-agent-guidance
```

Rerun that command after upgrading IoP to refresh the guides, skills, and
offline cookbooks to the installed framework version.

## Install Skills Directly

Developers who only need the portable skills can install them from the IoP
repository with the cross-agent Skills CLI:

```bash
npx skills add \
  https://github.com/grongierisc/interoperability-embedded-python/tree/master/src/iop/ai/skills \
  --skill build-iop-app \
  --skill validate-iop-app
```

Direct installation provides the self-contained skills and their references.
It does not add the always-on `AGENTS.md`, `CLAUDE.md`, or `GEMINI.md` project
guidance; use the IoP installer when those entrypoints are wanted.

## Skill Responsibilities

- `build-iop-app` inspects the application, selects the relevant bundled
  cookbook, and guides message, component, production graph, sample, and test
  changes.
- `validate-iop-app` runs project tests and strict migration dry-run first, then
  requires container-backed runtime verification when the project provides a
  disposable environment, while protecting shared or remote IRIS instances.

The skill files use the shared Agent Skills `SKILL.md` format with only portable
frontmatter. Client-specific wrappers contain no duplicated IoP policy; the
installed `.config/AGENTS` snapshot remains the local source of truth.
