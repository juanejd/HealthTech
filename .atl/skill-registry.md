# Skill Registry — HealthTech

Generated: 2026-06-18
Artifact store: engram
Project: healthtech

## Skills Index

| Name | Trigger / Description | Scope | Path |
|------|-----------------------|-------|------|
| gpio-config | Assigns, validates, and generates code for GPIO pin configurations on Raspberry Pi and ESP32 embedded projects. Activates for queries about GPIO pins, wiring, pin mapping, pin conflicts, I2C, SPI, UART, PWM, 1-Wire, CAN, ADC configuration, device tree overlays, config.txt, sdkconfig, strapping pins, boot pins, flash voltage, or connecting sensors, displays, and modules. Covers Pi Zero 2W. | user | `~/.claude/skills/gpio-config/SKILL.md` |
| branch-pr | Create Gentle AI pull requests with issue-first checks. Trigger: creating, opening, or preparing PRs for review. | user | `~/.claude/skills/branch-pr/SKILL.md` |
| chained-pr | Trigger: PRs over 400 lines, stacked PRs, review slices. Split oversized changes into chained PRs that protect review focus. | user | `~/.claude/skills/chained-pr/SKILL.md` |
| work-unit-commits | Plan commits as reviewable work units. Trigger: implementation, commit splitting, chained PRs, or keeping tests and docs with code. | user | `~/.claude/skills/work-unit-commits/SKILL.md` |
| comment-writer | Write warm, direct collaboration comments. Trigger: PR feedback, issue replies, reviews, Slack messages, or GitHub comments. | user | `~/.claude/skills/comment-writer/SKILL.md` |
| judgment-day | Trigger: judgment day, dual review, adversarial review, juzgar. Run blind dual review, fix confirmed issues, then re-judge. | user | `~/.claude/skills/judgment-day/SKILL.md` |
| cognitive-doc-design | Design docs that reduce cognitive load. Trigger: writing guides, READMEs, RFCs, onboarding, architecture, or review-facing docs. | user | `~/.claude/skills/cognitive-doc-design/SKILL.md` |
| issue-creation | Create Gentle AI issues with issue-first checks. Trigger: creating GitHub issues, bug reports, or feature requests. | user | `~/.claude/skills/issue-creation/SKILL.md` |
| skill-creator | Trigger: new skills, agent instructions, documenting AI usage patterns. Create LLM-first skills with valid frontmatter. | user | `~/.claude/skills/skill-creator/SKILL.md` |
| skill-improver | Trigger: improve skills, audit skills, refactor skills, skill quality. Audit and upgrade existing LLM-first skills. | user | `~/.claude/skills/skill-improver/SKILL.md` |

## Highlighted Skills for This Project

- **gpio-config** — primary hardware skill for RPi Zero 2W + HX711 (DT=GPIO17, SCK=GPIO23) + FS90R servo (GPIO18). Load for any GPIO, wiring, or pin-safety work.
- **chained-pr** + **work-unit-commits** — load for any `sdd-apply` that may exceed 400 changed lines.
- **branch-pr** — load whenever creating a PR.

## Excluded

- `sdd-*` skills: pipeline infrastructure, not domain skills.
- `_shared` skills: internal SDD shared protocol.
- `skill-registry` skill: meta/infrastructure.
- `go-testing` skill: Go-specific, no Go code in this project.

## Project Convention Files

None found at project root (no AGENTS.md, CLAUDE.md, .cursorrules, or GEMINI.md).
