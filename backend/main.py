"""
This is the main FastAPI server - the "brain" of EduEscape.
It handles all the backend logic: uploading PDFs, generating levels, checking answers, etc.
NO AI REQUIRED - uses simple text processing instead!
"""

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import os
from datetime import datetime
import csv

# Import our helper functions
from pdf_utils import extract_text_from_pdf, detect_topics
from content_generator import generate_level_content


# Create the FastAPI app
app = FastAPI(title="EduEscape API")

# Allow the frontend to talk to the backend (CORS settings)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# File to store game progress
PROGRESS_FILE = "progress.json"


# Data models for requests
class AnswerSubmission(BaseModel):
    """When a student submits an answer"""
    level_id: int
    question_index: int
    answer: str


class ProgressUpdate(BaseModel):
    """Update student progress"""
    level_id: int
    attempts: int
    time_taken: int
    correct_answers: int


# ===== Helper Functions =====

def load_progress():
    """Load progress from JSON file"""
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r') as f:
            return json.load(f)
    return {"levels": [], "current_level": 0, "unlocked_levels": [0], "history": []}


def save_progress(progress_data):
    """Save progress to JSON file"""
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress_data, f, indent=2)


# ===== API Endpoints =====

@app.get("/")
def read_root():
    """Homepage - just a welcome message"""
    return {"message": "Welcome to EduEscape API! Upload a PDF to get started."}


@app.post("/upload-pdf")
async def upload_pdf(file: UploadFile = File(...)):
    """
    Upload a PDF and generate levels from it.
    This is step 1 of the workflow.
    """
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    # Save the uploaded file temporarily
    file_path = f"temp_{file.filename}"
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    try:
        # Extract text from PDF
        text = extract_text_from_pdf(file_path)
        
        if not text:
            raise HTTPException(status_code=400, detail="Could not extract text from PDF")
        
        # Detect topics (these become levels)
        topics = detect_topics(text)
        
        # Limit to first 5 topics for simplicity
        topics = topics[:5]
        
        # Generate content for each level using text processing (NO AI!)
        levels = []
        for i, topic in enumerate(topics):
            level_content = generate_level_content(
                topic['title'], 
                topic['content']
            )
            
            levels.append({
                "level_id": i,
                "title": topic['title'],
                "summary": level_content['summary'],
                "questions": level_content['questions'],
                "hints": level_content['hints'],
                "keyword": level_content['keyword']
            })
        
        # Save to progress file
        progress_data = {
            "levels": levels,
            "current_level": 0,
            "unlocked_levels": [0],  # Only first level is unlocked
            "history": []
        }
        save_progress(progress_data)
        
        # Clean up temp file
        os.remove(file_path)
        
        return {
            "message": "PDF processed successfully!",
            "total_levels": len(levels),
            "levels": levels
        }
        
    except Exception as e:
        # Clean up temp file if there's an error
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")


@app.get("/levels")
def get_levels():
    """
    Get all levels and which ones are unlocked.
    """
    progress = load_progress()
    
    levels_info = []
    for level in progress['levels']:
        levels_info.append({
            "level_id": level['level_id'],
            "title": level['title'],
            "unlocked": level['level_id'] in progress['unlocked_levels'],
            "keyword": level.get('keyword', '')
        })
    
    return {
        "levels": levels_info,
        "current_level": progress['current_level']
    }


@app.get("/level/{level_id}")
def get_level(level_id: int):
    """
    Get details for a specific level (summary and questions).
    This is when the student starts playing a level.
    """
    progress = load_progress()
    
    # Check if level exists
    if level_id >= len(progress['levels']):
        raise HTTPException(status_code=404, detail="Level not found")
    
    # Check if level is unlocked
    if level_id not in progress['unlocked_levels']:
        raise HTTPException(status_code=403, detail="Level is locked. Complete previous levels first!")
    
    level = progress['levels'][level_id]
    
    return {
        "level_id": level['level_id'],
        "title": level['title'],
        "summary": level['summary'],
        "questions": level['questions'],
        "hints": level['hints']
    }


@app.post("/submit-answer")
def submit_answer(submission: AnswerSubmission):
    """
    Check if a student's answer is correct.
    Returns whether it's correct and provides hints if wrong.
    """
    progress = load_progress()
    
    level = progress['levels'][submission.level_id]
    question = level['questions'][submission.question_index]
    
    # Simple answer checking (case-insensitive, checks if key words are present)
    user_answer = submission.answer.lower().strip()
    correct_answer = question['answer'].lower().strip()
    
    # Check if answer contains key terms from the correct answer
    # Extract meaningful words from correct answer
    answer_words = [w for w in correct_answer.split() if len(w) > 3]
    
    # Check if at least 30% of key words are in user's answer
    matches = sum(1 for word in answer_words if word in user_answer)
    is_correct = matches >= max(1, len(answer_words) * 0.3)
    
    response = {
        "correct": is_correct,
        "question": question['question']
    }
    
    if is_correct:
        response["message"] = "Correct! Well done!"
        response["keyword"] = level.get('keyword', '')
    else:
        response["message"] = "Not quite right. Here's a hint!"
        response["hint"] = level['hints'][0] if level['hints'] else "Think about the main concepts."
    
    return response


@app.post("/complete-level")
def complete_level(progress_update: ProgressUpdate):
    """
    Mark a level as complete and unlock the next one.
    Save statistics about the level.
    """
    progress = load_progress()
    
    level_id = progress_update.level_id
    
    # Add to history
    progress['history'].append({
        "level_id": level_id,
        "attempts": progress_update.attempts,
        "time_taken": progress_update.time_taken,
        "correct_answers": progress_update.correct_answers,
        "timestamp": datetime.now().isoformat()
    })
    
    # Unlock next level
    next_level = level_id + 1
    if next_level < len(progress['levels']) and next_level not in progress['unlocked_levels']:
        progress['unlocked_levels'].append(next_level)
    
    progress['current_level'] = next_level if next_level < len(progress['levels']) else level_id
    
    save_progress(progress)
    
    return {
        "message": "Level complete!",
        "next_level_unlocked": next_level < len(progress['levels']),
        "next_level_id": next_level if next_level < len(progress['levels']) else None
    }


@app.get("/analytics")
def get_analytics():
    """
    Get analytics data for the student.
    """
    progress = load_progress()
    
    return {
        "total_levels": len(progress['levels']),
        "completed_levels": len(progress['history']),
        "unlocked_levels": len(progress['unlocked_levels']),
        "history": progress['history']
    }


@app.get("/export-csv")
def export_csv():
    """
    Export progress data as CSV for analysis.
    """
    progress = load_progress()
    
    csv_filename = "eduescape_progress.csv"
    
    with open(csv_filename, 'w', newline='') as csvfile:
        fieldnames = ['level_id', 'level_title', 'attempts', 'time_taken', 'correct_answers', 'timestamp']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for entry in progress['history']:
            level_title = progress['levels'][entry['level_id']]['title'] if entry['level_id'] < len(progress['levels']) else "Unknown"
            writer.writerow({
                'level_id': entry['level_id'],
                'level_title': level_title,
                'attempts': entry['attempts'],
                'time_taken': entry['time_taken'],
                'correct_answers': entry['correct_answers'],
                'timestamp': entry['timestamp']
            })
    
    return {
        "message": "CSV exported successfully!",
        "filename": csv_filename
    }


@app.post("/reset-progress")
def reset_progress():
    """
    Reset all progress (useful for testing).
    """
    if os.path.exists(PROGRESS_FILE):
        os.remove(PROGRESS_FILE)
    
    return {"message": "Progress reset successfully!"}