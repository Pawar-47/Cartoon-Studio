from __future__ import annotations
import json
import os
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
ROOT=Path(__file__).resolve().parent.parent
DATA_DIR=Path(os.environ.get("CARTOON_STUDIO_DATA",ROOT/"data"))
DB_PATH=DATA_DIR/"cartoon_studio.sqlite3"
STATIC_DIR=Path(__file__).resolve().parent/"static"
app=FastAPI(title="Cartoon Studio",description="Local-first original Urdu 3D cartoon studio",version="0.1.0")
app.mount("/static",StaticFiles(directory=STATIC_DIR),name="static")
def connect_db():
 DATA_DIR.mkdir(parents=True,exist_ok=True)
 c=sqlite3.connect(DB_PATH); c.row_factory=sqlite3.Row; return c
def initialize_database():
 with connect_db() as c:
  c.execute("""CREATE TABLE IF NOT EXISTS projects(id TEXT PRIMARY KEY,name TEXT NOT NULL,description TEXT NOT NULL DEFAULT '',created_at TEXT NOT NULL,updated_at TEXT NOT NULL,metadata_json TEXT NOT NULL DEFAULT '{}')""")
@app.on_event("startup")
def on_startup(): initialize_database()
class ProjectCreate(BaseModel):
 name:str=Field(min_length=1,max_length=100)
 description:str=Field(default="",max_length=1000)
class ProjectRecord(BaseModel):
 id:str; name:str; description:str; created_at:str; updated_at:str; metadata:dict[str,Any]
@app.get("/",include_in_schema=False)
def index(): return FileResponse(STATIC_DIR/"index.html")
@app.get("/api/health")
def health(): return {"status":"ok","application":"Cartoon Studio","version":app.version}
@app.get("/api/status")
def status():
 initialize_database()
 with connect_db() as c: count=c.execute("SELECT COUNT(*) FROM projects").fetchone()[0]
 return {"application":"Cartoon Studio","version":app.version,"project_count":count,"production_engine":"not integrated yet","rendering":"not available in bootstrap build","next_milestone":"research-backed 3D preview and character-animation foundation"}
@app.get("/api/projects",response_model=list[ProjectRecord])
def list_projects():
 initialize_database()
 with connect_db() as c: rows=c.execute("SELECT * FROM projects ORDER BY updated_at DESC").fetchall()
 return [ProjectRecord(id=r["id"],name=r["name"],description=r["description"],created_at=r["created_at"],updated_at=r["updated_at"],metadata=json.loads(r["metadata_json"])) for r in rows]
@app.post("/api/projects",response_model=ProjectRecord,status_code=201)
def create_project(payload:ProjectCreate):
 initialize_database(); name=payload.name.strip()
 if not name: raise HTTPException(status_code=422,detail="Project name cannot be blank.")
 now=datetime.now(timezone.utc).isoformat(); pid=str(uuid.uuid4()); desc=payload.description.strip()
 with connect_db() as c:
  c.execute("INSERT INTO projects(id,name,description,created_at,updated_at,metadata_json) VALUES(?,?,?,?,?,'{}')",(pid,name,desc,now,now))
 return ProjectRecord(id=pid,name=name,description=desc,created_at=now,updated_at=now,metadata={})
