# backend/app.py (Version 6 - Final with Pytest Templating)
import os
import uuid
import importlib.util
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from . import ds_plugins
from . import generator_core
import textwrap

class GenerateRequest(BaseModel):
    code: str
    target_name: str

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

TEMP_CODE_DIR = "temp_code"
KNOWN_DS_CLASSES = ['ListNode', 'TreeNode', 'BinarySearchTree', 'Graph', 'Stack', 'Queue']

# --- NEW: The Templating Function ---
def generate_pytest_file_content(target_name: str, user_code: str, snapshots: list) -> str:
    # We need the helper functions for creating/converting the data structures in the test
    # In a real library, these would be imported, but for a self-contained script, we embed them.
    helper_code = """
from typing import Optional, List
from collections import deque

# --- Helper functions required for this test ---
def create_from_list(items: List[int]) -> Optional[ListNode]:
    if not items: return None
    head = ListNode(val=items[0])
    curr = head
    for val in items[1:]:
        curr.next = ListNode(val=val)
        curr = curr.next
    return head

def convert_to_list(head: Optional[ListNode]) -> List[int]:
    items = []
    curr = head
    while curr:
        items.append(curr.val)
        curr = curr.next
    return items
"""

    # Properly indent the user's code to place it inside the template
    indented_user_code = textwrap.indent(user_code, '    ')
    
    # Use an f-string to build the entire Python file content
    template = f"""
import pytest
from typing import Optional, List

# --- User's Code Under Test ---
# The user's submitted code is embedded here to make the test self-contained.
{indented_user_code}

# --- Test Infrastructure ---
{helper_code}

# --- Captured Behavioral Snapshots ---
SNAPSHOTS = {repr(snapshots)}

@pytest.mark.parametrize("snapshot", SNAPSHOTS)
def test_{target_name}_behavior(snapshot):
    \"\"\"Characterization test for {target_name}\"\"\"
    
    # Recreate the input arguments from their simple representations
    input_reprs = snapshot["inputs_repr"]
    
    # This logic assumes the first arg is a ListNode and the second is an int
    # A more advanced version would handle this more dynamically
    head_input = create_from_list(input_reprs[0])
    val_input = input_reprs[1]
    
    # Execute the function under test
    result_node = {target_name}(head_input, val_input)
    
    # Serialize the actual result for comparison
    actual_return_repr = convert_to_list(result_node)

    # Assert that the behavior matches the snapshot
    assert actual_return_repr == snapshot["return_value_repr"]
"""
    return template.strip()


@app.post("/api/generate")
async def generate_test_script(body: GenerateRequest):
    user_code = body.code
    target_name = body.target_name
    
    unique_id = str(uuid.uuid4())
    temp_module_name = f"user_code_{unique_id}"
    temp_file_path = os.path.join(TEMP_CODE_DIR, f"{temp_module_name}.py")
    
    if not os.path.exists(TEMP_CODE_DIR):
        os.makedirs(TEMP_CODE_DIR)
        
    context = {}
    try:
        with open(temp_file_path, "w") as f:
            f.write(user_code)

        spec = importlib.util.spec_from_file_location(temp_module_name, temp_file_path)
        user_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(user_module)

        context = {name: getattr(user_module, name) for name in KNOWN_DS_CLASSES if hasattr(user_module, name)}
        
        if '.' in target_name:
            cls_name, method_name = target_name.split('.')
            cls = getattr(user_module, cls_name)
            target_func = getattr(cls, method_name)
        else:
            target_func = getattr(user_module, target_name)

        plugins = {
            'INPUT_STRATEGIES': ds_plugins.INPUT_STRATEGIES,
            'INPUT_CONVERTERS': ds_plugins.INPUT_CONVERTERS,
            'STATE_SERIALIZERS': ds_plugins.STATE_SERIALIZERS,
        }
        
        snapshots = generator_core.capture_behavior_snapshots(target_func, plugins, context)
        
        # --- Use the new templating function ---
        generated_code = generate_pytest_file_content(target_name, user_code, snapshots)
        
        return {"test_script": generated_code}

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {repr(e)}\n\nTraceback:\n{error_details}")
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)