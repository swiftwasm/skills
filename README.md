# SwiftWasm Agent Skills

A collection of [Agent Skills](https://agentskills.io/) designed to help AI coding agents build and maintain Swift applications targeting WebAssembly.

## What are Agent Skills?

Agent Skills are specialized modules containing instructions, scripts, and documentation that give AI agents (like Claude, Gemini, or Codex) the domain expertise needed to perform complex tasks.

This repository is compatible with major agent tools, leveraging standardized formats to ensure your agent has the right context for SwiftWasm development.

## Installation

### Claude Code

1. Add this repository as a plugin marketplace:
   ```bash
   claude plugin marketplace add swiftwasm/skills
   ```

2. Install skills using a loop:
   ```bash
   for skill in javascriptkit bridgejs porting; do
     claude plugin install ${skill}@swiftwasm-skills
   done
   ```

### OpenAI Codex

OpenAI Codex CLI and compatible tools support the Agent Skills format by searching specific directories.

#### User-Level Installation
To make all skills from this repository available across all your projects:

```bash
# Create the Codex skills directory
mkdir -p ~/.codex/skills

# Clone and copy all skills
git clone https://github.com/swiftwasm/skills.git /tmp/swiftwasm-skills
for skill_path in /tmp/swiftwasm-skills/skills/*; do
  [ -d "$skill_path" ] || continue
  cp -r "$skill_path" ~/.codex/skills/
done
```

#### Project-Level Installation
To use skills only within a specific project:

```bash
# In your project root
mkdir -p .codex/skills
for skill_path in /path/to/swiftwasm-skills/skills/*; do
  [ -d "$skill_path" ] || continue
  cp -r "$skill_path" .codex/skills/
done
```

### Gemini CLI

This repository includes a `gemini-extension.json` for integration. Install it using the following command:

```bash
gemini extensions install https://github.com/swiftwasm/skills.git --consent
```

### Cursor

For Cursor, please refer to [Installing Skills from GitHub](https://cursor.com/docs/context/skills#installing-skills-from-github).

## Available Skills

| Name | Description | Documentation |
|------|-------------|---------------|
| `javascriptkit` | Assist with Swift & JavaScript interop, project initialization, and memory management for WebAssembly. | [SKILL.md](skills/javascriptkit/SKILL.md) |
| `bridgejs` | Assist with BridgeJS for type-safe Swift-to-JavaScript bindings, exporting Swift APIs, and importing TypeScript definitions. | [SKILL.md](skills/bridgejs/SKILL.md) |
| `porting` | Check Swift on Wasm compatibility, identify incompatible frameworks, port and refactor code for WebAssembly. | [SKILL.md](skills/porting/SKILL.md) |

## Usage

Once a skill is installed or loaded, you can trigger its logic by mentioning relevant tasks to your agent. For example, using the `javascriptkit` skill:

- "Initialize a new JavaScriptKit project named 'MyWebApp' in the current directory."
- "How do I safely pass a Swift closure to a JavaScript event listener?"
- "Check my environment using the doctor script to ensure I can build for Wasm."

The agent will automatically refer to the appropriate `SKILL.md` file and any associated helper scripts to fulfill your request.
