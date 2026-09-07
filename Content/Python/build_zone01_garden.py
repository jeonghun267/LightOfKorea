"""Reference-directed garden blocking with native primitive mesh instances."""
import math
import random
import unreal as u
import build_zone01 as b

def material(name,base,glow,collection,control=None):
    mat,fresh=b.asset(b.BASE+"/Materials/Master/"+name,u.Material,u.MaterialFactoryNew())
    if fresh:
        b.output(mat,b.color(mat,base),u.MaterialProperty.MP_BASE_COLOR)
        b.output(mat,b.scalar(mat,.63),u.MaterialProperty.MP_ROUGHNESS)
        value=b.color(mat,glow)
        if control:
            value=b.multiply(mat,value,b.mpc_node(mat,collection,control))
        b.output(mat,value,u.MaterialProperty.MP_EMISSIVE_COLOR)
        mat.set_editor_property("used_with_instanced_static_meshes",True)
        b.finish_material(mat)
    return mat

def mesh_component(bp,name,shape,mat):
    subsystem=u.get_engine_subsystem(u.SubobjectDataSubsystem)
    for handle in subsystem.k2_gather_subobject_data_for_blueprint(bp):
        data=u.SubobjectDataBlueprintFunctionLibrary.get_data(handle)
        comp=u.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(data,bp)
        if isinstance(comp,u.InstancedStaticMeshComponent) and comp.get_name().startswith(name+"_"):
            comp.clear_instances()
            b.configure_mesh(comp,shape,mat)
            return comp
    comp=b.component(bp,name,u.InstancedStaticMeshComponent)
    b.configure_mesh(comp,shape,mat)
    return comp

def add(comp,p,scale,rotation=None):
    rotation=rotation or u.Rotator(pitch=0,yaw=0,roll=0)
    comp.add_instance(u.Transform(location=u.Vector(*p),rotation=rotation,scale=u.Vector(*scale)))

def segment(comp,start,end,radius):
    vector=u.Vector(*end)-u.Vector(*start)
    length=math.sqrt(vector.x**2+vector.y**2+vector.z**2)
    rot=u.MathLibrary.find_look_at_rotation(u.Vector(*start),u.Vector(*end))
    rot.pitch-=90
    add(comp,tuple((a+c)/2 for a,c in zip(start,end)),(radius/50,radius/50,length/100),rot)

