"""
Seed script: run with:
  docker compose exec backend python app/seed.py
"""
from sqlmodel import Session, select
from app.core.db import engine
from app.models import Client, Policy, Quote, IndustryType, ProductType, QuoteStatus


CLIENTS = [
    {"name": "Kiwi Café Ltd", "industry": IndustryType.hospitality,
     "annual_turnover_nzd": 200_000, "notes": "Small Auckland café, 3 staff"},
    {"name": "BuildRight NZ", "industry": IndustryType.construction,
     "annual_turnover_nzd": 1_500_000, "notes": "Residential builder, Wellington"},
    {"name": "TechSpark Limited", "industry": IndustryType.technology,
     "annual_turnover_nzd": 800_000, "notes": "SaaS startup, Christchurch"},
    {"name": "Green Thumb Gardens", "industry": IndustryType.retail,
     "annual_turnover_nzd": 350_000, "notes": "Garden centre, Hamilton"},
    {"name": "MedFirst Clinic", "industry": IndustryType.healthcare,
     "annual_turnover_nzd": 600_000, "notes": "GP clinic, Dunedin"},
    {"name": "Pacific Freight Co", "industry": IndustryType.other,
     "annual_turnover_nzd": 2_200_000, "notes": "Logistics, Auckland port"},
    {"name": "Legal Eagles LLP", "industry": IndustryType.professional_services,
     "annual_turnover_nzd": 1_100_000, "notes": "Law firm, Auckland CBD"},
]

POLICIES = [
    {
        "product_type": ProductType.public_liability,
        "insurer": "Vero Insurance NZ",
        "sum_insured_nzd": 2_000_000,
        "description": (
            "Public Liability insurance protects your business against claims from third parties "
            "for bodily injury or property damage caused during your business operations. "
            "This policy covers legal defence costs, compensation payments, and medical expenses "
            "for injured parties. It is essential for any business that interacts with customers "
            "or members of the public on its premises. Exclusions include intentional acts, "
            "product liability (separate cover available), and claims arising from professional advice."
        ),
    },
    {
        "product_type": ProductType.professional_indemnity,
        "insurer": "QBE New Zealand",
        "sum_insured_nzd": 1_000_000,
        "description": (
            "Professional Indemnity insurance covers businesses and individuals who provide "
            "professional advice or services. If a client claims your advice caused them financial "
            "loss, this policy covers your legal defence costs and any compensation awarded. "
            "Particularly important for consultants, IT firms, architects, engineers, accountants, "
            "and legal professionals. Covers errors, omissions, and negligent acts. "
            "Excludes fraud, deliberate misconduct, and claims known prior to inception."
        ),
    },
    {
        "product_type": ProductType.cyber,
        "insurer": "Chubb Insurance NZ",
        "sum_insured_nzd": 500_000,
        "description": (
            "Cyber Liability insurance provides protection against the financial impact of "
            "cyberattacks, data breaches, and digital threats. Coverage includes incident response "
            "costs, forensic investigation, customer notification expenses, credit monitoring "
            "services, regulatory fines, and business interruption losses caused by a cyber event. "
            "Also covers social engineering fraud and ransomware payments up to a sub-limit. "
            "Excludes infrastructure failures caused by the insured's own negligence and "
            "pre-existing vulnerabilities knowingly ignored."
        ),
    },
    {
        "product_type": ProductType.business_interruption,
        "insurer": "IAG New Zealand",
        "sum_insured_nzd": 500_000,
        "description": (
            "Business Interruption insurance compensates you for lost income and ongoing expenses "
            "if your business is unable to operate following an insured event such as fire, flood, "
            "or storm damage to your premises. Covers gross profit, fixed costs, payroll, and "
            "additional expenses to resume trading. The indemnity period can be set from 6 to "
            "24 months. Exclusions include losses from supply chain disruptions without physical "
            "damage, pandemic-related closures, and losses below the policy excess threshold."
        ),
    },
    {
        "product_type": ProductType.property,
        "insurer": "Vero Insurance NZ",
        "sum_insured_nzd": 3_000_000,
        "description": (
            "Commercial Property insurance covers physical damage or destruction of your business "
            "premises, stock, equipment, and contents due to insured perils including fire, "
            "explosion, storm, flood, earthquake, and theft. Replacement cost basis applies to "
            "building and plant; indemnity basis applies to stock unless upgraded. "
            "EQC contributions deducted on residential components. "
            "Exclusions include gradual deterioration, maintenance issues, mechanical breakdown, "
            "and losses resulting from unoccupied premises beyond 60 days."
        ),
    },
    {
        "product_type": ProductType.employers_liability,
        "insurer": "Zurich NZ",
        "sum_insured_nzd": 1_000_000,
        "description": (
            "Employers Liability insurance supplements ACC cover by protecting businesses against "
            "claims from employees for work-related injuries or illnesses not fully covered by ACC. "
            "In New Zealand, this primarily covers exemplary damages claims and situations where "
            "an employee suffers a mental injury as a result of employer negligence not recognised "
            "under ACC. Also includes cover for employment disputes and personal grievance claims "
            "up to a sub-limit. Excludes intentional harm and claims from contractors."
        ),
    },
    {
        "product_type": ProductType.cyber,
        "insurer": "Marsh NZ",
        "sum_insured_nzd": 2_000_000,
        "description": (
            "Enterprise Cyber Shield covers large-scale cyber incidents including nation-state "
            "attacks, widespread ransomware, and multi-system data breaches. "
            "Includes 24/7 incident response hotline, dedicated forensic team deployment, "
            "third-party liability for customer data exposure, regulatory defence including "
            "Privacy Act 2020 investigations, reputational harm management, and extortion "
            "negotiation services. Covers cloud outages and SaaS provider failures as an "
            "extension. Suitable for businesses with revenue above NZ$5M or handling "
            "sensitive personal data at scale."
        ),
    },
    {
        "product_type": ProductType.public_liability,
        "insurer": "Allianz NZ",
        "sum_insured_nzd": 5_000_000,
        "description": (
            "Enhanced Public & Products Liability provides combined cover for public liability "
            "and product liability in a single policy, ideal for manufacturers, importers, and "
            "retailers. Covers third-party bodily injury and property damage arising from your "
            "products after they leave your control. Includes product recall expenses up to a "
            "sub-limit and legal defence worldwide (excluding USA/Canada). "
            "Particularly suited to hospitality businesses serving food and drink to the public. "
            "Exclusions include wilful product adulteration, known defect exposure, and "
            "asbestos-related claims."
        ),
    },
    {
        "product_type": ProductType.professional_indemnity,
        "insurer": "AIG New Zealand",
        "sum_insured_nzd": 2_000_000,
        "description": (
            "Technology Professional Indemnity is tailored for IT service providers, software "
            "developers, and digital consultants. Covers claims arising from software errors, "
            "data loss, failed system implementations, and IP infringement in deliverables. "
            "Includes cyber liability extension so one policy covers both professional and "
            "cyber exposures. Defence costs are outside the limit of indemnity. "
            "Retroactive date typically from business inception. Exclusions include "
            "contractual penalties, performance guarantees, and bodily injury from technology."
        ),
    },
    {
        "product_type": ProductType.business_interruption,
        "insurer": "QBE New Zealand",
        "sum_insured_nzd": 1_000_000,
        "description": (
            "Hospitality Business Interruption is specifically designed for cafés, restaurants, "
            "bars, and accommodation providers. Covers loss of revenue following fire, storm, "
            "flood, or equipment breakdown including commercial kitchen equipment failure. "
            "Includes a seasonal adjustment clause to better reflect peak trading periods "
            "(e.g. summer or Christmas). Also covers loss of attraction if a neighbouring "
            "business suffers damage. Indemnity period options from 6 to 18 months. "
            "Excludes losses due to health inspections, food safety closures, and "
            "voluntary shutdowns by the insured."
        ),
    },
]


