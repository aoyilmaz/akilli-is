## 2026-02-23 - Hardcoded Admin Backdoor in Exception Handler
**Vulnerability:** Found a hardcoded "admin/admin" login bypass in the `except Exception` block of `ui/screens/login_screen.py`. This would allow anyone to login as admin if the database connection failed or any other exception occurred during login.
**Learning:** Developers likely added this for testing without a database connection but forgot to remove it or wrap it in a proper debug flag check that is disabled in production.
**Prevention:** Use environment variables (DEBUG=True) to gate such logic, or better yet, use a proper mocking strategy for development and never commit authentication bypass code to the main branch.