def main():
    collection=u.load_asset(b.BASE+"/Materials/MPC/MPC_LOK_Global")
    wood=material("M_Garden_Wood",(.008,.012,.018),(.015,.035,.055),collection)
    blue=material("M_Blossom_Cyan",(.02,.05,.08),(.18,1.4,2.8),collection,"ForestGlow")
    violet=material("M_Blossom_Violet",(.04,.015,.08),(.95,.25,2.5),collection,"ForestGlow")
    rock=material("M_Garden_Rock",(.012,.02,.03),(.001,.003,.005),collection)
    warm=material("M_Lantern_Warm",(.12,.07,.025),(2.0,1.0,.32),collection,"TransitionAlpha")
    dark=material("M_Jar_Opening",(.006,.012,.022),(.01,.025,.055),collection,"MoonGlow")
    bp,_=b.blueprint(b.BASE+"/Blueprints/Environment/BP_LuminousGarden")
    trunk=mesh_component(bp,"GardenWood","Cylinder",wood)
    cyan=mesh_component(bp,"CyanBlossoms","Sphere",blue)
    purple=mesh_component(bp,"VioletBlossoms","Sphere",violet)
    streak=mesh_component(bp,"LightRain","Cylinder",blue)
    rocks=mesh_component(bp,"GardenRocks","Sphere",rock)
    lanterns=mesh_component(bp,"LanternFrames","Cube",wood)
    lamps=mesh_component(bp,"LanternGlow","Cube",warm)
    rng=random.Random(2109)
    for side in (-1,1):
        for tree_index in range(7):
            x=400+tree_index*570
            y=side*(1550+rng.uniform(-110,200))
            height=rng.uniform(950,1650)
            crown=(x+rng.uniform(-90,90),y,height)
            segment(trunk,(x,y,0),crown,14)
            for branch_index in range(7):
                angle=branch_index*math.tau/7+rng.uniform(-.25,.25)
                radius=rng.uniform(170,390)
                endpoint=(crown[0]+math.cos(angle)*radius,crown[1]+math.sin(angle)*radius,height+rng.uniform(-120,260))
                segment(trunk,(x,y,height*.63),endpoint,6)
                for twig_index in range(3):
                    tip=(endpoint[0]+rng.uniform(-90,90),endpoint[1]+rng.uniform(-90,90),endpoint[2]+rng.uniform(20,120))
                    segment(trunk,endpoint,tip,2.5)
                for leaf in range(65):
                    a=rng.random()*math.tau
                    r=math.sqrt(rng.random())*155
                    p=(endpoint[0]+math.cos(a)*r,endpoint[1]+math.sin(a)*r,endpoint[2]+rng.uniform(-65,110))
                    size=rng.uniform(.13,.28)
                    add(cyan if (tree_index+branch_index)%3 else purple,p,(size,size,size*.6))
            for rain in range(5):
                rx=x+rng.uniform(-230,230)
                ry=y+rng.uniform(-230,230)
                low=rng.uniform(80,550)
                segment(streak,(rx,ry,low),(rx,ry,height+300),.9)
            for stone in range(3):
                sx=x+rng.uniform(-220,220)
                sy=y+rng.uniform(-210,210)
                h=rng.uniform(150,500)
                add(rocks,(sx,sy,h*.38),(rng.uniform(1.2,3.0),rng.uniform(1.1,2.6),h/100),
                    u.Rotator(pitch=rng.uniform(-18,18),yaw=rng.uniform(0,180),roll=rng.uniform(-18,18)))
        for index in range(8):
            x=-1400+index*480
            y=side*(1120+index*12)
            add(lanterns,(x,y,26),(.30,.30,.52))
            add(lamps,(x-16,y,27),(.035,.22,.35))
            add(lamps,(x,y-side*16,27),(.22,.035,.35))
            light=b.actor("GardenLantern_%s_%02d"%(side,index),u.PointLight,(x,y,45))
            comp=light.get_component_by_class(u.PointLightComponent)
            comp.set_mobility(u.ComponentMobility.MOVABLE)
            comp.set_intensity(3)
            comp.set_light_color(u.LinearColor(1,.57,.22,1))
            comp.set_editor_property("attenuation_radius",210)
            comp.set_editor_property("cast_shadows",False)
        for index in range(5):
            add(rocks,(5200+index*300,side*(1700+index*160),700+index*100),(9,5,18+index*3),
                u.Rotator(pitch=8,yaw=15*index,roll=side*12))
    u.BlueprintEditorLibrary.compile_blueprint(bp)
    b.save(bp)
    b.actor("LuminousGarden",bp.generated_class())
    moonmat=u.load_asset(b.BASE+"/Materials/Instances/MI_Zone01_Moon")
    neck=b.actor("MoonJar_Neck",u.StaticMeshActor,(3000,0,2235))
    b.configure_mesh(neck.static_mesh_component,"Cylinder",moonmat,scale=(12,12,.70))
    opening=b.actor("MoonJar_Opening",u.StaticMeshActor,(3000,0,2273))
    b.configure_mesh(opening.static_mesh_component,"Cylinder",dark,scale=(11.5,11.5,.06))
    rim_bp,_=b.blueprint(b.BASE+"/Blueprints/Environment/BP_MoonJarRim")
    rim=mesh_component(rim_bp,"PorcelainRim","Sphere",moonmat)
    for index in range(64):
        angle=index*math.tau/64
        add(rim,(math.cos(angle)*598,math.sin(angle)*598,0),(.62,.62,.24))
    u.BlueprintEditorLibrary.compile_blueprint(rim_bp)
    b.save(rim_bp)
    b.actor("MoonJar_Rim",rim_bp.generated_class(),(3000,0,2282))
    for index in range(7):
        step=b.actor("GardenStep_%02d"%index,u.StaticMeshActor,(2000+index*80,0,index*14+7))
        b.configure_mesh(step.static_mesh_component,"Cube",rock,scale=(.86,6.5,.14))
    # Keep the halo centered on the revised central installation.
    for actor in b.ACTORS.get_all_level_actors():
        if actor.get_actor_label()=="NS_Zone01_MoonHalo":
            actor.set_actor_location(u.Vector(3000,0,1400),False,False)
        elif actor.get_actor_label()=="NS_Zone01_FogParticles":
            actor.set_actor_location(u.Vector(1200,800,100),False,False)
    if not b.LEVELS.save_current_level():
        raise RuntimeError("Garden map save failed")
    b.log("Reference-directed garden blockout saved: 14 trees, 6370 blossom instances, moon jar rim, rocks and lanterns")

if __name__=="__main__":
    main()
