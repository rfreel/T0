#!/usr/bin/env python3
from pathlib import Path
import json, hashlib, sys
try:
    import jsonschema
except ImportError:
    print('FAIL: jsonschema unavailable')
    sys.exit(2)
root=Path(__file__).resolve().parents[1]
errors=[]
required=['kernel/KERNEL.yaml','state/ACTIVE_TRAJECTORY.json','skills/provenance.json','schemas/trajectory.schema.json','schemas/procedure.schema.json']
for rel in required:
    if not (root/rel).exists(): errors.append(f'missing {rel}')
# schema validation
pairs=[('state/ACTIVE_TRAJECTORY.json','schemas/trajectory.schema.json')]
for rel in sorted((root/'procedures/candidate').glob('*.json')):
    pairs.append((str(rel.relative_to(root)),'schemas/procedure.schema.json'))
for docrel, schrel in pairs:
    try:
        doc=json.loads((root/docrel).read_text()); sch=json.loads((root/schrel).read_text()); jsonschema.validate(doc,sch)
    except Exception as e: errors.append(f'{docrel}: {e}')
# hashes
prov=json.loads((root/'skills/provenance.json').read_text())
for item in prov['skills']:
    p=root/item['path']
    if not p.exists(): errors.append(f"missing {item['path']}"); continue
    got=hashlib.sha256(p.read_bytes()).hexdigest()
    if got!=item['sha256']: errors.append(f"hash mismatch {item['path']}")
if len(prov['skills'])!=27: errors.append(f"expected 27 skills, got {len(prov['skills'])}")
# reconstructibility fields
traj=json.loads((root/'state/ACTIVE_TRAJECTORY.json').read_text())
for field in ['objective','next_decision','selected_action','verification','recovery']:
    if not traj.get(field): errors.append(f'empty trajectory field {field}')
if errors:
    print('FAIL')
    for e in errors: print('-',e)
    sys.exit(1)
print('PASS')
print(f"skills_verified={len(prov['skills'])}")
print(f"candidate_procedures={len(list((root/'procedures/candidate').glob('*.json')))}")
print(f"trajectory={traj['trajectory_id']}")
print(f"stopping_boundary={traj['selected_action']['stopping_boundary']}")
