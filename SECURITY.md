# Security Policy

## Supported Versions

We actively support the following versions with security updates:

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

If you discover a security vulnerability, please report it to us as follows:

### Contact

**Please DO NOT report security vulnerabilities through public GitHub issues.**

Instead, please report security vulnerabilities by emailing:
- **security@stateset.io** (preferred)
- Or open a private security advisory on GitHub

### What to Include

When reporting a vulnerability, please include:

- A clear description of the vulnerability
- Steps to reproduce the issue
- Potential impact and severity
- Any suggested fixes or mitigations
- Your contact information for follow-up

### Our Response Process

1. **Acknowledgment**: We'll acknowledge receipt within 24 hours
2. **Investigation**: We'll investigate and validate the vulnerability
3. **Fix Development**: We'll develop and test a fix
4. **Disclosure**: We'll coordinate disclosure with you
5. **Release**: We'll release the fix and security advisory

We follow responsible disclosure practices and will work with you to ensure vulnerabilities are fixed before public disclosure.

## Security Best Practices

### For Users

- Keep your API keys and tokens secure
- Use strong, unique passwords
- Regularly update dependencies
- Monitor your usage and logs for suspicious activity
- Use HTTPS when accessing the application

### For Contributors

- Never commit API keys or sensitive credentials
- Use environment variables for configuration
- Validate all inputs and sanitize outputs
- Follow secure coding practices
- Keep dependencies updated

## Known Security Considerations

### API Keys and Authentication

- Store API keys securely using environment variables
- Never commit API keys to version control
- Rotate keys regularly
- Use least-privilege access

### Data Privacy

- This application processes text data for synthetic data generation
- No user data is stored permanently unless explicitly saved
- Generated data should be reviewed before use
- Consider data privacy regulations (GDPR, CCPA, etc.)

### Network Security

- The application runs locally by default
- Configure firewalls appropriately
- Use HTTPS in production deployments
- Monitor network traffic for anomalies

## Security Updates

Security updates will be released as patch versions and will be clearly marked in the changelog. We recommend keeping the application updated to the latest version.

## Contact

For security-related questions or concerns:
- Email: security@stateset.com
- GitHub Security Advisories: https://github.com/stateset/stateset-data-studio/security/advisories
