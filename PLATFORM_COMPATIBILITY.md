# Platform Compatibility Matrix

## Supported Platforms

| Platform | Install Format | Location | Auto-Detection | Updates | Status |
|----------|---------------|----------|----------------|---------|---------|
| **Claude.ai** (Web/Mobile) | `.skill` ZIP file | Upload via Settings | ✅ Automatic | Manual re-upload | ✅ Fully Supported |
| **Claude Code** (CLI) | Folder w/ SKILL.md | `~/.claude/skills/` | ✅ Automatic | `git pull` | ✅ Fully Supported |
| **Codex CLI** (OpenAI) | Folder w/ SKILL.md | `~/.codex/skills/` | ✅ Automatic | `git pull` | ✅ Compatible |
| **Cursor** (IDE) | `.cursorrules` or folder | `.cursorrules` or `~/.claude/skills/` | ⚠️ Manual invoke | Edit file / `git pull` | ✅ Compatible |
| **VS Code** (Extensions) | Folder w/ SKILL.md | `.claude/skills/` | ⚠️ Extension-dependent | `git pull` | ✅ Compatible |
| **Antigravity** | Folder w/ SKILL.md | `~/.claude/skills/` | ✅ Automatic | `git pull` | ✅ Compatible |
| **Windsurf** | Folder w/ SKILL.md | `~/.claude/skills/` | ✅ Automatic | `git pull` | ✅ Compatible |
| **Aider** | Folder w/ SKILL.md | Via loader | ⚠️ Extension needed | `git pull` | ⚠️ Experimental |

## Feature Comparison

### By Platform

#### Claude.ai
**Advantages:**
- ✅ GUI-based upload (no terminal needed)
- ✅ Mobile access (iOS/Android apps)
- ✅ Team/Enterprise provisioning
- ✅ Built-in skill management UI
- ✅ No dependencies

**Limitations:**
- ❌ Manual updates (must re-upload)
- ❌ Single skill format (.skill ZIP)

**Best For:** Web users, teams, non-developers, mobile access

---

#### Claude Code
**Advantages:**
- ✅ Terminal-native workflow
- ✅ Git version control
- ✅ Project-specific skills (`.claude/skills/`)
- ✅ Global skills (`~/.claude/skills/`)
- ✅ Marketplace support
- ✅ Auto-detection and loading
- ✅ Easy updates (`git pull`)

**Limitations:**
- ❌ Requires npm/Node.js
- ❌ CLI only (no GUI)

**Best For:** Developers, automation, CI/CD integration

---

#### Cursor
**Advantages:**
- ✅ IDE integration (VS Code fork)
- ✅ Visual diff approval
- ✅ Simple `.cursorrules` format option
- ✅ Works with Claude Code skills

**Limitations:**
- ❌ Claude Code extension setup can be tricky
- ❌ `.cursorrules` less dynamic than full skills

**Best For:** IDE users, visual development, code review

---

#### Codex CLI
**Advantages:**
- ✅ Same SKILL.md format as Claude Code
- ✅ OpenAI integration
- ✅ Cross-compatible skills

**Limitations:**
- ❌ Requires OpenAI API access
- ❌ Different model capabilities

**Best For:** OpenAI users, multi-model workflows

---

#### VS Code / Antigravity / Windsurf
**Advantages:**
- ✅ Same SKILL.md format
- ✅ Flexible installation

**Limitations:**
- ⚠️ Varies by tool/extension

**Best For:** Users of these specific tools

## Installation Complexity

| Platform | Setup Time | Complexity | Prerequisites |
|----------|-----------|------------|---------------|
| Claude.ai | < 1 min | ⭐ Easy | Account only |
| Claude Code | 2-5 min | ⭐⭐ Medium | Node.js, terminal |
| Cursor (.cursorrules) | 1 min | ⭐ Easy | Cursor IDE |
| Cursor (w/ extension) | 5-10 min | ⭐⭐⭐ Advanced | Claude Code + Cursor |
| Codex CLI | 2-5 min | ⭐⭐ Medium | Codex installed |
| VS Code | 2-5 min | ⭐⭐ Medium | VS Code + extension |
| Antigravity/Windsurf | 2-5 min | ⭐⭐ Medium | Tool installed |

## File Format Differences

### .skill File (Claude.ai)
```
samsara-developer-expert.skill  # ZIP file containing:
├── SKILL.md
├── references/
│   ├── api_endpoints.md
│   └── ...
└── scripts/
    ├── rate_limiter.py
    └── ...
```

### Folder Structure (Claude Code, Codex, etc.)
```
~/.claude/skills/samsara-developer-expert/
├── SKILL.md
├── references/
│   ├── api_endpoints.md
│   └── ...
└── scripts/
    ├── rate_limiter.py
    └── ...
```

### .cursorrules File (Cursor)
```
your-project/
└── .cursorrules  # Single consolidated rules file
```

## Cross-Platform Usage

### Can I use the same skill on multiple platforms?
**Yes!** The skill content is identical. Just install using each platform's method.

Example workflow:
- **Development**: Use Claude Code in terminal
- **Code Review**: Use Cursor in IDE
- **Mobile**: Use Claude.ai app
- **Team**: Provision via Claude.ai Enterprise

### Update Strategy

**For Claude.ai:**
```bash
# Download updated .skill file
curl -L -O https://github.com/AutomationSquadOS/samsara-developer-expert/releases/latest/download/samsara-developer-expert.skill

# Re-upload via Settings → Skills
```

**For Claude Code / Codex / Others:**
```bash
cd ~/.claude/skills/samsara-developer-expert
git pull origin main
```

**For Cursor (.cursorrules):**
```bash
cd ~/your-project
curl -L -O https://github.com/AutomationSquadOS/samsara-developer-expert/raw/main/cursor/.cursorrules
```

## Version Compatibility

| Skill Version | Claude.ai | Claude Code | Codex | Cursor | Others |
|--------------|-----------|-------------|-------|--------|--------|
| 1.0.0+ | ✅ | ✅ | ✅ | ✅ | ✅ |

All platforms use the same skill version. No platform-specific versions needed.

## Choosing the Right Platform

**Use Claude.ai if you:**
- Want the simplest installation
- Need mobile access
- Are part of a team/enterprise
- Prefer web interfaces

**Use Claude Code if you:**
- Work primarily in terminal
- Want Git version control
- Need automation/CI-CD
- Build dev tools

**Use Cursor if you:**
- Work in an IDE daily
- Want visual diff review
- Need code completion + AI
- Prefer IDE integration

**Use Codex CLI if you:**
- Use OpenAI models
- Want multi-model support
- Already use Codex

## Migration Between Platforms

**From Claude.ai → Claude Code:**
```bash
# Extract from .skill file
unzip samsara-developer-expert.skill -d ~/.claude/skills/samsara-developer-expert
```

**From Claude Code → Claude.ai:**
```bash
# Package as .skill file
python scripts/package_skill.py source/samsara-developer-expert releases/
# Upload releases/samsara-developer-expert.skill
```

**From Any → Cursor:**
```bash
# Copy .cursorrules to project
cp cursor/.cursorrules ~/your-project/.cursorrules
```

---

**Recommendation:** Most users should start with **Claude.ai** (simplest) or **Claude Code** (most powerful). Add other platforms as needed.
