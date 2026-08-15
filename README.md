# Samsara Developer Expert - Universal AI Agent Skill

Expert guidance for developing with the Samsara Fleet Management API. Works across **Claude.ai, Claude Code, Codex CLI, Antigravity, Cursor, VS Code, and more**.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Claude Skill](https://img.shields.io/badge/Claude-Skill-purple.svg)](https://claude.ai)
[![Agent Skills](https://img.shields.io/badge/Agent-Skills-blue.svg)](https://agentskills.io)

## 🎯 Universal Compatibility

This skill uses the **Agent Skills standard** (SKILL.md format), making it compatible with:

| Platform | Installation Method | Status |
|----------|-------------------|---------|
| **Claude.ai** (Web/Mobile) | Upload `.skill` file | ✅ Tested |
| **Claude Code** (CLI) | Copy folder to `~/.claude/skills/` | ✅ Tested |
| **Codex CLI** (OpenAI) | Copy folder to `~/.codex/skills/` | ✅ Compatible |
| **Antigravity** | Copy folder to skills directory | ✅ Compatible |
| **Cursor** (IDE) | Multiple methods (see below) | ✅ Compatible |
| **VS Code** (with Claude extension) | Copy to workspace `.claude/skills/` | ✅ Compatible |
| **Windsurf** | Same as Claude Code | ✅ Compatible |
| **Aider** | Via SKILL.md loader | ✅ Compatible |

## 🚀 Quick Install (Choose Your Platform)

### Option 1: Claude.ai (Web/Mobile/Desktop)

**Best for**: Web users, Teams, Enterprise

```bash
# Download the .skill file
curl -L -O https://github.com/AutomationSquadOS/samsara-developer-expert/releases/latest/download/samsara-developer-expert.skill
```

Then:
1. Go to [Claude.ai](https://claude.ai) → Settings → Skills
2. Click "Upload Skill"
3. Select `samsara-developer-expert.skill`
4. Enable the skill ✅

### Option 2: Claude Code (CLI)

**Best for**: Terminal users, automation

```bash
# Install from GitHub
git clone https://github.com/AutomationSquadOS/samsara-developer-expert.git
cp -r samsara-developer-expert/source/samsara-developer-expert ~/.claude/skills/

# Or use the marketplace (if published)
/plugin marketplace add AutomationSquadOS/samsara-developer-expert
```

Verify installation:
```bash
claude
# Type: /samsara-developer-expert
# Or just mention "Samsara API" and it auto-loads!
```

### Option 3: Codex CLI (OpenAI)

**Best for**: OpenAI users

```bash
# Clone and install
git clone https://github.com/AutomationSquadOS/samsara-developer-expert.git
cp -r samsara-developer-expert/source/samsara-developer-expert ~/.codex/skills/
```

### Option 4: Cursor (IDE)

**Best for**: IDE users

**Method A: Use with Claude Code Extension**
```bash
# Install Claude Code extension in Cursor
cursor --install-extension ~/.claude/local/node_modules/@anthropic-ai/claude-code/vendor/claude-code.vsix

# Then copy skill
cp -r samsara-developer-expert/source/samsara-developer-expert ~/.claude/skills/
```

**Method B: Use .cursorrules (Simpler)**
```bash
# Copy the .cursorrules file to your project
cp cursor/.cursorrules ~/your-project/.cursorrules
```

### Option 5: Antigravity / Windsurf

**Best for**: Alternative AI coding tools

```bash
git clone https://github.com/AutomationSquadOS/samsara-developer-expert.git
cp -r samsara-developer-expert/source/samsara-developer-expert ~/.claude/skills/
```

### Option 6: VS Code (with Extensions)

**Best for**: VS Code + AI extensions

```bash
# For workspace-specific
cp -r samsara-developer-expert/source/samsara-developer-expert ./.claude/skills/

# For global
cp -r samsara-developer-expert/source/samsara-developer-expert ~/.claude/skills/
```

## 📦 What's Included

All platforms get the same comprehensive skill content:

- ✅ Complete API endpoint reference
- ✅ Data synchronization patterns (feeds, snapshots, historical)
- ✅ Route management with state preservation
- ✅ Rate limiting implementations
- ✅ Webhook integration and security
- ✅ 50+ production code examples
- ✅ Helper scripts (Python)

## 🎨 Platform-Specific Features

### Claude.ai Advantages
- ✅ GUI upload (no terminal needed)
- ✅ Team/Enterprise provisioning
- ✅ Mobile access
- ✅ Automatic updates (when re-uploaded)

### Claude Code / Codex Advantages
- ✅ Terminal-native workflow
- ✅ Git version control
- ✅ Project-specific skills (`.claude/skills/`)
- ✅ Marketplace support

### Cursor Advantages
- ✅ IDE integration
- ✅ `.cursorrules` for simpler setup
- ✅ Visual diff approval
- ✅ Works alongside Composer/Agent

## 📚 Usage Examples

Once installed, usage is identical across all platforms:

**Claude.ai:**
```
User: "Help me sync routes from Samsara to my database"
Claude: [Auto-loads skill, provides guidance]
```

**Claude Code:**
```bash
claude
> Help me implement rate limiting for Samsara API
[Skill auto-loads with code examples]
```

**Cursor:**
```
# In Cursor chat
> Show me how to verify Samsara webhook signatures
[Provides HMAC verification code]
```

## 🔧 Manual Installation (Any Platform)

If automated methods don't work:

1. **Download the source**:
   ```bash
   git clone https://github.com/AutomationSquadOS/samsara-developer-expert.git
   cd samsara-developer-expert
   ```

2. **Find your skills directory**:
   - **Claude.ai**: Upload via Settings → Skills
   - **Claude Code**: `~/.claude/skills/` or `.claude/skills/`
   - **Codex**: `~/.codex/skills/`
   - **Cursor**: `~/.claude/skills/` or `.cursorrules` file
   - **VS Code**: `.claude/skills/` in workspace

3. **Copy the skill**:
   ```bash
   cp -r source/samsara-developer-expert YOUR_SKILLS_DIRECTORY/
   ```

## 🌟 Key Features Across All Platforms

### 1. Stop State Preservation (Critical!)
```typescript
// CORRECT: Preserves arrival/departure times
const existing = await fetch(`/fleet/routes/${routeId}`);
const updatedStops = existing.stops.map(stop => ({
  id: stop.id,  // CRITICAL: Keep the ID
  // ... other fields
}));
```

### 2. Production Rate Limiting
```python
# Python rate limiter included in scripts/
from rate_limiter import SamsaraRateLimiter

limiter = SamsaraRateLimiter(requests_per_second=5)
await limiter.throttle()
```

### 3. Webhook Security
```typescript
// HMAC verification for Flask/FastAPI
function verifyWebhookSignature(payload, signature, secret) {
  const hmac = crypto.createHmac('sha256', secret);
  const digest = hmac.update(payload).digest('hex');
  return crypto.timingSafeEqual(Buffer.from(signature), Buffer.from(digest));
}
```

## 🛠️ For Developers

### Repository Structure
```
samsara-developer-expert/
├── README.md                    # This file
├── INSTALL.md                   # Detailed installation guide
├── releases/
│   ├── samsara-developer-expert.skill  # For Claude.ai
│   └── latest/                  # Folder for Claude Code/Codex
├── source/
│   └── samsara-developer-expert/
│       ├── SKILL.md             # Universal skill file
│       ├── references/          # 6 reference guides
│       └── scripts/             # 3 helper scripts
├── cursor/
│   └── .cursorrules             # Cursor-specific format
└── scripts/
    └── package_skill.py         # Build tool
```

### Building for Different Platforms

```bash
# Build .skill file for Claude.ai
python scripts/package_skill.py source/samsara-developer-expert releases/

# The source folder works directly for Claude Code/Codex/etc
# No build needed!
```

## 🔄 Updates & Versioning

When we release updates:

| Platform | Update Method |
|----------|--------------|
| Claude.ai | Re-upload new `.skill` file |
| Claude Code | `git pull` in skills directory |
| Codex | `git pull` in skills directory |
| Cursor | Update `.cursorrules` or `git pull` |

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for:
- How to add features
- Testing across platforms
- Submission guidelines

## 📄 License

MIT License - See [LICENSE](LICENSE)

## 🔗 Resources

- [Agent Skills Standard](https://agentskills.io)
- [Claude.ai Skills Docs](https://support.claude.com/en/articles/12512180-using-skills-in-claude)
- [Claude Code Skills Docs](https://code.claude.com/docs/en/skills)
- [Samsara API Docs](https://developers.samsara.com)

## ❓ FAQ

**Q: Which platform should I use?**
- **Web/mobile users**: Claude.ai
- **Terminal users**: Claude Code or Codex CLI
- **IDE users**: Cursor or VS Code

**Q: Can I use this skill on multiple platforms?**
Yes! Install once per platform using the appropriate method.

**Q: Does the skill work offline?**
The skill files are local, but Claude needs internet to process requests.

**Q: How do I know if it's working?**
Just mention "Samsara API" in your conversation. If the skill is active, Claude will use the enhanced knowledge automatically.

---

**Made with ❤️ for developers across all AI coding platforms**

*Compatible with Claude.ai, Claude Code, Codex CLI, Antigravity, Cursor, VS Code, Windsurf, Aider, and more*
