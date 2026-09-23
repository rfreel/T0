#!/usr/bin/env python3
from pathlib import Path
import json
import run_public_benchmark as b

b.MODELS = ['smollm2:360m-instruct-q4_K_M', 'qwen2.5:0.5b-instruct-q4_K_M']
_original_read_tasks = b.read_tasks

def read_tasks_fixed():
    tasks = _original_read_tasks()
    for task in tasks:
        if task['target'] in ('Yes', 'No'):
            if '\nOptions:\n' not in task['input']:
                task['input'] += '\nOptions:\n(A) Yes\n(B) No'
            task['target'] = '(A)' if task['target'] == 'Yes' else '(B)'
    return tasks

def wrong_label_fixed(target):
    # A and B exist in every selected task; choose a valid wrong option.
    return '(B)' if target == '(A)' else '(A)'

b.read_tasks = read_tasks_fixed
b.wrong_label = wrong_label_fixed

if __name__ == '__main__':
    rows = b.run()
    summary = b.summarize(rows)
    b.write_outputs(rows, summary)
    print('FINAL_SUMMARY=' + json.dumps(summary, sort_keys=True), flush=True)
