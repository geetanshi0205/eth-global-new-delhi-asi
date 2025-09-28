#!/usr/bin/env python3
"""
Script to fix the missing patient issue by creating the patient in the database
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.operations import PatientOperations

def create_missing_patient():
    """Create the missing patient geetanshigoel63@gmail.com"""
    try:
        print("Creating patient: geetanshigoel63@gmail.com")
        
        patient = PatientOperations.get_or_create_patient(
            email="geetanshigoel63@gmail.com",
            first_name="Geetanshi", 
            last_name="Goel"
        )
        
        print(f"✅ Patient created successfully!")
        print(f"Patient ID: {patient.id}")
        print(f"Name: {patient.name}")
        print(f"Email: {patient.email}")
        
    except Exception as e:
        print(f"❌ Error creating patient: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    success = create_missing_patient()
    sys.exit(0 if success else 1)