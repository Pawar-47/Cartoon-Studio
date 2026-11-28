# ruff: noqa
import argparse, json, math, sys
from pathlib import Path
import bpy
from mathutils import Vector

def args():
    values=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    p=argparse.ArgumentParser()
    p.add_argument("--asset-kind",choices=("character","world","prop","building","vehicle","vegetation"),required=True)
    p.add_argument("--asset-id",required=True); p.add_argument("--name",required=True)
    p.add_argument("--output-dir",type=Path,required=True)
    p.add_argument("--culture-profile",choices=("pakistani_storybook_v1",),default="pakistani_storybook_v1")
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
    kurta = mat("Clothing | peacock teal", (.018, .27, .31))
    kurta_dark = mat("Clothing | deep teal seams", (.012, .12, .16))
    gold = mat("Clothing | brass piping", (.91, .55, .16))
    shirt = mat("Clothing | warm ivory", (.91, .78, .55))
    shalwar = mat("Clothing | indigo", (.075, .12, .28))
    shalwar_seam = mat("Clothing | seam blue", (.16, .23, .42))
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
        "Body | tailored kurta shell", (0, 0, 1.47),
        [(-.59, .27, .20, 0), (-.54, .32, .23, 0),
         (-.39, .35, .25, 0), (-.18, .39, .28, 0),
         (.08, .44, .29, 0), (.30, .46, .28, 0),
         (.46, .39, .24, 0), (.55, .25, .18, 0)],
        kurta, 56,
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

    # Pakistani kurta details: band collar, button placket, side slits and restrained piping.
    add(block("Kurta | front placket", (0, -.292, 1.52),
              (.13, .04, .58), shirt, .025), "chest")
    add(curve("Kurta | band collar",
              [(-.17, -.29, 1.94), (-.10, -.34, 2.00),
               (0, -.35, 1.97), (.10, -.34, 2.00),
               (.17, -.29, 1.94)], .028, gold), "chest")
    for sign, side in ((-1, "L"), (1, "R")):
        add(curve("Kurta | front seam." + side,
                  [(sign * .18, -.30, 1.78), (sign * .17, -.31, 1.48),
                   (sign * .14, -.28, 1.12)], .012, gold), "spine")
        add(block("Kurta | chest pocket." + side,
                  (sign * .245, -.286, 1.65), (.16, .035, .18), kurta, .018), "chest")
        add(curve("Kurta | side slit." + side,
                  [(sign * .31, -.16, 1.06), (sign * .32, -.18, .88),
                   (sign * .28, -.17, .78)], .012, shirt), "spine")
        add(block("Kurta | cuff piping." + side,
                  (sign * .515, -.015, 1.27), (.24, .20, .045), gold, .018), "forearm." + side)
    for z in (1.72, 1.58, 1.44, 1.30):
        add(ball("Kurta | brass button", (0, -.326, z),
                 (.022, .012, .022), gold, 20), "chest")
    add(curve("Shalwar | drawstring",
              [(-.12, -.22, .99), (0, -.27, .94), (.12, -.22, .99)], .018, gold), "pelvis")

    for sign, side in ((-1, "L"), (1, "R")):
        lapel = add(block("Kurta | lapel." + side,
                          (sign * .135, -.302, 1.80),
                          (.115, .045, .25), gold, .025), "chest")
        lapel.rotation_euler[1] = sign * .24
        add(curve("Kurta | front piping." + side,
                  [(sign * .17, -.30, 1.70),
                   (sign * .16, -.31, 1.43),
                   (sign * .13, -.29, 1.20)], .012, gold), "spine")
        add(block("Kurta | pocket." + side,
                  (sign * .235, -.285, 1.37), (.105, .035, .12),
                  kurta_dark, .018), "spine")
    for z in (1.60, 1.47, 1.34):
        add(ball("Kurta | brass button", (0, -.326, z),
                 (.022, .012, .022), gold, 20), "spine")
    add(curve("Kurta | collar",
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
            kurta, 40,
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
            "Shalwar | thigh." + side, (sign * .19, 0, .64),
            [(-.42, .105, .13, 0), (-.32, .14, .16, 0),
             (-.08, .16, .17, 0), (.20, .17, .18, 0),
             (.38, .145, .16, 0), (.43, .11, .13, 0)],
            shalwar, 40,
        ), "thigh." + side)
        add(curve("Shalwar | seam." + side,
                  [(sign * .19, -.17, .93), (sign * .19, -.17, .66),
                   (sign * .19, -.13, .40)], .008, shalwar_seam), "thigh." + side)
        add(loft(
            "Shalwar | shin." + side, (sign * .19, 0, .245),
            [(-.22, .09, .11, 0), (-.16, .11, .12, 0),
             (.04, .12, .13, 0), (.20, .13, .14, 0),
             (.25, .12, .13, 0)],
            shalwar, 36,
        ), "shin." + side)
        add(block("Peshawari Chappal | sole." + side,
                  (sign * .19, -.12, .035), (.30, .42, .055), sole, .025), "shin." + side)
        add(curve("Peshawari Chappal | toe strap." + side,
                  [(sign * .08, -.30, .12), (sign * .19, -.19, .18),
                   (sign * .30, -.30, .12)], .035, leather), "shin." + side)
        add(curve("Peshawari Chappal | instep strap." + side,
                  [(sign * .07, -.12, .16), (sign * .19, -.02, .20),
                   (sign * .31, -.12, .16)], .032, leather), "shin." + side)


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
        "character_profile": "pakistani_storybook_shalwar_kameez_v1",
        "culture_profile": "pakistani_storybook_v1",
        "outfit": "kurta_shalwar_with_peshawari_chappal",
    }


