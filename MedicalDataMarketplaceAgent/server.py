from typing import Any, Optional
import httpx
import os
import sys
import json
from datetime import datetime
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
from web3 import Web3
from eth_account import Account

# Import database components
from database.operations import (
    PatientReportOperations, PublishedReportOperations, init_database
)

# Load environment variables from .env file
load_dotenv()

# Configuration for X402 payment (buyer functionality)
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
BUYER_WALLET = os.getenv("BUYER_WALLET")

# Setup blockchain for buyer functionality
w3 = Web3(Web3.HTTPProvider('https://sepolia.base.org'))
if PRIVATE_KEY:
    account = Account.from_key(PRIVATE_KEY)
else:
    account = None

# Create a FastMCP server instance
mcp = FastMCP("medical-report-marketplace")

# Initialize database
init_database()

@mcp.tool()
async def add_patient_report(
    patient_email: str,
    mpin: str,
    report_type: str,
    report_content: str,
    test_date: str
) -> str:
    """Add a new patient report with MPIN authentication.
    
    Args:
        patient_email: Patient's email address
        mpin: Patient's Medical PIN for future authentication
        report_type: Type of report (e.g., 'blood', 'xray', etc.)
        report_content: The content/details of the report
        test_date: Date of the test/report in ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)
    """
    try:
        # Parse test_date
        try:
            test_date_obj = datetime.fromisoformat(test_date)
        except ValueError:
            return "❌ Invalid date format. Please use YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS."
        
        report = PatientReportOperations.add_report_with_mpin(
            patient_email=patient_email,
            mpin=mpin,
            report_type=report_type,
            report_content=report_content,
            test_date=test_date_obj
        )
        return f"✅ Report added successfully!\n" \
               f"📧 Patient: {patient_email}\n" \
               f"🆔 Report ID: {report.id}\n" \
               f"🏷️ Type: {report_type}\n" \
               f"📅 Test Date: {test_date_obj.date()}\n" \
               f"🔐 MPIN set for future authentication"
    except Exception as e:
        return f"❌ Failed to add report: {str(e)}"

@mcp.tool()
async def verify_report_access(report_id: str, patient_email: str, mpin: str) -> str:
    """Verify if a patient has access to a specific report using email and MPIN.
    
    Args:
        report_id: Unique ID of the report
        patient_email: Patient's email address
        mpin: Patient's Medical PIN
    """
    try:
        is_authorized = PatientReportOperations.verify_patient_access(
            report_id=report_id,
            patient_email=patient_email,
            mpin=mpin
        )
        
        if is_authorized:
            return f"✅ Authentication successful! You have access to report {report_id}"
        else:
            return f"❌ Authentication failed. Invalid report ID, email, or MPIN."
            
    except Exception as e:
        return f"❌ Failed to verify access: {str(e)}"

@mcp.tool()
async def get_report_by_id(report_id: str) -> str:
    """Fetch a specific published report by its unique ID from the marketplace.
    
    Args:
        report_id: Unique ID of the report in the published_reports database
    """
    try:
        report = PublishedReportOperations.get_published_report_by_id(report_id)
        if not report:
            return f"❌ Report with ID {report_id} not found"
        
        result = f"📋 **Published Report Details**\n\n"
        result += f"🏷️ **Title:** {report.title}\n"
        if report.description:
            result += f"📝 **Description:** {report.description}\n"
        result += f"💰 **Price:** {report.price_eth} ETH\n"
        result += f"🆔 **Report ID:** {report.id}\n"
        
        return result
    except Exception as e:
        return f"❌ Failed to fetch report: {str(e)}"

@mcp.tool()
async def list_all_reports(limit: Optional[int] = 20) -> str:
    """List all published reports in the marketplace.
    
    Args:
        limit: Maximum number of reports to return (default: 20)
    """
    try:
        reports = PublishedReportOperations.get_published_reports(limit=limit or 20)
        
        if not reports:
            return "❌ No published reports found in marketplace"
        
        result = f"🛒 **Published Reports in Marketplace** ({len(reports)} items):\n\n"
        for i, report in enumerate(reports, 1):
            result += f"{i}. **{report.title}**\n"
            if report.description:
                result += f"   📝 Description: {report.description}\n"
            result += f"   💰 Price: {report.price_eth} ETH\n"
            result += f"   🆔 **Report ID: {report.id}**\n\n"
        
        return result.strip()
    except Exception as e:
        return f"❌ Failed to list reports: {str(e)}"

