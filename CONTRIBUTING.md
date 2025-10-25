# Contributing to Unicrium Network

Thank you for your interest in contributing to Unicrium! 🎉

## Code of Conduct

Be respectful, constructive, and collaborative.

## How to Contribute

### 1. Report Bugs
Open an issue with:
- Description of the bug
- Steps to reproduce
- Expected vs actual behavior
- Environment details

### 2. Suggest Features
Open an issue with:
- Feature description
- Use case
- Proposed implementation (optional)

### 3. Submit Pull Requests

#### Setup
```bash
git clone https://github.com/yourusername/unicrium-network.git
cd unicrium-network
python3 -m venv venv
source venv/bin/activate
pip install -r requirements-dev.txt
```

#### Development Workflow
1. Create feature branch: `git checkout -b feature/my-feature`
2. Make changes
3. Run tests: `pytest`
4. Run linter: `black . && flake8`
5. Commit: `git commit -m "Add: my feature"`
6. Push: `git push origin feature/my-feature`
7. Open Pull Request

#### Commit Messages
- Use present tense: "Add feature" not "Added feature"
- Use imperative mood: "Move cursor to..." not "Moves cursor to..."
- Reference issues: "Fix #123: description"

### 4. Write Tests
All new features must include tests.

```python
def test_my_feature():
    # Test code
    assert result == expected
```

## Development Guidelines

### Code Style
- Follow PEP 8
- Use type hints
- Write docstrings
- Keep functions small and focused

### Testing
- Unit tests for all modules
- Integration tests for features
- Minimum 80% code coverage

### Documentation
- Update README for user-facing changes
- Add docstrings to functions/classes
- Update API docs if needed

## Questions?

Join our [Discord](https://discord.gg/unicrium) or open a discussion on GitHub!