def arch_curve(name, center_x, front_y, base_z, width, rise, material, radius=.035):
    points = [
        (center_x - width / 2, front_y, base_z),
        (center_x - width * .43, front_y, base_z + rise * .72),
        (center_x, front_y, base_z + rise),
        (center_x + width * .43, front_y, base_z + rise * .72),
        (center_x + width / 2, front_y, base_z),
    ]
    return curve(name, points, radius, material)


def pakistani_shopfront(prefix, x, y, plaster, trim, accent, wood, glass, dark):
    width = 3.55
    front = y - .88
    block(prefix + " | stone plinth", (x, y, .18), (3.82, 1.98, .36), dark, .07)
    block(prefix + " | plaster facade", (x, y, 1.98), (3.55, 1.72, 3.62), plaster, .09)
    block(prefix + " | roof cornice", (x, front, 3.72), (3.78, .24, .16), trim, .035)
    block(prefix + " | parapet", (x, y, 3.92), (3.68, 1.82, .34), accent, .06)
    block(prefix + " | parapet coping", (x, front, 4.12), (3.82, .18, .10), trim, .025)

    # Recessed central doorway with a traditional pointed-arch surround.
    block(prefix + " | doorway recess", (x, front - .035, 1.13), (.98, .10, 2.08), dark, .035)
    block(prefix + " | carved timber door", (x, front - .105, 1.08), (.78, .075, 1.82), wood, .025)
    arch_curve(prefix + " | entrance arch", x, front - .12, 2.02, 1.02, .55, trim, .045)
    for z in (.68, 1.12, 1.56):
        block(prefix + " | door inset", (x, front - .15, z), (.53, .025, .035), accent, .008)
    ball(prefix + " | brass door pull", (x + .25, front - .18, 1.08), (.035, .025, .07), trim, 20)

    # Paired arched windows, lattice screens, and projecting chajjas.
    for side in (-1, 1):
        wx = x + side * 1.12
        block(prefix + " | window recess", (wx, front - .035, 2.02), (.82, .10, 1.22), dark, .035)
        block(prefix + " | window glass", (wx, front - .10, 2.02), (.66, .045, 1.02), glass, .02)
        arch_curve(prefix + " | window arch", wx, front - .14, 2.53, .84, .43, trim, .03)
        for offset in (-.20, 0, .20):
            block(prefix + " | jali vertical", (wx + offset, front - .16, 2.00), (.025, .035, .92), accent, .008)
        for z in (1.72, 1.96, 2.20):
            block(prefix + " | jali horizontal", (wx, front - .16, z), (.62, .035, .025), accent, .008)
        block(prefix + " | chajja", (wx, front - .25, 2.72), (1.18, .48, .12), trim, .025)
        for dx in (-.43, .43):
            block(prefix + " | chajja corbel", (wx + dx, front - .16, 2.56), (.10, .24, .22), accent, .025)

    # Painted tile frieze and small balcony rail above the entrance.
    for index in range(9):
        tx = x - 1.52 + index * .38
        tile = block(prefix + " | truck-art tile", (tx, front - .055, 3.18), (.30, .055, .24), accent if index % 2 else trim, .025)
        ball(prefix + " | tile rosette", (tx, front - .095, 3.18), (.055, .025, .055), wood if index % 2 else accent, 16)
    block(prefix + " | balcony slab", (x, front - .20, 2.96), (1.55, .52, .13), trim, .025)
    for bx in (-.66, -.33, 0, .33, .66):
        block(prefix + " | balcony baluster", (x + bx, front - .39, 3.17), (.045, .06, .34), accent, .012)
    block(prefix + " | balcony handrail", (x, front - .39, 3.36), (1.58, .09, .08), wood, .025)
    return {"width": width, "height": 4.2, "front_y": front}


