import { showCharacterPreview } from "./character-preview.js";
const $=id=>document.getElementById(id);
let activeProject="", importedAsset=null;
const params=new URLSearchParams(window.location.search);
function lines(value){return value.split(/\r?\n/).map(x=>x.trim()).filter(Boolean)}
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
 activeProject=id;importedAsset=null;$("asset-report").hidden=true;$("profile-status").textContent="";$("save-character").disabled=true;$("refresh-characters").disabled=!id;
 $("project-status").textContent=id?"Project selected. Import a GLB model to begin.":"Choose a project to begin.";
 $("character-list").replaceChildren();
 if(!id){$("character-list").innerHTML='<div class="empty">Select a project to see its characters.</div>';return}
 await loadCharacters();
}
async function loadCharacters(){
 const response=await fetch("/api/projects/"+encodeURIComponent(activeProject)+"/characters");
 if(!response.ok)throw new Error("Could not load saved characters.");
 const characters=await response.json(),list=$("character-list");list.replaceChildren();
 if(!characters.length){list.innerHTML='<div class="empty">No saved characters in this project yet.</div>';return}
 for(const document of characters){
  const data=document.data,card=document.createElement("article");card.className="character-card";
  const title=document.createElement("h3");title.textContent=data.name;
  const description=document.createElement("p");description.textContent=data.description||"No description";
  const model=document.createElement("p");const asset=data.asset||{};model.textContent=(asset.original_filename||"GLB model")+" · "+(asset.engine_inspection?.mesh_count??asset.container?.mesh_count??0)+" meshes";
  const rig=document.createElement("span");rig.className="tag"+(data.rig_status==="ready"?"":" warning");rig.textContent=data.rig_status==="ready"?"Rig detected":"No skeleton detected";
  const animations=document.createElement("span");animations.className="tag";animations.textContent=(asset.engine_inspection?.animation_count??asset.container?.animation_count??0)+" animations";
  const revision=document.createElement("p");revision.textContent="Revision "+document.revision+" · "+new Date(document.updated_at).toLocaleDateString();
  const previewButton=document.createElement("button");previewButton.className="secondary preview-saved";previewButton.type="button";previewButton.textContent="Preview";
  previewButton.addEventListener("click",async()=>{try{const assetId=(asset.relative_path||"").split("/").pop().replace(/\.glb$/i,"");const response=await fetch("/api/projects/"+encodeURIComponent(activeProject)+"/character-assets/"+encodeURIComponent(assetId));if(!response.ok)throw new Error("Could not load the saved GLB asset.");const buffer=await response.arrayBuffer();await showCharacterPreview(buffer,data.name);document.querySelector(".preview-panel").scrollIntoView({behavior:"smooth",block:"center"})}catch(error){$("project-status").textContent=error.message}});
  card.append(title,description,model,rig,animations,revision,previewButton);list.append(card);
 }
}
$("project-select").addEventListener("change",event=>selectProject(event.target.value).catch(error=>$("project-status").textContent=error.message));
$("model-file").addEventListener("change",()=>{$("import-model").disabled=!activeProject||!$("model-file").files.length;importedAsset=null;$("save-character").disabled=true;$("asset-report").hidden=true});
$("import-model").addEventListener("click",async()=>{
 const file=$("model-file").files[0];if(!file||!activeProject)return;
 $("import-model").disabled=true;$("import-status").textContent="Uploading and inspecting with Godot…";
 try{
  const response=await fetch("/api/projects/"+encodeURIComponent(activeProject)+"/character-assets",{method:"POST",headers:{"Content-Type":"application/octet-stream","X-Asset-Filename":file.name},body:file});
  const data=await response.json();if(!response.ok)throw new Error(data.detail||"Model import failed.");
  importedAsset=data;await showCharacterPreview(await file.arrayBuffer(),file.name);$("asset-report").hidden=false;$("asset-report").replaceChildren();
  const heading=document.createElement("strong");heading.textContent="Godot import successful · "+data.container.format;
  const metrics=document.createElement("div");metrics.className="asset-metrics";
  const items=[["Meshes",data.engine_inspection.mesh_count],["Skeletons",data.engine_inspection.skeleton_count],["Animations",data.engine_inspection.animation_count],["Nodes",data.engine_inspection.node_count],["File size",(data.container.size_bytes/1048576).toFixed(2)+" MiB"],["Rig readiness",data.rig_ready?"Skeleton detected":"No skeleton"]];
  for(const [label,value] of items){const span=document.createElement("span");const b=document.createElement("b");b.textContent=String(value);span.append(document.createTextNode(label+": "),b);metrics.append(span)}
  $("asset-report").append(heading,metrics);$("import-status").textContent="Asset stored inside this project. Complete the profile to save it."; $("save-character").disabled=false;
 }catch(error){$("import-status").textContent=error.message}
 finally{$("import-model").disabled=!activeProject||!$("model-file").files.length}
});
$("character-form").addEventListener("submit",async event=>{
 event.preventDefault();if(!importedAsset||!activeProject)return;
 $("save-character").disabled=true;$("profile-status").textContent="Saving character profile…";
 try{
  let proportions={};const raw=$("body-proportions").value.trim();if(raw){proportions=JSON.parse(raw);if(!proportions||Array.isArray(proportions)||typeof proportions!=="object")throw new Error("Body proportions must be a JSON object.")}
  const height=$("height-cm").value;
  const payload={name:$("character-name").value,description:$("character-description").value,face_design:$("face-design").value,body_proportions:proportions,height_cm:height?Number(height):null,hair:$("hair").value,clothing:lines($("clothing").value),accessories:lines($("accessories").value),eye_design:$("eye-design").value,mouth_design:$("mouth-design").value,expressions:lines($("expressions").value),personality:$("personality").value,relationships:lines($("relationships").value),voice_profile:$("voice-profile").value,dialogue_style:$("dialogue-style").value,asset_path:importedAsset.relative_path};
  const response=await fetch("/api/projects/"+encodeURIComponent(activeProject)+"/characters",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(payload)});
  const data=await response.json();if(!response.ok)throw new Error(data.detail||"Could not save character.");
  $("profile-status").textContent="Character saved. Profile revision "+data.revision+".";
  $("character-form").reset();importedAsset=null;$("model-file").value="";$("asset-report").hidden=true;$("import-status").textContent="Import another model to create another character.";$("save-character").disabled=true;
  await loadCharacters();
 }catch(error){$("profile-status").textContent=error.message;$("save-character").disabled=!importedAsset}
});
$("refresh-characters").addEventListener("click",()=>loadCharacters().catch(error=>$("project-status").textContent=error.message));
loadProjects().catch(error=>{$("project-status").textContent=error.message;$("character-list").textContent=error.message});
