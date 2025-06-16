from flask import Flask, render_template, Response, redirect, url_for, jsonify, request, flash, send_file
from flask_socketio import SocketIO, emit
from flask_mail import Mail, Message
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from io import BytesIO
import cv2
import mediapipe as mp
import time
import math
import numpy as np
import os
import threading
import pyttsx3
import sys
from datetime import datetime
from dotenv import load_dotenv
import tempfile
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

# Import Supabase functions
from supabase_connection import get_all_measurements, get_latest_measurement, insert_measurement

# Load environment variables
load_dotenv()

# Email configuration
EMAIL_SENDER = os.environ.get('EMAIL_SENDER', 'your_email@gmail.com')
EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD', 'your_app_password')
SMTP_SERVER = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.environ.get('SMTP_PORT', 587))

app = Flask(__name__, 
    template_folder='../../templates',  # Adjust template path
    static_folder='../../static'        # Adjust static path
)

# Email configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key')
app.config['MAIL_SERVER'] = SMTP_SERVER
app.config['MAIL_PORT'] = SMTP_PORT
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = EMAIL_SENDER
app.config['MAIL_PASSWORD'] = EMAIL_PASSWORD
app.config['MAIL_DEFAULT_SENDER'] = EMAIL_SENDER

mail = Mail(app)
socketio = SocketIO(app, 
    cors_allowed_origins="*",
    logger=True,
    engineio_logger=True
)

# Global variables
camera = None
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
cascade_path = os.path.join(os.path.dirname(BASE_DIR), "config", "haarcascade_frontalface_default.xml")
print(f"Loading cascade classifier from: {cascade_path}")  # Debug print

if not os.path.exists(cascade_path):
    raise FileNotFoundError(f"Cascade classifier file not found at: {cascade_path}")

face_detector = cv2.CascadeClassifier(cascade_path)
if face_detector.empty():
    raise ValueError("Error loading cascade classifier")

button_clicked = False
is_measuring_height = False

# Constants for face detection
Known_distance = 230  # centimeter
Known_width = 14.3    # centimeter
GREEN = (0, 255, 0)
RED = (0, 0, 255)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (255, 0, 0)

# Calibration factors for body measurements
HEIGHT_CALIBRATION_FACTOR = 0.48
SHOULDER_CALIBRATION_FACTOR = 1
CHEST_CIRCUMFERENCE_FACTOR = 1.2
WAIST_CIRCUMFERENCE_FACTOR = 1.7
HIP_CIRCUMFERENCE_FACTOR = 2.5

# MediaPipe setup for body detection
mpPose = mp.solutions.pose
mpDraw = mp.solutions.drawing_utils
pose = mpPose.Pose()

# Text-to-speech function
def speak(audio):
    def speak_thread(text):
        engine = pyttsx3.init()
        voices = engine.getProperty('voices')
        engine.setProperty('rate', 150)
        engine.setProperty('voice', voices[0].id)
        engine.say(text)
        engine.runAndWait()
    
    # Start in a separate thread to not block the main thread
    threading.Thread(target=speak_thread, args=(audio,)).start()

# Face width calculation function
def face_data(image):
    face_width = 0
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    faces = face_detector.detectMultiScale(gray_image, 1.3, 5)
    
    for (x, y, h, w) in faces:
        cv2.rectangle(image, (x, y), (x+w, y+h), GREEN, 2)
        face_width = w
        
    return face_width

# Focal length finder function
def Focal_Length_Finder(measured_distance, real_width, width_in_rf_image):

    # finding the focal length
    focal_length = (width_in_rf_image * measured_distance) / real_width
    return focal_length

# Distance estimation function
def Distance_finder(Focal_Length, real_face_width, face_width_in_frame):

    distance = (real_face_width * Focal_Length)/face_width_in_frame

    # return the distance
    return distance