def world():
    grass = mat("Bazaar | warm courtyard stone", (.54, .48, .36))
    asphalt = mat("Bazaar | charcoal road", (.12, .14, .16))
    paving = mat("Bazaar | sandstone paving", (.72, .62, .46))
    cream = mat("Bazaar | limewash", (.90, .78, .59))
    terracotta = mat("Bazaar | terracotta", (.52, .16, .09))
    teal = mat("Bazaar | painted teal", (.025, .31, .32))
    wood = mat("Bazaar | carved timber", (.22, .075, .035))
    glass = mat("Bazaar | blue glass", (.08, .28, .36), .2)
    dark = mat("Bazaar | recess", (.045, .055, .06))
    block("Bazaar | ground", (0, 0, -.24), (17, 16, .48), grass, .12)
    block("Bazaar | road", (0, -3.4, .02), (17, 3.2, .10), asphalt, .08)
    block("Bazaar | near sidewalk", (0, -1.25, .10), (17, 1.05, .20), paving, .035)
    block("Bazaar | far sidewalk", (0, -5.45, .10), (17, .78, .20), paving, .035)
    for x in range(-7, 8, 2):
        block("Bazaar | road marking", (x, -3.4, .085), (.78, .055, .012), cream, .008)

    shopfronts = []
    for index, x in enumerate((-4.35, 0, 4.35)):
        shopfronts.append(pakistani_shopfront(
            "Lahore Bazaar Shop %d" % (index + 1), x, 1.85,
            cream if index != 1 else mat("Bazaar | saffron plaster", (.79, .48, .25)),
            paving, teal if index != 1 else terracotta, wood, glass, dark,
        ))

    # Streetlights, overhead utility wires, and a small roadside tea stall.
    for x in (-7.0, 7.0):
        block("Bazaar | streetlight pole", (x, -1.15, 2.1), (.10, .10, 4.2), dark, .025)
        curve("Bazaar | lamp arm", [(x, -1.15, 3.85), (x, -1.15, 4.05), (x + (.45 if x < 0 else -.45), -1.15, 4.05)], .035, wood)
        ball("Bazaar | lamp shade", (x + (.43 if x < 0 else -.43), -1.15, 4.0), (.18, .18, .09), cream, 20)
    curve("Bazaar | overhead cable", [(-8, 1.0, 5.0), (0, 1.4, 5.35), (8, 1.0, 5.0)], .018, dark)
    curve("Bazaar | second overhead cable", [(-8, 1.35, 4.72), (0, 1.6, 4.95), (8, 1.35, 4.72)], .014, dark)
    block("Chai stall | counter", (-6.0, -.15, .72), (1.55, .75, 1.25), wood, .06)
    block("Chai stall | striped canopy", (-6.0, -.10, 1.55), (1.95, 1.05, .12), terracotta, .04)
    for x in (-6.68, -6.34, -6.0, -5.66, -5.32):
        block("Chai stall | canopy stripe", (x, -.10, 1.62), (.12, 1.04, .025), cream, .01)
    ball("Chai stall | brass kettle", (-6.0, -.22, 1.08), (.20, .20, .24), mat("Bazaar | brass", (.72, .43, .14), .3, .55), 24)

    # A small neem-like shade tree at the lane end.
    bark = mat("Bazaar tree | bark", (.24, .09, .035))
    leaves = mat("Bazaar tree | neem foliage", (.12, .34, .13))
    bpy.ops.mesh.primitive_cone_add(vertices=20, radius1=.22, radius2=.12, depth=2.5, location=(7.2, 3.9, 1.25))
    smooth(bpy.context.object, bark, .035)
    for loc, scale in (((7.2, 3.9, 2.75), (1.0, .85, .9)), ((6.55, 3.8, 2.55), (.62, .58, .62)), ((7.85, 4.0, 2.58), (.66, .62, .65))):
        ball("Bazaar tree | foliage", loc, scale, leaves, 32)
    return {
        "layout": "lahore_walled_city_bazaar_lane_v1",
        "culture_profile": "pakistani_storybook_v1",
        "features": ["arched_haveli_shopfronts", "jali_screens", "painted_tile_friezes", "chai_stall", "overhead_wires", "streetlights", "sandstone_sidewalks"],
        "shopfront_count": len(shopfronts),
    }


