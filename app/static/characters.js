import { showCharacterPreview, showRetargetPreview, getCharacterMaterials, applyCharacterAppearance, getCharacterMorphTargets, applyCharacterMorphTargets } from "./character-preview.js";
const $=id=>document.getElementById(id);
let activeProject="", importedAsset=null, activeCharacter=null, editingCharacter=null, appearanceRecipe={materials:{},morph_targets:{}}, retargetCharacters=[], assemblyAssets=[], assemblyAccessories=[];
const params=new URLSearchParams(window.location.search);
function lines(value){return value.split(/\r?\n/).map(x=>x.trim()).filter(Boolean)}
function resetProfileEditor(){editingCharacter=null;$("character-form").reset();$("profile-heading").textContent="Save reusable profile";$("save-character").textContent="Save character profile";$("cancel-edit-profile").hidden=true;$("save-character").disabled=!importedAsset}
function cancelProfileEdit(){resetProfileEditor();$("profile-status").textContent="Profile editing cancelled. The saved character was not changed."}
function editCharacterProfile(document){
 const data=document.data||{};editingCharacter=document;importedAsset=null;
 $("character-name").value=data.name||"";$("character-description").value=data.description||"";
 $("face-design").value=data.face_design||"";$("body-proportions").value=JSON.stringify(data.body_proportions||{},null,2);
 $("height-cm").value=data.height_cm??"";$("hair").value=data.hair||"";
 $("clothing").value=(data.clothing||[]).join("\n");$("accessories").value=(data.accessories||[]).join("\n");
 $("eye-design").value=data.eye_design||"";$("mouth-design").value=data.mouth_design||"";
 $("expressions").value=(data.expressions||[]).join("\n");$("personality").value=data.personality||"";
 $("relationships").value=(data.relationships||[]).join("\n");$("voice-profile").value=data.voice_profile||"";
 $("dialogue-style").value=data.dialogue_style||"";
 $("profile-heading").textContent="Edit character profile";$("save-character").textContent="Save profile changes";
 $("save-character").disabled=false;$("cancel-edit-profile").hidden=false;
 $("profile-status").textContent="Editing "+(data.name||"character")+". The original GLB and saved appearance recipe will be preserved.";
 $("profile-panel").scrollIntoView({behavior:"smooth",block:"start"});
}
async function loadProjects(){
 const response=await fetch("/api/projects");
 if(!response.ok)throw new Error("Could not load projects.");
 const projects=await response.json(),select=$("project-select");
 select.replaceChildren();
 const empty=document.createElement("option");empty.value="";empty.textContent="Choose a project…";select.append(empty);
 for(const project of projects){const option=document.createElement("option");option.value=project.id;option.textContent=project.name;select.append(option)}
 if(params.get("project")&&projects.some(p=>p.id===params.get("project")))select.value=params.get("project");
 if(!select.value&&projects.length===1)select.value=projects[0].id;
 await selectProject(select.value);
}
async function selectProject(id){
 activeProject=id;assemblyAssets=[];assemblyAccessories=[];renderAssemblyAccessories();refreshAssemblyControls();$("library-import").disabled=!id||!selectedLibraryModel();importedAsset=null;activeCharacter=null;resetProfileEditor();appearanceRecipe={materials:{},morph_targets:{}};$("material-editor").hidden=true;$("morph-editor").hidden=true;$("save-appearance").disabled=true;$("asset-report").hidden=true;$("profile-status").textContent="";$("save-character").disabled=true;$("refresh-characters").disabled=!id;
 $("project-status").textContent=id?"Project selected. Import a GLB model to begin.":"Choose a project to begin.";
 $("character-list").replaceChildren();
 if(!id){$("character-list").innerHTML='<div class="empty">Select a project to see its characters.</div>';return}
 await loadCharacters();
}
function documentElementOption(characterDoc){
 const option=window.document.createElement("option");
 option.value=characterDoc.id;option.textContent=characterDoc.data.name||"Unnamed character";return option;
}
function updateRetargetButtonState(){
 const source=$("retarget-source").value,target=$("retarget-target").value;
 $("create-retarget").disabled=!source||!target||source===target;
}
function updateRetargetAnimationOptions(){
 const select=$("retarget-animation"),sourceId=$("retarget-source").value;
 const selected=retargetCharacters.find(item=>item.id===sourceId);
 const inspection=selected?.data?.asset?.engine_inspection||{};
 const names=Array.isArray(inspection.animation_names)?inspection.animation_names:[];
 const previous=select.value;
 select.replaceChildren();
 const first=document.createElement("option");first.value="";
 first.textContent=names.length?"Use first imported animation…":"No clip list available · use first imported animation";
 select.append(first);
 for(const name of names){
  const option=document.createElement("option");option.value=name;option.textContent=name;select.append(option);
 }
 if(names.includes(previous))select.value=previous;
 select.disabled=!names.length;
}
function updateRetargetCharacterOptions(characters){
 retargetCharacters=characters;
 const source=$("retarget-source"),target=$("retarget-target");
 const previousSource=source.value,previousTarget=target.value;
 source.replaceChildren();target.replaceChildren();
 for(const [select,label] of [[source,"Select animated source…"],[target,"Select target rig…"]]){
  const option=document.createElement("option");option.value="";option.textContent=label;select.append(option);
 }
 for(const characterDoc of characters){
  const data=characterDoc.data||{},asset=data.asset||{},inspection=asset.engine_inspection||{},container=asset.container||{},rig=asset.rig_analysis||{},hierarchy=rig.hierarchy_validation||{};
  const sourceHierarchyAllowed=["valid","valid_with_ik_foot_hierarchy"].includes(hierarchy.status);
  const sourceCompatible=rig.status==="humanoid_names_complete"&&sourceHierarchyAllowed&&Number(inspection.skeleton_count||0)===1;
  const targetCompatible=rig.status==="humanoid_names_complete"&&hierarchy.status==="valid"&&Number(inspection.skeleton_count||0)===1;
  const clipNames=inspection.animation_names;
  const hasPlayableClips=Array.isArray(clipNames)?clipNames.length>0:Number(inspection.animation_count||0)>0;
  const skinCount=Number(container.skin_count??inspection.skin_count??0);
  if(sourceCompatible&&hasPlayableClips){
   const option=documentElementOption(characterDoc);
   if(hierarchy.status==="valid_with_ik_foot_hierarchy")option.textContent+=" · IK-foot rig";
   source.append(option);
  }
  if(targetCompatible&&skinCount>0)target.append(documentElementOption(characterDoc));
 }
 if([...source.options].some(option=>option.value===previousSource))source.value=previousSource;
 if([...target.options].some(option=>option.value===previousTarget))target.value=previousTarget;
 updateRetargetAnimationOptions();
 updateRetargetButtonState();
}
async function loadRetargets(){
 if(!activeProject)return;
 const response=await fetch("/api/projects/"+encodeURIComponent(activeProject)+"/retargets");
 if(!response.ok)throw new Error("Could not load saved retarget scenes.");
 const documents=await response.json(),container=$("retarget-list");container.replaceChildren();
 for(const item of documents){
  const row=document.createElement("div");row.className="retarget-record";
  const title=document.createElement("strong");title.textContent=(item.data.source_character_name||"Source")+" → "+(item.data.target_character_name||"Target");
  const poseLabel=item.data.pose_transferred?"pose transfer verified":"pose transfer unverified";
  const angles=Number.isFinite(item.data.source_pose_angle_degrees)&&Number.isFinite(item.data.target_pose_angle_degrees)?" · local angles (source/target; rest-axis dependent): "+Number(item.data.source_pose_angle_degrees).toFixed(1)+"° / "+Number(item.data.target_pose_angle_degrees).toFixed(1)+"°":"";
  const detail=document.createElement("span");detail.textContent=(item.data.animation_name||"Imported animation")+" · "+item.data.mapped_bone_count+"/15 bones · "+(item.data.scene_reopened?"scene reopened":"scene saved")+" · "+poseLabel+angles;
  const previewButton=document.createElement("button");previewButton.type="button";previewButton.className="secondary preview-saved";previewButton.textContent="Preview retarget";
  previewButton.addEventListener("click",async()=>{
   previewButton.disabled=true;detail.textContent="Loading source and target models for browser preview…";
   try{
    const base="/api/projects/"+encodeURIComponent(activeProject)+"/retargets/"+encodeURIComponent(item.id);
    const infoResponse=await fetch(base+"/preview"),info=await infoResponse.json();
    if(!infoResponse.ok)throw new Error(info.detail||"Could not load retarget preview data.");
    const [sourceResponse,targetResponse]=await Promise.all([fetch(info.source_asset_url),fetch(info.target_asset_url)]);
    if(!sourceResponse.ok||!targetResponse.ok)throw new Error("A source or target GLB could not be loaded.");
    const [sourceBuffer,targetBuffer]=await Promise.all([sourceResponse.arrayBuffer(),targetResponse.arrayBuffer()]);
    const opened=await showRetargetPreview(sourceBuffer,targetBuffer,info.source_mapping,info.target_mapping,info.animation_name,title.textContent);
    if(!opened)throw new Error("The browser preview could not be created. See the preview status above.");
    document.querySelector(".preview-panel").scrollIntoView({behavior:"smooth",block:"center"});
    detail.textContent=(item.data.animation_name||"Imported animation")+" · browser preview (Three.js) · saved Godot scene remains authoritative.";
   }catch(error){detail.textContent=error.message}
   finally{previewButton.disabled=false}
  });
  const download=document.createElement("a");download.href="/api/projects/"+encodeURIComponent(activeProject)+"/retargets/"+encodeURIComponent(item.id)+"/scene";download.textContent="Download Godot scene";download.className="retarget-download";
  row.append(title,detail,previewButton,download);container.append(row);
 }
 if(!documents.length){const empty=document.createElement("p");empty.className="inline-status";empty.textContent="No retarget scenes saved in this project yet.";container.append(empty)}
}
function assemblyAssetId(relativePath){
 return (relativePath||"").split("/").pop().replace(/\\.glb$/i,"");
}
async function loadAssemblyAssetManifest(relativePath){
 const assetId=assemblyAssetId(relativePath);
 if(!assetId)throw new Error("An assembly source asset path is missing.");
 const existing=assemblyAssets.find(asset=>asset.asset_id===assetId);
 if(existing)return existing;
 const response=await fetch("/api/projects/"+encodeURIComponent(activeProject)+"/character-assets/"+encodeURIComponent(assetId)+"/manifest");
 if(!response.ok)throw new Error("Could not restore source asset "+assetId.slice(0,8)+".");
 const asset=await response.json();
 rememberAssemblyAsset(asset,asset.original_filename||"Saved source asset");
 return asset;
}
async function loadAssemblySources(recipe){
 const paths=[recipe.base_relative_path,...(recipe.parts||[]).map(part=>part.relative_path),...(recipe.accessories||[]).map(item=>item.relative_path)].filter(Boolean);
 return Promise.all([...new Set(paths)].map(loadAssemblyAssetManifest));
}
async function loadCharacters(){
 const response=await fetch("/api/projects/"+encodeURIComponent(activeProject)+"/characters");
 if(!response.ok)throw new Error("Could not load saved characters.");
 const characters=await response.json(),list=$("character-list");list.replaceChildren();updateRetargetCharacterOptions(characters);await loadRetargets();
 if(!characters.length){list.innerHTML='<div class="empty">No saved characters in this project yet.</div>';return}
 for(const document of characters){
  const data=document.data,card=document.createElement("article");card.className="character-card";
  const title=document.createElement("h3");title.textContent=data.name;
  const description=document.createElement("p");description.textContent=data.description||"No description";
  const model=document.createElement("p");const asset=data.asset||{};model.textContent=(asset.original_filename||"GLB model")+" · "+(asset.engine_inspection?.mesh_count??asset.container?.mesh_count??0)+" meshes";
  if(asset.assembly){
   const savedAssetId=assemblyAssetId(asset.relative_path);
   rememberAssemblyAsset({asset_id:savedAssetId,...asset},data.name);
   try{await loadAssemblySources(asset.assembly)}catch(error){$("assembly-status").textContent="Some saved assembly sources could not be restored: "+error.message}
  }
  const rigAnalysis=asset.rig_analysis||{};const rig=document.createElement("span");rig.className="tag"+(asset.rig_ready?"":" warning");
  rig.textContent=asset.rig_ready?"Skeleton detected":"No skeleton detected";
  if(rigAnalysis.required_bone_count)rig.textContent+=" · humanoid names "+rigAnalysis.matched_bone_count+"/"+rigAnalysis.required_bone_count;
  rig.title=rigAnalysis.retargeting_note||"Skeleton presence alone does not prove humanoid retarget compatibility";
  const animations=document.createElement("span");animations.className="tag";animations.textContent=(asset.engine_inspection?.animation_count??asset.container?.animation_count??0)+" animations";
  const revision=document.createElement("p");revision.textContent="Revision "+document.revision+" · "+new Date(document.updated_at).toLocaleDateString();
  const previewButton=document.createElement("button");previewButton.className="secondary preview-saved";previewButton.type="button";previewButton.textContent="Preview";
  previewButton.addEventListener("click",async()=>{try{const assetId=(asset.relative_path||"").split("/").pop().replace(/\.glb$/i,"");const response=await fetch("/api/projects/"+encodeURIComponent(activeProject)+"/character-assets/"+encodeURIComponent(assetId));if(!response.ok)throw new Error("Could not load the saved GLB asset.");const buffer=await response.arrayBuffer();await showCharacterPreview(buffer,data.name,data.appearance_recipe||{});document.querySelector(".preview-panel").scrollIntoView({behavior:"smooth",block:"center"})}catch(error){$("project-status").textContent=error.message}});
  const editButton=document.createElement("button");editButton.className="secondary preview-saved";editButton.type="button";editButton.textContent="Edit profile";
  editButton.addEventListener("click",()=>editCharacterProfile(document));
  const customizeButton=document.createElement("button");customizeButton.className="secondary preview-saved";customizeButton.type="button";customizeButton.textContent="Customize appearance";
  customizeButton.addEventListener("click",()=>openCharacterAppearance(document).catch(error=>$("project-status").textContent=error.message));
  if(asset.assembly){
   const reopenAssemblyButton=document.createElement("button");reopenAssemblyButton.className="secondary preview-saved";reopenAssemblyButton.type="button";reopenAssemblyButton.textContent="Reopen assembly";
   reopenAssemblyButton.addEventListener("click",async()=>{
    try{
     await loadAssemblySources(asset.assembly);
     $("assembly-base").value=assemblyAssetId(asset.assembly.base_relative_path);
     for(const part of asset.assembly.parts||[]){
      const select=$("assembly-"+part.slot),sourceId=assemblyAssetId(part.relative_path);
      select.value=sourceId+"|"+part.mesh_path;
     }
     assemblyAccessories=(asset.assembly.accessories||[]).map(item=>({
      relative_path:item.relative_path,mesh_path:item.mesh_path,attachment_bone:item.attachment_bone||"",
      label:(assemblyAssets.find(source=>source.relative_path===item.relative_path)?.assembly_label||"Saved source")+" / "+item.mesh_path.split("/").pop()
     }));
     renderAssemblyAccessories();
     refreshAssemblyControls();
     document.querySelector(".assembly-panel").scrollIntoView({behavior:"smooth",block:"start"});
     $("assembly-status").textContent="Saved assembly recipe restored. Adjust any part and assemble again to create a new asset.";
    }catch(error){$("assembly-status").textContent=error.message}
   });
   card.append(reopenAssemblyButton);
  }
  card.append(title,description,model,rig,animations,revision,previewButton,editButton,customizeButton);
  const savedAssetId=assemblyAssetId(asset.relative_path);
  if(savedAssetId){
   const downloadButton=document.createElement("a");downloadButton.className="secondary preview-saved";
   downloadButton.href="/api/projects/"+encodeURIComponent(activeProject)+"/character-assets/"+encodeURIComponent(savedAssetId);
   downloadButton.download=(data.name||"character")+".glb";downloadButton.textContent="Download GLB";
   card.append(downloadButton);
  }
  list.append(card);
 }
}
async function openCharacterAppearance(characterDoc){
 const data=characterDoc.data,asset=data.asset||{},assetId=(asset.relative_path||"").split("/").pop().replace(/\.glb$/i,"");
 if(!assetId)throw new Error("This character has no saved source model.");
 const response=await fetch("/api/projects/"+encodeURIComponent(activeProject)+"/character-assets/"+encodeURIComponent(assetId));
 if(!response.ok)throw new Error("Could not load the saved GLB asset.");
 const buffer=await response.arrayBuffer();
 activeCharacter=characterDoc;
 appearanceRecipe=JSON.parse(JSON.stringify(data.appearance_recipe||{materials:{},morph_targets:{}}));
 appearanceRecipe.materials=appearanceRecipe.materials||{};appearanceRecipe.morph_targets=appearanceRecipe.morph_targets||{};
 const loaded=await showCharacterPreview(buffer,data.name,appearanceRecipe,{playAnimations:false});
 if(!loaded)throw new Error("The browser could not preview this GLB. Check WebGL 2 and model compression.");
 const materials=getCharacterMaterials(),select=$("material-select");
 select.replaceChildren();
 for(const material of materials){
  const option=window.document.createElement("option");
  option.value=material.key;
  option.textContent=material.name+" · "+material.key.slice(-24);
  select.append(option);
 }
 $("material-editor").hidden=false;
 $("morph-editor").hidden=false;
 $("save-appearance").disabled=!materials.length&&!getCharacterMorphTargets().length;
 buildMorphControls();
 $("appearance-status").textContent=materials.length?materials.length+" editable material slot(s). Changes are a saved recipe; the source GLB is unchanged.":"No editable materials were found in this model.";
 if(materials.length)selectMaterial(materials[0].key);
 window.document.querySelector(".preview-panel").scrollIntoView({behavior:"smooth",block:"center"});
}
function selectMaterial(key){
 const material=getCharacterMaterials().find(item=>item.key===key);if(!material)return;
 const values=appearanceRecipe.materials[key]||material;
 $("material-color").value=values.color||material.color;
 $("material-roughness").value=String(values.roughness??material.roughness);
 $("material-metalness").value=String(values.metalness??material.metalness);
 $("roughness-value").value=Number($("material-roughness").value).toFixed(2);
 $("metalness-value").value=Number($("material-metalness").value).toFixed(2);
}
function previewSelectedMaterial(){
 const key=$("material-select").value;if(!key)return;
 const values={color:$("material-color").value,roughness:Number($("material-roughness").value),metalness:Number($("material-metalness").value)};
 appearanceRecipe.materials[key]=values;applyCharacterAppearance({[key]:values});
 $("roughness-value").value=values.roughness.toFixed(2);$("metalness-value").value=values.metalness.toFixed(2);
 $("appearance-status").textContent="Preview updated. Save to keep this appearance with the character.";
}
function buildMorphControls(){
 const targets=getCharacterMorphTargets(),container=$("morph-controls");
 container.replaceChildren();
 $("morph-status").textContent=targets.length?targets.length+" facial morph target(s) detected. Adjust them to preview expressions.":"This model has no facial morph targets. Import a model with blend shapes to use facial controls.";
 $("reset-expressions").disabled=!targets.length;
 for(const target of targets){
  const label=window.document.createElement("label");label.className="morph-control";
  const title=window.document.createElement("span");title.textContent=(target.meshName?target.meshName+" · ":"")+target.name;
  const value=appearanceRecipe.morph_targets[target.key]??target.value;
  const output=window.document.createElement("output");output.value=Number(value).toFixed(2);
  const input=window.document.createElement("input");input.type="range";input.min="-1";input.max="1";input.step="0.01";input.value=String(value);input.setAttribute("aria-label",(target.meshName?target.meshName+" ":"")+target.name+" morph weight");
  input.addEventListener("input",()=>{
   const weight=Number(input.value);appearanceRecipe.morph_targets[target.key]=weight;
   output.value=weight.toFixed(2);applyCharacterMorphTargets({[target.key]:weight});
   $("appearance-status").textContent="Facial preview updated. Save to keep these expression values.";
  });
  label.append(title,output,input);container.append(label);
 }
}
$("reset-expressions").addEventListener("click",()=>{
 for(const target of getCharacterMorphTargets())appearanceRecipe.morph_targets[target.key]=target.value;
 applyCharacterMorphTargets(appearanceRecipe.morph_targets);buildMorphControls();
 $("appearance-status").textContent="Facial controls restored to imported defaults. Save to keep these values.";
});
$("material-select").addEventListener("change",event=>selectMaterial(event.target.value));
for(const id of ["material-color","material-roughness","material-metalness"])$(id).addEventListener("input",previewSelectedMaterial);
$("save-appearance").addEventListener("click",async()=>{
 if(!activeCharacter||!activeProject)return;
 $("save-appearance").disabled=true;$("appearance-status").textContent="Saving appearance recipe…";
 try{
  const response=await fetch("/api/projects/"+encodeURIComponent(activeProject)+"/characters/"+encodeURIComponent(activeCharacter.id)+"/appearance",{method:"PUT",headers:{"Content-Type":"application/json"},body:JSON.stringify(appearanceRecipe)});
  const result=await response.json();if(!response.ok)throw new Error(result.detail||"Could not save appearance.");
  activeCharacter=result;$("appearance-status").textContent="Appearance saved · profile revision "+result.revision+".";
  await loadCharacters();
 }catch(error){$("appearance-status").textContent=error.message}
 finally{$("save-appearance").disabled=!(getCharacterMaterials().length||getCharacterMorphTargets().length)}
});
$("retarget-source").addEventListener("change",()=>{$("create-retarget").disabled=!$("retarget-source").value||!$("retarget-target").value||$("retarget-source").value===$("retarget-target").value});
$("retarget-target").addEventListener("change",()=>{$("create-retarget").disabled=!$("retarget-source").value||!$("retarget-target").value||$("retarget-source").value===$("retarget-target").value});
$("retarget-source").addEventListener("change",()=>{updateRetargetAnimationOptions();updateRetargetButtonState()});
$("retarget-target").addEventListener("change",updateRetargetButtonState);
$("create-retarget").addEventListener("click",async()=>{
 const sourceId=$("retarget-source").value,targetId=$("retarget-target").value;
 if(!activeProject||!sourceId||!targetId||sourceId===targetId)return;
 $("create-retarget").disabled=true;$("retarget-status").textContent="Validating both rigs and creating a Godot retarget scene…";
 try{
  const response=await fetch("/api/projects/"+encodeURIComponent(activeProject)+"/retargets",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({source_character_id:sourceId,target_character_id:targetId,animation_name:$("retarget-animation").value.trim()})});
  const result=await response.json();if(!response.ok)throw new Error(result.detail||"Retarget scene creation failed.");
  $("retarget-status").textContent="Retarget scene saved at "+result.data.scene_relative_path+". Both source GLBs were preserved.";
  await loadRetargets();
 }catch(error){$("retarget-status").textContent=error.message}
 finally{$("create-retarget").disabled=!$("retarget-source").value||!$("retarget-target").value||$("retarget-source").value===$("retarget-target").value}
});
$("project-select").addEventListener("change",event=>selectProject(event.target.value).catch(error=>$("project-status").textContent=error.message));
$("model-file").addEventListener("change",()=>{if(editingCharacter)cancelProfileEdit();$("import-model").disabled=!activeProject||!$("model-file").files.length;importedAsset=null;$("save-character").disabled=true;$("asset-report").hidden=true});
$("import-model").addEventListener("click",async()=>{
 const file=$("model-file").files[0];if(!file||!activeProject)return;
 $("import-model").disabled=true;$("import-status").textContent="Uploading and inspecting with Godot…";
 try{
  const response=await fetch("/api/projects/"+encodeURIComponent(activeProject)+"/character-assets",{method:"POST",headers:{"Content-Type":"application/octet-stream","X-Asset-Filename":file.name},body:file});
  const data=await response.json();if(!response.ok)throw new Error(data.detail||"Model import failed.");
  importedAsset=data;rememberAssemblyAsset(data,file.name);await showCharacterPreview(await file.arrayBuffer(),file.name);$("asset-report").hidden=false;$("asset-report").replaceChildren();
  const heading=document.createElement("strong");heading.textContent="Godot import successful · "+data.container.format;
  const metrics=document.createElement("div");metrics.className="asset-metrics";
  const rigAnalysis=data.rig_analysis||{};
  const coverage=rigAnalysis.required_bone_count?rigAnalysis.matched_bone_count+"/"+rigAnalysis.required_bone_count:"Unavailable";
  const missing=Array.isArray(rigAnalysis.missing_bones)?rigAnalysis.missing_bones.join(", "):"Not reported";
  const hierarchy=rigAnalysis.hierarchy_validation||{};
  const hierarchyLabel=hierarchy.status==="valid"?"Valid":hierarchy.status==="valid_with_ik_foot_hierarchy"?"Valid · IK-foot source":hierarchy.status==="invalid"?"Needs review":hierarchy.status==="incomplete"?"Incomplete":"Not available";
  const restPose=rigAnalysis.rest_pose_summary||{};
  const morphTargets=Array.isArray(data.engine_inspection.morph_targets)?data.engine_inspection.morph_targets:[];
  const morphNames=morphTargets.map(target=>target.name).filter(Boolean);
  const items=[["Meshes",data.engine_inspection.mesh_count],["Skeletons",data.engine_inspection.skeleton_count],["Animations",data.engine_inspection.animation_count],["Nodes",data.engine_inspection.node_count],["File size",(data.container.size_bytes/1048576).toFixed(2)+" MiB"],["Humanoid bone-name coverage",coverage],["Missing core humanoid names",missing],["Humanoid hierarchy",hierarchyLabel],["Rest-pose bone transforms",restPose.measured_bone_count??0],["Godot facial blend shapes",data.engine_inspection.morph_target_count??morphTargets.length]];
  for(const [label,value] of items){const span=document.createElement("span");const b=document.createElement("b");b.textContent=String(value);span.append(document.createTextNode(label+": "),b);metrics.append(span)}
  const rigNote=document.createElement("p");rigNote.className="inline-status";rigNote.textContent=rigAnalysis.retargeting_note||"Skeleton presence is not proof of retarget compatibility.";
  const hierarchyNote=document.createElement("p");hierarchyNote.className="inline-status";
  const hierarchyIssues=Array.isArray(hierarchy.issues)?hierarchy.issues:[];
  const restNote=restPose.measured_bone_count?(" Godot also reported local rest offsets for "+restPose.measured_bone_count+" mapped bones; these are not world-space limb lengths."):"";
  hierarchyNote.textContent=(hierarchy.status==="valid"?"Required humanoid parent chains are structurally consistent; rest pose, axes, scale, skin weights and real animation transfer remain unverified.":hierarchyIssues.length?hierarchyIssues.join(" "):(hierarchy.note||"Parent-chain validation is not available for this asset."))+restNote;
  const morphNote=document.createElement("p");morphNote.className="inline-status";morphNote.textContent=morphNames.length?"Godot imported facial blend shapes: "+morphNames.join(", ")+". Browser preview controls are checked separately.":"Godot did not detect facial blend shapes in this asset."; 
  const meshInventory=Array.isArray(data.engine_inspection.mesh_inventory)?data.engine_inspection.mesh_inventory:[];
  const slotCounts={head:0,body:0,legs:0,feet:0,unclassified:0};
  for(const mesh of meshInventory){const slot=mesh.slot_candidate||"unclassified";slotCounts[slot]=(slotCounts[slot]||0)+1}
  const inventory=document.createElement("details");inventory.className="mesh-inventory";
  const inventorySummary=document.createElement("summary");inventorySummary.textContent="Mesh inventory · "+meshInventory.length+" mesh nodes · candidate slots: "+["head","body","legs","feet"].map(slot=>slot+" "+slotCounts[slot]).join(" / ");
  const inventoryList=document.createElement("ul");
  for(const mesh of meshInventory){const item=document.createElement("li");const title=document.createElement("strong");title.textContent=mesh.node_name||mesh.node_path||"Mesh";const metadata=document.createElement("span");metadata.textContent=" · "+(mesh.slot_candidate||"unclassified")+" · "+(mesh.skin_bound?"skinned":"not skinned")+" · "+(mesh.skeleton_bone_count||0)+" skeleton bones · "+(mesh.surface_count||0)+" surfaces";item.append(title,metadata);inventoryList.append(item)}
  inventory.append(inventorySummary,inventoryList);
  const inventoryNote=document.createElement("p");inventoryNote.className="inline-status";inventoryNote.textContent="Slot labels are name-based candidates only; geometry, skin weights and shared-skeleton compatibility still require validation before parts can be combined.";
  $("asset-report").append(heading,metrics,rigNote,hierarchyNote,morphNote,inventory,inventoryNote);$("import-status").textContent="Asset stored inside this project. Complete the profile to save it."; $("save-character").disabled=false;
 }catch(error){$("import-status").textContent=error.message}
 finally{$("import-model").disabled=!activeProject||!$("model-file").files.length}
});
$("character-form").addEventListener("submit",async event=>{
 event.preventDefault();if((!importedAsset&&!editingCharacter)||!activeProject)return;
 $("save-character").disabled=true;$("profile-status").textContent="Saving character profile…";
 try{
  let proportions={};const raw=$("body-proportions").value.trim();if(raw){proportions=JSON.parse(raw);if(!proportions||Array.isArray(proportions)||typeof proportions!=="object")throw new Error("Body proportions must be a JSON object.")}
  const height=$("height-cm").value;
  const payload={name:$("character-name").value,description:$("character-description").value,face_design:$("face-design").value,body_proportions:proportions,height_cm:height?Number(height):null,hair:$("hair").value,clothing:lines($("clothing").value),accessories:lines($("accessories").value),eye_design:$("eye-design").value,mouth_design:$("mouth-design").value,expressions:lines($("expressions").value),personality:$("personality").value,relationships:lines($("relationships").value),voice_profile:$("voice-profile").value,dialogue_style:$("dialogue-style").value,asset_path:editingCharacter?editingCharacter.data.asset.relative_path:importedAsset.relative_path};
  const editing=Boolean(editingCharacter),url="/api/projects/"+encodeURIComponent(activeProject)+"/characters"+(editing?"/"+encodeURIComponent(editingCharacter.id):"");
  const response=await fetch(url,{method:editing?"PUT":"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(payload)});
  const data=await response.json();if(!response.ok)throw new Error(data.detail||"Could not save character.");
  $("profile-status").textContent=(editing?"Character profile updated.":"Character saved.")+" Revision "+data.revision+".";
  importedAsset=null;resetProfileEditor();$("model-file").value="";$("asset-report").hidden=true;$("import-status").textContent="Import another model to create another character.";$("save-character").disabled=true;
  await loadCharacters();
 }catch(error){$("profile-status").textContent=error.message;$("save-character").disabled=!importedAsset&&!editingCharacter}
});
$("cancel-edit-profile").addEventListener("click",cancelProfileEdit);
$("refresh-characters").addEventListener("click",()=>loadCharacters().catch(error=>$("project-status").textContent=error.message));

const assemblySlots=["head","body","legs","feet"];
function rememberAssemblyAsset(asset,label){
 if(!asset||!asset.asset_id||!asset.relative_path)return;
 const entry={...asset,assembly_label:label||asset.original_filename||"Character asset"};
 const existing=assemblyAssets.findIndex(item=>item.asset_id===asset.asset_id);
 if(existing>=0)assemblyAssets[existing]=entry;else assemblyAssets.push(entry);
 refreshAssemblyControls();
}
function assemblyEligibleAssets(){return assemblyAssets.filter(asset=>Number(asset.engine_inspection?.skeleton_count)===1)}
function renderAssemblyAccessories(){
 const list=$("assembly-accessory-list");list.replaceChildren();
 assemblyAccessories.forEach((item,index)=>{
  const row=document.createElement("div");row.className="accessory-chip";
  const label=document.createElement("span");label.textContent=item.label+(item.attachment_bone?" · "+item.attachment_bone:" · skinned");
  const remove=document.createElement("button");remove.type="button";remove.className="secondary";remove.textContent="Remove";
  remove.addEventListener("click",()=>{assemblyAccessories.splice(index,1);renderAssemblyAccessories()});
  row.append(label,remove);list.append(row);
 });
}
function refreshAssemblyControls(){
 const eligible=assemblyEligibleAssets(),base=$("assembly-base"),previousBase=base.value;
 base.replaceChildren();
 const empty=document.createElement("option");empty.value="";empty.textContent=eligible.length?"Choose base character…":"Import a character with exactly one skeleton…";base.append(empty);
 for(const asset of eligible){const option=document.createElement("option");option.value=asset.asset_id;option.textContent=asset.assembly_label+" · "+asset.asset_id.slice(0,8);base.append(option)}
 if(eligible.some(asset=>asset.asset_id===previousBase))base.value=previousBase;
 for(const slot of assemblySlots){
  const select=$("assembly-"+slot),previous=select.value;select.replaceChildren();
  const placeholder=document.createElement("option");placeholder.value="";placeholder.textContent="Choose "+slot+" mesh…";select.append(placeholder);
  for(const asset of eligible){
   const meshes=Array.isArray(asset.engine_inspection?.mesh_inventory)?asset.engine_inspection.mesh_inventory:[];
   for(const mesh of meshes){
    if(!mesh.skin_bound||!mesh.skeleton_path||Number(mesh.skeleton_bone_count)<=0||!mesh.node_path)continue;
    if(mesh.slot_candidate&&mesh.slot_candidate!==slot)continue;
    const option=document.createElement("option");option.value=asset.asset_id+"|"+mesh.node_path;
    option.textContent=asset.assembly_label+" / "+(mesh.node_name||mesh.mesh_resource_name||"Mesh")+" ["+(mesh.slot_candidate||"unclassified")+"]";
    select.append(option);
   }
  }
  if([...select.options].some(option=>option.value===previous))select.value=previous;
 }
 const accessorySelect=$("assembly-accessory"),previousAccessory=accessorySelect.value;accessorySelect.replaceChildren();
 const accessoryPlaceholder=document.createElement("option");accessoryPlaceholder.value="";accessoryPlaceholder.textContent="Choose optional accessory…";accessorySelect.append(accessoryPlaceholder);
 for(const asset of eligible){
  const meshes=Array.isArray(asset.engine_inspection?.mesh_inventory)?asset.engine_inspection.mesh_inventory:[];
  for(const mesh of meshes){
   if(mesh.slot_candidate||!mesh.node_path||(!mesh.skin_bound&&!mesh.attachment_bone))continue;
   const option=document.createElement("option");option.value=asset.asset_id+"|"+mesh.node_path;
   option.textContent=asset.assembly_label+" / "+(mesh.node_name||mesh.mesh_resource_name||"Accessory")+(mesh.attachment_bone?" · "+mesh.attachment_bone:" · shared skin");
   accessorySelect.append(option);
  }
 }
 if([...accessorySelect.options].some(option=>option.value===previousAccessory))accessorySelect.value=previousAccessory;
 $("add-assembly-accessory").disabled=!accessorySelect.value;
 $("assemble-character").disabled=!activeProject||!eligible.length||assemblySlots.some(slot=>!$("assembly-"+slot).value)||!base.value;
 $("randomize-assembly").disabled=!activeProject||!eligible.length||assemblySlots.some(slot=>![...$("assembly-"+slot).options].some(option=>option.value));
 $("assembly-status").textContent=eligible.length+" compatible-rig candidate asset(s) loaded in this session. Godot validates every selected mesh before export.";
}
$("assembly-base").addEventListener("change",refreshAssemblyControls);
$("assembly-accessory").addEventListener("change",refreshAssemblyControls);
$("add-assembly-accessory").addEventListener("click",()=>{
 const [assetId,meshPath]=$("assembly-accessory").value.split("|");
 const asset=assemblyEligibleAssets().find(item=>item.asset_id===assetId);
 const mesh=asset?.engine_inspection?.mesh_inventory?.find(item=>item.node_path===meshPath);
 if(!asset||!mesh)return;
 if(assemblyAccessories.some(item=>item.relative_path===asset.relative_path&&item.mesh_path===meshPath)){
  $("assembly-status").textContent="That accessory is already in this assembly.";return;
 }
 assemblyAccessories.push({relative_path:asset.relative_path,mesh_path:meshPath,attachment_bone:mesh.attachment_bone||"",label:asset.assembly_label+" / "+(mesh.node_name||mesh.mesh_resource_name||"Accessory")});
 renderAssemblyAccessories();refreshAssemblyControls();
});
for(const slot of assemblySlots)$("assembly-"+slot).addEventListener("change",refreshAssemblyControls);
$("randomize-assembly").addEventListener("click",()=>{
 const eligible=assemblyEligibleAssets();
 if(!eligible.length)return;
 $("assembly-base").value=eligible[Math.floor(Math.random()*eligible.length)].asset_id;
 refreshAssemblyControls();
 const usedAssetIds=new Set();
 const selectedMeshKeys=new Set();
 for(const slot of assemblySlots){
  const select=$("assembly-"+slot),options=[...select.options].filter(option=>option.value);
  const distinct=options.filter(option=>!usedAssetIds.has(option.value.split("|")[0]));
  const pool=distinct.length?distinct:options;
  if(!pool.length){$("assembly-status").textContent="Import source meshes for all four slots before shuffling.";return}
  const choice=pool[Math.floor(Math.random()*pool.length)],[assetId,meshPath]=choice.value.split("|");
  select.value=choice.value;usedAssetIds.add(assetId);selectedMeshKeys.add(choice.value);
 }
 const accessoryOptions=[...$("assembly-accessory").options].filter(option=>option.value&&!selectedMeshKeys.has(option.value));
 const accessoryCount=Math.min(accessoryOptions.length,Math.floor(Math.random()*3));
 assemblyAccessories=[];
 for(let index=0;index<accessoryCount;index++){
  const choiceIndex=Math.floor(Math.random()*accessoryOptions.length);
  const [assetId,meshPath]=accessoryOptions.splice(choiceIndex,1)[0].value.split("|");
  const asset=eligible.find(item=>item.asset_id===assetId);
  const mesh=asset?.engine_inspection?.mesh_inventory?.find(item=>item.node_path===meshPath);
  if(asset&&mesh)assemblyAccessories.push({
   relative_path:asset.relative_path,mesh_path:meshPath,attachment_bone:mesh.attachment_bone||"",
   label:asset.assembly_label+" / "+(mesh.node_name||mesh.mesh_resource_name||"Accessory")
  });
 }
 renderAssemblyAccessories();refreshAssemblyControls();
 $("assembly-status").textContent="Shuffled a four-part outfit using "+eligible.length+" imported rigged assets and "+assemblyAccessories.length+" optional accessory item(s).";
});
$("assemble-character").addEventListener("click",async()=>{
 const base=assemblyEligibleAssets().find(asset=>asset.asset_id===$("assembly-base").value);
 if(!base||!activeProject)return;
 const parts=[];
 for(const slot of assemblySlots){
  const [assetId,meshPath]=$("assembly-"+slot).value.split("|");
  const asset=assemblyEligibleAssets().find(item=>item.asset_id===assetId);
  if(!asset||!meshPath){$("assembly-status").textContent="Choose a skinned "+slot+" mesh.";return}
  parts.push({slot,relative_path:asset.relative_path,mesh_path:meshPath});
 }
 const button=$("assemble-character");button.disabled=true;$("assembly-status").textContent="Godot is validating four skeleton bindings and assembling the GLB…";
 try{
  const response=await fetch("/api/projects/"+encodeURIComponent(activeProject)+"/modular-assemblies",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({base_relative_path:base.relative_path,parts,accessories:assemblyAccessories.map(({relative_path,mesh_path,attachment_bone})=>({relative_path,mesh_path,attachment_bone}))})});
  const result=await response.json();if(!response.ok)throw new Error(result.detail||"Modular character assembly failed.");
  importedAsset=result;editingCharacter=null;rememberAssemblyAsset(result,"Assembled character");
  const assetResponse=await fetch("/api/projects/"+encodeURIComponent(activeProject)+"/character-assets/"+encodeURIComponent(result.asset_id));
  if(!assetResponse.ok)throw new Error("Assembly was saved, but its preview asset could not be retrieved.");
  const loaded=await showCharacterPreview(await assetResponse.arrayBuffer(),"Assembled character");
  $("asset-report").replaceChildren();$("asset-report").hidden=false;
  const heading=document.createElement("strong");heading.textContent="Modular assembly verified · "+result.engine_inspection.mesh_count+" meshes";
  const note=document.createElement("p");note.className="inline-status";note.textContent="Four skinned parts and "+(result.assembly?.added_accessories?.length||0)+" accessory item(s) were attached. Base animation clips survived GLB export and re-import.";
  const downloadLink=document.createElement("a");downloadLink.className="secondary";downloadLink.href="/api/projects/"+encodeURIComponent(activeProject)+"/character-assets/"+encodeURIComponent(result.asset_id);downloadLink.download="assembled-character.glb";downloadLink.textContent="Download assembled GLB";
  $("asset-report").append(heading,note,downloadLink);$("save-character").disabled=false;
  $("assembly-status").textContent="Assembly exported and re-import verified. "+(loaded?"Preview loaded. ":"")+"Save a character profile to add it to the project library.";
  $("profile-panel").scrollIntoView({behavior:"smooth",block:"start"});
 }catch(error){$("assembly-status").textContent=error.message}
 finally{refreshAssemblyControls()}
});
let characterLibrary=[];
function selectedLibraryModel(){
 return characterLibrary.find(item=>item.pack===$("library-pack").value&&item.id===$("library-outfit").value)||null;
}
function populateLibraryOutfits(){
 const pack=$("library-pack").value,select=$("library-outfit"),previous=select.value;
 select.replaceChildren();
 const models=characterLibrary.filter(item=>item.pack===pack);
 for(const model of models){
  const option=document.createElement("option");option.value=model.id;option.textContent=model.name.replaceAll("_"," ");select.append(option);
 }
 if(models.some(item=>item.id===previous))select.value=previous;
 $("library-preview").disabled=!models.length;
 $("library-import").disabled=!models.length||!activeProject;
}
async function loadCharacterLibrary(){
 const status=$("library-status");
 try{
  const response=await fetch("/api/character-builder/catalog");
  if(!response.ok)throw new Error("The verified model catalog could not be loaded.");
  const catalog=await response.json();
  if(!Array.isArray(catalog.outfits)||catalog.outfits.length!==21)throw new Error("The model catalog did not pass its expected 21-outfit check.");
  characterLibrary=catalog.outfits;
  populateLibraryOutfits();
  status.textContent=catalog.outfits.length+" pinned models ready · "+catalog.source.license+" · source revision "+catalog.source.commit.slice(0,12)+".";
 }catch(error){status.textContent=error.message}
}
$("library-pack").addEventListener("change",populateLibraryOutfits);
$("library-outfit").addEventListener("change",()=>{const model=selectedLibraryModel();$("library-preview").disabled=!model;$("library-import").disabled=!model||!activeProject});
$("library-preview").addEventListener("click",async()=>{
 const model=selectedLibraryModel();if(!model)return;
 const button=$("library-preview");button.disabled=true;$("library-status").textContent="Downloading and verifying "+model.name+"…";
 try{
  const response=await fetch(model.asset_url);if(!response.ok)throw new Error("Could not retrieve the selected pinned model.");
  const buffer=await response.arrayBuffer();
  const loaded=await showCharacterPreview(buffer,model.pack+" · "+model.name);
  if(!loaded)throw new Error("The model downloaded, but the browser preview could not be created.");
  $("library-status").textContent=model.name+" preview loaded. The pinned source GLB is unchanged.";
  document.querySelector(".preview-panel").scrollIntoView({behavior:"smooth",block:"center"});
 }catch(error){$("library-status").textContent=error.message}
 finally{button.disabled=!selectedLibraryModel()}
});
$("library-import").addEventListener("click",async()=>{
 const model=selectedLibraryModel();if(!model||!activeProject)return;
 const button=$("library-import");button.disabled=true;$("library-status").textContent="Fetching "+model.name+" for project import…";
 try{
  const response=await fetch(model.asset_url);if(!response.ok)throw new Error("Could not retrieve the selected pinned model.");
  const blob=await response.blob(),file=new File([blob],model.name+".glb",{type:"model/gltf-binary"});
  const transfer=new DataTransfer();transfer.items.add(file);$("model-file").files=transfer.files;
  $("model-file").dispatchEvent(new Event("change",{bubbles:true}));
  $("library-status").textContent=model.name+" selected. Godot inspection and project import started.";
  $("import-model").click();
  document.querySelector("#profile-panel").scrollIntoView({behavior:"smooth",block:"start"});
 }catch(error){$("library-status").textContent=error.message}
 finally{button.disabled=!selectedLibraryModel()||!activeProject}
});

loadCharacterLibrary();
loadProjects().catch(error=>{$("project-status").textContent=error.message;$("character-list").textContent=error.message});
