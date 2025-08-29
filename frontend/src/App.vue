<script setup>
import { ref } from 'vue';

const userCode = ref(`from typing import Optional, List

# --- PASTE YOUR COMPLETE CODE HERE ---
# The code must be self-contained and runnable.
# This example includes the REAL ListNode class.

class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next

def delete_node(head: Optional[ListNode], val: int) -> Optional[ListNode]:
    if not head:
        return None
    if head.val == val:
        return head.next
    
    current = head
    while current.next and current.next.val != val:
        current = current.next
    
    if current.next:
        current.next = current.next.next
        
    return head
`);
const targetName = ref('delete_node');
const generatedTestCode = ref('');
const isLoading = ref(false);
const errorMessage = ref('');

async function generateTest() {
  isLoading.value = true;
  errorMessage.value = '';
  generatedTestCode.value = '';

  try {
    const response = await fetch('http://localhost:8000/api/generate', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        code: userCode.value,
        target_name: targetName.value,
      }),
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || 'An unknown error occurred.');
    }

    generatedTestCode.value = data.test_script;
  } catch (error) {
    errorMessage.value = error.message;
  } finally {
    isLoading.value = false;
  }
}
</script>

<template>
  <main class="container">
    <header>
      <h1>Python Test Script Generator</h1>
      <p>Paste your Python code, provide the target name, and generate a test.</p>
    </header>
    
    <div class="form-group">
      <label for="target-name">Target Function or Method Name (e.g., `delete_node` or `Graph.delete_vertex`)</label>
      <input id="target-name" type="text" v-model="targetName" />
    </div>

    <div class="form-group">
      <label for="code-input">Python Code (must include necessary class definitions and type hints)</label>
      <textarea id="code-input" v-model="userCode" rows="15"></textarea>
    </div>

    <button @click="generateTest" :disabled="isLoading">
      {{ isLoading ? 'Generating...' : 'Generate Test Script' }}
    </button>

    <div v-if="errorMessage" class="error-box">
      <h3>Error</h3>
      <p>{{ errorMessage }}</p>
    </div>

    <div v-if="generatedTestCode" class="result-box">
      <h3>Generated Test Snapshots</h3>
      <pre><code>{{ generatedTestCode }}</code></pre>
    </div>
  </main>
</template>

<style>
:root { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
body { background-color: #f4f7f9; }
.container { max-width: 800px; margin: 2rem auto; padding: 2rem; background-color: white; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
header { text-align: center; margin-bottom: 2rem; }
.form-group { margin-bottom: 1.5rem; }
label { display: block; margin-bottom: 0.5rem; font-weight: bold; color: #333; }
textarea, input { width: 100%; padding: 0.75rem; border-radius: 4px; border: 1px solid #ccc; font-family: monospace; font-size: 14px; box-sizing: border-box; }
button { width: 100%; padding: 1rem; font-size: 1.2rem; background-color: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; transition: background-color 0.2s; }
button:hover { background-color: #0056b3; }
button:disabled { background-color: #aaa; cursor: not-allowed; }
.error-box, .result-box { margin-top: 2rem; padding: 1rem; border-radius: 4px; }
.error-box { background-color: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; }
.result-box { background-color: #e2e3e5; border: 1px solid #d6d8db; }
pre { white-space: pre-wrap; word-wrap: break-word; }
code { font-family: 'Courier New', Courier, monospace; }
</style>