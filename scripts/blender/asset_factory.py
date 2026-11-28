# ruff: noqa
import argparse, json, math, sys
from pathlib import Path
import bpy
from mathutils import Vector

def args():
    values=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    p=argparse.ArgumentParser()
    p.add_argument("--asset-kind",choices=("character","world","prop"),required=True)
    p.add_argument("--asset-id",required=True); p.add_argument("--name",required=True)
    p.add_argument("--output-dir",type=Path,required=True)
    return p.parse_args(values)

def mat(name,color,rough=.72,metal=0):
    m=bpy.data.materials.new(name); m.diffuse_color=(*color,1); m.use_nodes=True
    bs=m.node_tree.nodes.get("Principled BSDF")
    bs.inputs["Base Color"].default_value=(*color,1); bs.inputs["Roughness"].default_value=rough
    bs.inputs["Metallic"].default_value=metal
    return m

def smooth(obj,material,bevel=0):
    obj.data.materials.append(material)
    for face in obj.data.polygons: face.use_smooth=True
    if bevel:
        mod=obj.modifiers.new("Soft crafted edges","BEVEL"); mod.width=bevel; mod.segments=3
        obj.modifiers.new("Weighted corner normals","WEIGHTED_NORMAL")
    return obj

def ball(name,loc,scale,material,seg=32):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg,ring_count=24,location=loc)
    o=bpy.context.object; o.name=name; o.scale=scale
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    return smooth(o,material)

def block(name,loc,dims,material,bevel=.06):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc)
    o=bpy.context.object; o.name=name; o.dimensions=dims
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    return smooth(o,material,bevel)

def curve(name,coords,radius,material):
    c=bpy.data.curves.new(name,"CURVE"); c.dimensions="3D"; c.bevel_depth=radius; c.bevel_resolution=4
    s=c.splines.new("BEZIER"); s.bezier_points.add(len(coords)-1)
    for p,v in zip(s.bezier_points,coords): p.co=v; p.handle_left_type="AUTO"; p.handle_right_type="AUTO"
    o=bpy.data.objects.new(name,c); bpy.context.collection.objects.link(o); o.data.materials.append(material)
    return o

def rig(parts):
    # Curves are converted to meshes so they can be skinned and exported with the rig.
    for obj, _bone in parts:
        if obj.type != "MESH":
            bpy.ops.object.select_all(action="DESELECT")
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.convert(target="MESH")
    data=bpy.data.armatures.new("CartoonStudio_HumanoidRig")
    arm=bpy.data.objects.new("CartoonStudio_HumanoidRig",data); bpy.context.collection.objects.link(arm)
    bpy.context.view_layer.objects.active=arm; arm.select_set(True); bpy.ops.object.mode_set(mode="EDIT")
    specs={
      "root":((0,0,0),(0,0,.2),None),"pelvis":((0,0,.85),(0,0,1.1),"root"),
      "spine":((0,0,1.05),(0,0,1.78),"pelvis"),"chest":((0,0,1.7),(0,0,2),"spine"),
      "neck":((0,0,1.95),(0,0,2.2),"chest"),"head":((0,0,2.15),(0,0,2.95),"neck"),
      "upper_arm.L":((-.38,0,1.82),(-.68,0,1.35),"chest"),
      "forearm.L":((-.68,0,1.35),(-.7,0,.98),"upper_arm.L"),
      "upper_arm.R":((.38,0,1.82),(.68,0,1.35),"chest"),
      "forearm.R":((.68,0,1.35),(.7,0,.98),"upper_arm.R"),
      "thigh.L":((-.2,0,1),(-.2,0,.5),"pelvis"),"shin.L":((-.2,0,.5),(-.2,0,.1),"thigh.L"),
      "thigh.R":((.2,0,1),(.2,0,.5),"pelvis"),"shin.R":((.2,0,.5),(.2,0,.1),"thigh.R")}
    for name,(head,tail,parent) in specs.items():
        b=data.edit_bones.new(name); b.head=head; b.tail=tail
        if parent: b.parent=data.edit_bones[parent]; b.use_connect=(b.parent.tail==b.head)
    bpy.ops.object.mode_set(mode="OBJECT"); arm.select_set(False)
    for obj,bone in parts:
        obj.parent=arm; group=obj.vertex_groups.new(name=bone)
        group.add(list(range(len(obj.data.vertices))),1,"REPLACE")
        mod=obj.modifiers.new("Humanoid deformation","ARMATURE"); mod.object=arm
    arm["cartoon_studio_rig_profile"]="humanoid_stylized_v1"
    return arm

