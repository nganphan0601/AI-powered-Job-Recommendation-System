from flask import Flask, render_template, request, redirect, url_for 
import pandas as pd
import sqlite3
import os

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'

# Ensure the uploads folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Load job dataset
job_data = pd.read_csv("DataAnalyst.csv")  # Ensure this file exists in your project folder

# Extract unique locations and industries
unique_locations = sorted(job_data['Location'].dropna().unique())
unique_roles = sorted(job_data['Job Title'].dropna().unique())
unique_industries = sorted(job_data['Industry'].dropna().unique())

# Create or connect to SQLite database
conn = sqlite3.connect('user_data.db', check_same_thread=False)
cursor = conn.cursor()

# Drop the existing table if needed (for schema updates)
cursor.execute('DROP TABLE IF EXISTS users')

# Create the table with the correct schema
cursor.execute('''
    CREATE TABLE users (
        id INTEGER PRIMARY KEY,
        name TEXT,
        email TEXT,
        location TEXT,
        job_type TEXT,
        experience TEXT,
        roles TEXT,
        industry TEXT,
        resume TEXT
    )
''')

@app.route('/')
def index():
    return render_template('index.html', locations=unique_locations, roles=unique_roles, industries=unique_industries)

@app.route('/register', methods=['POST'])
def register():
    # Collect user data from the form
    name = request.form['name']
    email = request.form['email']
    location = request.form['location']
    job_type = request.form['jobType']
    experience = request.form['experience']
    roles = request.form['roles']
    industry = request.form['industry']

    # Handle file upload
    resume = request.files['resume']
    resume_path = None
    if resume:
        resume_path = os.path.join(app.config['UPLOAD_FOLDER'], resume.filename)
        resume.save(resume_path)

    # Insert user data into the database
    cursor.execute('INSERT INTO users (name, email, location, job_type, experience, roles, industry, resume) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                   (name, email, location, job_type, experience, roles, industry, resume_path))
    conn.commit()

    # Redirect to the results page
    return redirect(url_for('results', location=location, roles=roles, industry=industry))

@app.route('/results')
def results():
    # Get filtering parameters
    user_location = request.args.get('location', '')
    user_roles = request.args.get('roles', '')
    user_industry = request.args.get('industry', '')

    # Filter job data based on location, roles, and industry
    filtered_jobs = job_data[
        job_data['Location'].str.contains(user_location, case=False, na=False) &
        job_data['Job Title'].str.contains(user_roles, case=False, na=False) &
        job_data['Industry'].str.contains(user_industry, case=False, na=False)
    ]
    
    # Extract the first 3-4 main points from the description
    jobs = []
    for _, row in filtered_jobs.iterrows():
        description_points = row['Job Description'].split('. ')[:4]  # Extract up to 4 main points
        job = {
            "title": row['Job Title'],
            "company": row['Company Name'],
            "location": row['Location'],
            "industry": row['Industry'],
            "salary": row.get('Salary Estimate', 'Not Available'),
            "description": description_points  # Use the shortened description
        }
        jobs.append(job)

    return render_template('results.html', jobs=jobs)

if __name__ == '__main__':
    app.run(debug=True)