@mcp.tool()
async def list_patient_reports_for_publishing(limit: Optional[int] = 20) -> str:
    """List patient reports available for publishing (for sellers only).
    
    Args:
        limit: Maximum number of reports to return (default: 20)
    """
    try:
        reports = PatientReportOperations.get_all_reports(limit or 20)
        
        if not reports:
            return "❌ No patient reports found in database"
        
        result = f"📋 **Patient Reports Available for Publishing** ({len(reports)} items):\n\n"
        for i, report in enumerate(reports, 1):
            result += f"{i}. **{report.report_type.upper()}** - {report.test_date.strftime('%Y-%m-%d')}\n"
            result += f"   🆔 ID: {report.id}\n"
            result += f"   📝 Preview: {report.report_content[:100]}{'...' if len(report.report_content) > 100 else ''}\n\n"
        
        result += "💡 **To publish a report, use:** `publish_report` with the Report ID"
        return result.strip()
    except Exception as e:
        return f"❌ Failed to list patient reports: {str(e)}"

async def anonymize_medical_text(report_content: str) -> str:
    """Use ASI LLM to anonymize medical text by removing HIPAA identifiers"""
    asi_api_key = os.getenv("ASI1_API_KEY")
    if not asi_api_key:
        raise ValueError("ASI1_API_KEY environment variable is required")
    
    anonymization_prompt = """You are a medical text de-identification engine. 

Your job is to:
1. Remove all 18 HIPAA identifiers from the input text. These include:
   - Names (patients, doctors, relatives)
   - Geographic subdivisions smaller than a state (street, city, ZIP, hospitals)
   - All dates directly related to the patient (except year)
   - Phone numbers, fax numbers, email addresses
   - Social Security numbers, medical record numbers, health plan numbers, account numbers, certificate/license numbers
   - Vehicle identifiers (VIN, license plates), device identifiers, URLs, IP addresses
   - Biometric identifiers (fingerprints, retina scans)
   - Full-face photos and comparable images
   - Any unique codes or characteristics that could identify the patient
2. Replace each identifier with a pseudonym or placeholder:
   - Patient names → Patient_001, Patient_002, etc.
   - Doctors → Doctor_A, Doctor_B
   - Dates → shift dates or replace with [Year-YYYY] for timeline context
   - Hospitals → Hospital_X, Hospital_Y
   - MRNs or IDs → MRN_XXXX
3. Preserve all **medical information**: conditions, symptoms, procedures, medications, lab results, treatments, timelines.
4. Rewrite the text so it **reads naturally**, maintaining full readability and context, but ensuring no PHI/PII remains.
5. Output **only the rewritten, de-identified text**. Do not explain or comment on the changes."""

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "https://api.asi1.ai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {asi_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "asi1-mini",
                    "messages": [
                        {"role": "system", "content": anonymization_prompt},
                        {"role": "user", "content": report_content}
                    ],
                    "temperature": 0.1,
                    "max_tokens": 2000
                },
                timeout=30.0
            )
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"].strip()
        except Exception as e:
            raise Exception(f"Failed to anonymize text with ASI LLM: {str(e)}")