def character():
    skin=mat("Skin | warm peach",(.78,.43,.29)); light=mat("Skin | highlights",(.94,.64,.46))
    hair=mat("Hair | espresso",(.065,.028,.018)); teal=mat("Clothing | teal jacket",(.025,.32,.37))
    gold=mat("Clothing | piping",(.94,.62,.19)); pants=mat("Clothing | indigo",(.10,.15,.34))
    leather=mat("Shoes | leather",(.20,.07,.035)); white=mat("Eyes | ivory",(.98,.92,.79),.3)
    iris=mat("Eyes | amber",(.35,.15,.04),.25); dark=mat("Eyes | pupil",(.012,.009,.008),.2)
    parts=[]
    def add(obj,bone): parts.append((obj,bone)); return obj
    add(ball("Body | torso",(0,0,1.47),(.43,.30,.62),teal),"spine")
    add(ball("Body | neck",(0,0,2.04),(.15,.14,.22),skin),"neck")
    add(ball("Body | head",(0,-.01,2.52),(.39,.34,.49),skin,48),"head")
    for x,side in ((-.21,"L"),(.21,"R")): add(ball("Face | cheek."+side,(x,-.26,2.39),(.16,.10,.15),light),"head")
    add(ball("Face | nose",(0,-.36,2.48),(.08,.10,.13),light),"head")
    for x,side in ((-.145,"L"),(.145,"R")):
        add(ball("Eye | white."+side,(x,-.31,2.61),(.105,.075,.13),white),"head")
        add(ball("Eye | iris."+side,(x,-.378,2.60),(.052,.027,.073),iris),"head")
        add(ball("Eye | pupil."+side,(x,-.401,2.60),(.026,.016,.046),dark),"head")
        add(ball("Eye | glint."+side,(x-.014,-.417,2.635),(.013,.009,.018),white),"head")
        add(curve("Face | brow."+side,[(x-.09,-.34,2.77),(x,-.38,2.80),(x+.09,-.34,2.77)],.024,hair),"head")
    add(curve("Face | smile",[(-.12,-.35,2.34),(0,-.39,2.30),(.12,-.35,2.34)],.018,hair),"head")
    add(ball("Hair | sculpted cap",(0,.005,2.89),(.405,.35,.19),hair,40),"head")
    for i,x in enumerate((-.27,-.12,.04,.20,.31)):
        lock=ball("Hair | swept lock %02d"%i,(x,-.14,2.92+(.06 if i in (1,2) else 0)),(.12,.22,.12),hair)
        lock.rotation_euler[1]=-.35+i*.12; add(lock,"head")
    add(ball("Clothing | jacket panel",(0,-.245,1.48),(.34,.09,.50),gold),"spine")
    add(block("Clothing | lapel.L",(-.12,-.32,1.77),(.13,.055,.31),teal,.03),"chest")
    add(block("Clothing | lapel.R",(.12,-.32,1.77),(.13,.055,.31),teal,.03),"chest")
    for side,sign in (("L",-1),("R",1)):
        add(ball("Sleeve."+side,(sign*.48,0,1.67),(.17,.17,.37),teal),"upper_arm."+side)
        add(ball("Forearm."+side,(sign*.56,0,1.20),(.12,.13,.31),skin),"forearm."+side)
        add(ball("Hand."+side,(sign*.58,-.03,.91),(.13,.12,.15),light),"forearm."+side)
        add(ball("Trouser."+side,(sign*.20,0,.62),(.18,.20,.48),pants),"thigh."+side)
        add(ball("Shin."+side,(sign*.20,0,.25),(.13,.14,.25),pants),"shin."+side)
        add(ball("Boot."+side,(sign*.20,-.11,.10),(.18,.29,.12),leather),"shin."+side)
        add(ball("Cuff."+side,(sign*.55,0,1.0),(.135,.14,.07),gold),"forearm."+side)
    add(ball("Accessory | buckle",(0,-.315,1.02),(.075,.035,.075),gold),"pelvis")
    arm=rig(parts); head=bpy.data.objects["Body | head"]
    bpy.context.view_layer.objects.active=head; head.select_set(True)
    bpy.ops.object.shape_key_add(from_mix=False)\n    head.data.shape_keys.key_blocks[-1].name="Basis"
    bpy.ops.object.shape_key_add(from_mix=False); head.data.shape_keys.key_blocks[-1].name="Smile"
    bpy.ops.object.shape_key_add(from_mix=False); head.data.shape_keys.key_blocks[-1].name="Blink"
    for v in head.data.shape_keys.key_blocks["Smile"].data:
        if v.co.z<-.12 and abs(v.co.x)<.22: v.co.z-=.025
    for v in head.data.shape_keys.key_blocks["Blink"].data:
        if v.co.z>.05: v.co.z*=.94
    head.select_set(False)
    return {"rig":arm.name,"mesh_count":len(parts),"shape_keys":["Smile","Blink"]}

