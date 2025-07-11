import json
from pathlib import Path
from typing import Dict, Any
from ..validators import validate_args, required_string


# this is made to demonstrate functionality but it could just as durably be an API call
# called as part of a temporal activity with automatic retries
def get_order(args: Dict[str, Any]) -> Dict[str, Any]:
    # Define validation rules
    validators = [
        required_string("order_id", error_message="Order ID is required")
    ]
    
    # Validate arguments
    validated = validate_args(args, validators)
    if "error" in validated:
        return validated
    
    order_id = validated["order_id"]

    file_path = (
        Path(__file__).resolve().parent.parent / "data" / "customer_order_data.json"
    )
    if not file_path.exists():
        return {"error": "Data file not found."}

    with open(file_path, "r") as file:
        data = json.load(file)
    order_list = data["orders"]

    for order in order_list:
        if order["id"] == order_id:
            return order

    return_msg = "Order " + order_id + " not found."
    return {"error": return_msg}
