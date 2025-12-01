/*
 * EduEscape Frontend JavaScript
 * Handles all user interactions and connects to the backend API
 */

// Backend API URL - change this if your backend runs on a different port
const API_URL = 'http://localhost:8000';

// Global state
let currentLevel = null;
let currentQuestionIndex = 0;
let levelAttempts = 0;
let correctAnswers = 0;
let levelStartTime = null;
let timerInterval = null;
let timerSeconds = 25 * 60; // 25 minutes in seconds

// =========================
// Screen Navigation
// =========================

function showScreen(screenId) {
    // Hide all screens
    document.querySelectorAll('.screen').forEach(screen => {
        screen.classList.remove('active');
    });
    
    // Show the requested screen
    document.getElementById(screenId).classList.add('active');
}

// =========================
// Upload PDF Functionality
// =========================

document.getElementById('upload-btn').addEventListener('click', async () => {
    const fileInput = document.getElementById('pdf-file');
    const file = fileInput.files[0];
    
    if (!file) {
        showStatus('Please select a PDF file first!', 'error');
        return;
    }
    
    showStatus('Uploading and processing PDF... This may take a minute.', 'info');
    
    // Create form data
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const response = await fetch(`${API_URL}/upload-pdf`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error('Upload failed');
        }
        
        const data = await response.json();
        
        showStatus(`Success! Generated ${data.total_levels} levels.`, 'success');
        
        // Wait a moment then show level selection
        setTimeout(() => {
            loadLevels();
            showScreen('level-select-screen');
        }, 1500);
        
    } catch (error) {
        showStatus('Error uploading PDF. Make sure the backend server is running!', 'error');
        console.error(error);
    }
});

function showStatus(message, type) {
    const statusDiv = document.getElementById('upload-status');
    statusDiv.textContent = message;
    statusDiv.className = `status-message ${type}`;
}

// =========================
// Level Selection
// =========================

async function loadLevels() {
    try {
        const response = await fetch(`${API_URL}/levels`);
        const data = await response.json();
        
        const levelsList = document.getElementById('levels-list');
        levelsList.innerHTML = '';
        
        data.levels.forEach(level => {
            const levelCard = document.createElement('div');
            levelCard.className = `level-card ${level.unlocked ? 'unlocked' : 'locked'}`;
            
            levelCard.innerHTML = `
                <h3>Level ${level.level_id + 1}</h3>
                <p>${level.title}</p>
                ${level.keyword ? `<p class="keyword">🔑 Keyword: ${level.keyword}</p>` : ''}
                ${!level.unlocked ? '<p>🔒 Locked</p>' : ''}
            `;
            
            if (level.unlocked) {
                levelCard.addEventListener('click', () => startLevel(level.level_id));
            }
            
            levelsList.appendChild(levelCard);
        });
        
    } catch (error) {
        console.error('Error loading levels:', error);
        alert('Error loading levels. Make sure the backend is running!');
    }
}

// =========================
// Level Play
// =========================

async function startLevel(levelId) {
    try {
        const response = await fetch(`${API_URL}/level/${levelId}`);
        const data = await response.json();
        
        currentLevel = data;
        currentQuestionIndex = 0;
        levelAttempts = 0;
        correctAnswers = 0;
        levelStartTime = Date.now();
        
        // Display level info
        document.getElementById('level-title').textContent = data.title;
        document.getElementById('level-summary').textContent = data.summary;
        
        // Set up questions
        document.getElementById('total-questions').textContent = data.questions.length;
        
        // Show first question
        displayQuestion();
        
        // Reset timer
        resetTimer();
        
        // Show the play screen
        showScreen('level-play-screen');
        
    } catch (error) {
        console.error('Error starting level:', error);
        alert('Error starting level!');
    }
}

function displayQuestion() {
    const question = currentLevel.questions[currentQuestionIndex];
    
    document.getElementById('current-question').textContent = question.question;
    document.getElementById('current-question-num').textContent = currentQuestionIndex + 1;
    document.getElementById('answer-input').value = '';
    document.getElementById('answer-feedback').innerHTML = '';
    
    // Update progress bar
    const progress = ((currentQuestionIndex) / currentLevel.questions.length) * 100;
    document.getElementById('progress-fill').style.width = `${progress}%`;
    
    // Hide/show buttons
    document.getElementById('submit-answer-btn').style.display = 'inline-block';
    document.getElementById('next-question-btn').style.display = 'none';
    document.getElementById('complete-level-btn').style.display = 'none';
}

// =========================
// Answer Submission
// =========================

document.getElementById('submit-answer-btn').addEventListener('click', async () => {
    const answer = document.getElementById('answer-input').value.trim();
    
    if (!answer) {
        alert('Please type an answer!');
        return;
    }
    
    levelAttempts++;
    
    try {
        const response = await fetch(`${API_URL}/submit-answer`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                level_id: currentLevel.level_id,
                question_index: currentQuestionIndex,
                answer: answer
            })
        });
        
        const data = await response.json();
        
        const feedbackDiv = document.getElementById('answer-feedback');
        
        if (data.correct) {
            correctAnswers++;
            feedbackDiv.className = 'feedback correct';
            feedbackDiv.innerHTML = `
                <p>✅ ${data.message}</p>
                <p>🔑 Keyword Earned: <strong>${data.keyword}</strong></p>
            `;
            
            // Hide submit button, show next button
            document.getElementById('submit-answer-btn').style.display = 'none';
            
            if (currentQuestionIndex < currentLevel.questions.length - 1) {
                document.getElementById('next-question-btn').style.display = 'inline-block';
            } else {
                document.getElementById('complete-level-btn').style.display = 'inline-block';
            }
        } else {
            feedbackDiv.className = 'feedback incorrect';
            feedbackDiv.innerHTML = `
                <p>❌ ${data.message}</p>
                <p>💡 Hint: ${data.hint}</p>
                <p>Try again!</p>
            `;
        }
        
    } catch (error) {
        console.error('Error submitting answer:', error);
        alert('Error submitting answer!');
    }
});