def world():
    grass=mat("World | meadow",(.22,.42,.19)); road=mat("World | asphalt",(.15,.17,.19))
    peach=mat("World | peach plaster",(.82,.48,.31)); butter=mat("World | butter plaster",(.91,.70,.36))
    roof=mat("World | terracotta",(.4,.12,.075)); cream=mat("World | cream trim",(.94,.84,.65))
    glass=mat("World | blue glass",(.13,.4,.54),.22)
    block("Terrain | green",(0,0,-.2),(14,14,.4),grass,.2)
    block("Road | lane",(0,-2.7,.015),(14,2,.06),road,.1)
    for x in (-5.5,-3.5,-1.5,.5,2.5,4.5): block("Road | dash",(x,-2.7,.05),(.9,.06,.015),cream,.01)
    for i,x in enumerate((-4.1,.2,4.0)):
        block("Building | facade",(x,1.5,1.25),(2.5,2,2.5),peach if i%2==0 else butter,.12)
        bpy.ops.mesh.primitive_cone_add(vertices=4,radius1=1.65,radius2=0,depth=1.2,location=(x,1.5,3.1),rotation=(0,0,math.pi/4))
        smooth(bpy.context.object,roof)
        for wx in (-.65,.65):
            block("Window | frame",(x+wx,.475,1.75),(.52,.08,.72),cream,.04)
            block("Window | glass",(x+wx,.425,1.75),(.39,.045,.58),glass,.02)
        block("Door",(x,.43,.63),(.52,.09,1.1),roof,.04)
    for i,(x,y) in enumerate(((-5.5,0),(5.8,.4),(-2.8,4.8),(3,5))):
        block("Tree | trunk",(x,y,.75),(.25,.28,1.5),roof,.05)
        ball("Tree | crown",(x,y,1.9),(.85,.8,.95),grass)
    return {"layout":"storybook_village_blockout_v1"}

def prop():
    wood=mat("Prop | honey oak",(.48,.23,.095)); gold=mat("Prop | brass",(.83,.53,.20),.35,.2)
    inset=mat("Prop | inset",(.12,.065,.035))
    block("Treasure chest | body",(0,0,.55),(1.65,1,.95),wood,.13)
    block("Treasure chest | lid",(0,0,1.12),(1.72,1.05,.25),gold,.11)
    block("Treasure chest | inset",(0,-.51,.58),(1.18,.045,.52),inset,.05)
    block("Treasure chest | clasp",(0,-.56,.84),(.18,.08,.35),gold,.04)
    for x in (-.65,-.32,0,.32,.65): block("Treasure chest | band",(x,-.535,1.13),(.035,.025,.21),gold,.01)
    return {"prop_family":"storybook_treasure_chest_v1"}

def main():
    a=args(); out=a.output_dir.resolve(); out.mkdir(parents=True,exist_ok=True)
    bpy.ops.object.select_all(action="SELECT"); bpy.ops.object.delete(use_global=False)
    details=character() if a.asset_kind=="character" else world() if a.asset_kind=="world" else prop()
    scene=bpy.context.scene
    w=bpy.data.worlds[0] if bpy.data.worlds else bpy.data.worlds.new("Cartoon Studio | studio")
    scene.world=w; w.color=(.16,.19,.24)
    bpy.ops.object.light_add(type="AREA",location=(4,-6,8)); bpy.context.object.data.energy=1100
    bpy.context.object.data.shape="DISK"; bpy.context.object.data.size=6
    bpy.ops.object.camera_add(location=(5.8,-9.5,5))
    camera=bpy.context.object; camera.rotation_euler=(Vector((0,0,1.35))-camera.location).to_track_quat("-Z","Y").to_euler()
    scene.camera=camera; scene.render.engine="BLENDER_EEVEE_NEXT"
    scene.render.resolution_x=1200; scene.render.resolution_y=1200
    scene["cartoon_studio_asset_kind"]=a.asset_kind; scene["cartoon_studio_asset_id"]=a.asset_id
    blend=out/(a.asset_id+".blend"); glb=out/(a.asset_id+".glb")
    bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    bpy.ops.export_scene.gltf(filepath=str(glb),export_format="GLB",export_animations=True,
      export_skins=True,export_morph=True,export_materials="EXPORT",export_cameras=False,export_lights=False)
    manifest={"schema_version":1,"asset_id":a.asset_id,"asset_kind":a.asset_kind,"name":a.name,
      "generator":"cartoon-studio-blender-factory","generator_version":"0.1.0",
      "blender_version":bpy.app.version_string,"source_file":blend.name,"glb_file":glb.name,
      "editable_source":True,"license":"Original procedural asset; no third-party geometry included.",
      "details":details}
    (out/"manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
    print("CARTOON_STUDIO_ASSET_COMPLETE "+json.dumps(manifest))
if __name__=="__main__": main()