def prop():
    timber = mat("Charpai | sheesham timber", (.30, .12, .055))
    rope = mat("Charpai | natural woven cord", (.72, .57, .34))
    indigo = mat("Charpai | indigo weave", (.10, .20, .29))
    rust = mat("Charpai | rust weave", (.56, .18, .10))
    brass = mat("Chai set | brass", (.72, .43, .14), .32, .55)
    # Traditional woven charpai with a rigid timber frame and crossed rope webbing.
    for x in (-.78, .78):
        for y in (-.52, .52):
            block("Charpai | turned leg", (x, y, .30), (.13, .13, .60), timber, .035)
    block("Charpai | long side rail L", (-.78, 0, .58), (.16, 1.30, .16), timber, .035)
    block("Charpai | long side rail R", (.78, 0, .58), (.16, 1.30, .16), timber, .035)
    block("Charpai | head rail", (0, -.52, .58), (1.55, .16, .16), timber, .035)
    block("Charpai | foot rail", (0, .52, .58), (1.55, .16, .16), timber, .035)
    for index in range(17):
        x = -.68 + index * .085
        curve("Charpai | warp cord %02d" % index, [(x, -.47, .68), (x, 0, .69), (x, .47, .68)], .018, rope if index % 2 else indigo)
    for index in range(13):
        y = -.45 + index * .075
        curve("Charpai | weft cord %02d" % index, [(-.70, y, .70), (0, y, .72), (.70, y, .70)], .019, rust if index % 3 == 0 else rope)
    # Everyday brass tea service makes the object set recognisably local.
    ball("Chai set | kettle body", (0, -.10, .91), (.20, .18, .20), brass, 28)
    ball("Chai set | kettle lid", (0, -.10, 1.12), (.09, .09, .035), brass, 20)
    curve("Chai set | spout", [(-.15, -.10, .98), (-.28, -.10, 1.08), (-.34, -.10, 1.12)], .035, brass)
    ball("Chai set | cup one", (.38, -.12, .80), (.075, .075, .085), cream if False else rope, 20)
    return {
        "prop_family": "pakistani_charpai_and_chai_set_v1",
        "features": ["four_leg_sheesham_frame", "woven_cotton_rope_bed", "brass_kettle", "tea_cup"],
    }


