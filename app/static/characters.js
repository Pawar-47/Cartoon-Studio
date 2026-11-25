import { showCharacterPreview, getCharacterMaterials, applyCharacterAppearance, getCharacterMorphTargets, applyCharacterMorphTargets } from "./character-preview.js";
const $=id=>document.getElementById(id);
let activeProject="", importedAsset=null, activeCharacter=null, editingCharacter=null, appearanceRecipe={materials:{},morph_targets:{}};
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
 activeProject=id;importedAsset=null;activeCharacter=null;resetProfileEditor();appearanceRecipe={materials:{},morph_targets:{}};$("material-editor").hidden=true;$("morph-editor").hidden=true;$("save-appearance").disabled=true;$("asset-report").hidden=true;$("profile-status").textContent="";$("save-character").disabled=true;$("refresh-characters").disabled=!id;
 $("project-status").textContent=id?"Project selected. Import a GLB model to begin.":"Choose a project to begin.";
 $("character-list").replaceChildren();
 if(!id){$("character-list").innerHTML='<div class="empty">Select a project to see its characters.</div>';return}
 await loadCharacters();
}
function documentElementOption(characterDoc){
 const option=window.document.createElement("option");
 option.value=characterDoc.id;option.textContent=characterDoc.data.name||"Unnamed character";return option;
}
function updateRetargetCharacterOptions(characters){
 const source=$("retarget-source"),target=$("retarget-target");
 const previousSource=source.value,previousTarget=target.value;
 source.replaceChildren();target.replaceChildren();
 for(const [select,label] of [[source,"Select animated source…"],[target,"Select target rig…"]]){
  const option=document.createElement("option");option.value="";option.textContent=label;select.append(option);
 }
 for(const characterDoc of characters){
  const data=characterDoc.data||{},asset=data.asset||{},inspection=asset.engine_inspection||{},container=asset.container||{},rig=asset.rig_analysis||{},hierarchy=rig.hierarchy_validation||{};
  const compatible=rig.status==="humanoid_names_complete"&&hierarchy.status==="valid";
  const skinCount=Number(container.skin_count??inspection.skin_count??0);
  if(compatible&&Number(inspection.animation_count||0)>0)source.append(documentElementOption(characterDoc));
  if(compatible&&skinCount>0)target.append(documentElementOption(characterDoc));
 }
 if([...source.options].some(option=>option.value===previousSource))source.value=previousSource;
 if([...target.options].some(option=>option.value===previousTarget))target.value=previousTarget;
 $("create-retarget").disabled=!source.value||!target.value||source.value===target.value;
}
async function loadRetargets(){
 if(!activeProject)return;
 const response=await fetch("/api/projects/"+encodeURIComponent(activeProject)+"/retargets");
 if(!response.ok)throw new Error("Could not load saved retarget scenes.");
 const documents=await response.json(),container=$("retarget-list");container.replaceChildren();
 for(const item of documents){
  const row=document.createElement("div");row.className="retarget-record";
  const title=document.createElement("strong");title.textContent=(item.data.source_character_name||"Source")+" → "+(item.data.target_character_name||"Target");
  const detail=document.createElement("span");detail.textContent=(item.data.animation_name||"Imported animation")+" · "+item.data.mapped_bone_count+"/15 bones · "+(item.data.scene_reopened?"saved scene reopened":"scene saved");
  row.append(title,detail);container.append(row);
 }
 if(!documents.length){const empty=document.createElement("p");empty.className="inline-status";empty.textContent="No retarget scenes saved in this project yet.";container.append(empty)}
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
  card.append(title,description,model,rig,animations,revision,previewButton,editButton,customizeButton);list.append(card);
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
 const loaded=await showCharacterPreview(buffer,data.name,appearanceRecipe);
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
  const title=window.document.createElement("span");title.textContent=target.name;
  const value=appearanceRecipe.morph_targets[target.key]??target.value;
  const output=window.document.createElement("output");output.value=Number(value).toFixed(2);
  const input=window.document.createElement("input");input.type="range";input.min="0";input.max="1";input.step="0.01";input.value=String(value);
  input.addEventListener("input",()=>{
   const weight=Number(input.value);appearanceRecipe.morph_targets[target.key]=weight;
   output.value=weight.toFixed(2);applyCharacterMorphTargets({[target.key]:weight});
   $("appearance-status").textContent="Facial preview updated. Save to keep these expression values.";
  });
  label.append(title,output,input);container.append(label);
 }
}
$("reset-expressions").addEventListener("click",()=>{
 for(const target of getCharacterMorphTargets())appearanceRecipe.morph_targets[target.key]=0;
 applyCharacterMorphTargets(appearanceRecipe.morph_targets);buildMorphControls();
 $("appearance-status").textContent="Facial controls reset. Save to keep the neutral expression.";
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
  importedAsset=data;await showCharacterPreview(await file.arrayBuffer(),file.name);$("asset-report").hidden=false;$("asset-report").replaceChildren();
  const heading=document.createElement("strong");heading.textContent="Godot import successful · "+data.container.format;
  const metrics=document.createElement("div");metrics.className="asset-metrics";
  const rigAnalysis=data.rig_analysis||{};
  const coverage=rigAnalysis.required_bone_count?rigAnalysis.matched_bone_count+"/"+rigAnalysis.required_bone_count:"Unavailable";
  const missing=Array.isArray(rigAnalysis.missing_bones)?rigAnalysis.missing_bones.join(", "):"Not reported";
  const hierarchy=rigAnalysis.hierarchy_validation||{};
  const hierarchyLabel=hierarchy.status==="valid"?"Valid":hierarchy.status==="invalid"?"Needs review":hierarchy.status==="incomplete"?"Incomplete":"Not available";
  const restPose=rigAnalysis.rest_pose_summary||{};
  const items=[["Meshes",data.engine_inspection.mesh_count],["Skeletons",data.engine_inspection.skeleton_count],["Animations",data.engine_inspection.animation_count],["Nodes",data.engine_inspection.node_count],["File size",(data.container.size_bytes/1048576).toFixed(2)+" MiB"],["Humanoid bone-name coverage",coverage],["Missing core humanoid names",missing],["Humanoid hierarchy",hierarchyLabel],["Rest-pose bone transforms",restPose.measured_bone_count??0]];
  for(const [label,value] of items){const span=document.createElement("span");const b=document.createElement("b");b.textContent=String(value);span.append(document.createTextNode(label+": "),b);metrics.append(span)}
  const rigNote=document.createElement("p");rigNote.className="inline-status";rigNote.textContent=rigAnalysis.retargeting_note||"Skeleton presence is not proof of retarget compatibility.";
  const hierarchyNote=document.createElement("p");hierarchyNote.className="inline-status";
  const hierarchyIssues=Array.isArray(hierarchy.issues)?hierarchy.issues:[];
  const restNote=restPose.measured_bone_count?(" Godot also reported local rest offsets for "+restPose.measured_bone_count+" mapped bones; these are not world-space limb lengths."):"";
  hierarchyNote.textContent=(hierarchy.status==="valid"?"Required humanoid parent chains are structurally consistent; rest pose, axes, scale, skin weights and real animation transfer remain unverified.":hierarchyIssues.length?hierarchyIssues.join(" "):(hierarchy.note||"Parent-chain validation is not available for this asset."))+restNote;
  $("asset-report").append(heading,metrics,rigNote,hierarchyNote);$("import-status").textContent="Asset stored inside this project. Complete the profile to save it."; $("save-character").disabled=false;
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
loadProjects().catch(error=>{$("project-status").textContent=error.message;$("character-list").textContent=error.message});
