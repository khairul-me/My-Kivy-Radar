import kivy
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.graphics import Line, Color, Ellipse, Rectangle
from kivy.clock import Clock
from kivy.core.text import Label as CoreLabel
import serial
import math

class RadarWidget(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Open the serial port (Make sure to adjust this based on your setup)
        self.serial_port = serial.Serial('COM3', 9600)  # Adjust COM port accordingly
        self.angle = 0
        self.distance = 0
        self.detected_objects = []  # To store detected objects (angle, distance)
        self.max_distance = 40  # 40 cm range
        self.bind(size=self.update_radar, pos=self.update_radar)

        # Schedule data reading and radar sweep
        Clock.schedule_interval(self.read_serial_data, 0.1)  # Read serial data every 100 ms
        Clock.schedule_interval(self.update_sweep_line, 0.05)  # Rotating sweep line every 50 ms
        Clock.schedule_interval(self.update_radar, 1.0 / 30)  # Update radar display at 30 FPS

    def read_serial_data(self, dt):
        """Read data from the serial port."""
        if self.serial_port.in_waiting > 0:
            data = self.serial_port.readline().decode('utf-8').strip()

            # Handle the "Angle: X degrees, Distance: Y cm" format
            if 'Angle' in data and 'Distance' in data:
                try:
                    # Extract angle and distance from the string
                    angle_str = data.split(',')[0]
                    distance_str = data.split(',')[1]

                    # Remove the text parts to isolate the numeric values
                    angle = int(angle_str.replace('Angle:', '').replace('degrees', '').strip())
                    distance = int(distance_str.replace('Distance:', '').replace('cm', '').strip())

                    print(f"Parsed data - Angle: {angle}, Distance: {distance}")  # Print for debugging

                    # Only add detected objects within a valid range
                    if 0 < distance <= self.max_distance:
                        self.distance = distance  # Update distance for display
                        self.detected_objects.append((angle, distance))  # Add object if in valid range
                    else:
                        print(f"Out of range data received: {distance} cm")  # Log out-of-range values
                except ValueError:
                    print(f"Error parsing data: {data}")  # Log invalid data

    def update_sweep_line(self, dt):
        """Update the sweep line's angle for the radar sweep."""
        self.angle = (self.angle + 2) % 180  # Increment the angle for the sweeping line, looping back to 0 after 180°

    def update_radar(self, *args):
        """Update radar display."""
        self.canvas.clear()
        with self.canvas:
            self.draw_radar()
            self.draw_line()
            self.draw_objects()  # Draw the red dot for the detected object
            self.draw_labels()

    def draw_radar(self):
        """Draws the radar arcs and angle lines."""
        cx, cy = self.center
        radius = min(self.size) * 0.4  # Reduce radius to fit inside the window
        Color(0.38, 0.96, 0.12)  # Green color like the Processing sketch

        # Drawing arcs for distance (like the Processing radar arcs)
        for factor, label in zip([0.25, 0.5, 0.75, 1], ["10cm", "20cm", "30cm", "40cm"]):
            Line(circle=(cx, cy, radius * factor), width=2)
            self.draw_text(label, cx + (radius * factor), cy - 20)

        # Drawing angle lines at 0°, 30°, 60°, 90°, 120°, 150°, 180°
        for angle in [0, 30, 60, 90, 120, 150, 180]:
            radians_angle = math.radians(angle)
            Line(points=[cx, cy, cx + radius * math.cos(radians_angle), 
                         cy + radius * math.sin(radians_angle)], width=1)

    def draw_line(self):
        """Draw the sweeping radar line."""
        cx, cy = self.center
        radius = min(self.size) * 0.4  # Reduce radius to fit inside the window
        Color(0.12, 0.96, 0.24)  # Green color like in Processing
        radians_angle = math.radians(self.angle)
        Line(points=[cx, cy, cx + radius * math.cos(radians_angle), 
                     cy + radius * math.sin(radians_angle)], width=2)

    def draw_objects(self):
        """Draws detected objects as red dots based on recorded angle and distance."""
        cx, cy = self.center
        radius = min(self.size) * 0.4  # Reduce radius to fit inside the window
        Color(1, 0, 0)  # Red color for detected objects

        # Cluster objects that are close to each other to avoid clutter
        unique_objects = {}
        for obj in self.detected_objects:
            obj_angle, obj_distance = obj
            if obj_angle not in unique_objects or obj_distance < unique_objects[obj_angle]:
                unique_objects[obj_angle] = obj_distance  # Keep the closest object at each angle

        for obj_angle, obj_distance in unique_objects.items():
            rad = math.radians(obj_angle)
            obj_x = cx + math.cos(rad) * (obj_distance * radius / self.max_distance)  # Scale distance
            obj_y = cy + math.sin(rad) * (obj_distance * radius / self.max_distance)

            # Print calculated position for debugging
            print(f"Drawing object at: ({obj_x}, {obj_y})")

            # Draw a smaller red circle for each object (Reduced size to 5x5)
            Ellipse(pos=(obj_x - 2.5, obj_y - 2.5), size=(5, 5))

    def draw_labels(self):
        """Draws the text labels for distances and angles."""
        cx, cy = self.center
        radius = min(self.size) * 0.4  # Reduce radius to fit inside the window

        # Distance labels (10cm, 20cm, 30cm, 40cm)
        for i, dist_label in enumerate(["10cm", "20cm", "30cm", "40cm"], start=1):
            self.draw_text(dist_label, cx + (radius * i / 4), cy - 20)

        # Drawing angle and distance at the bottom of the screen
        self.draw_text(f"Angle: {self.angle}°", cx - radius * 0.8, cy - radius * 1.2)
        if self.distance > self.max_distance:
            self.draw_text(f"Distance: Out of Range", cx, cy - radius * 1.2)
        else:
            self.draw_text(f"Distance: {self.distance} cm", cx, cy - radius * 1.2)

        # Drawing the angle labels on the arc (0°, 30°, 60°, 90°, etc.)
        for angle, label_pos_factor in [(0, 1.1), (30, 1.1), (60, 1.1), (90, 1.0), (120, 1.1), (150, 1.1), (180, 1.1)]:
            radians_angle = math.radians(angle)
            label_x = cx + radius * math.cos(radians_angle) * label_pos_factor
            label_y = cy + radius * math.sin(radians_angle) * label_pos_factor
            self.draw_text(f"{angle}°", label_x, label_y)

    def draw_text(self, text, x, y):
        """Helper function to render text."""
        label = CoreLabel(text=text, font_size=20)
        label.refresh()
        self.canvas.add(Rectangle(texture=label.texture, pos=(x, y), size=label.texture.size))


class RadarApp(App):
    def build(self):
        return RadarWidget()


if __name__ == '__main__':
    RadarApp().run()