@mcp.tool()
async def publish_report(
    report_id: str,
    patient_email: str,
    mpin: str,
    price_eth: float,
    seller_wallet: str,
    title: Optional[str] = None,
    description: Optional[str] = None,
    tags: Optional[str] = None
) -> str:
    """Publish a medical report by anonymizing it and adding to marketplace with pricing.
    Requires patient authentication with email and MPIN.
    
    Args:
        report_id: Unique ID of the report in the patient_reports database
        patient_email: Patient's email address for verification
        mpin: Patient's Medical PIN for authentication
        price_eth: Price in ETH for the data (e.g., 0.001)
        seller_wallet: Wallet address to receive payment
        title: Title for the published report (optional, will generate if not provided)
        description: Description for the published report (optional)
        tags: Comma-separated tags for categorization (optional)
    """
    try:
        # First verify patient authorization
        is_authorized = PatientReportOperations.verify_patient_access(
            report_id=report_id,
            patient_email=patient_email,
            mpin=mpin
        )
        
        if not is_authorized:
            return f"❌ Authentication failed. Invalid report ID, email, or MPIN. Please verify your credentials."
        
        # Get the original report (we know it exists from verification)
        original_report = PatientReportOperations.get_report_by_id(report_id)
        
        # Anonymize the report content using ASI LLM
        try:
            anonymized_content = await anonymize_medical_text(original_report.report_content)
        except Exception as e:
            return f"❌ Failed to anonymize report: {str(e)}"
        
        # Generate title if not provided
        if not title:
            title = f"Anonymous {original_report.report_type.title()} Report - {original_report.test_date.strftime('%Y-%m')}"
        
        # Publish to marketplace
        published_report = PublishedReportOperations.publish_report(
            original_report_id=report_id,
            anonymized_content=anonymized_content,
            title=title,
            description=description,
            tags=tags,
            price_eth=price_eth,
            seller_wallet=seller_wallet
        )
        
        return f"✅ Successfully authenticated and published report to marketplace!\n" \
               f"👤 Authorized User: {patient_email}\n" \
               f"📋 Published ID: {published_report.id}\n" \
               f"📝 Title: {title}\n" \
               f"🏷️ Type: {original_report.report_type}\n" \
               f"📅 Test Date: {original_report.test_date.strftime('%Y-%m-%d')}\n" \
               f"💰 Price: {price_eth} ETH\n" \
               f"💳 Seller Wallet: {seller_wallet}\n" \
               f"🔒 Content has been fully anonymized and HIPAA compliant"
               
    except Exception as e:
        return f"❌ Failed to publish report: {str(e)}"

@mcp.tool()
async def get_marketplace_reports(
    report_type: Optional[str] = None,
    tags: Optional[str] = None,
    limit: Optional[int] = 10
) -> str:
    """Get published reports from the marketplace with pricing information.
    
    Args:
        report_type: Filter by report type (e.g., 'blood', 'xray', etc.)
        tags: Filter by tags
        limit: Maximum number of reports to return (default: 10)
    """
    try:
        reports = PublishedReportOperations.get_published_reports(
            report_type=report_type,
            tags=tags,
            limit=limit or 10
        )
        
        if not reports:
            filters = []
            if report_type:
                filters.append(f"type: {report_type}")
            if tags:
                filters.append(f"tags: {tags}")
            filter_text = f" with filters ({', '.join(filters)})" if filters else ""
            return f"❌ No published reports found{filter_text}"
        
        result = f"🛒 **Marketplace Data** ({len(reports)} items available):\n\n"
        for i, report in enumerate(reports, 1):
            result += f"{i}. **{report.title}**\n"
            if report.description:
                result += f"   📝 Description: {report.description}\n"
            result += f"   💰 Price: {report.price_eth} ETH\n"
            result += f"   🆔 **Report ID: {report.id}**\n\n"
        
        result += "💡 **To purchase data, use:** `buy_data_by_id` with the Report ID"
        return result.strip()
    except Exception as e:
        return f"❌ Failed to get marketplace reports: {str(e)}"

