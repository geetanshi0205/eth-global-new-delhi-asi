# Medical Data Marketplace with X402 Integration

## Overview

This project has been converted into a comprehensive **Buyer Agent** that integrates with the X402 payment protocol for purchasing medical data from a marketplace. The agent can retrieve, search, and purchase anonymized medical reports using ETH payments.

## Features

### 🛒 Buyer Functionality
- **List Available Data**: Browse all published medical reports with pricing
- **Search Data**: Find specific types of reports (blood, x-ray, MRI, etc.)
- **Get Data Details**: View detailed information about specific reports
- **Purchase Data**: Buy reports using X402 ETH payment protocol
- **Wallet Management**: Check balance and transaction capacity

### 📋 Seller Functionality (Existing)
- **Add Patient Reports**: Store medical reports with patient authentication
- **Publish Reports**: Anonymize and publish reports to marketplace with pricing
- **List Reports**: View all patient reports for publishing

### 🔒 Security & Privacy
- **HIPAA Compliance**: All published data is fully anonymized
- **Patient Authentication**: MPIN-based access control
- **Blockchain Payments**: Secure ETH transactions on Base Sepolia

## Available MCP Tools

### For Buyers:
1. **`get_marketplace_reports`** - List available data with pricing
2. **`search_data`** - Search for specific types of medical data
3. **`get_data_details`** - Get detailed info about a specific report
4. **`buy_data_by_id`** - Purchase data using X402 ETH payment
5. **`check_buyer_wallet`** - Check wallet balance and purchase capacity

### For Sellers:
1. **`add_patient_report`** - Add new patient reports
2. **`publish_report`** - Publish anonymized reports with pricing
3. **`list_all_reports`** - View all patient reports

## Usage Examples

### 🔍 Browsing and Searching Data
```
# List all available data
get_marketplace_reports

# Search for blood test reports
search_data blood

# Search for X-ray reports
search_data xray

# Get details about a specific report
get_data_details <report-id>
```

### 💳 Purchasing Data
```
# Check your wallet balance first
check_buyer_wallet

# Purchase a specific report
buy_data_by_id <report-id>
```

### 📋 Publishing Data (Sellers)
```
# Publish a report to marketplace
publish_report <report-id> <patient-email> <mpin> <price-eth> <seller-wallet> --title "Report Title" --description "Description"
```

## X402 Payment Integration

The agent integrates the X402 payment protocol for seamless ETH transactions:

1. **Automatic Payment**: When purchasing data, the agent automatically initiates ETH payment
2. **Real-time Verification**: Payments are verified on Base Sepolia blockchain
3. **Instant Delivery**: Upon successful payment, anonymized content is immediately delivered
4. **Transaction Tracking**: All purchases include transaction hash for verification

## Database Schema

### Published Reports Table
- `id`: UUID primary key
- `title`: Report title
- `description`: Report description
- `report_type`: Type of medical report
- `price_eth`: Price in ETH (e.g., 0.001)
- `seller_wallet`: Wallet address to receive payment
- `anonymized_content`: HIPAA-compliant anonymized medical data
- `tags`: Searchable tags
- `test_date`: Original test date
- `published_at`: Publication timestamp
- `is_active`: Available for purchase

## Environment Configuration

Required environment variables:
```env
# Database
DATABASE_URL=postgresql://...

# X402 Payment
PRIVATE_KEY=your_eth_private_key
RECIPIENT_WALLET=your_wallet_address

# LLM for anonymization
ASI1_API_KEY=your_asi_api_key
```

## Getting Started

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment**
   - Copy `.env.example` to `.env`
   - Add your private key and wallet address
   - Configure database connection

3. **Run Database Migration**
   ```bash
   python3 migrate_db.py
   ```

4. **Start the Agent**
   ```bash
   python3 agent.py
   ```

5. **Test Functionality**
   ```bash
   python3 test_buyer_agent.py
   ```

## Security Considerations

- **Private Keys**: Store securely, never commit to version control
- **Data Anonymization**: All PHI/PII is removed before publishing
- **Payment Security**: Transactions are verified on blockchain
- **Access Control**: MPIN-based patient authentication

## Blockchain Network

- **Network**: Base Sepolia (Testnet)
- **Currency**: ETH
- **Gas Optimization**: Uses efficient gas pricing for transactions

## Contributing

This marketplace agent provides a complete solution for buying and selling anonymized medical data with integrated X402 payments. The system ensures privacy, security, and seamless transactions for all participants.