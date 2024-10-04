import base64
import json
import os
import random
import tkinter as tk
from tkinter import messagebox, ttk

import cv2
import requests
from dotenv import load_dotenv
from PIL import Image, ImageTk

load_dotenv()
API_KEY = os.environ.get("API_KEY")
API_ENDPOINT = os.environ.get("API_ENDPOINT_URL")


class FaceRecognitionApp:
    def __init__(self, master):
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
        self.accessibility_needs = tk.BooleanVar()

        ttk.Checkbutton(
            self.index_frame, text="Lounge Access", variable=self.has_lounge_access
        ).grid(row=1, column=0, columnspan=3, sticky="w")
        ttk.Checkbutton(
            self.index_frame,
            text="Accessibility Needs",
            variable=self.accessibility_needs,
        ).grid(row=2, column=0, columnspan=3, sticky="w")

        tk.Button(
            self.index_frame,
            text="Capture & Index Face",
            command=lambda: self.start_capture("index"),
        ).grid(row=3, column=0, columnspan=3)

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

    def start_capture(self, action):
        self.action = action
        self.is_capturing = True
        self.stop_button.config(state=tk.NORMAL)
        self.capture_image()

    def stop_capture(self):
        self.is_capturing = False
        self.stop_button.config(state=tk.DISABLED)
        if self.cap:
            self.cap.release()
        if self.action == "index":
            self.index_face()
        elif self.action == "recognize":
            self.recognize_face()

    def capture_image(self):
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

            self.master.after(10, self.update_frame)
        else:
            if self.cap:
                self.cap.release()

    def index_face(self):
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
                "accessibility_needs": self.accessibility_needs.get(),
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
        if self.frame is None:
            messagebox.showerror("Error", "No image captured.")
            return

        # Use a generic name for recognition images
        image_path = os.path.join("users", "recognition_image.jpg")
        cv2.imwrite(image_path, cv2.cvtColor(self.frame, cv2.COLOR_RGB2BGR))

        with open(image_path, "rb") as image_file:
            image_bytes = image_file.read()

        image_base64 = base64.b64encode(image_bytes).decode("utf-8")
        payload = {"image": image_base64}

        response = requests.post(f"{API_ENDPOINT}/recognize", json=payload)

        if response.status_code == 200:
            result = response.json()
            print("Face recognized:")
            print(json.dumps(result, indent=2))
            messagebox.showinfo("Recognition Result", json.dumps(result, indent=2))
        elif response.status_code == 404:
            messagebox.showinfo(
                "Result",
                "No matching face found or no passenger data associated with the face.",
            )
        else:
            messagebox.showerror(
                "Error", f"Error: {response.status_code} - {response.text}"
            )


if __name__ == "__main__":
    root = tk.Tk()
    app = FaceRecognitionApp(root)
    root.mainloop()
