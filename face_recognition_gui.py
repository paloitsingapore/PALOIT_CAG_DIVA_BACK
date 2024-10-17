import base64
import json
import logging
import os
import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk

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


# Define the personna list here
class FaceRecognitionApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Face Recognition App")
        logger.info("Initializing FaceRecognitionApp")

        self.is_capturing = False
        self.frame = None
        self.cap = None
        self.display_width = 640
        self.display_height = 480

        # Define the personna list here
        self.personna = personna = [
            [
                {
                    "id": "SQ001-2024-08-15",
                    "flightno": "SQ001",
                    "scheduled_date": "2024-08-15",
                    "scheduled_time": "1150",
                    "terminal": "3",
                    "display_terminal": "3",
                    "aircraft_type": "A320",
                    "origin": "SYD",
                    "display_time": "1155",
                    "display_date": "2024-08-15",
                    "display_belt": "",
                    "firstbag_time": "1230",
                    "lastbag_time": "1245",
                    "display_gate": "D46",
                    "display_parkingstand": "D46",
                    "flight_status": "Landed",
                },
                {
                    "Passenger Name": "Albert",
                    "Date of Birth": "2000-05-01",
                    "Language": "English",
                    "Lounge Name": "SilverKris Business Class Lounge",
                    "passengerId": "passenger_albert",
                    "changi_app_user_id": "CAU12345SQ",
                    "next_flight_id": "SQ123",
                    "has_lounge_access": True,
                    "accessibilityPreferences": {
                        "increaseFontSize": False,
                        "wheelchairAccessibility": False,
                    },
                    "airline": "SQ",
                    "gate": "D46",
                    "flight_time": "1155",
                },
            ],
            [
                {
                    "id": "SQ002-2024-08-15",
                    "flightno": "SQ002",
                    "scheduled_date": "2024-08-15",
                    "scheduled_time": "1150",
                    "terminal": "3",
                    "display_terminal": "3",
                    "aircraft_type": "A350",
                    "origin": "SYD",
                    "display_time": "1155",
                    "display_date": "2024-08-15",
                    "display_belt": "",
                    "firstbag_time": "1230",
                    "lastbag_time": "1245",
                    "display_gate": "D47",
                    "display_parkingstand": "D47",
                    "flight_status": "Landed",
                },
                {
                    "Passenger Name": "Beatrice",
                    "Date of Birth": "1985-12-15",
                    "Language": "Mandarin",
                    "Lounge Name": "KrisFlyer Gold Lounge",
                    "passengerId": "passenger_beatrice",
                    "changi_app_user_id": "CAU67890SQ",
                    "next_flight_id": "SQ456",
                    "has_lounge_access": True,
                    "accessibilityPreferences": {
                        "increaseFontSize": True,
                        "wheelchairAccessibility": False,
                    },
                    "airline": "SQ",
                    "gate": "D47",
                    "flight_time": "1155",
                },
            ],
            [
                {
                    "id": "SQ003-2024-08-15",
                    "flightno": "SQ003",
                    "scheduled_date": "2024-08-15",
                    "scheduled_time": "1150",
                    "terminal": "3",
                    "display_terminal": "3",
                    "aircraft_type": "A380",
                    "origin": "SYD",
                    "display_time": "1155",
                    "display_date": "2024-08-15",
                    "display_belt": "",
                    "firstbag_time": "1230",
                    "lastbag_time": "1245",
                    "display_gate": "D48",
                    "display_parkingstand": "D48",
                    "flight_status": "Landed",
                },
                {
                    "Passenger Name": "Charlie",
                    "Date of Birth": "1970-03-22",
                    "Language": "French",
                    "Lounge Name": "The Private Room",
                    "passengerId": "passenger_charlie",
                    "changi_app_user_id": "CAU24680SQ",
                    "next_flight_id": "SQ789",
                    "has_lounge_access": True,
                    "accessibilityPreferences": {
                        "increaseFontSize": False,
                        "wheelchairAccessibility": True,
                    },
                    "airline": "SQ",
                    "gate": "D48",
                    "flight_time": "1155",
                },
            ],
        ]

        # Main frame
        self.main_frame = ttk.Frame(self.master, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Persona selection
        tk.Label(self.main_frame, text="Select Persona:").grid(
            row=0, column=0, sticky="w", pady=(0, 10)
        )
        self.persona_var = tk.StringVar()
        self.persona_dropdown = ttk.Combobox(
            self.main_frame,
            textvariable=self.persona_var,
            values=[f"Persona {i+1}" for i in range(len(self.personna))],
        )
        self.persona_dropdown.grid(row=0, column=1, sticky="we", pady=(0, 10))
        self.persona_dropdown.bind("<<ComboboxSelected>>", self.update_data_displays)

        # Frame for displaying persona data
        self.persona_frame = ttk.Frame(self.main_frame)
        self.persona_frame.grid(row=1, column=0, columnspan=2, sticky="nsew")

        # Flight data display
        tk.Label(self.persona_frame, text="Flight Data:").grid(
            row=0, column=0, sticky="w"
        )
        self.flight_data_display = scrolledtext.ScrolledText(
            self.persona_frame, height=10, width=80
        )
        self.flight_data_display.grid(row=1, column=0, pady=(0, 10))

        # Passenger data display
        tk.Label(self.persona_frame, text="Passenger Data:").grid(
            row=2, column=0, sticky="w"
        )
        self.passenger_data_display = scrolledtext.ScrolledText(
            self.persona_frame, height=10, width=80
        )
        self.passenger_data_display.grid(row=3, column=0)

        # Camera control buttons
        self.camera_frame = ttk.Frame(self.main_frame)
        self.camera_frame.grid(
            row=2, column=0, columnspan=2, sticky="nsew", pady=(10, 0)
        )

        self.start_camera_button = ttk.Button(
            self.camera_frame, text="1) Init", command=self.start_capture
        )
        self.start_camera_button.grid(row=0, column=0, padx=5)

        self.capture_button = ttk.Button(
            self.camera_frame,
            text="2) Capture 2-3 Images",
            command=self.capture_face,
            state=tk.DISABLED,
        )
        self.capture_button.grid(row=0, column=1, padx=5)

        self.index_button = ttk.Button(
            self.camera_frame,
            text="3) Save",
            command=self.index_face,
            state=tk.DISABLED,
        )
        self.index_button.grid(row=0, column=2, padx=5)

        self.recognize_button = ttk.Button(
            self.camera_frame,
            text="Recognize Face",
            command=self.recognize_face,
            state=tk.DISABLED,
        )
        self.recognize_button.grid(row=0, column=3, padx=5)

        # Canvas for displaying the camera feed
        self.canvas = tk.Canvas(
            self.main_frame, width=self.display_width, height=self.display_height
        )
        self.canvas.grid(row=3, column=0, columnspan=2, pady=10)

        # Configure grid weights
        self.main_frame.columnconfigure(1, weight=1)
        self.main_frame.rowconfigure(3, weight=1)

        # Initialize captured faces
        self.captured_faces = []

    def update_data_displays(self, event):
        selected_value = self.persona_var.get()
        if not selected_value:
            return  # Exit the method if no value is selected

        try:
            selected_persona = int(selected_value.split()[-1]) - 1
        except (ValueError, IndexError):
            messagebox.showerror("Error", "Invalid persona selection")
            return

        if 0 <= selected_persona < len(self.personna):
            flight_data = self.personna[selected_persona][0]
            passenger_data = self.personna[selected_persona][1]

            # Display the flight data
            self.flight_data_display.delete("1.0", tk.END)
            self.flight_data_display.insert(tk.END, json.dumps(flight_data, indent=2))

            # Display the passenger data
            self.passenger_data_display.delete("1.0", tk.END)
            self.passenger_data_display.insert(
                tk.END, json.dumps(passenger_data, indent=2)
            )
        else:
            messagebox.showerror("Error", "Invalid persona selection")

    def start_capture(self):
        logger.info("Starting capture")
        self.is_capturing = True
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
        self.update_frame()
        self.start_camera_button.config(state=tk.DISABLED)
        self.capture_button.config(state=tk.NORMAL)
        self.recognize_button.config(state=tk.NORMAL)  # Enable recognize button

    def update_frame(self):
        if self.is_capturing:
            ret, frame = self.cap.read()
            if ret:
                frame = cv2.flip(frame, 1)
                frame = cv2.resize(frame, (self.display_width, self.display_height))
                self.frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                self.photo = ImageTk.PhotoImage(image=Image.fromarray(self.frame))
                self.canvas.create_image(0, 0, image=self.photo, anchor=tk.NW)
            self.master.after(10, self.update_frame)

    def capture_face(self):
        logger.info("Attempting to capture face")
        if self.frame is None:
            logger.error("No frame available for capture")
            messagebox.showerror("Error", "No frame available for capture.")
            return

        if self.frame.size == 0:
            logger.error("Frame is empty")
            messagebox.showerror("Error", "Captured frame is empty.")
            return

        # Create a copy of the frame to avoid modifying the original
        captured_frame = self.frame.copy()

        # Convert the frame from RGB to BGR (OpenCV format)
        captured_frame_bgr = cv2.cvtColor(captured_frame, cv2.COLOR_RGB2BGR)

        # Append the BGR frame to the captured_faces list
        self.captured_faces.append(captured_frame_bgr)

        logger.info(
            f"Face captured successfully. Total faces: {len(self.captured_faces)}"
        )
        logger.debug(f"Captured frame shape: {captured_frame_bgr.shape}")
        messagebox.showinfo(
            "Success", f"Face captured. Total faces: {len(self.captured_faces)}"
        )

        if len(self.captured_faces) > 0:
            self.index_button.config(state=tk.NORMAL)
            logger.debug("Index button enabled")

    def index_face(self):
        logger.info("Indexing face")
        if not self.captured_faces:
            messagebox.showerror("Error", "No faces captured.")
            return

        selected_value = self.persona_var.get()
        if not selected_value:
            messagebox.showerror("Error", "No persona selected.")
            return

        try:
            selected_persona = int(selected_value.split()[-1]) - 1
        except (ValueError, IndexError):
            messagebox.showerror("Error", "Invalid persona selection")
            return

        if 0 <= selected_persona < len(self.personna):
            flight_data = self.personna[selected_persona][0]
            passenger_data = self.personna[selected_persona][1]
        else:
            messagebox.showerror("Error", "Invalid persona selection")
            return

        # Convert all captured faces to base64
        images_base64 = []
        for face in self.captured_faces:
            # face is already in BGR format, so we don't need to convert it
            _, buffer = cv2.imencode(".jpg", face)
            images_base64.append(base64.b64encode(buffer).decode("utf-8"))

        # Prepare payload
        payload = {
            "userId": passenger_data["passengerId"],
            "images": images_base64,
            "passengerData": {
                "name": passenger_data["Passenger Name"],
                "dateOfBirth": passenger_data["Date of Birth"],
                "changi_app_user_id": passenger_data["changi_app_user_id"],
                "next_flight_id": passenger_data["next_flight_id"],
                "has_lounge_access": passenger_data["has_lounge_access"],
                "accessibilityPreferences": passenger_data["accessibilityPreferences"],
                "language": passenger_data["Language"],
                "airline": passenger_data["airline"],
                "lounge_name": passenger_data["Lounge Name"],
                "gate": passenger_data["gate"],
                "flight_time": passenger_data["flight_time"],
                "flightno": flight_data["flightno"],
                "scheduled_date": flight_data["scheduled_date"],
                "terminal": flight_data["terminal"],
                "aircraft_type": flight_data["aircraft_type"],
                "origin": flight_data["origin"],
                "display_date": flight_data["display_date"],
                "firstbag_time": flight_data["firstbag_time"],
                "lastbag_time": flight_data["lastbag_time"],
                "flight_status": flight_data["flight_status"],
            },
        }

        # Log the payload (excluding the image data for brevity)
        payload_log = payload.copy()
        payload_log["images"] = [
            f"<base64_encoded_image_{i}>" for i in range(len(images_base64))
        ]
        logger.info(f"Payload being sent: {json.dumps(payload_log, indent=2)}")

        headers = {"x-api-key": API_KEY, "Content-Type": "application/json"}

        try:
            response = requests.post(
                f"{API_ENDPOINT}/index", json=payload, headers=headers
            )
            if response.status_code == 200:
                result = response.json()
                logger.info("Faces indexed successfully:")
                logger.info(json.dumps(result, indent=2))
                messagebox.showinfo(
                    "Indexing Result",
                    f"{len(self.captured_faces)} faces indexed successfully.",
                )
                # Clear captured faces after successful indexing
                self.captured_faces = []
                self.index_button.config(state=tk.DISABLED)
            else:
                logger.error(f"Error: {response.status_code} - {response.text}")
                messagebox.showerror(
                    "Error", f"Error: {response.status_code} - {response.text}"
                )
        except requests.RequestException as e:
            logger.error(f"Error connecting to the server: {str(e)}")
            messagebox.showerror("Error", f"Error connecting to the server: {str(e)}")

    def recognize_face(self):
        logger.info("Recognizing face")
        if self.frame is None:
            logger.error("No image captured")
            messagebox.showerror("Error", "No image captured.")
            return

        # Use a generic name for recognition images
        image_path = os.path.join("users", "recognition_image.jpg")

        # Save the image in high quality
        cv2.imwrite(
            image_path,
            cv2.cvtColor(self.frame, cv2.COLOR_RGB2BGR),
            [cv2.IMWRITE_JPEG_QUALITY, 100],
        )
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
                headers = {"x-api-key": API_KEY, "Content-Type": "application/json"}
                response = requests.post(
                    f"{API_ENDPOINT}/remove_all_faces", headers=headers
                )
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


def main():
    root = tk.Tk()
    app = FaceRecognitionApp(root)
    root.mainloop()


if __name__ == "__main__":
    logger.info("Starting FaceRecognitionApp")
    main()
    logger.info("FaceRecognitionApp closed")
