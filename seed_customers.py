#!/usr/bin/env python
"""Seed sample Indian defense customers with contacts"""

from database import SessionLocal
from models.entities import Customer

def seed_customers():
    db = SessionLocal()
    
    # Check if customers already exist
    existing = db.query(Customer).count()
    if existing > 0:
        print(f"[INFO] Database already has {existing} customer(s). Skipping seeding.")
        return
    
    customers_data = [
        {
            "name": "Indian Air Force",
            "primary_address": "Air Headquarters, New Delhi, India",
            "contact_name": "Wing Commander Rajesh Kumar",
            "contact_designation": "Deputy Director, Air Operations",
            "contact_email": "r.kumar@iaf.gov.in",
            "contact_phone": "+91 11 2338 1111",
            "contact_rank": "Wing Commander",
            "contact_site": "New Delhi",
            "contacts": [
                {
                    "name": "Squadron Leader Priya Sharma",
                    "designation": "Technical Officer",
                    "email": "p.sharma@iaf.gov.in",
                    "phone": "+91 11 2338 1112",
                    "rank": "Squadron Leader",
                    "site": "Bangalore"
                },
                {
                    "name": "Flight Lieutenant Vikram Singh",
                    "designation": "Maintenance Lead",
                    "email": "v.singh@iaf.gov.in",
                    "phone": "+91 11 2338 1113",
                    "rank": "Flight Lieutenant",
                    "site": "Jodhpur"
                }
            ]
        },
        {
            "name": "Indian Army",
            "primary_address": "Army Headquarters, South Block, New Delhi, India",
            "contact_name": "Colonel Arun Patel",
            "contact_designation": "Chief, Army Aviation",
            "contact_email": "a.patel@army.nic.in",
            "contact_phone": "+91 11 2411 6969",
            "contact_rank": "Colonel",
            "contact_site": "New Delhi",
            "contacts": [
                {
                    "name": "Lieutenant Colonel Deepak Verma",
                    "designation": "Operations Officer",
                    "email": "d.verma@army.nic.in",
                    "phone": "+91 11 2411 6970",
                    "rank": "Lieutenant Colonel",
                    "site": "Pune"
                },
                {
                    "name": "Major Neha Chopra",
                    "designation": "Logistics Coordinator",
                    "email": "n.chopra@army.nic.in",
                    "phone": "+91 11 2411 6971",
                    "rank": "Major",
                    "site": "Meerut"
                },
                {
                    "name": "Captain Sanjay Mishra",
                    "designation": "Technical Support",
                    "email": "s.mishra@army.nic.in",
                    "phone": "+91 11 2411 6972",
                    "rank": "Captain",
                    "site": "Lucknow"
                }
            ]
        },
        {
            "name": "Indian Navy",
            "primary_address": "Naval Headquarters, South Block, New Delhi, India",
            "contact_name": "Commodore Suresh Desai",
            "contact_designation": "Director, Naval Aviation",
            "contact_email": "s.desai@navy.gov.in",
            "contact_phone": "+91 11 2411 1111",
            "contact_rank": "Commodore",
            "contact_site": "New Delhi",
            "contacts": [
                {
                    "name": "Captain Manish Kumar",
                    "designation": "Fleet Operations",
                    "email": "m.kumar@navy.gov.in",
                    "phone": "+91 11 2411 1112",
                    "rank": "Captain",
                    "site": "Kochi"
                },
                {
                    "name": "Commander Anita Gupta",
                    "designation": "Supply Chain Manager",
                    "email": "a.gupta@navy.gov.in",
                    "phone": "+91 11 2411 1113",
                    "rank": "Commander",
                    "site": "Mumbai"
                }
            ]
        }
    ]
    
    for customer_data in customers_data:
        contacts = customer_data.pop("contacts", [])
        
        # Build contacts array
        contacts_array = [
            {
                "name": customer_data.pop("contact_name"),
                "designation": customer_data.pop("contact_designation"),
                "email": customer_data.pop("contact_email"),
                "phone": customer_data.pop("contact_phone"),
                "rank": customer_data.pop("contact_rank"),
                "site": customer_data.pop("contact_site")
            }
        ]
        
        # Add additional contacts
        for contact in contacts:
            contacts_array.append({
                "name": contact["name"],
                "designation": contact["designation"],
                "email": contact["email"],
                "phone": contact["phone"],
                "rank": contact["rank"],
                "site": contact["site"]
            })
        
        customer = Customer(
            name=customer_data["name"],
            data={
                **customer_data,
                "contacts": contacts_array,
                "status": "Active"
            }
        )
        
        db.add(customer)
        print(f"✓ Created customer: {customer_data['name']}")
    
    db.commit()
    print("\n✓ All customers seeded successfully!")


if __name__ == "__main__":
    seed_customers()
