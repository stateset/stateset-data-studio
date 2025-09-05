#!/usr/bin/env python
"""
Script to query the StateSet Data Studio database
"""
import sqlite3
import json

DB_PATH = "synthetic_data_api.db"

def pretty_print_json(data):
    """Print JSON data in a readable format"""
    print(json.dumps(data, indent=2))

def query_projects():
    """Query all projects"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM projects")
    rows = cursor.fetchall()
    
    print("\n=== PROJECTS ===")
    for row in rows:
        project = dict(row)
        print(f"ID: {project['id']}")
        print(f"Name: {project['name']}")
        print(f"Description: {project['description']}")
        print(f"Created: {project['created_at']}")
        print("---")
    
    conn.close()

def query_jobs():
    """Query all jobs"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM jobs")
    rows = cursor.fetchall()
    
    print("\n=== JOBS ===")
    for row in rows:
        job = dict(row)
        print(f"ID: {job['id']}")
        print(f"Project ID: {job['project_id']}")
        print(f"Type: {job['job_type']}")
        print(f"Status: {job['status']}")
        print(f"Input: {job['input_file']}")
        print(f"Output: {job['output_file']}")
        
        if job['stats']:
            try:
                stats = json.loads(job['stats'])
                print("Stats:")
                pretty_print_json(stats)
            except:
                print(f"Stats: {job['stats']}")
        
        print(f"Created: {job['created_at']}")
        print("---")
    
    conn.close()

if __name__ == "__main__":
    query_projects()
    query_jobs()