def building():
    plaster = mat("Haveli | warm limewash", (.82, .63, .42))
    trim = mat("Haveli | pale sandstone", (.94, .82, .62))
    accent = mat("Haveli | indigo enamel", (.035, .22, .28))
    wood = mat("Haveli | carved sheesham", (.20, .065, .03))
    glass = mat("Haveli | blue glass", (.08, .30, .39), .2)
    dark = mat("Haveli | deep recess", (.045, .055, .06))
    details = pakistani_shopfront("Standalone Lahore Haveli", 0, 0, plaster, trim, accent, wood, glass, dark)
    return {
        "building_family": "lahore_haveli_shopfront_v1",
        "culture_profile": "pakistani_storybook_v1",
        "features": ["flat_roof_parapet", "pointed_arch_doorway", "jali_windows", "chajja", "projecting_balcony", "painted_tile_frieze"],
        "dimensions": details,
    }


def vehicle():
    body = mat("Rickshaw | deep bottle green", (.025, .25, .16), .34, .08)
    canopy = mat("Rickshaw | warm ivory canopy", (.91, .78, .55), .48)
    accent = mat("Rickshaw | truck-art vermilion", (.78, .12, .045), .35)
    blue = mat("Rickshaw | cobalt enamel", (.035, .16, .42), .32)
    glass = mat("Rickshaw | blue windscreen", (.055, .22, .31), .16)
    rubber = mat("Rickshaw | tyre rubber", (.018, .022, .025), .9)
    chrome = mat("Rickshaw | polished metal", (.66, .62, .52), .28, .7)
    lamp = mat("Rickshaw | headlamp", (1.0, .75, .34), .2)
    # Three-wheel auto-rickshaw: open passenger bay, driver's windscreen and canopy.
    block("Rickshaw | lower chassis", (0, .05, .66), (1.48, 2.18, .34), body, .16)
    block("Rickshaw | front nose", (0, -.91, .91), (1.15, .58, .63), blue, .17)
    block("Rickshaw | windscreen", (0, -1.205, 1.42), (.92, .055, .62), glass, .08)
    block("Rickshaw | canopy roof", (0, .05, 2.10), (1.62, 2.0, .16), canopy, .12)
    for x in (-.70, .70):
        block("Rickshaw | canopy support", (x, .12, 1.58), (.07, .08, 1.08), chrome, .025)
        block("Rickshaw | passenger side panel", (x, .42, .96), (.10, 1.15, .72), body, .06)
        block("Rickshaw | painted side stripe", (x * 1.075, .43, 1.10), (.025, .94, .10), accent, .02)
        block("Rickshaw | passenger step", (x * 1.05, .32, .48), (.22, .72, .09), chrome, .025)
    block("Rickshaw | rear bench", (0, .55, 1.12), (1.12, .42, .18), wood, .05)
    block("Rickshaw | backrest", (0, .83, 1.40), (1.12, .12, .52), accent, .05)
    for x in (-.36, .36):
        ball("Rickshaw | headlamp", (x, -1.22, .98), (.13, .06, .13), lamp, 24)
        ball("Rickshaw | rear lamp", (x, 1.10, .84), (.09, .06, .12), accent, 20)
    # Rear wheels and a single steerable front wheel.
    for x in (-.78, .78):
        bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=.38, depth=.20, location=(x, .60, .39), rotation=(0, math.pi / 2, 0))
        smooth(bpy.context.object, rubber, .035)
        bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=.20, depth=.215, location=(x * 1.02, .60, .39), rotation=(0, math.pi / 2, 0))
        smooth(bpy.context.object, chrome, .02)
    bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=.34, depth=.18, location=(0, -1.03, .37), rotation=(0, math.pi / 2, 0))
    smooth(bpy.context.object, rubber, .03)
    bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=.17, depth=.195, location=(0, -1.03, .37), rotation=(0, math.pi / 2, 0))
    smooth(bpy.context.object, chrome, .018)
    curve("Rickshaw | front fork", [(0, -1.02, .40), (0, -.95, .75), (0, -.85, .94)], .055, chrome)
    # Hand-painted truck-art style floral medallions, kept as original motifs.
    for x in (-.48, .48):
        ball("Rickshaw | floral medallion", (x, -1.22, .72), (.09, .035, .09), accent, 20)
    block("Rickshaw | front bumper", (0, -1.28, .48), (1.12, .12, .10), chrome, .035)
    return {
        "vehicle_family": "pakistani_auto_rickshaw_v1",
        "culture_profile": "pakistani_storybook_v1",
        "features": ["three_wheels", "open_passenger_bay", "canopy", "windscreen", "painted_side_panels", "front_fork", "passenger_bench"],
    }


