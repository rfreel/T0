#!/usr/bin/env python3
import json, os, time, urllib.request
import run_public_benchmark as b

b.MODELS = ['smollm2:1.7b-instruct-q4_K_M', 'qwen2.5:1.5b-instruct-q4_K_M']
b.METHODS = {
    'direct': 'Solve the multiple-choice question using only the supplied information. Select exactly one option.',
    'repair': ('Before selecting, silently identify the exact missing relation or ambiguity; separate explicit evidence from inference; preserve exact entities, dates, quantities, and relationships; use conditional scope when needed; make the smallest targeted correction; avoid overgeneralization; convert uncertainty into a precise verification step. Select exactly one option.'),
    'repair_route': ('Before selecting, silently identify the exact missing relation or ambiguity; separate explicit evidence from inference; preserve exact entities, dates, quantities, and relationships; use conditional scope when needed; make the smallest targeted correction; avoid overgeneralization; convert uncertainty into a precise verification step. Silently choose only necessary transformations from: distinguish states, relate entities, change representation, reverse a causal direction, generate one credible rival, eliminate forbidden candidates, retain what survives perturbation, constrain scope, run a reversible probe, verify, and update. Select exactly one option.'),
}
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
    return '(B)' if target == '(A)' else '(A)'

def call_ollama_constrained(model, system, user):
    schema = {
        'type': 'object',
        'properties': {'answer': {'type': 'string', 'enum': ['A','B','C','D','E','F']}},
        'required': ['answer'],
        'additionalProperties': False,
    }
    payload = {
        'model': model,
        'messages': [{'role':'system','content':system},{'role':'user','content':user}],
        'stream': False,
        'format': schema,
        'options': {'temperature':0,'seed':b.SEED,'num_predict':24,'num_ctx':4096},
    }
    req = urllib.request.Request(b.OLLAMA + '/api/chat', data=json.dumps(payload).encode(), headers={'Content-Type':'application/json'})
    start = time.perf_counter()
    with urllib.request.urlopen(req, timeout=300) as response:
        obj = json.loads(response.read())
    wall = time.perf_counter() - start
    raw = obj.get('message',{}).get('content','').strip()
    try:
        answer = json.loads(raw).get('answer','')
    except Exception:
        answer = ''
    normalized = f'({answer})' if answer in 'ABCDEF' and len(answer) == 1 else ''
    return {
        'text': normalized,
        'prompt_tokens': obj.get('prompt_eval_count',0) or 0,
        'completion_tokens': obj.get('eval_count',0) or 0,
        'duration_sec': wall,
        'server_duration_sec': (obj.get('total_duration',0) or 0)/1e9,
    }

b.read_tasks = read_tasks_fixed
b.wrong_label = wrong_label_fixed
b.call_ollama = call_ollama_constrained

if __name__ == '__main__':
    rows = b.run()
    summary = b.summarize(rows)
    b.write_outputs(rows, summary)
    report = b.OUT / 'report.md'
    text = report.read_text()
    text = text.replace('# Prompt Method Benchmark — Public Holdout Run', '# Prompt Method Benchmark — Constrained Replication')
    text = text.replace('- Temperature 0, fixed seed, identical answer format and token limit.', '- Temperature 0, fixed seed, identical token limit, and JSON-schema-constrained option output.')
    text = text.replace('two small open models', 'two 1.5–1.7B open models')
    report.write_text(text)
    print('FINAL_SUMMARY=' + json.dumps(summary, sort_keys=True), flush=True)