# Face detection generator function (from ex.py)
def generate_face_frames():
    global camera, button_clicked, is_measuring_height
    
    # Load reference image for calibration
    ref_image = cv2.imread("Ref_image.jpg")
    
    # Find if reference image exists, if not check other possible locations
    if ref_image is None:
        # Try alternative paths
        possible_paths = ["./Ref_image.jpg", "./images/Ref_image.jpg", "Ref_image.jpg"]
        for path in possible_paths:
            if os.path.exists(path):
                ref_image = cv2.imread(path)
                if ref_image is not None:
                    print(f"Found reference image at: {path}")
                    break
        
        if ref_image is None:
            print("Error: Reference image not found.")
            return
    
    # Find the face width in the reference image
    ref_image_face_width = face_data(ref_image)
    
    # Calculate focal length
    Focal_length_found = Focal_Length_Finder(
        Known_distance, Known_width, ref_image_face_width)
    
    print(f"Calibrated focal length: {Focal_length_found}")
    
    camera = cv2.VideoCapture(0)
    if not camera.isOpened():
        print("Error: Could not open camera")
        return
    
    while True:
        success, frame = camera.read()
        if not success:
            print("Error: Could not read frame")
            break
        
        # Face distance detection
        face_width_in_frame = face_data(frame)
        
        if face_width_in_frame != 0:
            Distance = Distance_finder(Focal_length_found, Known_width, face_width_in_frame)
            Distance = round(Distance)
            
            # Draw distance indicator
            cv2.line(frame, (30, 30), (230, 30), RED, 32)
            cv2.line(frame, (30, 30), (230, 30), BLACK, 28)
            
            # Check if person is at correct distance (290-310 cm)
            if Distance in range(290, 310):
                cv2.putText(frame, "Perfect distance for measurement!", (30, 90),
                            cv2.FONT_HERSHEY_COMPLEX, 0.6, GREEN, 2)
            elif Distance < 290:
                cv2.putText(frame, "Too close - move back!", (30, 90),
                            cv2.FONT_HERSHEY_COMPLEX, 0.6, RED, 2)
            else:
                cv2.putText(frame, "Too far - move closer!", (30, 90),
                            cv2.FONT_HERSHEY_COMPLEX, 0.6, RED, 2)
            
            # Drawing Text on the screen
            cv2.putText(frame, f"Distance: {Distance} cms", (30, 35),
                       cv2.FONT_HERSHEY_COMPLEX, 0.6, GREEN, 2)
        
        # Check if button was clicked
        if button_clicked or is_measuring_height:
            if camera.isOpened():
                camera.release()
            break
        
        try:
            # Encode the frame as JPEG
            ret, buffer = cv2.imencode('.jpg', frame)
            if not ret:
                print("Error: Could not encode frame")
                continue
            frame = buffer.tobytes()
            
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        except Exception as e:
            print(f"Error in frame processing: {e}")
            continue

# Functions from Body_Detection.py
def calculate_distance(x1, y1, x2, y2):
    return np.sqrt((x2 - x1)**2 + (y2 - y1)**2)

def get_body_measurements(landmarks, img_width, img_height):
    measurements = {}
    
    if not landmarks:
        return None
    
    try:
        # Extract landmarks
        left_shoulder = landmarks.landmark[mpPose.PoseLandmark.LEFT_SHOULDER]
        right_shoulder = landmarks.landmark[mpPose.PoseLandmark.RIGHT_SHOULDER]
        left_hip = landmarks.landmark[mpPose.PoseLandmark.LEFT_HIP]
        right_hip = landmarks.landmark[mpPose.PoseLandmark.RIGHT_HIP]
        
        # Verify visibility
        if (left_shoulder.visibility < 0.5 or right_shoulder.visibility < 0.5 or
            left_hip.visibility < 0.5 or right_hip.visibility < 0.5):
            return None
            
        # Calculate pixel coordinates
        ls_x, ls_y = int(left_shoulder.x * img_width), int(left_shoulder.y * img_height)
        rs_x, rs_y = int(right_shoulder.x * img_width), int(right_shoulder.y * img_height)
        lh_x, lh_y = int(left_hip.x * img_width), int(left_hip.y * img_height)
        rh_x, rh_y = int(right_hip.x * img_width), int(right_hip.y * img_height)
        
        # Calculate measurements
        shoulder_width_px = calculate_distance(ls_x, ls_y, rs_x, rs_y)
        waist_width_px = abs(rh_x - lh_x)
        
        # Convert to centimeters
        shoulder_width_cm = round(shoulder_width_px * HEIGHT_CALIBRATION_FACTOR, 1)
        waist_width_cm = round(waist_width_px * HEIGHT_CALIBRATION_FACTOR, 1)
        
        # Estimate circumferences
        chest_circumference_cm = round(shoulder_width_cm * CHEST_CIRCUMFERENCE_FACTOR, 1)
        waist_circumference_cm = round(waist_width_cm * WAIST_CIRCUMFERENCE_FACTOR, 1)
        
        # Store results
        measurements['shoulder_width'] = shoulder_width_cm
        measurements['chest_circumference'] = chest_circumference_cm
        measurements['waist_circumference'] = waist_circumference_cm
        
        return measurements
        
    except Exception as e:
        print(f"Error calculating body measurements: {e}")
        return None

