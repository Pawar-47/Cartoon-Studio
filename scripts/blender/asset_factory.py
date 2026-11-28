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

def loft(name, location, profile, material, segments=48):
    """Create a continuous organic mesh from elliptical cross-section rings."""
    vertices = []
    for z, radius_x, radius_y, depth_offset in profile:
        for index in range(segments):
            angle = 2 * math.pi * index / segments
            vertices.append((
                radius_x * math.cos(angle),
                depth_offset + radius_y * math.sin(angle),
                z,
            ))
    faces = []
    for ring in range(len(profile) - 1):
        for index in range(segments):
            current = ring * segments + index
            following = ring * segments + (index + 1) % segments
            faces.append((current, following, following + segments, current + segments))
    bottom_center = len(vertices)
    vertices.append((0, profile[0][3], profile[0][0]))
    top_center = len(vertices)
    vertices.append((0, profile[-1][3], profile[-1][0]))
    last_ring = (len(profile) - 1) * segments
    for index in range(segments):
        following = (index + 1) % segments
        faces.append((bottom_center, following, index))
        faces.append((top_center, last_ring + index, last_ring + following))
    mesh = bpy.data.meshes.new(name + " | sculpted mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.location = location
    return smooth(obj, material)


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
    skin = mat("Skin | warm peach", (.76, .40, .27))
    highlight = mat("Skin | soft highlights", (.91, .58, .41))
    ear_inner = mat("Skin | ear detail", (.43, .16, .12))
    hair = mat("Hair | deep espresso", (.045, .018, .012))
    hair_light = mat("Hair | warm highlights", (.12, .045, .022))
    jacket = mat("Clothing | peacock teal", (.018, .27, .31))
    jacket_dark = mat("Clothing | deep teal seams", (.012, .12, .16))
    gold = mat("Clothing | brass piping", (.91, .55, .16))
    shirt = mat("Clothing | warm ivory", (.91, .78, .55))
    pants = mat("Clothing | indigo", (.075, .12, .28))
    pants_seam = mat("Clothing | seam blue", (.16, .23, .42))
    leather = mat("Shoes | dark leather", (.16, .055, .025))
    sole = mat("Shoes | sole", (.045, .035, .03))
    eye_white = mat("Eyes | ivory", (.98, .93, .81), .28)
    iris = mat("Eyes | amber", (.35, .13, .025), .24)
    pupil = mat("Eyes | dark pupil", (.009, .006, .004), .18)
    mouth = mat("Face | mouth interior", (.12, .018, .018), .6)
    parts = []

    def add(obj, bone):
        parts.append((obj, bone))
        return obj

    # Continuous cross-section meshes define the torso, jaw, limbs and clothing silhouette.
    add(loft(
        "Body | tailored jacket shell", (0, 0, 1.47),
        [(-.59, .27, .20, 0), (-.54, .32, .23, 0),
         (-.39, .35, .25, 0), (-.18, .39, .28, 0),
         (.08, .44, .29, 0), (.30, .46, .28, 0),
         (.46, .39, .24, 0), (.55, .25, .18, 0)],
        jacket, 56,
    ), "spine")
    add(loft(
        "Body | neck", (0, 0, 2.02),
        [(-.17, .12, .12, 0), (-.10, .14, .13, 0),
         (.08, .14, .13, 0), (.17, .11, .11, 0)],
        skin, 40,
    ), "neck")
    head = add(loft(
        "Face | sculpted head", (0, 0, 2.53),
        [(-.51, .055, .09, 0), (-.47, .15, .17, 0),
         (-.37, .23, .23, -.005), (-.23, .29, .27, -.008),
         (-.05, .34, .30, 0), (.16, .36, .31, .008),
         (.34, .31, .27, .012), (.46, .21, .19, .01),
         (.51, .055, .07, 0)],
        skin, 64,
    ), "head")

    for sign, side in ((-1, "L"), (1, "R")):
        add(ball("Ear | outer." + side, (sign * .335, -.005, 2.51),
                 (.082, .075, .13), highlight), "head")
        add(ball("Ear | inner." + side, (sign * .382, -.055, 2.51),
                 (.032, .025, .073), ear_inner), "head")

    blink_meshes = []
    for x, side in ((-.145, "L"), (.145, "R")):
        white = add(ball("Eye | sclera." + side, (x, -.286, 2.625),
                         (.079, .061, .103), eye_white, 40), "head")
        iris_obj = add(ball("Eye | iris." + side, (x, -.342, 2.615),
                            (.041, .025, .058), iris, 32), "head")
        pupil_obj = add(ball("Eye | pupil." + side, (x, -.361, 2.615),
                             (.021, .014, .038), pupil, 32), "head")
        add(ball("Eye | catchlight." + side, (x - .012, -.375, 2.642),
                 (.011, .008, .016), eye_white, 20), "head")
        blink_meshes.extend((white, iris_obj, pupil_obj))
        add(curve("Face | upper eyelid." + side,
                  [(x - .085, -.29, 2.62), (x, -.35, 2.72),
                   (x + .085, -.29, 2.62)], .018, ear_inner), "head")
        add(curve("Face | brow." + side,
                  [(x - .085, -.285, 2.765), (x, -.335, 2.79),
                   (x + .085, -.285, 2.765)], .026, hair), "head")

    add(loft(
        "Face | shaped nose", (0, -.305, 2.455),
        [(-.10, .025, .025, 0), (-.055, .052, .055, -.015),
         (.035, .044, .05, 0), (.09, .018, .025, .005)],
        highlight, 32,
    ), "head")
    mouth_obj = add(ball("Face | mouth cavity", (0, -.275, 2.245),
                         (.105, .035, .048), mouth, 32), "head")
    add(curve("Face | upper lip",
              [(-.12, -.308, 2.285), (0, -.323, 2.275),
               (.12, -.308, 2.285)], .014, ear_inner), "head")
    add(curve("Face | lower lip",
              [(-.09, -.30, 2.225), (0, -.315, 2.205),
               (.09, -.30, 2.225)], .012, highlight), "head")
    for sign, side in ((-1, "L"), (1, "R")):
        add(ball("Face | cheek highlight." + side,
                 (sign * .225, -.222, 2.405), (.075, .035, .055),
                 highlight, 24), "head")

    add(loft(
        "Hair | sculpted cap", (0, .012, 2.91),
        [(-.10, .30, .25, 0), (-.045, .365, .30, 0),
         (.035, .375, .31, .015), (.12, .33, .28, .025),
         (.19, .22, .19, .02), (.215, .055, .06, .01)],
        hair, 56,
    ), "head")
    add(curve("Hair | swept fringe",
              [(-.34, -.20, 2.91), (-.23, -.285, 2.96),
               (-.07, -.315, 2.99), (.10, -.29, 2.96),
               (.25, -.23, 2.91)], .065, hair_light), "head")
    add(curve("Hair | side sweep",
              [(.30, -.17, 2.94), (.37, -.10, 2.88),
               (.35, -.02, 2.78)], .055, hair), "head")
    add(curve("Hair | part highlight",
              [(-.04, -.27, 3.00), (.08, -.26, 3.025),
               (.20, -.22, 3.00)], .012, hair_light), "head")

    # Jacket tailoring: center shirt, lapels, piping, pockets, buttons and collar.
    add(block("Jacket | center placket", (0, -.286, 1.47),
              (.115, .035, .49), shirt, .025), "chest")
    for sign, side in ((-1, "L"), (1, "R")):
        lapel = add(block("Jacket | lapel." + side,
                          (sign * .135, -.302, 1.80),
                          (.115, .045, .25), gold, .025), "chest")
        lapel.rotation_euler[1] = sign * .24
        add(curve("Jacket | front piping." + side,
                  [(sign * .17, -.30, 1.70),
                   (sign * .16, -.31, 1.43),
                   (sign * .13, -.29, 1.20)], .012, gold), "spine")
        add(block("Jacket | pocket." + side,
                  (sign * .235, -.285, 1.37), (.105, .035, .12),
                  jacket_dark, .018), "spine")
    for z in (1.60, 1.47, 1.34):
        add(ball("Jacket | brass button", (0, -.326, z),
                 (.022, .012, .022), gold, 20), "spine")
    add(curve("Jacket | collar",
              [(-.17, -.285, 1.94), (-.08, -.33, 2.00),
               (0, -.345, 1.94), (.08, -.33, 2.00),
               (.17, -.285, 1.94)], .025, shirt), "chest")
    add(block("Body | waist belt", (0, -.02, .94),
              (.61, .43, .09), leather, .025), "pelvis")
    add(block("Body | belt buckle", (0, -.245, .94),
              (.105, .035, .075), gold, .018), "pelvis")

    for sign, side in ((-1, "L"), (1, "R")):
        add(loft(
            "Sleeve | upper." + side, (sign * .455, 0, 1.65),
            [(-.40, .12, .13, 0), (-.31, .16, .16, 0),
             (-.10, .17, .17, 0), (.16, .16, .16, 0),
             (.34, .13, .14, 0), (.40, .09, .10, 0)],
            jacket, 40,
        ), "upper_arm." + side)
        add(ball("Sleeve | cuff." + side, (sign * .515, 0, 1.28),
                 (.13, .14, .055), gold, 28), "forearm." + side)
        add(loft(
            "Arm | forearm." + side, (sign * .53, 0, 1.10),
            [(-.28, .085, .095, 0), (-.20, .105, .11, 0),
             (0, .12, .12, 0), (.18, .13, .13, 0),
             (.27, .105, .11, 0)],
            skin, 36,
        ), "forearm." + side)
        add(ball("Hand | palm." + side, (sign * .54, -.015, .79),
                 (.115, .095, .13), highlight, 28), "forearm." + side)
        for finger in range(4):
            fx = sign * (.54 + (finger - 1.5) * .045)
            fz = .675 - (.018 if finger in (0, 3) else 0)
            add(ball("Hand | finger.%s.%d" % (side, finger + 1),
                     (fx, -.025, fz), (.026, .031, .085),
                     skin, 20), "forearm." + side)
        add(ball("Hand | thumb." + side,
                 (sign * .405, -.045, .785), (.045, .04, .075),
                 skin, 20), "forearm." + side)

    for sign, side in ((-1, "L"), (1, "R")):
        add(loft(
            "Trousers | thigh." + side, (sign * .19, 0, .64),
            [(-.42, .105, .13, 0), (-.32, .14, .16, 0),
             (-.08, .16, .17, 0), (.20, .17, .18, 0),
             (.38, .145, .16, 0), (.43, .11, .13, 0)],
            pants, 40,
        ), "thigh." + side)
        add(curve("Trousers | seam." + side,
                  [(sign * .19, -.17, .93), (sign * .19, -.17, .66),
                   (sign * .19, -.13, .40)], .008, pants_seam), "thigh." + side)
        add(loft(
            "Trousers | shin." + side, (sign * .19, 0, .245),
            [(-.22, .09, .11, 0), (-.16, .11, .12, 0),
             (.04, .12, .13, 0), (.20, .13, .14, 0),
             (.25, .12, .13, 0)],
            pants, 36,
        ), "shin." + side)
        add(ball("Boot | upper." + side, (sign * .19, -.105, .105),
                 (.16, .27, .115), leather, 32), "shin." + side)
        add(block("Boot | sole." + side, (sign * .19, -.115, .035),
                  (.30, .40, .055), sole, .025), "shin." + side)

    # Facial animation targets are real mesh shape keys, not metadata-only controls.
    head.shape_key_add(name="Basis")
    smile = head.shape_key_add(name="Smile")
    for vertex in smile.data:
        x, _, z = vertex.co
        if -.30 < z < -.08:
            vertex.co.z += .025 * min(abs(x) / .22, 1.0)
    jaw = head.shape_key_add(name="JawOpen")
    for vertex in jaw.data:
        x, _, z = vertex.co
        if z < -.10:
            vertex.co.z -= .055 * max(0.0, 1.0 - abs(x) / .34)
    for obj in blink_meshes:
        obj.shape_key_add(name="Basis")
        blink = obj.shape_key_add(name="Blink")
        for vertex in blink.data:
            vertex.co.z *= .16
    mouth_obj.shape_key_add(name="Basis")
    open_key = mouth_obj.shape_key_add(name="Open")
    phoneme_a = mouth_obj.shape_key_add(name="Phoneme_A")
    phoneme_o = mouth_obj.shape_key_add(name="Phoneme_O")
    for vertex in open_key.data:
        vertex.co.z *= 2.2
    for vertex in phoneme_a.data:
        vertex.co.z *= 3.0
    for vertex in phoneme_o.data:
        vertex.co.z *= 2.1
        vertex.co.x *= .72

    arm = rig(parts)
    arm["cartoon_studio_rig_profile"] = "humanoid_stylized_v2"
    arm["facial_controls"] = ["Smile", "JawOpen", "Blink", "Open", "Phoneme_A", "Phoneme_O"]
    return {
        "rig": arm.name,
        "mesh_count": len(parts),
        "shape_keys": ["Smile", "JawOpen", "Blink", "Open", "Phoneme_A", "Phoneme_O"],
        "character_profile": "tailored_storybook_humanoid_v2",
    }

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
    if a.asset_kind=="character":
        camera_location=(3.7,-8.5,3.0); target=(0,0,1.48)
    elif a.asset_kind=="prop":
        camera_location=(3.2,-5.2,2.5); target=(0,0,.72)
    else:
        camera_location=(10.5,-17.5,9.0); target=(0,0,1.45)
    bpy.ops.object.camera_add(location=camera_location)
    camera=bpy.context.object; camera.rotation_euler=(Vector(target)-camera.location).to_track_quat("-Z","Y").to_euler()
    camera.data.lens=55
    scene.camera=camera; scene.render.engine="BLENDER_EEVEE_NEXT"
    scene.render.resolution_x=1200; scene.render.resolution_y=1200
    scene["cartoon_studio_asset_kind"]=a.asset_kind; scene["cartoon_studio_asset_id"]=a.asset_id
    blend=out/(a.asset_id+".blend"); glb=out/(a.asset_id+".glb")
    bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    bpy.ops.export_scene.gltf(filepath=str(glb),export_format="GLB",export_animations=True,
      export_skins=True,export_morph=True,export_materials="EXPORT",export_cameras=False,export_lights=False)
    # Produce a review image alongside the editable source and runtime GLB.
    # Workbench keeps this headless preview deterministic and does not require a GPU.
    preview=out/(a.asset_id+"_preview.png")
    scene.render.engine="BLENDER_WORKBENCH"
    scene.display.shading.light="STUDIO"
    scene.display.shading.studio_light="paint.sl"
    scene.display.shading.color_type="MATERIAL"
    scene.display.shading.show_cavity=True
    scene.display.shading.cavity_type="WORLD"
    scene.render.resolution_x=900; scene.render.resolution_y=900
    scene.render.resolution_percentage=100
    scene.render.image_settings.file_format="PNG"
    scene.render.filepath=str(preview)
    bpy.ops.render.render(write_still=True)
    scene.render.engine="BLENDER_EEVEE_NEXT"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    manifest={"schema_version":1,"asset_id":a.asset_id,"asset_kind":a.asset_kind,"name":a.name,
      "generator":"cartoon-studio-blender-factory","generator_version":"0.2.0",
      "blender_version":bpy.app.version_string,"source_file":blend.name,"glb_file":glb.name,
      "preview_file":preview.name,"editable_source":True,
      "license":"Original procedural asset; no third-party geometry included.",
      "details":details}
    (out/"manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
    print("CARTOON_STUDIO_ASSET_COMPLETE "+json.dumps(manifest))
if __name__=="__main__": main()
