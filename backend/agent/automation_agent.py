from fastapi import HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
from langchain_openai import OpenAI  # Updated import
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from supabase import create_client, Client
import os
from dotenv import load_dotenv
import logging
import json
from backend.utils.roi_calculator import calculate_roi
import csv

# Load environment variables
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pydantic model for user input
class UserQuery(BaseModel):
    problem: str

# Pydantic model for response
class AutomationResponse(BaseModel):
    suggestion: str
    machine_name: Optional[str] = None
    machine_cost: Optional[float] = None
    roi_months: Optional[float] = None
    manpower_savings: Optional[str] = None
    vendors: Optional[List[Dict]] = None

# Supabase query for vendors
def get_vendors(machine_name: str) -> List[Dict]:
    """Fetch vendors from Supabase based on machine name."""
    try:
        supabase: Client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
        response = supabase.table("vendors").select("*").ilike("machine_name", f"%{machine_name}%").execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Supabase error: {str(e)}")

# LangChain Agent Setup
prompt_template = PromptTemplate(
    input_variables=["user_input"],
    template="""
    You are an AI assistant helping small-scale manufacturers in Tamil Nadu automate their processes.
    Based on the user's input, suggest a suitable low-cost automation machine and estimate manpower savings.
    Use the provided vendor data to recommend machines and vendors.

    User input: {user_input}

    Respond in JSON format with:
    - machine_suggestion: Name of the machine
    - machine_cost: Cost in INR
    - roi_months: Estimated ROI in months (assume labor cost of ₹9000/worker/month)
    - manpower_savings: Number of workers replaced
    - vendors: List of vendor details (name, contact, location, link)
    """
)

# Initialize LLM with explicit API key
llm = OpenAI(
    openai_api_key=os.getenv("OPENAI_API_KEY"),
    temperature=0.7,
    model_name="gpt-3.5-turbo-instruct"
)
agent_chain = LLMChain(llm=llm, prompt=prompt_template)

def keyword_based_suggestion(problem: str) -> dict:
    """Fallback function when OpenAI API is unavailable"""
    problem = problem.lower()
    
    if "pack" in problem or "packing" in problem:
        return {
            "machine_suggestion": "Semi-automatic powder packing machine",
            "machine_cost": 28000,
            "roi_months": 2,
            "manpower_savings": "Replaces 2 workers, increases speed by 3x",
        }
    elif "seal" in problem or "sealing" in problem:
        return {
            "machine_suggestion": "Automatic sealing machine",
            "machine_cost": 22000,
            "roi_months": 3,
            "manpower_savings": "Replaces 1 worker, doubles speed",
        }
    else:
        return {
            "machine_suggestion": "Custom automation solution",
            "machine_cost": 35000,
            "roi_months": 4,
            "manpower_savings": "Typically replaces 1-2 workers",
        }

MACHINES_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'machines.json')
VENDORS_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'vendors_tamilnadu.csv')

def load_machines():
    with open(MACHINES_PATH, encoding='utf-8') as f:
        return json.load(f)

def load_vendors():
    vendors = {}
    with open(VENDORS_PATH, encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            vendors[row['id']] = row
    return vendors

def match_machine(problem: str):
    machines = load_machines()
    problem_lower = problem.lower()
    for machine in machines:
        if machine['type'].lower() in problem_lower or machine['name'].lower() in problem_lower:
            return machine
    return None

def suggest_automation(query: UserQuery) -> AutomationResponse:
    """Main suggestion function with fallback and local data."""
    try:
        logger.info(f"Processing automation request for: {query.problem}")
        # Try to match from local data first
        machine = match_machine(query.problem)
        vendors = []
        if machine:
            vendor_db = load_vendors()
            vendors = [vendor_db[vid] for vid in machine.get('vendor_refs', []) if vid in vendor_db]
            monthly_labor_savings = machine['manpower_savings'] * 9000 if 'manpower_savings' in machine else 0
            roi_months = calculate_roi(machine['cost'], monthly_labor_savings)
            suggestion = (
                f"Suggested: {machine['name']}\n"
                f"Estimated Cost: ₹{machine['cost']}\n"
                f"ROI: {roi_months if roi_months else 'N/A'} months\n"
                f"Manpower Savings: Replaces {machine['manpower_savings']} workers\n"
                f"Vendors: {', '.join([v['vendor_name'] for v in vendors]) if vendors else 'N/A'}"
            )
            return AutomationResponse(
                suggestion=suggestion,
                machine_name=machine['name'],
                machine_cost=machine['cost'],
                roi_months=roi_months,
                manpower_savings=f"Replaces {machine['manpower_savings']} workers",
                vendors=vendors
            )
        # If no match, fallback to LLM/keyword
        try:
            llm_response = agent_chain.run({"user_input": query.problem})
            data = json.loads(llm_response)
        except Exception as e:
            logger.error(f"LLM error: {str(e)}")
            data = keyword_based_suggestion(query.problem)
        machine_name = data.get("machine_suggestion")
        machine_cost = data.get("machine_cost")
        roi_months = data.get("roi_months")
        manpower_savings = data.get("manpower_savings")
        # Try to fetch vendors from local DB if possible
        vendor_db = load_vendors()
        vendors = [v for v in vendor_db.values() if machine_name and machine_name.lower() in v.get('machine_types', '').lower()]
        suggestion = (
            f"Suggested: {machine_name}\n"
            f"Estimated Cost: ₹{machine_cost if machine_cost else 'N/A'}\n"
            f"ROI: {roi_months if roi_months else 'N/A'} months\n"
            f"Manpower Savings: {manpower_savings}\n"
            f"Vendors: {', '.join([v['vendor_name'] for v in vendors]) if vendors else 'N/A'}"
        )
        return AutomationResponse(
            suggestion=suggestion,
            machine_name=machine_name,
            machine_cost=machine_cost,
            roi_months=roi_months,
            manpower_savings=manpower_savings,
            vendors=vendors
        )
    except Exception as e:
        logger.error(f"Automation suggestion error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing automation suggestion: {str(e)}")