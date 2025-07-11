import json
from pathlib import Path
from typing import Dict, Any
from ..validators import validate_args, required_email


def sorting(e):
    return e["order_date"]


def list_orders(args: Dict[str, Any]) -> Dict[str, Any]:
    # Define validation rules
    validators = [
        required_email("email_address")
    ]
    
    # Validate arguments
    validated = validate_args(args, validators)
    if "error" in validated:
        return validated
    
    email_address = validated["email_address"]

    file_path = (
        Path(__file__).resolve().parent.parent / "data" / "customer_order_data.json"
    )
    if not file_path.exists():
        return {"error": "Data file not found."}

    with open(file_path, "r") as file:
        data = json.load(file)
    order_list = data["orders"]

    rtn_order_list = []
    for order in order_list:
        if order["email"] == email_address:
            rtn_order_list.append(order)

    if len(rtn_order_list) > 0:
        rtn_order_list.sort(key=sorting)
        return {"orders": rtn_order_list}
    else:
        return_msg = "No orders for customer " + email_address + " found."
        return {"error": return_msg}
