# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, email: security@unicrium.network

Include:
- Type of issue
- Full paths of source file(s) related to the issue
- Location of affected source code
- Step-by-step instructions to reproduce
- Proof-of-concept or exploit code (if possible)
- Impact of the issue

## Security Measures

Unicrium implements multiple security layers:

### Cryptography
- ECDSA signatures on all transactions
- SHA-256 hashing
- Message authentication

### Network
- P2P message verification
- Rate limiting
- DDoS protection
- Peer reputation system

### Consensus
- BFT finality
- Slashing for misbehavior
- Double-sign detection
- Fork resolution

### API
- Input validation
- Client-side signing
- Rate limiting
- CORS configuration

## Bug Bounty

Coming soon! We will reward researchers who responsibly disclose vulnerabilities.
