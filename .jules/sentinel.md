## 2024-05-30 - Insecure Defaults in Settings
**Vulnerability:** The `config/settings.py` module uses insecure default values for `DB_PASSWORD` ("akilli123") and `SECRET_KEY` ("change-this-in-production").
**Learning:** These defaults can inadvertently leak into production environments if not explicitly overridden by environment variables, leading to severe security risks (e.g., unauthorized database access, compromised sessions or cryptographic operations).
**Prevention:** Avoid providing default values for highly sensitive configuration settings. Instead, ensure the application fails fast (e.g., raises an error or throws an exception) if these critical secrets are missing in the environment, enforcing the user to explicitly define them before running the system.
