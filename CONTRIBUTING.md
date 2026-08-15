# Contributing to Samsara Developer Expert Skill

Thank you for your interest in contributing! This document provides guidelines for contributing to this Claude skill.

## How to Contribute

### Reporting Issues

If you find a bug or have a suggestion:

1. Check if the issue already exists in [Issues](../../issues)
2. If not, create a new issue with:
   - Clear title and description
   - Steps to reproduce (for bugs)
   - Expected vs actual behavior
   - Your environment details

### Submitting Changes

1. **Fork the Repository**
   ```bash
   git clone https://github.com/AutomationSquadOS/samsara-developer-expert.git
   cd samsara-developer-expert
   ```

2. **Create a Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make Your Changes**
   - Edit files in `source/samsara-developer-expert/`
   - Follow the existing structure:
     - `SKILL.md` - Main skill documentation
     - `references/` - Detailed reference guides
     - `scripts/` - Helper scripts

4. **Test Your Changes**
   - Package the skill: 
     ```bash
     python scripts/package_skill.py source/samsara-developer-expert releases/
     ```
   - Upload the generated `.skill` file to Claude
   - Test that it works as expected

5. **Commit Your Changes**
   ```bash
   git add .
   git commit -m "Add feature: description of your changes"
   ```

6. **Push and Create PR**
   ```bash
   git push origin feature/your-feature-name
   ```
   - Go to GitHub and create a Pull Request
   - Describe your changes clearly
   - Link any related issues

## Skill Structure Guidelines

### SKILL.md

- Keep concise (< 500 lines)
- Use imperative form ("Create the route" not "You should create")
- Reference detailed docs in `references/`
- Include when-to-use info in frontmatter description

### Reference Documents

- Create focused, topic-specific guides
- Include code examples
- Use real-world patterns
- Keep under 1000 lines each

### Scripts

- Must be executable (`chmod +x`)
- Include docstrings
- Test before committing
- Add usage examples at bottom

## Code Style

### Markdown
- Use headers appropriately (# for main, ## for sections)
- Include code blocks with language tags
- Keep line length reasonable (< 120 chars when possible)

### Python
- Follow PEP 8
- Include type hints
- Add docstrings to functions
- Use meaningful variable names

### TypeScript
- Use clear type annotations
- Follow consistent indentation (2 spaces)
- Add JSDoc comments for complex functions

## What to Contribute

We welcome contributions in these areas:

### Documentation Improvements
- Clarifying existing content
- Adding more examples
- Fixing typos or errors
- Adding diagrams or visualizations

### Code Examples
- Real-world implementation patterns
- Error handling examples
- Performance optimizations
- Testing examples

### Helper Scripts
- Additional utility functions
- New language implementations
- Improved error handling
- Better logging

### Reference Updates
- New API endpoints
- Updated best practices
- Additional use cases
- Common pitfalls

## Questions?

Feel free to:
- Open an issue for discussion
- Ask questions in pull request comments
- Reach out to maintainers

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
