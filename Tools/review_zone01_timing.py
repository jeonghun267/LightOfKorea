"""Verify preserved files and assemble unretouched actual-render review frames."""
import hashlib,json
from pathlib import Path
from PIL import Image,ImageDraw

root=Path(__file__).resolve().parents[1];saved=root/'Saved/LOK'
backup=sorted((root/'Saved/Backups').glob('TimingPolish_*'))[-1]
changed=[]
for row in json.loads((backup/'before_hashes.json').read_text(encoding='utf-8-sig')):
    p=root/row['Path']
    if hashlib.sha256(p.read_bytes()).hexdigest().upper()!=row['SHA256']:changed.append(p.relative_to(root).as_posix())
protected=[p for p in changed if p.startswith(('Content/LOK/Meshes/','Content/LOK/Blueprints/','Content/LOK/Niagara/','Config/')) or (p.startswith('Content/LOK/Maps/') and p!='Content/LOK/Maps/Zone01/LV_Zone01_Moonlight.umap')]
assert not protected,protected
runtime=json.loads((saved/'runtime_zone01.json').read_text())
assert runtime['status']=='PASS',runtime['errors']
curves=json.loads((saved/'timing_polish.json').read_text())['curves']
def value(keys,t):
    if t<=keys[0][0]:return keys[0][1]
    for (a,x),(b,y) in zip(keys,keys[1:]):
        if t<=b:return x+(y-x)*(t-a)/(b-a)
    return keys[-1][1]
checks=0
for sample in runtime['samples']:
    controls=sample['visual_controls'];t=controls['ExhibitTime']
    for name,actual in controls.items():
        assert abs(actual-value(curves[name],t))<.003,(t,name,actual,value(curves[name],t))
        checks+=1
    for name,level in [('Hero_JarKey',1800.),('Hero_JarFill',1100.)]:
        expected=value([(0,0),(5,0),(8,level*.32),(12,level),(60,level)],t)
        assert abs(sample['jar_light_intensities'][name]-expected)<1.,(t,name,expected,sample['jar_light_intensities'])
        checks+=1
render=json.loads((saved/'render_timing_review.json').read_text())
assert render['status']=='PASS' and render['frames']==1800,render
folder=Path(render['output']);frames=sorted(folder.glob('Zone01.*.png'))
assert [p.name for p in frames]==['Zone01.%04d.png'%i for i in range(1800)]
review=saved/'TimingReview';review.mkdir(exist_ok=True)
stages=[(3,'Outline'),(8,'Surface'),(12,'Ink reveal'),(17,'Halo'),(21,'Nearby particles'),(23,'First ripple'),
        (27,'Near trees'),(31,'Pavilion / middle trees'),(36,'Far trees'),(47,'Soft echo'),(52,'Echo travels'),(55,'Final hierarchy')]
sheet=Image.new('RGB',(1440,4*294),(8,13,22));draw=ImageDraw.Draw(sheet)
for i,(sec,label) in enumerate(stages):
    with Image.open(folder/('Zone01.%04d.png'%(sec*30))) as im:tile=im.convert('RGB').resize((480,270),Image.Resampling.LANCZOS)
    x=(i%3)*480;y=(i//3)*294;sheet.paste(tile,(x,y));draw.text((x+10,y+276),f'{sec:02d}s | {label}',fill=(222,227,237))
sheet.save(review/'Timing_ContactSheet.jpg',quality=95)
clip=[]
for p in frames[::3]:
    with Image.open(p) as im:clip.append(im.convert('RGB').resize((640,360),Image.Resampling.LANCZOS))
webp=review/'Zone01_Reveal_60s.webp'
clip[0].save(webp,save_all=True,append_images=clip[1:],duration=100,loop=0,quality=83,method=2)
with Image.open(webp) as im:assert im.n_frames==600
report={'status':'PASS','preserved_meshes_blueprints_niagara_config':True,'changed_existing_files':changed,
 'map_changes':'Moon/key/fill lighting channels and jar-light spill controls; actor transforms and camera preserved.',
 'native_autoplay':'PASS','sampled_mpc_curve_checks':checks,
 'render_frames':1800,'duration_seconds':60,'review':str(webp),'contact_sheet':str(review/'Timing_ContactSheet.jpg'),
 'note':'File preservation and render completion; visual hierarchy requires review of actual images, not a numerical brightness guarantee.'}
(saved/'timing_verification.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report))
