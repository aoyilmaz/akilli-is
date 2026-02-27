## 2024-05-24 - [CRITICAL] Development Backdoors in Production Code
**Vulnerability:** Authentication bypass logic ("Direct Mode") and hardcoded credentials (`admin`/`admin`) were found in `main.py` and `ui/screens/login_screen.py`. These were likely intended for development convenience but were left in the production codebase.
**Learning:** Developers often add shortcuts to bypass repetitive login flows during testing. Without strict separation of development and production configurations, these shortcuts become critical vulnerabilities.
**Prevention:**
1. Use environment variables (e.g., `ENV=development`) to conditionally enable debug features, and ensure these blocks are unreachable in production builds.
2. Never hardcode credentials, even for "fallback" scenarios.
3. Implement automated tests that verify the authentication flow is *enforced* by default, ensuring no "bypass" flag is accidentally left on.