# Calibration functions
def calibrate_camera():
    global camera, calibration_complete
    
    # Load reference image
    ref_image = cv2.imread("Ref_image.jpg")
    if ref_image is None:
        # Try alternative paths
        possible_paths = ["./Ref_image.jpg", "./images/Ref_image.jpg", "Ref_image.jpg"]
        for path in possible_paths:
            if os.path.exists(path):
                ref_image = cv2.imread(path)
                if ref_image is not None:
                    print(f"Found reference image at: {path}")
                    break
    
    if ref_image is None:
        print("Error: Reference image not found.")
        return None
    
    # Find face width in reference image
    ref_image_face_width = face_data(ref_image)
    
    # Calculate focal length
    focal_length = Focal_Length_Finder(Known_distance, Known_width, ref_image_face_width)
    print(f"Calibrated focal length: {focal_length}")
    
    return focal_length

# Body detection generator function
def generate_body_frames():
    global camera
    
    # Initialize camera if not already open
    if camera is None or not camera.isOpened():
        camera = cv2.VideoCapture(0)
    
    ptime = 0
    measurements_captured = False
    current_measurements = {
        "height": 0,
        "shoulder_width": 0,
        "chest_circumference": 0,
        "waist_circumference": 0,
        "timestamp": "",
    }
    
    # Initialize countdown variables
    start_time = time.time()
    countdown_started = False
    countdown_duration = 8  # seconds - to match user's code
    
    while True:
        success, img = camera.read()
        if not success:
            break
            
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        result = pose.process(img_rgb)

        if result.pose_landmarks:
            mpDraw.draw_landmarks(img, result.pose_landmarks, mpPose.POSE_CONNECTIONS)
            h, w, c = img.shape
            
            # Get body measurements using our function
            body_measurements = get_body_measurements(result.pose_landmarks, w, h)
            
            if body_measurements:
                current_measurements["shoulder_width"] = body_measurements["shoulder_width"]
                current_measurements["chest_circumference"] = body_measurements["chest_circumference"]
                current_measurements["waist_circumference"] = body_measurements["waist_circumference"]
                
                # Display measurements on frame
                cv2.putText(img, f"Shoulder: {body_measurements['shoulder_width']}cm", (40, 110), 
                          cv2.FONT_HERSHEY_COMPLEX, 0.7, (0, 255, 255), 2)
                cv2.putText(img, f"Chest: {body_measurements['chest_circumference']}cm", (40, 150), 
                          cv2.FONT_HERSHEY_COMPLEX, 0.7, (0, 255, 255), 2)
                cv2.putText(img, f"Waist: {body_measurements['waist_circumference']}cm", (40, 190), 
                          cv2.FONT_HERSHEY_COMPLEX, 0.7, (0, 255, 255), 2)
            
            # Measure height
            cx1, cy1, cx2, cy2 = 0, 0, 0, 0
            for id, lm in enumerate(result.pose_landmarks.landmark):
                if id == 32 or id == 31:  # Left/Right ankle
                    cx1, cy1 = int(lm.x * w), int(lm.y * h)
                    cv2.circle(img, (cx1, cy1), 15, (0, 0, 0), cv2.FILLED)
                if id == 6:  # Nose
                    cx2, cy2 = int(lm.x * w), int(lm.y * h)
                    cy2 += 20  # Adjust for top of head
                    cv2.circle(img, (cx2, cy2), 15, (0, 0, 0), cv2.FILLED)

            if cx1 and cy1 and cx2 and cy2:
                d = math.sqrt((cx2 - cx1) ** 2 + (cy2 - cy1) ** 2)
                height_cm = round(d * HEIGHT_CALIBRATION_FACTOR)
                cv2.putText(img, "Height : ", (40, 70), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 255, 255), 2)
                cv2.putText(img, str(height_cm), (180, 70), cv2.FONT_HERSHEY_DUPLEX, 1, (0, 255, 255), 2)
                cv2.putText(img, "cms", (240, 70), cv2.FONT_HERSHEY_PLAIN, 2, (0, 255, 255), 2)
                current_measurements["height"] = height_cm

            # Handle countdown and measurement capture
            if not countdown_started:
                countdown_started = True
                start_time = time.time()
            
            elapsed_time = time.time() - start_time
            remaining_time = max(0, countdown_duration - int(elapsed_time))
            
            if remaining_time > 0:
                # Display countdown
                cv2.putText(img, f"Capturing in: {remaining_time}s", (40, 400), 
                          cv2.FONT_HERSHEY_COMPLEX, 0.7, (0, 255, 255), 2)
            elif not measurements_captured:
                # Capture measurements and insert into Supabase
                current_measurements["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # Insert into Supabase instead of SQLite
                result = insert_measurement(current_measurements)
                measurements_captured = True
                speak("Pengukuran selesai")  # Add voice notification in Indonesian

            # Display capture status
            if measurements_captured:
                cv2.putText(img, "Measurements saved to database!", (40, 440), 
                          cv2.FONT_HERSHEY_COMPLEX, 0.7, (0, 255, 0), 2)

        img = cv2.resize(img, (700, 500))
        ctime = time.time()
        fps = 1 / (ctime - ptime)
        ptime = ctime
        cv2.putText(img, "FPS : ", (40, 30), cv2.FONT_HERSHEY_PLAIN, 2, (0, 0, 0), 2)
        cv2.putText(img, str(int(fps)), (160, 30), cv2.FONT_HERSHEY_PLAIN, 2, (0, 0, 0), 2)
        
        # Encode the frame as JPEG
        ret, buffer = cv2.imencode('.jpg', img)
        frame = buffer.tobytes()
        
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    # Clean up
    if camera.isOpened():
        camera.release()

# Socket.IO event handlers
@socketio.on('connect')
def handle_connect():
    print('Client connected')
    emit('message', {'type': 'connection', 'data': 'Connected successfully'})

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@socketio.on('error')
def handle_error(error):
    print(f'Socket.IO error: {error}')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/face_detection')
def face_detection():
    global is_measuring_height, button_clicked
    button_clicked = False
    is_measuring_height = False
    return render_template('face_detection.html')

@app.route('/body_detection')
def body_detection():
    global is_measuring_height
    is_measuring_height = True
    speak("Starting body measurement")
    latest_measurement = get_latest_measurement()
    return render_template('body_detection.html', last_measurement=latest_measurement)

@app.route('/measurements')
def measurements():
    all_measurements = get_all_measurements()
    latest_measurement = get_latest_measurement()
    return render_template('measurements.html', 
                         measurements=all_measurements,
                         latest=latest_measurement)

@app.route('/api/measurements')
def api_measurements():
    measurements = get_all_measurements()
    return jsonify(measurements)

@app.route('/api/latest-measurement')
def api_latest_measurement():
    measurement = get_latest_measurement()
    return jsonify(measurement if measurement else {})

@app.route('/video_feed_face')
def video_feed_face():
    return Response(generate_face_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/video_feed_body')
def video_feed_body():
    return Response(generate_body_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/switch_to_body')
def switch_to_body():
    global button_clicked
    button_clicked = True
    return redirect(url_for('body_detection'))

@app.route('/switch_to_face')
def switch_to_face():
    return redirect(url_for('face_detection'))

def generate_measurement_pdf(measurement_data):
    """Generate a PDF with measurement results"""
    # Create a temporary file
    temp_file = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
    pdf_path = temp_file.name
    temp_file.close()
    
    # Create PDF with measurement data
    doc = SimpleDocTemplate(pdf_path, pagesize=letter)
    styles = getSampleStyleSheet()
    
    # Build content
    content = []
    content.append(Paragraph("Measurement Results", styles['Heading1']))
    
    # Create table with measurements
    data = [
        ["Measurement", "Value (cm)"],
        ["Height", f"{measurement_data['height']}"],
        ["Shoulder Width", f"{measurement_data['shoulder_width']}"],
        ["Chest Circumference", f"{measurement_data['chest_circumference']}"],
        ["Waist Circumference", f"{measurement_data['waist_circumference']}"]
    ]
    
    table = Table(data)
    table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BACKGROUND', (0, 0), (1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (1, 0), colors.whitesmoke)
    ]))
    
    content.append(table)
    doc.build(content)
    
    return pdf_path

