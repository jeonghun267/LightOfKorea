"""Encode a lightweight animated WebP from MRQ PNGs using ordinary Python/Pillow."""
import json
from pathlib import Path
from PIL import Image

def main():
    root=Path(__file__).resolve().parents[2]/"Saved"/"LOK"
    report=json.loads((root/"render_zone01.json").read_text(encoding="utf-8"))
    if report["status"]!="PASS":
        raise RuntimeError("MRQ must finish successfully before review encoding")
    folder=Path(report["output"])
    files=sorted(folder.glob("Zone01.*.png"))
    if [p.name for p in files]!=["Zone01.%04d.png"%i for i in range(1800)]:
        raise RuntimeError("Missing or unexpected MRQ frame indices")
    frames=[]
    for index,path in enumerate(files):
        with Image.open(path) as source:
            if source.size!=tuple(report["resolution"]):
                raise RuntimeError("Unexpected frame size: "+str(path))
            if index%3==0:
                frame=source.convert("RGB")
                frame.thumbnail((640,360),Image.Resampling.LANCZOS)
                frames.append(frame)
    output=root/"Zone01_Opening_60s.webp"
    frames[0].save(output,save_all=True,append_images=frames[1:],duration=100,loop=0,
                   format="WEBP",quality=80,method=3)
    with Image.open(output) as verify:
        if verify.n_frames!=600:
            raise RuntimeError("Animated review frame count mismatch")
    result={"status":"PASS","source_frames":1800,"source_resolution":report["resolution"],
            "review_frames":600,"review_fps":10,"duration_seconds":60,"output":str(output),
            "bytes":output.stat().st_size,"note":"Silent review animation; 30fps source PNGs retained."}
    (root/"review_zone01.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
    print(json.dumps(result))

if __name__=="__main__":
    main()