// =========================
// Next Question
// =========================

document.getElementById('next-question-btn').addEventListener('click', () => {
    currentQuestionIndex++;
    displayQuestion();
});

// =========================
// Complete Level
// =========================

document.getElementById('complete-level-btn').addEventListener('click', async () => {
    const timeTaken = Math.floor((Date.now() - levelStartTime) / 1000);
    
    try {
        const response = await fetch(`${API_URL}/complete-level`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                level_id: currentLevel.level_id,
                attempts: levelAttempts,
                time_taken: timeTaken,
                correct_answers: correctAnswers
            })
        });
        
        const data = await response.json();
        
        alert(`🎉 ${data.message}\nAttempts: ${levelAttempts}\nTime: ${timeTaken}s\nCorrect: ${correctAnswers}/${currentLevel.questions.length}`);
        
        // Go back to level selection
        loadLevels();
        showScreen('level-select-screen');
        
    } catch (error) {
        console.error('Error completing level:', error);
        alert('Error completing level!');
    }
});

// =========================
// Pomodoro Timer
// =========================

document.getElementById('start-timer-btn').addEventListener('click', () => {
    if (timerInterval) {
        // Stop timer
        clearInterval(timerInterval);
        timerInterval = null;
        document.getElementById('start-timer-btn').textContent = 'Start Timer';
        document.getElementById('timer').classList.remove('running');
    } else {
        // Start timer
        timerInterval = setInterval(updateTimer, 1000);
        document.getElementById('start-timer-btn').textContent = 'Pause Timer';
        document.getElementById('timer').classList.add('running');
    }
});

function updateTimer() {
    if (timerSeconds > 0) {
        timerSeconds--;
        
        const minutes = Math.floor(timerSeconds / 60);
        const seconds = timerSeconds % 60;
        
        document.getElementById('timer').textContent = 
            `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    } else {
        clearInterval(timerInterval);
        timerInterval = null;
        alert('⏰ Pomodoro complete! Time for a break!');
        resetTimer();
    }
}

function resetTimer() {
    clearInterval(timerInterval);
    timerInterval = null;
    timerSeconds = 25 * 60;
    document.getElementById('timer').textContent = '25:00';
    document.getElementById('start-timer-btn').textContent = 'Start Timer';
    document.getElementById('timer').classList.remove('running');
}

// =========================
// Analytics
// =========================

document.getElementById('view-analytics-btn').addEventListener('click', async () => {
    try {
        const response = await fetch(`${API_URL}/analytics`);
        const data = await response.json();
        
        const analyticsDiv = document.getElementById('analytics-data');
        
        analyticsDiv.innerHTML = `
            <div class="stat-card">
                <h3>${data.total_levels}</h3>
                <p>Total Levels</p>
            </div>
            <div class="stat-card">
                <h3>${data.completed_levels}</h3>
                <p>Completed</p>
            </div>
            <div class="stat-card">
                <h3>${data.unlocked_levels}</h3>
                <p>Unlocked</p>
            </div>
        `;
        
        if (data.history.length > 0) {
            const tableHTML = `
                <h3 style="margin-top: 30px;">Recent Activity</h3>
                <table class="history-table">
                    <thead>
                        <tr>
                            <th>Level</th>
                            <th>Attempts</th>
                            <th>Time</th>
                            <th>Correct</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${data.history.slice(-5).reverse().map(entry => `
                            <tr>
                                <td>Level ${entry.level_id + 1}</td>
                                <td>${entry.attempts}</td>
                                <td>${entry.time_taken}s</td>
                                <td>${entry.correct_answers}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            `;
            analyticsDiv.innerHTML += tableHTML;
        }
        
        showScreen('analytics-screen');
        
    } catch (error) {
        console.error('Error loading analytics:', error);
        alert('Error loading analytics!');
    }
});

document.getElementById('export-csv-btn').addEventListener('click', async () => {
    try {
        const response = await fetch(`${API_URL}/export-csv`);
        const data = await response.json();
        
        alert(`CSV exported to backend folder: ${data.filename}`);
        
    } catch (error) {
        console.error('Error exporting CSV:', error);
        alert('Error exporting CSV!');
    }
});

// =========================
// Navigation Buttons
// =========================

document.getElementById('back-to-levels-btn').addEventListener('click', () => {
    loadLevels();
    showScreen('level-select-screen');
});

document.getElementById('back-from-analytics-btn').addEventListener('click', () => {
    showScreen('level-select-screen');
});

document.getElementById('reset-btn').addEventListener('click', async () => {
    if (!confirm('Are you sure you want to reset all progress? This cannot be undone!')) {
        return;
    }
    
    try {
        const response = await fetch(`${API_URL}/reset-progress`, {
            method: 'POST'
        });
        
        const data = await response.json();
        alert(data.message);
        
        showScreen('upload-screen');
        
    } catch (error) {
        console.error('Error resetting progress:', error);
        alert('Error resetting progress!');
    }
});

// =========================
// Initialize
// =========================

// Check if we have levels already loaded
window.addEventListener('load', async () => {
    try {
        const response = await fetch(`${API_URL}/levels`);
        const data = await response.json();
        
        if (data.levels && data.levels.length > 0) {
            // We have levels, show level selection
            loadLevels();
            showScreen('level-select-screen');
        } else {
            // No levels, show upload screen
            showScreen('upload-screen');
        }
    } catch (error) {
        // Backend not running or error, show upload screen
        showScreen('upload-screen');
    }
});