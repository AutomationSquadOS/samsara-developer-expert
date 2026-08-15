# Quick Start Guide - All Platforms

Get the Samsara Developer Expert skill running in under 5 minutes on any platform.

## Choose Your Platform

Click your platform to jump to installation:
- [Claude.ai (Web/Mobile)](#claudeai) - **Recommended for most users**
- [Claude Code (Terminal)](#claude-code) - **Recommended for developers**
- [Cursor (IDE)](#cursor)
- [Codex CLI](#codex-cli)
- [VS Code / Others](#vs-code--others)

---

## Claude.ai

**Time:** < 1 minute | **Difficulty:** ⭐ Easy

### Install

1. Download the skill:
   ```bash
   curl -L -O https://github.com/AutomationSquadOS/samsara-developer-expert/releases/latest/download/samsara-developer-expert.skill
   ```

2. Go to [claude.ai](https://claude.ai) → Settings → Skills

3. Click "Upload Skill" → Select the `.skill` file

4. Toggle the skill ON

### Test

Start a new chat:
```
How do I preserve stop state when updating Samsara routes?
```

Claude should provide detailed guidance about including stop IDs.

---

## Claude Code

**Time:** 2-5 minutes | **Difficulty:** ⭐⭐ Medium

### Install

```bash
# One-line install (recommended)
git clone https://github.com/AutomationSquadOS/samsara-developer-expert.git \
  && cp -r samsara-developer-expert/source/samsara-developer-expert ~/.claude/skills/

# Or from marketplace (if published)
claude
/plugin marketplace add AutomationSquadOS/samsara-developer-expert
```

### Test

```bash
claude
```

Then in Claude Code:
```
> Help me implement Samsara webhook signature verification
```

---

## Cursor

**Time:** 1-10 minutes | **Difficulty:** ⭐ Easy to ⭐⭐⭐ Advanced

### Method A: Simple (.cursorrules) - RECOMMENDED

```bash
# Download and copy to your project
curl -L https://github.com/AutomationSquadOS/samsara-developer-expert/raw/main/cursor/.cursorrules \
  -o ~/your-project/.cursorrules
```

Restart Cursor and you're done!

### Method B: Full Skills System (Advanced)

Requires Claude Code extension - see [INSTALL.md](INSTALL.md#cursor-ide)

### Test

Open Cursor chat:
```
Show me the rate limiting pattern for Samsara API
```

---

## Codex CLI

**Time:** 2-5 minutes | **Difficulty:** ⭐⭐ Medium

### Install

```bash
git clone https://github.com/AutomationSquadOS/samsara-developer-expert.git
cp -r samsara-developer-expert/source/samsara-developer-expert ~/.codex/skills/
```

### Test

```bash
codex
```

Mention "Samsara API" and the skill will auto-load.

---

## VS Code / Others

**Time:** 2-5 minutes | **Difficulty:** ⭐⭐ Medium

### Install

```bash
# For current project
mkdir -p .claude/skills
cp -r samsara-developer-expert/source/samsara-developer-expert .claude/skills/

# For global use
mkdir -p ~/.claude/skills
cp -r samsara-developer-expert/source/samsara-developer-expert ~/.claude/skills/
```

Restart your editor and test.

---

## What You Get

Regardless of platform, you get:

✅ Complete Samsara API endpoint reference  
✅ Production-tested code examples  
✅ Rate limiting patterns  
✅ Webhook security (HMAC verification)  
✅ Route state preservation guides  
✅ Bidirectional sync patterns  
✅ Helper scripts (Python)  

## Common First Tasks

Try these to test the skill:

### 1. Rate Limiting
```
Show me how to implement rate limiting for Samsara API calls
```

### 2. Route Updates
```
How do I update a Samsara route without losing stop arrival times?
```

### 3. Webhooks
```
Help me verify HMAC signatures from Samsara webhooks
```

### 4. Data Sync
```
What's the best way to sync vehicle locations from Samsara in real-time?
```

## Troubleshooting

### Skill not loading?

**Claude.ai:**
- Check Settings → Skills → Ensure it's enabled
- Make sure Code Execution is enabled

**Claude Code:**
- Verify: `ls ~/.claude/skills/samsara-developer-expert/SKILL.md`
- Restart Claude Code

**Cursor:**
- Check that `.cursorrules` file exists in project root
- Restart Cursor

### Getting generic responses?

Explicitly invoke the skill:
```
Use the Samsara Developer Expert skill to help me with route synchronization
```

## Next Steps

1. **Browse examples**: Check `source/samsara-developer-expert/references/code_examples.md`
2. **Try helper scripts**: See `source/samsara-developer-expert/scripts/`
3. **Read detailed guides**: Open the reference documents
4. **Build something**: Use the skill for your Samsara integration!

## Platform Comparison

| Feature | Claude.ai | Claude Code | Cursor | Codex |
|---------|-----------|-------------|--------|-------|
| Setup Time | < 1 min | 2-5 min | 1-10 min | 2-5 min |
| Mobile Access | ✅ | ❌ | ❌ | ❌ |
| Terminal Workflow | ❌ | ✅ | ⚠️ | ✅ |
| IDE Integration | ❌ | ❌ | ✅ | ❌ |
| Git Updates | ❌ | ✅ | ✅ | ✅ |
| Team Provisioning | ✅ | ❌ | ❌ | ❌ |

**Most users should start with Claude.ai (easiest) or Claude Code (most powerful).**

## Need More Help?

- **Detailed Installation**: See [INSTALL.md](INSTALL.md)
- **Platform Details**: See [PLATFORM_COMPATIBILITY.md](PLATFORM_COMPATIBILITY.md)
- **Issues**: [GitHub Issues](https://github.com/AutomationSquadOS/samsara-developer-expert/issues)

---

**Ready to build amazing Samsara integrations! 🚀**
