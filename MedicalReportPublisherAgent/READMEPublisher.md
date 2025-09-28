# Medical Report Publisher Agent
![tag:innovationlab](https://img.shields.io/badge/innovationlab-3D8BD3)
![tag:hackathon](https://img.shields.io/badge/hackathon-5F43F1)

A secure, HIPAA-compliant AI agent for managing and publishing anonymized medical reports to a decentralized marketplace. Built for ETHGlobal New Delhi, this agent enables healthcare professionals and patients to securely share medical data while maintaining privacy and earning cryptocurrency rewards.

## 🏥 Overview

The Medical Report Publisher Agent is a specialized AI agent that handles the complete lifecycle of medical report management - from secure storage with MPIN authentication to HIPAA-compliant anonymization and marketplace publication. It uses advanced AI for medical text de-identification and integrates with Ethereum for decentralized payments.

## ✨ Key Features

- **🔐 Secure Authentication**: MPIN-based patient authentication system
- **🏥 Medical Data Management**: Store and retrieve medical reports with full metadata
- **🤖 AI-Powered Anonymization**: Automatic HIPAA-compliant de-identification using ASI LLM
- **💰 Decentralized Marketplace**: Publish anonymized reports for ETH payments
- **🛡️ Privacy-First**: Zero personal health information (PHI) in published content
- **📊 Multi-Format Support**: Support for various medical report types (blood work, X-rays, etc.)

## 🏗️ Architecture

```
┌─────────────────────┐    ┌──────────────────────┐    ┌─────────────────────┐
│   uAgents Network   │    │    FastMCP Server    │    │   PostgreSQL DB     │
│                     │◄──►│                      │◄──►│                     │
│ - Agent Discovery   │    │ - Medical Report API │    │ - Patient Reports   │
│ - Protocol Handling │    │ - HIPAA Anonymizer   │    │ - Published Reports │
│ - Mailbox System   │    │ - Marketplace Tools  │    │ - Authentication    │
└─────────────────────┘    └──────────────────────┘    └─────────────────────┘
                                       │
                                       ▼
                           ┌──────────────────────┐
                           │     ASI1 LLM API     │
                           │                      │
                           │ - Text Anonymization │
                           │ - HIPAA Compliance   │
                           │ - Medical Context    │
                           └──────────────────────┘
```

