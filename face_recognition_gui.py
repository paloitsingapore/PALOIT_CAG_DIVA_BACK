import base64
import json
import logging
import os
import random
import tkinter as tk
from tkinter import messagebox, ttk

import cv2
import requests
from dotenv import load_dotenv
from PIL import Image, ImageTk

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

load_dotenv()
API_KEY = os.environ.get("API_KEY")
API_ENDPOINT = os.environ.get("API_ENDPOINT_URL")


class FaceRecognitionApp:
    def __init__(self, master):
        logger.info("Initializing FaceRecognitionApp")
        self.master = master
        self.master.title("Face Recognition App")
        self.is_capturing = False
        self.frame = None
        self.action = None
        self.cap = None

        self.display_width = 640
        self.display_height = 480

        if not os.path.exists("users"):
            os.makedirs("users")

        # Frame for indexing face
        self.index_frame = tk.Frame(self.master)
        self.index_frame.pack(pady=10)

        tk.Label(self.index_frame, text="Passenger Name:").grid(
            row=0, column=0, sticky="e"
        )
        self.passenger_name_entry = tk.Entry(self.index_frame)
        self.passenger_name_entry.grid(row=0, column=1, columnspan=2, sticky="we")

        self.has_lounge_access = tk.BooleanVar()
        self.increase_font_size = tk.BooleanVar()
        self.wheelchair_accessibility = tk.BooleanVar()

        ttk.Checkbutton(
            self.index_frame, text="Lounge Access", variable=self.has_lounge_access
        ).grid(row=1, column=0, columnspan=3, sticky="w")
        ttk.Checkbutton(
            self.index_frame,
            text="Increase Font Size",
            variable=self.increase_font_size,
        ).grid(row=2, column=0, columnspan=3, sticky="w")
        ttk.Checkbutton(
            self.index_frame,
            text="Wheelchair Accessibility",
            variable=self.wheelchair_accessibility,
        ).grid(row=3, column=0, columnspan=3, sticky="w")

        # Add language field
        tk.Label(self.index_frame, text="Language:").grid(row=4, column=0, sticky="e")
        self.language_entry = tk.Entry(self.index_frame)
        self.language_entry.grid(row=4, column=1, columnspan=2, sticky="we")

        self.capture_button = tk.Button(
            self.index_frame, text="Capture Face", command=self.capture_face
        )
        self.capture_button.grid(row=5, column=0)

        self.index_button = tk.Button(
            self.index_frame,
            text="Index User",
            command=self.index_user,
            state=tk.DISABLED,
        )
        self.index_button.grid(row=5, column=1)

        # Frame for recognizing face
        self.recognize_frame = tk.Frame(self.master)
        self.recognize_frame.pack(pady=10)

        tk.Button(
            self.recognize_frame,
            text="Capture & Recognize Face",
            command=lambda: self.start_capture("recognize"),
        ).grid(row=0, columnspan=2)

        # Stop capture button
        self.stop_button = tk.Button(
            self.master,
            text="Stop Capture",
            command=self.stop_capture,
            state=tk.DISABLED,
        )
        self.stop_button.pack(pady=10)

        # Canvas for displaying the camera feed
        self.canvas = tk.Canvas(
            self.master, width=self.display_width, height=self.display_height
        )
        self.canvas.pack()

        self.captured_faces = []

        # Add a new button for removing all faces
        self.remove_all_button = tk.Button(
            self.master,
            text="Remove All Faces",
            command=self.remove_all_faces,
            bg="red",
            fg="white",
        )
        self.remove_all_button.pack(pady=10)

    def start_capture(self, action):
        logger.info(f"Starting capture for action: {action}")
        self.action = action
        self.is_capturing = True
        self.stop_button.config(state=tk.NORMAL)
        self.capture_image()

    def stop_capture(self):
        logger.info("Stopping capture")
        self.is_capturing = False
        self.stop_button.config(state=tk.DISABLED)
        if self.cap:
            self.cap.release()
        if self.action == "index":
            self.index_face()
        elif self.action == "recognize":
            self.recognize_face()

    def capture_image(self):
        logger.info("Capturing image")
        self.cap = cv2.VideoCapture(0)

        # Set the capture resolution (you may need to adjust these values)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

        self.update_frame()

    def update_frame(self):
        if self.is_capturing:
            ret, frame = self.cap.read()
            if ret:
                frame = cv2.flip(frame, 1)

                # Resize the frame to fit the display size
                frame = cv2.resize(frame, (self.display_width, self.display_height))

                self.frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                self.photo = ImageTk.PhotoImage(image=Image.fromarray(self.frame))
                self.canvas.create_image(0, 0, image=self.photo, anchor=tk.NW)
                logger.debug("Frame updated")
            else:
                logger.warning("Failed to capture frame")
            self.master.after(10, self.update_frame)
        else:
            if self.cap:
                self.cap.release()
                logger.info("Camera released")

    def capture_face(self):
        logger.info("Capturing face")
        if self.frame is None:
            logger.error("No image captured")
            messagebox.showerror("Error", "No image captured.")
            return

        self.captured_faces.append(self.frame)
        logger.info(f"Face captured. Total faces: {len(self.captured_faces)}")
        messagebox.showinfo(
            "Success", f"Face captured. Total faces: {len(self.captured_faces)}"
        )

        if len(self.captured_faces) > 0:
            self.index_button.config(state=tk.NORMAL)
            logger.debug("Index button enabled")

    def index_user(self):
        logger.info("Indexing user")
        passenger_name = self.passenger_name_entry.get()
        date_of_birth = self.date_of_birth_entry.get()
        if not passenger_name:
            logger.error("Passenger name is empty")
            messagebox.showerror("Error", "Passenger name cannot be empty.")
            return
        if not date_of_birth:
            logger.error("Date of birth is empty")
            messagebox.showerror("Error", "Date of birth cannot be empty.")
            return

        if not self.captured_faces:
            logger.error("No faces captured")
            messagebox.showerror("Error", "No faces captured.")
            return

        user_id = f"user_{passenger_name.replace(' ', '_').lower()}"
        logger.info(f"User ID: {user_id}")

        # Prepare payload
        payload = {
            "userId": user_id,
            "images": [],
            "passengerData": {
                "name": passenger_name,
                "dateOfBirth": date_of_birth,
                "passengerId": f"passenger_{passenger_name.replace(' ', '_').lower()}",
                "changi_app_user_id": f"CAU{random.randint(10000, 99999)}SQ",
                "next_flight_id": f"SQ{random.randint(100, 999)}",
                "has_lounge_access": self.has_lounge_access.get(),
                "accessibilityPreferences": {
                    "increaseFontSize": self.increase_font_size.get(),
                    "wheelchairAccessibility": self.wheelchair_accessibility.get(),
                },
                "language": self.language_entry.get(),
            },
        }

        for i, face in enumerate(self.captured_faces):
            filename = f"{user_id}_face_{i}.jpg"
            image_path = os.path.join("users", filename)
            cv2.imwrite(image_path, cv2.cvtColor(face, cv2.COLOR_RGB2BGR))
            logger.info(f"Saved face image: {image_path}")

            with open(image_path, "rb") as image_file:
                encoded_image = base64.b64encode(image_file.read()).decode("utf-8")
                payload["images"].append(encoded_image)

        # Send payload to backend
        logger.info(f"Sending indexing request to {API_ENDPOINT}/index")
        response = requests.post(f"{API_ENDPOINT}/index", json=payload)

        if response.status_code == 200:
            result = response.json()
            logger.info(f"User indexed successfully. User ID: {result['userId']}")
            messagebox.showinfo(
                "Success", f"User indexed successfully. User ID: {result['userId']}"
            )
        else:
            logger.error(f"Failed to index user: {response.text}")
            messagebox.showerror("Error", f"Failed to index user: {response.text}")

        # Clear captured faces
        self.captured_faces = []
        self.index_button.config(state=tk.DISABLED)
        logger.info("Captured faces cleared and index button disabled")

    def index_face(self):
        logger.info("Indexing face")
        passenger_name = self.passenger_name_entry.get()
        if not passenger_name:
            messagebox.showerror("Error", "Passenger name cannot be empty.")
            return

        if self.frame is None:
            messagebox.showerror("Error", "No image captured.")
            return

        # Create a valid filename from the passenger name
        filename = f"{passenger_name.replace(' ', '_').lower()}.jpg"
        image_path = os.path.join("users", filename)

        # Save the captured image
        cv2.imwrite(image_path, cv2.cvtColor(self.frame, cv2.COLOR_RGB2BGR))

        # Encode image
        with open(image_path, "rb") as image_file:
            encoded_image = base64.b64encode(image_file.read()).decode("utf-8")

        # Prepare payload
        payload = {
            "image": encoded_image,
            "passengerData": {
                "name": passenger_name,
                "passengerId": f"passenger_{passenger_name.replace(' ', '_').lower()}",
                "changi_app_user_id": f"CAU{random.randint(10000, 99999)}SQ",
                "next_flight_id": f"SQ{random.randint(100, 999)}",
                "has_lounge_access": self.has_lounge_access.get(),
                "accessibilityPreferences": {
                    "increaseFontSize": self.increase_font_size.get(),
                    "wheelchairAccessibility": self.wheelchair_accessibility.get(),
                },
                "language": self.language_entry.get(),
            },
        }

        headers = {"x-api-key": API_KEY, "Content-Type": "application/json"}
        response = requests.post(API_ENDPOINT + "index", json=payload, headers=headers)

        if response.status_code == 200:
            result = response.json()
            face_id = result.get("faceId")
            if face_id:
                messagebox.showinfo(
                    "Success", f"Face indexed successfully. Face ID: {face_id}"
                )
            else:
                messagebox.showerror("Error", "Face ID not found in the response.")
        else:
            messagebox.showerror("Error", f"Failed to index face: {response.text}")

    def recognize_face(self):
        logger.info("Recognizing face")
        if self.frame is None:
            logger.error("No image captured")
            messagebox.showerror("Error", "No image captured.")
            return

        # Use a generic name for recognition images
        image_path = os.path.join("users", "recognition_image.jpg")
        cv2.imwrite(image_path, cv2.cvtColor(self.frame, cv2.COLOR_RGB2BGR))
        logger.info(f"Saved recognition image: {image_path}")

        with open(image_path, "rb") as image_file:
            image_bytes = image_file.read()

        image_base64 = base64.b64encode(image_bytes).decode("utf-8")
        payload = {"image": image_base64}

        logger.info(f"Sending recognition request to {API_ENDPOINT}/recognize")
        response = requests.post(f"{API_ENDPOINT}/recognize", json=payload)

        if response.status_code == 200:
            result = response.json()
            logger.info("Face recognized:")
            logger.info(json.dumps(result, indent=2))
            print("Face recognized:")
            print(json.dumps(result, indent=2))
            messagebox.showinfo("Recognition Result", json.dumps(result, indent=2))
        elif response.status_code == 404:
            logger.warning(
                "No matching face found or no passenger data associated with the face"
            )
            messagebox.showinfo(
                "Result",
                "No matching face found or no passenger data associated with the face.",
            )
        else:
            logger.error(f"Error: {response.status_code} - {response.text}")
            messagebox.showerror(
                "Error", f"Error: {response.status_code} - {response.text}"
            )

    def remove_all_faces(self):
        logger.info("Removing all faces")
        if messagebox.askyesno(
            "Confirm",
            "Are you sure you want to remove all registered faces? This action cannot be undone.",
        ):
            try:
                response = requests.post(f"{API_ENDPOINT}/remove_all_faces")
                if response.status_code == 200:
                    logger.info("All faces removed successfully")
                    messagebox.showinfo(
                        "Success", "All registered faces have been removed."
                    )
                else:
                    logger.error(f"Failed to remove faces: {response.text}")
                    messagebox.showerror(
                        "Error", f"Failed to remove faces: {response.text}"
                    )
            except requests.RequestException as e:
                logger.error(f"Error connecting to the server: {str(e)}")
                messagebox.showerror(
                    "Error", f"Error connecting to the server: {str(e)}"
                )


if __name__ == "__main__":
    logger.info("Starting FaceRecognitionApp")
    root = tk.Tk()
    app = FaceRecognitionApp(root)
    root.mainloop()
    logger.info("FaceRecognitionApp closed")
