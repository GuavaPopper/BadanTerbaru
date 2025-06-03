import cv2 as cv
import mediapipe as mp
import time
import math
import numpy as np
import json
from datetime import datetime
import sqlite3
import os

# Initialize MediaPipe
mpPose = mp.solutions.pose
mpDraw = mp.solutions.drawing_utils
pose = mpPose.Pose()
capture = cv.VideoCapture(0)

def calculate_distance(p1, p2):
    return math.sqrt((p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2)

def estimate_circumference(width):
    # Menggunakan faktor koreksi untuk estimasi yang lebih realistis
    # Asumsi: lingkar ≈ 2.5 kali lebar (faktor antropometri umum)
    return width * 2.5

def init_database():
    db_path = 'measurements.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS measurements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            height REAL,
            shoulder_width REAL,
            chest_circumference REAL,
            waist_circumference REAL
        )
    ''')
    conn.commit()
    return conn

def save_measurements_to_db(conn, measurements):
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO measurements (timestamp, height, shoulder_width, chest_circumference, waist_circumference)
        VALUES (?, ?, ?, ?, ?)
    ''', (
        measurements["timestamp"],
        measurements["height"],
        measurements["shoulder_width"],
        measurements["chest_circumference"],
        measurements["waist_circumference"]
    ))
    conn.commit()

# Faktor kalibrasi untuk konversi pixel ke cm
PIXEL_TO_CM = 0.264

ptime = 0
measurements_captured = False
current_measurements = {
    "height": 0,
    "shoulder_width": 0,
    "chest_circumference": 0,
    "waist_circumference": 0,
    "timestamp": "",
}

# Initialize database
db_conn = init_database()

# Initialize countdown variables
start_time = time.time()
countdown_started = False
countdown_duration = 10  # seconds

print("Pengukuran akan dimulai dalam 10 detik")
print("Tekan Q untuk keluar")

while True:
    isTrue, img = capture.read()
    img_rgb = cv.cvtColor(img, cv.COLOR_BGR2RGB)
    result = pose.process(img_rgb)

    if result.pose_landmarks:
        mpDraw.draw_landmarks(img, result.pose_landmarks, mpPose.POSE_CONNECTIONS)
        h, w, c = img.shape
        
        # Menyimpan koordinat landmark
        landmarks = {}
        for id, lm in enumerate(result.pose_landmarks.landmark):
            cx, cy = int(lm.x * w), int(lm.y * h)
            landmarks[id] = (cx, cy)
            
        # Mengukur lebar bahu (shoulder width)
        if 11 in landmarks and 12 in landmarks:
            shoulder_width = calculate_distance(landmarks[11], landmarks[12])
            shoulder_width_cm = round(shoulder_width * PIXEL_TO_CM)
            cv.line(img, landmarks[11], landmarks[12], (0, 255, 0), 2)
            cv.putText(img, f"Shoulder: {shoulder_width_cm}cm", (40, 110), 
                      cv.FONT_HERSHEY_COMPLEX, 0.7, (0, 255, 255), 2)
            current_measurements["shoulder_width"] = shoulder_width_cm

        # Memperkirakan lingkar dada (chest circumference)
        if 11 in landmarks and 12 in landmarks:
            chest_width = calculate_distance(landmarks[11], landmarks[12])
            chest_circumference = estimate_circumference(chest_width * PIXEL_TO_CM)
            chest_cm = round(chest_circumference)
            cv.putText(img, f"Chest: {chest_cm}cm", (40, 150), 
                      cv.FONT_HERSHEY_COMPLEX, 0.7, (0, 255, 255), 2)
            current_measurements["chest_circumference"] = chest_cm

        # Memperkirakan lingkar pinggang (waist circumference)
        if 23 in landmarks and 24 in landmarks:
            waist_width = calculate_distance(landmarks[23], landmarks[24])
            waist_circumference = estimate_circumference(waist_width * PIXEL_TO_CM)
            waist_cm = round(waist_circumference)
            cv.line(img, landmarks[23], landmarks[24], (0, 255, 0), 2)
            cv.putText(img, f"Waist: {waist_cm}cm", (40, 190), 
                      cv.FONT_HERSHEY_COMPLEX, 0.7, (0, 255, 255), 2)
            current_measurements["waist_circumference"] = waist_cm

        # Mengukur tinggi
        cx1, cy1, cx2, cy2 = 0, 0, 0, 0
        for id, lm in enumerate(result.pose_landmarks.landmark):
            if id == 32 or id == 31:
                cx1, cy1 = int(lm.x * w), int(lm.y * h)
                cv.circle(img, (cx1, cy1), 15, (0, 0, 0), cv.FILLED)
            if id == 6:
                cx2, cy2 = int(lm.x * w), int(lm.y * h)
                cy2 += 20
                cv.circle(img, (cx2, cy2), 15, (0, 0, 0), cv.FILLED)

        if cx1 and cy1 and cx2 and cy2:
            d = math.sqrt((cx2 - cx1) ** 2 + (cy2 - cy1) ** 2)
            height_cm = round(d * 0.5)
            cv.putText(img, "Height : ", (40, 70), cv.FONT_HERSHEY_COMPLEX, 1, (0, 255, 255), 2)
            cv.putText(img, str(height_cm), (180, 70), cv.FONT_HERSHEY_DUPLEX, 1, (0, 255, 255), 2)
            cv.putText(img, "cms", (240, 70), cv.FONT_HERSHEY_PLAIN, 2, (0, 255, 255), 2)
            current_measurements["height"] = height_cm

    # Handle countdown and measurement capture
    if not countdown_started:
        countdown_started = True
        start_time = time.time()
    
    elapsed_time = time.time() - start_time
    remaining_time = max(0, countdown_duration - int(elapsed_time))
    
    if remaining_time > 0:
        # Display countdown
        cv.putText(img, f"Capturing in: {remaining_time}s", (40, 400), 
                  cv.FONT_HERSHEY_COMPLEX, 0.7, (0, 255, 255), 2)
    elif not measurements_captured:
        # Capture measurements
        current_measurements["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        save_measurements_to_db(db_conn, current_measurements)
        print(f"\nPengukuran berhasil disimpan ke database")
        print(f"Hasil Pengukuran:")
        print(f"Tinggi: {current_measurements['height']} cm")
        print(f"Lebar Bahu: {current_measurements['shoulder_width']} cm")
        print(f"Lingkar Dada: {current_measurements['chest_circumference']} cm")
        print(f"Lingkar Pinggang: {current_measurements['waist_circumference']} cm")
        measurements_captured = True

    # Display capture status
    if measurements_captured:
        cv.putText(img, "Measurements saved to database!", (40, 440), 
                  cv.FONT_HERSHEY_COMPLEX, 0.7, (0, 255, 0), 2)

    img = cv.resize(img, (700, 500))
    ctime = time.time()
    fps = 1 / (ctime - ptime)
    ptime = ctime
    cv.putText(img, "FPS : ", (40, 30), cv.FONT_HERSHEY_PLAIN, 2, (0, 0, 0), 2)
    cv.putText(img, str(int(fps)), (160, 30), cv.FONT_HERSHEY_PLAIN, 2, (0, 0, 0), 2)
    cv.imshow("Body Measurement", img)

    if cv.waitKey(1) & 0xFF == ord('q'):
        break

db_conn.close()
capture.release()
cv.destroyAllWindows()