def vegetation():
    bark = mat("Mango tree | sheesham-brown bark", (.24, .085, .028))
    leaf_dark = mat("Mango tree | deep leaf green", (.055, .23, .075))
    leaf_mid = mat("Mango tree | fresh foliage", (.16, .39, .11))
    leaf_light = mat("Mango tree | sunlit foliage", (.34, .52, .14))
    mango = mat("Mango tree | ripe mango", (.95, .49, .06), .42)
    bpy.ops.mesh.primitive_cone_add(vertices=24, radius1=.34, radius2=.19, depth=3.15, location=(0, 0, 1.58))
    smooth(bpy.context.object, bark, .05)
    for sign in (-1, 1):
        curve("Mango tree | main branch", [(0, 0, 1.72), (sign * .45, 0, 2.25), (sign * .82, .02, 2.78)], .105, bark)
        curve("Mango tree | outer branch", [(sign * .45, 0, 2.25), (sign * .78, -.05, 2.62), (sign * 1.08, -.08, 2.86)], .065, bark)
    for name, loc, scale, material in (
        ("core", (0, 0, 3.05), (1.18, .96, .95), leaf_dark),
        ("left", (-.72, -.02, 3.18), (.78, .72, .72), leaf_mid),
        ("right", (.74, .03, 3.18), (.82, .76, .78), leaf_mid),
        ("front", (0, -.56, 3.12), (.72, .55, .70), leaf_light),
        ("top", (0, .02, 3.72), (.82, .72, .72), leaf_light),
    ):
        ball("Mango tree | crown " + name, loc, scale, material, 36)
    for index, (x, y, z) in enumerate(((-.58, -.58, 3.0), (.52, -.55, 3.08), (.82, .16, 3.34), (-.18, .34, 3.68))):
        ball("Mango tree | fruit %02d" % index, (x, y, z), (.10, .13, .20), mango, 20)
    for sign in (-1, 1):
        curve("Mango tree | surface root", [(0, 0, .18), (sign * .38, -.08, .08), (sign * .70, -.12, .035)], .075, bark)
    return {
        "vegetation_family": "pakistani_mango_tree_v1",
        "culture_profile": "pakistani_storybook_v1",
        "species": "Mangifera indica",
        "features": ["branching_trunk", "layered_leaf_canopy", "visible_mango_fruit", "surface_roots"],
    }



def main():
    a=args(); out=a.output_dir.resolve(); out.mkdir(parents=True,exist_ok=True)
    bpy.ops.object.select_all(action="SELECT"); bpy.ops.object.delete(use_global=False)
    builders = {"character": character, "world": world, "prop": prop, "building": building, "vehicle": vehicle, "vegetation": vegetation}
    details = builders[a.asset_kind]()
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
    scene["cartoon_studio_culture_profile"]=a.culture_profile
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
      "generator":"cartoon-studio-blender-factory","generator_version":"0.3.0","culture_profile":a.culture_profile,
      "blender_version":bpy.app.version_string,"source_file":blend.name,"glb_file":glb.name,
      "preview_file":preview.name,"editable_source":True,"culture_profile":a.culture_profile,
      "license":"Original procedural asset; no third-party geometry included.",
      "details":details}
    (out/"manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
    print("CARTOON_STUDIO_ASSET_COMPLETE "+json.dumps(manifest))
if __name__=="__main__": main()
