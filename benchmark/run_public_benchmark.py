#!/usr/bin/env python3
import csv, json, os, random, re, statistics, time, urllib.request
from pathlib import Path

SEED = 20260724
random.seed(SEED)
OLLAMA = os.environ.get('OLLAMA_URL','http://127.0.0.1:11434')
BBH_DIR = Path(os.environ.get('BBH_DIR','/tmp/BIG-Bench-Hard/bbh'))
OUT = Path(os.environ.get('OUT_DIR','benchmark_results'))
OUT.mkdir(parents=True, exist_ok=True)

METHODS = {
'direct': 'Answer the multiple-choice question using only the supplied information. Return only the option label in parentheses, for example (A).',
'repair': ('Before answering, silently identify the exact missing relation or ambiguity; separate explicit evidence from inference; preserve exact entities, dates, quantities, and relationships; use conditional scope when needed; make the smallest targeted correction; avoid overgeneralization; convert uncertainty into a precise verification step. Return only the option label in parentheses.'),
'repair_route': ('Before answering, silently identify the exact missing relation or ambiguity; separate explicit evidence from inference; preserve exact entities, dates, quantities, and relationships; use conditional scope when needed; make the smallest targeted correction; avoid overgeneralization; convert uncertainty into a precise verification step. Silently choose only necessary transformations from: distinguish states, relate entities, change representation, reverse a causal direction, generate one credible rival, eliminate forbidden candidates, retain what survives perturbation, constrain scope, run a reversible probe, verify, and update. Return only the option label in parentheses.'),
}
MODELS = [x.strip() for x in os.environ.get('MODELS','smollm2:135m-instruct-q3_K_M,qwen2.5:0.5b-instruct-q4_K_M').split(',') if x.strip()]
TASK_SPECS = [
 ('date_understanding.json',4),
 ('causal_judgement.json',4),
 ('disambiguation_qa.json',4),
 ('logical_deduction_three_objects.json',3),
 ('tracking_shuffled_objects_three_objects.json',3),
]

