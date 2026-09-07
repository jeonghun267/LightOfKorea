"""File-scope check and compact animated review for the petal-only pass."""
import hashlib,json
from pathlib import Path
from PIL import Image
root=Path(__file__).resolve().parents[1];saved=root/'Saved/LOK'
backup=root/'Saved/Backups/PetalPolish_20260907_172050'
changed=[]
for row in json.loads((backup/'before_hashes.json').read_text(encoding='utf-8-sig')):
    p=Path(row['Path'])
    if hashlib.sha256(p.read_bytes()).hexdigest().upper()!=row['SHA256']:changed.append(p.relative_to(root).as_posix())
assert set(changed)=={'Content/LOK/Maps/Zone01/LV_Zone01_Moonlight.umap','Content/LOK/Materials/Hero/M_Hero_BarkFlow.uasset','Content/LOK/Meshes/Hero/SM_HeroTrees_Curved.uasset'},changed
clip=json.loads((saved/'render_petal_clip.json').read_text())
assert clip['status']=='PASS' and clip['frames']==240
folder=Path(clip['output']);files=sorted(folder.glob('Zone01.*.png'))
assert [p.name for p in files]==['Zone01.%04d.png'%i for i in range(1500,1740)]
frames=[]
for p in files[::2]:
    with Image.open(p) as im:frames.append(im.convert('RGB'))
out=saved/'PetalReview/TreePetals_50-58s.webp'
frames[0].save(out,save_all=True,append_images=frames[1:],duration=[67,67,66]*40,loop=0,quality=85,method=3)
with Image.open(out) as check:assert check.n_frames==120
report={'status':'PASS','changed_existing_assets':changed,'sequence_blueprints_niagara_other_assets_unchanged':True,
 'clip_frames':240,'webp_frames':120,'duration_seconds':8,'webp':str(out),'still':str(folder/'Zone01.1650.png')}
(saved/'tree_petals_verification.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report))
