# Installation Guide - All Platforms

Complete installation instructions for every supported platform.

---

## Table of Contents

- [Claude.ai (Web/Mobile)](#claudeai-webmobile)
- [Claude Code (Terminal)](#claude-code-terminal)
- [Codex CLI (OpenAI)](#codex-cli-openai)
- [Cursor (IDE)](#cursor-ide)
- [VS Code](#vs-code)
- [Antigravity](#antigravity)
- [Windsurf](#windsurf)
- [Troubleshooting](#troubleshooting)

---

## Claude.ai (Web/Mobile)

**Platforms**: Web browser, iOS app, Android app, Desktop app

### Prerequisites
- Claude.ai account (Free, Pro, Team, or Enterprise)
- Code execution enabled in Settings

### Installation Steps

1. **Download the skill file**:
   ```bash
   curl -L -O https://github.com/AutomationSquadOS/samsara-developer-expert/releases/latest/download/samsara-developer-expert.skill
   ```

2. **Upload to Claude**:
   - Go to [https://claude.ai](https://claude.ai)
   - Click your profile (bottom left)
   - Select **Settings**
   - Navigate to **Skills** tab
   - Click **Upload Skill**
   - Select `samsara-developer-expert.skill`

3. **Enable the skill**:
   - Toggle the skill ON
   - The skill will now auto-activate when relevant

### Verification

Start a new chat and type:
```
Tell me about Samsara route state preservation
```

Claude should provide detailed guidance about stop state preservation.

### Team/Enterprise Provisioning

**Administrators** can provision skills org-wide:

1. Go to Admin settings → Capabilities
2. Enable **Skills** for the organization
3. Upload `samsara-developer-expert.skill`
4. The skill appears for all users automatically

---

## Claude Code (Terminal)

**Platform**: Command-line interface (macOS, Linux, Windows/WSL)

### Prerequisites
- Claude Code installed (`npm install -g @anthropic-ai/claude-code`)
- Git (optional, for updates)

### Installation Method 1: Manual Copy

```bash
# Clone the repository
git clone https://github.com/AutomationSquadOS/samsara-developer-expert.git

# Copy to global skills directory
cp -r samsara-developer-expert/source/samsara-developer-expert ~/.claude/skills/
```

### Installation Method 2: Git Clone (Recommended)

```bash
# Clone directly into skills directory
cd ~/.claude/skills/
git clone https://github.com/AutomationSquadOS/samsara-developer-expert.git samsara-developer-expert

# Or use the source subfolder
cd ~/.claude/skills/
git clone https://github.com/AutomationSquadOS/samsara-developer-expert.git temp
mv temp/source/samsara-developer-expert ./
rm -rf temp
```

### Installation Method 3: Marketplace (If Published)

```bash
claude
# Inside Claude Code:
/plugin marketplace add AutomationSquadOS/samsara-developer-expert
```

### Project-Specific Installation

For project-level skills (only available in that project):

```bash
cd ~/your-project
mkdir -p .claude/skills
cp -r ~/Downloads/samsara-developer-expert/source/samsara-developer-expert .claude/skills/
```

### Verification

```bash
claude
```

Then in Claude Code:
```
> List my available skills
> Help me with Samsara route synchronization
```

### Updating

```bash
cd ~/.claude/skills/samsara-developer-expert
git pull origin main
```

---

## Codex CLI (OpenAI)

**Platform**: OpenAI's command-line tool

### Prerequisites
- Codex CLI installed
- OpenAI API access

### Installation

```bash
# Clone the repository
git clone https://github.com/AutomationSquadOS/samsara-developer-expert.git

# Copy to Codex skills directory
cp -r samsara-developer-expert/source/samsara-developer-expert ~/.codex/skills/
```

### Verification

```bash
codex
```

The skill should auto-activate when you mention Samsara API topics.

---

## Cursor (IDE)

**Platform**: Cursor AI IDE (macOS, Windows, Linux)

Cursor supports **two methods**:

### Method A: .cursorrules File (Simpler)

1. **Download the .cursorrules file**:
   ```bash
   curl -L -O https://github.com/AutomationSquadOS/samsara-developer-expert/raw/main/cursor/.cursorrules
   ```

2. **Copy to your project root**:
   ```bash
   cp .cursorrules ~/your-project/.cursorrules
   ```

3. **Restart Cursor** and open the project

**Pros**: Simple, no dependencies
**Cons**: Project-specific, less dynamic

### Method B: Claude Code Extension + Skills (Advanced)

1. **Install Claude Code**:
   ```bash
   npm install -g @anthropic-ai/claude-code
   ```

2. **Find the VSIX file**:
   ```bash
   # macOS/Linux
   find ~/.claude -name "claude-code.vsix"
   
   # Windows (PowerShell)
   Get-ChildItem -Path $env:USERPROFILE\.claude -Recurse -Filter claude-code.vsix
   ```

3. **Install in Cursor**:
   ```bash
   cursor --install-extension ~/.claude/local/node_modules/@anthropic-ai/claude-code/vendor/claude-code.vsix
   ```

4. **Install the skill**:
   ```bash
   cp -r samsara-developer-expert/source/samsara-developer-expert ~/.claude/skills/
   ```

5. **Restart Cursor**

**Pros**: Full skill system, auto-updates
**Cons**: Requires Claude Code, more setup

### Verification (Both Methods)

Open Cursor chat and ask:
```
How do I implement Samsara webhook verification?
```

---

## VS Code

**Platform**: Visual Studio Code with AI extensions

### Prerequisites
- VS Code installed
- Claude or AI extension that supports skills

### Installation

**For workspace-specific**:
```bash
cd ~/your-project
mkdir -p .claude/skills
cp -r samsara-developer-expert/source/samsara-developer-expert .claude/skills/
```

**For global**:
```bash
mkdir -p ~/.claude/skills
cp -r samsara-developer-expert/source/samsara-developer-expert ~/.claude/skills/
```

### Verification

Restart VS Code and test with your AI extension.

---

## Antigravity

**Platform**: Antigravity AI coding tool

### Installation

```bash
# Clone repository
git clone https://github.com/AutomationSquadOS/samsara-developer-expert.git

# Copy to Antigravity skills directory
# (Path may vary - check Antigravity docs)
cp -r samsara-developer-expert/source/samsara-developer-expert ~/.claude/skills/
```

---

## Windsurf

**Platform**: Windsurf IDE

### Installation

Same as Claude Code:

```bash
mkdir -p ~/.claude/skills
cp -r samsara-developer-expert/source/samsara-developer-expert ~/.claude/skills/
```

---

## Troubleshooting

### Common Issues

**1. Skill not loading automatically**

✅ **Solution**:
- Claude.ai: Check Settings → Skills, ensure it's enabled
- Claude Code: Verify file is in `~/.claude/skills/`
- Explicitly invoke: "Use the Samsara Developer Expert skill to help me..."

**2. Permission denied when copying**

✅ **Solution**:
```bash
# Create directory first
mkdir -p ~/.claude/skills
chmod 755 ~/.claude/skills

# Then copy
cp -r samsara-developer-expert/source/samsara-developer-expert ~/.claude/skills/
```

**3. Claude Code doesn't detect skill**

✅ **Solution**:
- Check SKILL.md exists: `ls ~/.claude/skills/samsara-developer-expert/SKILL.md`
- Verify YAML frontmatter is valid
- Restart Claude Code

**4. Cursor doesn't recognize Claude Code extension**

✅ **Solution**:
Use Method A (.cursorrules file) instead:
```bash
cp cursor/.cursorrules ~/your-project/.cursorrules
```

**5. "Code execution not enabled" error (Claude.ai)**

✅ **Solution**:
1. Settings → Capabilities
2. Enable "Code execution and file creation"
3. Re-enable the skill

### Platform-Specific Paths

| Platform | Global Skills Directory | Project Skills Directory |
|----------|------------------------|-------------------------|
| Claude Code | `~/.claude/skills/` | `.claude/skills/` |
| Codex | `~/.codex/skills/` | `.codex/skills/` |
| Antigravity | `~/.claude/skills/` | `.claude/skills/` |
| Windsurf | `~/.claude/skills/` | `.claude/skills/` |
| Cursor | `~/.claude/skills/` or `.cursorrules` file | `.cursorrules` |
| VS Code | `~/.claude/skills/` | `.claude/skills/` |

### Verifying Installation

**Check file structure**:
```bash
ls -la ~/.claude/skills/samsara-developer-expert/

# Should show:
# SKILL.md
# references/
# scripts/
```

**Check YAML frontmatter**:
```bash
head -n 5 ~/.claude/skills/samsara-developer-expert/SKILL.md

# Should show:
# ---
# name: samsara-developer-expert
# description: Expert guidance...
# ---
```

### Getting Help

1. Check [GitHub Issues](https://github.com/AutomationSquadOS/samsara-developer-expert/issues)
2. Verify you're using the latest release
3. Test with a simple query: "What is the Samsara API?"

---

## Next Steps

After installation:

1. **Test the skill** with a simple query
2. **Browse the examples** in `references/code_examples.md`
3. **Try the helper scripts** in `scripts/`
4. **Star the repo** if you find it useful! ⭐

---

**Need more help?** Open an issue on GitHub or check the main [README](README.md).