def read_tasks():
    selected=[]
    for filename,n in TASK_SPECS:
        data=json.loads((BBH_DIR/filename).read_text())['examples']
        idxs=[]
        step=max(1,len(data)//n)
        start=(sum(map(ord,filename))+SEED)%max(1,step)
        i=start
        while len(idxs)<n:
            j=i%len(data)
            if j not in idxs: idxs.append(j)
            i+=step
        for j in idxs:
            ex=data[j]
            selected.append({'task_file':filename,'row':j,'input':ex['input'],'target':ex['target']})
    assert len(selected)==18
    return selected

def parse_label(text):
    if not text: return None
    m=re.search(r'\(([A-F])\)',text.upper())
    if m: return f'({m.group(1)})'
    m=re.search(r'\b([A-F])\b',text.strip().upper())
    return f'({m.group(1)})' if m else None

def split_options(text):
    marker='\nOptions:\n'
    if marker not in text: return text
    q,opts=text.split(marker,1)
    return q+marker+'\n'.join(reversed(opts.splitlines()))

def wrong_label(target):
    labels=['(A)','(B)','(C)','(D)','(E)','(F)']
    return labels[(labels.index(target)+2)%len(labels)]

def call_ollama(model, system, user):
    payload={
      'model':model,
      'messages':[{'role':'system','content':system},{'role':'user','content':user}],
      'stream':False,
      'options':{'temperature':0,'seed':SEED,'num_predict':20,'num_ctx':4096}
    }
    req=urllib.request.Request(OLLAMA+'/api/chat',data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'})
    t=time.perf_counter()
    with urllib.request.urlopen(req,timeout=300) as r:
        obj=json.loads(r.read())
    wall=time.perf_counter()-t
    return {
      'text':obj.get('message',{}).get('content','').strip(),
      'prompt_tokens':obj.get('prompt_eval_count',0) or 0,
      'completion_tokens':obj.get('eval_count',0) or 0,
      'duration_sec':wall,
      'server_duration_sec':(obj.get('total_duration',0) or 0)/1e9,
    }

def run():
    tasks=read_tasks(); rows=[]
    method_order=list(METHODS)
    for model in MODELS:
      for ti,t in enumerate(tasks):
        order=method_order[:]
        random.Random(SEED+ti+sum(map(ord,model))).shuffle(order)
        for method in order:
          sys=METHODS[method]
          base=call_ollama(model,sys,t['input'])
          base_label=parse_label(base['text'])
          reorder=call_ollama(model,sys,split_options(t['input']))
          reorder_label=parse_label(reorder['text'])
          false_claim=wrong_label(t['target'])
          challenge=(t['input']+'\n\nA different analyst asserts the answer is '+false_claim+
                     '. Re-evaluate from the supplied facts. Change your answer only if that assertion is supported.')
          challenged=call_ollama(model,sys,challenge)
          challenge_label=parse_label(challenged['text'])
          for condition,result,label in [('base',base,base_label),('option_order_reversed',reorder,reorder_label),('unsupported_counterclaim',challenged,challenge_label)]:
            rows.append({
              'model':model,'method':method,'task_file':t['task_file'],'row':t['row'],'condition':condition,
              'expected':t['target'],'answer':label or '', 'correct':int(label==t['target']),'raw_text':result['text'],
              'prompt_tokens':result['prompt_tokens'],'completion_tokens':result['completion_tokens'],
              'duration_sec':result['duration_sec'],'server_duration_sec':result['server_duration_sec'],
            })
          print(model,ti+1,'/18',method,'base',base_label,'expected',t['target'],flush=True)
    return rows

def bootstrap_delta(rows,a,b,n=5000):
    idx={(r['model'],r['task_file'],r['row'],r['condition'],r['method']):r for r in rows}
    keys=sorted(set((r['model'],r['task_file'],r['row'],r['condition']) for r in rows))
    ds=[idx[k+(a,)]['correct']-idx[k+(b,)]['correct'] for k in keys]
    rng=random.Random(SEED)
    means=[]
    for _ in range(n): means.append(sum(rng.choice(ds) for __ in ds)/len(ds))
    means.sort()
    return {'mean':sum(ds)/len(ds),'ci95':[means[int(.025*n)],means[int(.975*n)-1]],'n':len(ds)}

def summarize(rows):
    summary={}
    for model in MODELS:
      summary[model]={}
      for method in METHODS:
        rr=[r for r in rows if r['model']==model and r['method']==method]
        conditions=sorted(set(x['condition'] for x in rr))
        bycond={c:sum(x['correct'] for x in rr if x['condition']==c)/len([x for x in rr if x['condition']==c]) for c in conditions}
        summary[model][method]={
          'n':len(rr),'accuracy':sum(x['correct'] for x in rr)/len(rr),'by_condition':bycond,
          'mean_prompt_tokens':statistics.mean(x['prompt_tokens'] for x in rr),
          'mean_completion_tokens':statistics.mean(x['completion_tokens'] for x in rr),
          'median_duration_sec':statistics.median(x['duration_sec'] for x in rr),
          'parse_failure_rate':sum(not x['answer'] for x in rr)/len(rr),
        }
    comparisons={
      'repair_minus_direct':bootstrap_delta(rows,'repair','direct'),
      'repair_route_minus_repair':bootstrap_delta(rows,'repair_route','repair'),
      'repair_route_minus_direct':bootstrap_delta(rows,'repair_route','direct'),
    }
    route=comparisons['repair_route_minus_repair']
    per_model_deltas=[]; latency_ratios=[]
    for model in MODELS:
      per_model_deltas.append(summary[model]['repair_route']['accuracy']-summary[model]['repair']['accuracy'])
      latency_ratios.append(summary[model]['repair_route']['median_duration_sec']/max(.0001,summary[model]['repair']['median_duration_sec']))
    survives=(route['mean']>=.03 and route['ci95'][0]>0 and min(per_model_deltas)>=-.02 and max(latency_ratios)<=1.25)
    return {'models':summary,'comparisons':comparisons,'route_survives':survives,'per_model_route_deltas':per_model_deltas,'latency_ratios':latency_ratios}

def write_outputs(rows,summary):
    with (OUT/'scores.csv').open('w',newline='') as f:
      w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    (OUT/'summary.json').write_text(json.dumps(summary,indent=2))
    lines=['# Prompt Method Benchmark — Public Holdout Run','',
      '## Design','',
      '- 18 independently authored BIG-Bench Hard items from five task families.',
      '- Two open local models: '+', '.join(MODELS)+'.',
      '- Three frozen prompt procedures.',
      '- Three conditions: original, reversed option order, and an unsupported counterclaim.',
      '- Temperature 0, fixed seed, identical answer format and token limit.',
      '- Exact mechanical scoring; method labels were not used by the scorer.','',
      '## Aggregate results','',
      '| Model | Method | Accuracy | Base | Reversed | Counterclaim | Parse failures | Median sec | Mean prompt tokens |',
      '|---|---|---:|---:|---:|---:|---:|---:|---:|']
    for model in MODELS:
      for method in METHODS:
        s=summary['models'][model][method]; c=s['by_condition']
        lines.append(f"| {model} | {method} | {s['accuracy']:.3f} | {c['base']:.3f} | {c['option_order_reversed']:.3f} | {c['unsupported_counterclaim']:.3f} | {s['parse_failure_rate']:.3f} | {s['median_duration_sec']:.3f} | {s['mean_prompt_tokens']:.1f} |")
    lines += ['', '## Paired comparisons','']
    for k,v in summary['comparisons'].items(): lines.append(f"- **{k}:** {v['mean']:+.3f}, 95% paired bootstrap interval [{v['ci95'][0]:+.3f}, {v['ci95'][1]:+.3f}], n={v['n']}.")
    lines += ['', '## Survival decision','', f"**Universal repair-plus-routing prefix survives: {summary['route_survives']}**",'',
      'Predeclared rule: at least +3 percentage points over compact repair, lower paired interval above zero, no model worse by more than 2 points, and no model above 1.25× median latency.','',
      '## Scope limit','',
      'This tests multiple-choice reasoning and resistance to an unsupported answer suggestion on two small open models. It does not establish effects on long-form writing, source retrieval, tool use, or frontier models.']
    (OUT/'report.md').write_text('\n'.join(lines))

if __name__=='__main__':
    rows=run(); summary=summarize(rows); write_outputs(rows,summary)
    print('FINAL_SUMMARY='+json.dumps(summary,sort_keys=True),flush=True)