@app.route('/email_form')
def email_form():
    measurements = get_latest_measurement()
    if not measurements:
        flash('No measurements available', 'error')
        return redirect(url_for('measurements'))
    return render_template('email_form.html', measurements=measurements)

@app.route('/send_measurements', methods=['POST'])
def send_measurements():
    email = request.form.get('email')
    name = request.form.get('name', 'User')
    
    if not email:
        flash('Please provide an email address', 'error')
        return redirect(url_for('email_form'))
    
    measurements = get_latest_measurement()
    if not measurements:
        flash('No measurements available', 'error')
        return redirect(url_for('email_form'))
    
    try:
        # Generate PDF
        pdf_path = generate_measurement_pdf(measurements)
        
        try:
            # Create email message
            msg = MIMEMultipart()
            msg['From'] = EMAIL_SENDER
            msg['To'] = email
            msg['Subject'] = "Your Body Measurement Results"
            
            # Add body text
            body = f"""
Hello {name},

Thank you for using our Body Measurement System.

Your measurement results:
- Height: {measurements['height']} cm
- Shoulder Width: {measurements['shoulder_width']} cm
- Chest Circumference: {measurements['chest_circumference']} cm
- Waist Circumference: {measurements['waist_circumference']} cm

Measured on: {measurements['timestamp']}

Your measurement results are also attached as a PDF.

Best regards,
Body Measurement System
            """
            msg.attach(MIMEText(body, 'plain'))
            
            # Attach PDF
            with open(pdf_path, 'rb') as file:
                attachment = MIMEApplication(file.read(), _subtype='pdf')
                attachment.add_header('Content-Disposition', 'attachment', filename='measurement_results.pdf')
                msg.attach(attachment)
            
            # Send email via SMTP
            try:
                print(f"Connecting to {SMTP_SERVER}:{SMTP_PORT}")
                server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
                server.set_debuglevel(1)  # Enable debugging
                server.ehlo()  # Identify to SMTP server
                if server.has_extn('STARTTLS'):  # Check if TLS available
                    server.starttls()
                    server.ehlo()  # Re-identify over TLS connection
                print(f"Logging in with {EMAIL_SENDER}")
                server.login(EMAIL_SENDER, EMAIL_PASSWORD)
                print("Sending message")
                server.send_message(msg)
                print("Closing connection")
                server.quit()
                print("Email sent successfully")
            except Exception as smtp_error:
                print(f"Detailed SMTP error: {smtp_error}")
                raise
            
            os.unlink(pdf_path)  # Clean up temporary file
            
            flash('Measurement results sent successfully to your email!', 'success')
            return redirect(url_for('email_form'))
            
        except Exception as e:
            # If email fails, still provide the PDF as a download
            save_dir = os.path.join(os.path.dirname(app.root_path), 'static', 'downloads')
            os.makedirs(save_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"measurements_{timestamp}.pdf"
            output_path = os.path.join(save_dir, output_filename)
            
            import shutil
            shutil.copy2(pdf_path, output_path)
            os.unlink(pdf_path)
            
            download_url = url_for('static', filename=f'downloads/{output_filename}')
            
            flash(f'Email could not be sent: {str(e)}. <a href="{download_url}" download>Click here to download your PDF</a>', 'warning')
            return redirect(url_for('email_form'))
        
    except Exception as e:
        flash(f'Error generating PDF: {str(e)}', 'error')
        return redirect(url_for('email_form'))

if __name__ == '__main__':
    app.run(debug=True) 