def seed():
    with Session(engine) as session:
        # Skip if already seeded
        existing = session.exec(select(Policy)).first()
        if existing:
            print("Already seeded — skipping.")
            return

        print("Seeding clients...")
        client_objs = []
        for c in CLIENTS:
            obj = Client(**c)
            session.add(obj)
            client_objs.append(obj)
        session.commit()
        for obj in client_objs:
            session.refresh(obj)

        print("Seeding policies...")
        policy_objs = []
        for p in POLICIES:
            obj = Policy(**p)
            session.add(obj)
            policy_objs.append(obj)
        session.commit()
        for obj in policy_objs:
            session.refresh(obj)

        print("Seeding quotes...")
        quotes_data = [
            {"client_id": client_objs[0].id, "policy_id": policy_objs[0].id,
             "premium_nzd": 1_200, "status": QuoteStatus.draft},
            {"client_id": client_objs[0].id, "policy_id": policy_objs[9].id,
             "premium_nzd": 850, "status": QuoteStatus.sent},
            {"client_id": client_objs[1].id, "policy_id": policy_objs[4].id,
             "premium_nzd": 4_500, "status": QuoteStatus.accepted},
            {"client_id": client_objs[2].id, "policy_id": policy_objs[2].id,
             "premium_nzd": 2_800, "status": QuoteStatus.draft},
            {"client_id": client_objs[3].id, "policy_id": policy_objs[7].id,
             "premium_nzd": 1_600, "status": QuoteStatus.sent},
        ]
        for q in quotes_data:
            session.add(Quote(**q))
        session.commit()

        print("✅ Seed complete!")


if __name__ == "__main__":
    seed()