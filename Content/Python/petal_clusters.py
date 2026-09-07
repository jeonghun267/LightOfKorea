"""Visual-only petal clusters using the garden's existing two ISM components."""
import random, math

REV='petals-3'

def layout():
    import hero_geometry as geo
    _,_,tips=geo.trees(include_tips=True)
    rng=random.Random(92405);points=[];groups=[]
    for tree in range(6):
        kinds=['compact','medium','airy'];rng.shuffle(kinds)
        for twig,kind in zip((4,9,14),kinds):
            tip=tips[tree*18+twig];center=list(tip)
            center[0]+=rng.uniform(-25,25);center[1]+=rng.uniform(-25,25);center[2]+=rng.uniform(25,55)
            low,high,rx,ry,rz={'compact':(12,16,30,48,30),'medium':(20,25,42,82,52),'airy':(27,34,58,120,80)}[kind]
            n=rng.randint(low,high);groups.append({'tree':tree,'center':center,'tip':tip,'kind':kind,'count':n,'radii':(rx,ry,rz)})
            for i in range(n):
                category=rng.choices(['small','medium','large'],[.55,.35,.10])[0]
                lo,hi={'small':(12,21),'medium':(25,39),'large':(46,64)}[category]
                size=rng.uniform(lo,hi)
                p=(center[0]+rng.gauss(0,rx),center[1]+rng.gauss(0,ry),center[2]+rng.gauss(0,rz))
                points.append({'p':p,'size':size,'aspect':rng.uniform(.52,.86),'category':category,
                  'roll':rng.uniform(-40,40),'violet':rng.random()<.06})
    return points,groups

def material():
    import unreal as u
    import build_zone01 as b
    mat,fresh=b.asset(b.BASE+'/Materials/Hero/M_Tree_SoftPetal',u.Material,u.MaterialFactoryNew())
    if not fresh and b.EAL.get_metadata_tag(mat,'LOK.PetalRevision')==REV:return mat
    b.MAT.delete_all_material_expressions(mat)
    mat.set_editor_property('blend_mode',u.BlendMode.BLEND_TRANSLUCENT)
    mat.set_editor_property('shading_model',u.MaterialShadingModel.MSM_UNLIT)
    mat.set_editor_property('two_sided',True)
    mat.set_editor_property('used_with_instanced_static_meshes',True)
    collection=u.load_asset(b.BASE+'/Materials/MPC/MPC_LOK_Global')
    tex=b.expression(mat,u.MaterialExpressionTextureCoordinate)
    rnd=b.expression(mat,u.MaterialExpressionPerInstanceRandom)
    clock=b.mpc_node(mat,collection,'ExhibitTime')
    shape=b.custom(mat,r'''
        float2 p=(UV-.5)*2;float angle=R*6.283;
        p=mul(float2x2(cos(angle),-sin(angle),sin(angle),cos(angle)),p);
        float width=.53+.20*p.y;
        float petal=length(float2(p.x/max(.28,width),(p.y+.08)/.91));
        float blob=length(p*float2(1.38,1.8))+.06*sin(atan2(p.y,p.x)*3+R*11);
        float d=R<.76?blob:petal;
        float edge=(1-smoothstep(.60,1.0,d))*exp(-d*d*.95);
        float phase=frac(T*(.055+R*.037)+R*7);
        float life=smoothstep(.03,.25,phase)*(1-smoothstep(.64,.98,phase));
        life=lerp(life,.72,step(.82,R));
        float breath=.87+.13*sin(T*(1.1+R*1.6)+R*83);
        return edge*life*breath*.76;
    ''',{'UV':tex,'R':rnd,'T':clock},u.CustomMaterialOutputType.CMOT_FLOAT1)
    fade=b.expression(mat,u.MaterialExpressionDepthFade,fade_distance_default=35.)
    b.connect(shape,fade,'Opacity');b.output(mat,fade,u.MaterialProperty.MP_OPACITY)
    color=b.custom(mat,r'''return R<.70?float3(.78,.83,.90):(R<.94?float3(.51,.70,.77):float3(.64,.57,.72));''',{'R':rnd})
    glow=b.multiply(mat,color,b.scalar(mat,.68),b.mpc_node(mat,collection,'ForestGlow'),
      b.mpc_node(mat,collection,'GlobalIntensity'),b.mpc_node(mat,collection,'TransitionAlpha'))
    b.output(mat,glow,u.MaterialProperty.MP_EMISSIVE_COLOR)
    drift=b.custom(mat,r'''
        float travel=R>.28?36+R*45:7;
        float cycle=R>.82?0:floor(T*(.055+R*.037)+R*7);
        float seed=frac(sin(R*71+cycle*13.1)*43758.54);
        float3 v=float3(sin(T*.16+R*31),cos(T*.12+R*19),sin(T*.21+R*53))*travel;
        float3 offset=float3(seed-.5,frac(seed*7)-.5,frac(seed*13)-.5)*55;
        return v+offset+float3(sin(T*1.3+R*21)*(UV.y-.5)*13,0,0);
    ''',{'UV':tex,'R':rnd,'T':clock})
    b.output(mat,drift,u.MaterialProperty.MP_WORLD_POSITION_OFFSET)
    b.EAL.set_metadata_tag(mat,'LOK.PetalRevision',REV);b.finish_material(mat)
    return mat

def apply(garden):
    import unreal as u
    mat=material();points,groups=layout()
    components=[c for c in garden.get_components_by_class(u.InstancedStaticMeshComponent)
      if c.get_name().startswith(('CyanBlossoms','VioletBlossoms'))]
    if len(components)!=2:raise RuntimeError('Expected existing two blossom ISM components')
    plane=u.load_asset('/Engine/BasicShapes/Plane')
    for c in components:
        c.clear_instances();c.set_static_mesh(plane);c.set_material(0,mat);c.set_visibility(True,True)
        # Native setters avoid editor property notifications that reconstruct Blueprint
        # components and invalidate the instance handles during this loop.
        c.set_cast_shadow(False)
        c.set_bounds_scale(2.0)
        violet=c.get_name().startswith('Violet')
        for p in points:
            if p['violet']!=violet:continue
            c.add_instance(u.Transform(location=u.Vector(*p['p']),
              rotation=u.Rotator(pitch=90,yaw=0,roll=p['roll']),
              scale=u.Vector(p['size']/100,p['size']*p['aspect']/100,1)))
    assert sum(c.get_instance_count() for c in components)==len(points)
    return {'revision':REV,'instances':len(points),'clusters':len(groups),
      'sizes':{s:sum(p['category']==s for p in points) for s in ('small','medium','large')},
      'layout':groups,'material':mat.get_path_name()}
