# Lab Agent
![tag:innovationlab](https://img.shields.io/badge/innovationlab-3D8BD3)
![tag:hackathon](https://img.shields.io/badge/hackathon-5F43F1)

A healthcare management agent built with Fetch.ai's uAgents framework and MCP (Model Control Protocol) that provides comprehensive patient data management, appointment scheduling, and secure lab report distribution.

## Features

### Patient Management
- **Patient Registration**: Add and manage patient information with email, phone, and notes
- **Patient Data Retrieval**: Query patient information using email as identifier
- **Prescription Management**: Track medications, dosages, and prescription history

### Appointment System
- **Cal.com Integration**: Schedule appointments through Cal.com API
- **Appointment Management**: Create, view, and manage patient appointments
- **Multi-timezone Support**: Defaults to Asia/Kolkata timezone

### Lab Report System
- **Secure Report Storage**: Store patient lab reports with encrypted access
- **MPIN Authentication**: 6-digit secure access codes for report retrieval
- **Email Notifications**: Automated email alerts with report IDs and MPINs
- **Report Types**: Support for various report types (blood, xray, etc.)
- **Date Filtering**: Query reports by date and type
