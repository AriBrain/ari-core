## Contributing to ARIBrain (Internal Team)

This repository is actively maintained by the ARIBrain development team. If you are a contributor with internal access, please follow the workflow below to ensure smooth collaboration.

---

### Workflow Overview

1. **Fork the Repository**
   - Navigate to: https://github.com/AriBrain/ari-core
   - Click on **Fork** (top-right corner).
   - This will create a copy under your personal GitHub account.

2. **Clone Your Fork**
   ```bash
   git clone https://github.com/YOUR_USERNAME/ari-core.git
   cd ari-core
   ```

3. **Add Upstream Remote**
   This lets you pull updates from the official repo.
   ```bash
   git remote add upstream https://github.com/AriBrain/ari-core.git
   ```

4. **Create a New Feature or Fix Branch**
   Always branch off from `main`:
   ```bash
   git checkout main
   git fetch upstream
   git merge upstream/main
   git checkout -b feat/your-feature-name
   ```

5. **Develop and Commit**
   - Write your code and commit changes with meaningful messages.
   - Follow existing coding and style conventions.

6. **Push Your Branch**
   ```bash
   git push origin feat/your-feature-name
   ```

7. **Create a Pull Request (PR)**
   - Go to your fork on GitHub.
   - Open a PR against `AriBrain/ari-core:main`.
   - Add a short description and context for your changes.

8. **Review and Merge**
   - One team member reviews and approves your PR.
   - You or the reviewer merges once approved.

---

### Development Guidelines

- Use Python **3.10.14**
- All C++ extensions must compile cleanly across platforms (macOS, Linux)
- Install dependencies via `requirements.txt` or `pyproject.toml`
- Use `pipx` and `pyenv` for isolated testing

---

### 🔄 Staying Updated

To keep your local fork up to date:
```bash
git fetch upstream
git checkout main
git merge upstream/main
```