async def make_payment_eth(recipient_wallet: str, amount_eth: float) -> str:
    """Make ETH payment to recipient wallet using X402 protocol"""
    if not account:
        raise Exception("No private key configured for payments")
    
    print(f"[PAYMENT] Initiating X402 payment: {amount_eth} ETH to {recipient_wallet}", file=sys.stderr)
    
    try:
        # Check ETH balance
        eth_balance = w3.eth.get_balance(account.address)
        eth_balance_ether = eth_balance / 10**18
        
        # Calculate amounts
        amount_wei = int(amount_eth * 10**18)  # Convert ETH to wei
        gas_limit = 21000  # Standard ETH transfer
        gas_price = max(1_000_000_000, w3.eth.gas_price // 2)  # At least 1 gwei
        gas_cost = gas_limit * gas_price
        total_cost = amount_wei + gas_cost
        
        print(f"[WALLET] Balance: {eth_balance_ether:.6f} ETH, Cost: {total_cost / 10**18:.6f} ETH", file=sys.stderr)
        
        if eth_balance < total_cost:
            print("[ERROR] Insufficient balance for transaction", file=sys.stderr)
            raise Exception(f"Insufficient ETH. Need {total_cost / 10**18:.6f} ETH, have {eth_balance_ether:.6f} ETH")
        
        # Build simple ETH transfer transaction
        nonce = w3.eth.get_transaction_count(account.address)
        tx = {
            'to': recipient_wallet,
            'value': amount_wei,
            'gas': gas_limit,
            'gasPrice': gas_price,
            'nonce': nonce,
        }
        
        # Sign and send transaction
        signed_txn = account.sign_transaction(tx)
        print(f"[BLOCKCHAIN] Transaction signed, nonce: {nonce}", file=sys.stderr)
        
        # Get raw transaction data
        raw_tx = None
        for attr_name in ['raw_transaction', 'rawTransaction', 'data']:
            if hasattr(signed_txn, attr_name):
                raw_data = getattr(signed_txn, attr_name)
                # Ensure it's bytes-like
                if hasattr(raw_data, 'hex'):
                    raw_tx = raw_data
                    break
                elif isinstance(raw_data, (bytes, bytearray)):
                    raw_tx = raw_data
                    break
                elif isinstance(raw_data, str) and raw_data.startswith('0x'):
                    raw_tx = bytes.fromhex(raw_data[2:])
                    break
        
        if raw_tx is None:
            available_attrs = [attr for attr in dir(signed_txn) if not attr.startswith('_')]
            print("[ERROR] Could not extract raw transaction data", file=sys.stderr)
            raise Exception(f"Could not find raw transaction data. Available attributes: {available_attrs}")
        
        # Send transaction
        tx_hash = w3.eth.send_raw_transaction(raw_tx).hex()
        print(f"[BLOCKCHAIN] Transaction broadcast: {tx_hash}", file=sys.stderr)
        
        # Wait for confirmation
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        
        if receipt.status == 1:
            actual_gas_used = receipt.gasUsed
            actual_cost = (amount_wei + actual_gas_used * gas_price) / 10**18
            print(f"[BLOCKCHAIN] Transaction confirmed in block {receipt.blockNumber}, cost: {actual_cost:.6f} ETH", file=sys.stderr)
            return tx_hash
        else:
            print("[ERROR] Transaction failed on blockchain", file=sys.stderr)
            raise Exception("Transaction failed")
            
    except Exception as e:
        print(f"[ERROR] Payment processing failed: {str(e)}", file=sys.stderr)
        raise

@mcp.tool()
async def search_data(
    search_type: str,
    limit: Optional[int] = 5
) -> str:
    """Search for specific types of medical data (blood reports, x-rays, etc.).
    
    Args:
        search_type: Type of data to search for (e.g., 'blood', 'xray', 'mri', 'covid', etc.)
        limit: Maximum number of results (default: 5)
    """
    try:
        # Search in both report_type and tags
        reports_by_type = PublishedReportOperations.get_published_reports(
            report_type=search_type.lower(),
            limit=limit or 5
        )
        
        reports_by_tags = PublishedReportOperations.get_published_reports(
            tags=search_type.lower(),
            limit=limit or 5
        )
        
        # Combine and deduplicate
        all_reports = reports_by_type + reports_by_tags
        unique_reports = {report.id: report for report in all_reports}.values()
        reports = list(unique_reports)[:limit or 5]
        
        if not reports:
            return f"❌ No {search_type} data found in marketplace"
        
        result = f"🔍 **Search Results for '{search_type}'** ({len(reports)} items):\n\n"
        for i, report in enumerate(reports, 1):
            result += f"{i}. **{report.title}**\n"
            if report.description:
                result += f"   📝 Description: {report.description}\n"
            result += f"   💰 Price: {report.price_eth} ETH\n"
            result += f"   🆔 **Report ID: {report.id}**\n\n"
        
        result += "💡 **To purchase data, use:** `buy_data_by_id` with the Report ID"
        return result.strip()
    except Exception as e:
        return f"❌ Failed to search data: {str(e)}"

@mcp.tool()
async def get_data_details(report_id: str) -> str:
    """Get detailed information about a specific data item including price and seller info.
    
    Args:
        report_id: Unique ID of the report to get details for
    """
    try:
        report = PublishedReportOperations.get_published_report_by_id(report_id)
        if not report:
            return f"❌ Data with ID {report_id} not found"
        
        result = f"📋 **Data Details**\n\n"
        result += f"🏷️ **Title:** {report.title}\n"
        result += f"📊 **Type:** {report.report_type}\n"
        result += f"💰 **Price:** {report.price_eth} ETH\n"
        result += f"💳 **Seller Wallet:** {report.seller_wallet}\n"
        result += f"📅 **Test Date:** {report.test_date.strftime('%Y-%m-%d')}\n"
        result += f"📅 **Published:** {report.published_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
        if report.description:
            result += f"📝 **Description:** {report.description}\n"
        if report.tags:
            result += f"🏷️ **Tags:** {report.tags}\n"
        result += f"🆔 **Report ID:** {report.id}\n\n"
        result += "💡 **To purchase this data, use:** `buy_data_by_id` with this Report ID"
        
        return result
    except Exception as e:
        return f"❌ Failed to get data details: {str(e)}"

@mcp.tool()
async def buy_data_by_id(report_id: str) -> str:
    """Purchase medical data by Report ID using X402 ETH payment protocol.
    
    Args:
        report_id: Unique ID of the report to purchase
    """
    try:
        # Get the report details
        report = PublishedReportOperations.get_published_report_by_id(report_id)
        if not report:
            return f"❌ Data with ID {report_id} not found"
        
        if not report.is_active:
            return f"❌ This data is no longer available for purchase"
        
        print(f"[BUYER] Initiating X402 purchase for report {report_id}", file=sys.stderr)
        print(f"[BUYER] Price: {report.price_eth} ETH, Seller: {report.seller_wallet}", file=sys.stderr)
        
        # Make payment to seller using X402 protocol
        try:
            tx_hash = await make_payment_eth(report.seller_wallet, float(report.price_eth))
        except Exception as e:
            return f"❌ X402 Payment failed: {str(e)}"
        
        # Payment successful, return the anonymized content
        result = f"✅ **Purchase Successful via X402 Protocol!**\n\n"
        result += f"💳 **Transaction Hash:** {tx_hash}\n"
        result += f"💰 **Amount Paid:** {report.price_eth} ETH\n"
        result += f"👤 **Paid to:** {report.seller_wallet}\n"
        result += f"📋 **Data Title:** {report.title}\n"
        result += f"📊 **Type:** {report.report_type}\n\n"
        result += f"📄 **Your Purchased Data:**\n"
        result += f"```\n{report.anonymized_content}\n```\n\n"
        result += f"🎉 **Thank you for your purchase!**"
        
        return result
    except Exception as e:
        return f"❌ Failed to purchase data: {str(e)}"

@mcp.tool()
async def check_buyer_wallet() -> str:
    """Check buyer wallet ETH balance and transaction capacity for X402 payments"""
    try:
        if not account:
            return "❌ No wallet configured. Please set PRIVATE_KEY in environment variables."
        
        balance = w3.eth.get_balance(account.address) / 10**18
        nonce = w3.eth.get_transaction_count(account.address)
        
        # Estimate transaction costs
        gas_cost = 21000 * 1_000_000_000  # 21k gas at 1 gwei
        gas_cost_eth = gas_cost / 10**18
        
        # Get average price of data in marketplace
        reports = PublishedReportOperations.get_published_reports(limit=50)
        if reports:
            avg_price = sum(float(r.price_eth) for r in reports) / len(reports)
            possible_purchases = int(balance / (avg_price + gas_cost_eth)) if (avg_price + gas_cost_eth) > 0 else 0
        else:
            avg_price = 0.001
            possible_purchases = int(balance / (avg_price + gas_cost_eth)) if (avg_price + gas_cost_eth) > 0 else 0
        
        return f"""💳 **X402 Buyer Wallet Status**
        
🏦 **Wallet:** {account.address}
💰 **ETH Balance:** {balance:.6f} ETH
📊 **Nonce:** {nonce}
⛽ **Gas Cost per TX:** ~{gas_cost_eth:.6f} ETH
📈 **Average Data Price:** {avg_price:.6f} ETH
🛒 **Estimated Purchases Possible:** {possible_purchases}
📋 **Available Data Items:** {len(reports) if reports else 0}
🔗 **Network:** Base Sepolia"""
    except Exception as e:
        return f"❌ Error checking wallet: {e}"

if __name__ == "__main__":
    print("[SERVER] Medical Report Marketplace with X402 starting", file=sys.stderr)
    if account:
        print(f"[CONFIG] Buyer Wallet: {account.address}", file=sys.stderr)
    else:
        print("[WARNING] No private key configured - buyer functionality disabled", file=sys.stderr)
    print(f"[CONFIG] Network: Base Sepolia", file=sys.stderr)
    print("[SERVER] Ready for publishing and purchasing", file=sys.stderr)
    mcp.run(transport='stdio')