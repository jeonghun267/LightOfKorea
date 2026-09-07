"""Deterministic surface meshes for the Zone01 visual pass (centimeters)."""
import math, random

def add(a,b): return tuple(x+y for x,y in zip(a,b))
def sub(a,b): return tuple(x-y for x,y in zip(a,b))
def mul(a,s): return tuple(x*s for x in a)
def cross(a,b): return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def unit(a): return mul(a,1/max(1e-9,math.sqrt(sum(x*x for x in a))))

class Mesh:
    def __init__(self): self.vertices=[];self.uv=[];self.triangles=[]
    def grid(self,rows,uvrows):
        start=len(self.vertices);n=len(rows[0])
        for row,uv in zip(rows,uvrows):self.vertices.extend(row);self.uv.extend(uv)
        for j in range(len(rows)-1):
            for i in range(n-1):
                a=start+j*n+i;b=a+1;c=b+n;d=a+n
                self.triangles.extend([(a,b,c),(a,c,d)])
    def normals(self):
        normals=[(0,0,0) for _ in self.vertices]
        for a,b,c in self.triangles:
            n=cross(sub(self.vertices[b],self.vertices[a]),sub(self.vertices[c],self.vertices[a]))
            for i in (a,b,c):normals[i]=add(normals[i],n)
        return [unit(n) for n in normals]

def catmull(p0,p1,p2,p3,t):
    return tuple(.5*((2*b)+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t*t*t) for a,b,c,d in zip(p0,p1,p2,p3))

def jar():
    # Broad shoulder, narrower foot, short neck, rolled lip and visible inner wall.
    profile=[(375,0),(395,50),(550,170),(810,420),(1025,800),(1115,1190),
      (1090,1490),(970,1800),(780,2060),(555,2220),(500,2270),(502,2322),
      (516,2340),(512,2360),(490,2368),(471,2353),(471,2318),(474,2275),
      (524,2200),(742,2030),(930,1770),(1045,1470),(1070,1190),(980,815),
      (760,450),(500,220),(320,135),(5,130)]
    smooth=[]
    for k in range(len(profile)-1):
        for i in range(5):smooth.append(catmull(profile[max(0,k-1)],profile[k],profile[k+1],profile[min(len(profile)-1,k+2)],i/5))
    smooth.append(profile[-1]);rows=[];uv=[]
    for r,z in smooth:
        row=[];tex=[]
        for i in range(161):
            t=i/160;ang=t*math.tau
            # Potter's asymmetry, continuous around the seam; never faceted noise.
            radius=r*1.10*(1+.018*math.sin(ang+z*.0007)+.008*math.cos(2*ang-z*.0004))
            row.append((radius*math.cos(ang)+15*math.sin(z*.0015),radius*math.sin(ang),z*.95+5*math.sin(ang)*math.sin(z/2368*math.pi)))
            tex.append((t,z/2368))
        rows.append(row);uv.append(tex)
    mesh=Mesh();mesh.grid(rows,uv);return mesh

def bezier(p,t):
    a,b,c,d=p;s=1-t
    return add(add(mul(a,s*s*s),mul(b,3*s*s*t)),add(mul(c,3*s*t*t),mul(d,t*t*t)))

def tube(mesh,control,r0,r1,segments=24,sides=10,flow_start=0):
    rows=[];uv=[]
    for j in range(segments+1):
        t=j/segments;p=bezier(control,t)
        direction=unit(sub(bezier(control,min(1,t+.001)),bezier(control,max(0,t-.001))))
        normal=unit(cross(direction,(1,0,0) if abs(direction[0])<.8 else (0,1,0)))
        bitangent=cross(direction,normal);radius=r1+(r0-r1)*(1-t)**1.25
        rows.append([add(p,add(mul(normal,math.cos(i/sides*math.tau)*radius),mul(bitangent,math.sin(i/sides*math.tau)*radius))) for i in range(sides+1)])
        uv.append([(i/sides,flow_start+t*(1-flow_start)) for i in range(sides+1)])
    mesh.grid(rows,uv)

def trees(include_tips=False):
    mesh=Mesh();blossoms=[];tips=[];rng=random.Random(7351)
    for side in (-1,1):
        for index,(x,y,h) in enumerate([(300,2050,1920),(2550,2380,1780),(4700,2900,2050)]):
            y*=side;p=[(x,y,0),(x-140,y+side*125,h*.32),(x+130,y-side*155,h*.7),(x-40,y-side*150,h)]
            tube(mesh,p,55 if index==0 else 41,6.5,40,12)
            for k in range(6):
                t=.32+k*.095;start=bezier(p,t);angle=k*2.4+side*.4
                reach=rng.uniform(300,650);tip=add(start,(math.cos(angle)*reach,math.sin(angle)*reach,h*(1-t)*.7))
                branch=[start,add(start,(40,side*70,160)),add(tip,(-150,-side*90,-30)),tip]
                tube(mesh,branch,25*(1-t)+5,2.1,25,9,t)
                for twig in range(3):
                    joint=bezier(branch,.48+twig*.16)
                    end=add(joint,(rng.uniform(-160,160),rng.uniform(-160,160),rng.uniform(140,240)))
                    tube(mesh,[joint,add(joint,(0,side*25,70)),add(end,(-20,0,-35)),end],5.2,0.65,14,7,.75)
                    tips.append(end)
                    for leaf in range(24):
                        pos=add(end,(rng.gauss(0,65),rng.gauss(0,85),rng.gauss(0,40)))
                        blossoms.append((pos,rng.uniform(7.,12.),index==1 and k%3==0))
    return (mesh,blossoms,tips) if include_tips else (mesh,blossoms)

def pavilion_roof():
    mesh=Mesh();rows=[];uv=[]
    # Long ridge parallel to the pavilion facade, with four hips and lifted corners.
    for j in range(65):
        y=-850+1700*j/64;row=[];tex=[]
        for i in range(49):
            x=-520+1040*i/48;rx=abs(x)/520;ry=abs(y)/850
            hip=max(0,min(1-rx,(850-abs(y))/330))
            z=680+250*hip+72*rx**4+45*rx**4*ry**5
            row.append((x,y,z));tex.append((j/64,i/48))
        rows.append(row);uv.append(tex)
    mesh.grid(rows,uv)
    return mesh

def curved_wall():
    mesh=Mesh()
    for side in (-1,1):
        rows=[];uv=[]
        for j in range(2):
            row=[];tex=[]
            for i in range(161):
                t=i/160;y=side*(700+3400*t)
                z=400+85*math.cos(t*math.tau*2.2)+90*t
                row.append((4800+j*220,y,z-j*45));tex.append((t,j))
            if side==1:row.reverse();tex.reverse()
            rows.append(row);uv.append(tex)
        mesh.grid(rows,uv)
    return mesh

def rock():
    mesh=Mesh();rows=[];uv=[]
    for j in range(33):
        a=.005+(math.pi-.01)*j/32;row=[];tex=[]
        for i in range(65):
            t=i/64*math.tau
            radius=50*(1+.13*math.sin(t*5+a*3)+.09*math.cos(t*3-a*5)+.045*math.sin(t*9+a*7))
            row.append((radius*math.sin(a)*math.cos(t),radius*math.sin(a)*math.sin(t),radius*math.cos(a)))
            tex.append((i/64,j/32))
        row.reverse();tex.reverse();rows.append(row);uv.append(tex)
    mesh.grid(rows,uv);return mesh
