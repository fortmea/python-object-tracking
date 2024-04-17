import tkinter as tk
from tkinter import ttk, filedialog
from PIL import Image, ImageTk
import cv2
import numpy as np

global videoFile
videoFile = ""
    

class FormFrame(ttk.Frame):
    def submit_form(self):
        name = self.name_entry.get()
        
        print("Name:", name)
        self.parent.notebook.select(1)
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent

        tk.Label(self, text="Dataset name:").grid(row=0, column=0, sticky="w")
        self.name_entry = tk.Entry(self)
        self.name_entry.grid(row=0, column=1)

        submit_button = tk.Button(self, text="Submit", command=self.submit_form)
        submit_button.grid(row=3, columnspan=2)

    def submit_form(self):
        name = self.name_entry.get()
        print("Name:", name)
        if(name == ""):
            tk.messagebox.showerror("Error", "Name cannot be empty")
        else:  
            self.parent.select(1)


class SelectVideoFrame(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent

        file_button = tk.Button(self, text="Select File", command=self.select_file)
        file_button.pack(pady=20)   
        next_button = tk.Button(self, text="Next", command=self.next)
        next_button.pack(pady=20)

    def next(self):
        draw_rectangle_frame = VideoFrame(notebook)
        notebook.add(draw_rectangle_frame, text='Draw Rectangle')
        self.parent.select(2)
    def select_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Video Files", "*.mp4;*.avi;*.mkv;*.mov")])
        global videoFile
        videoFile = file_path
        print("Selected File:", file_path)

        

class VideoFrame(ttk.Frame):
    
    #store previous frames to navigate through them
    previous_frames = []
    mouse_down_x = 0
    mouse_down_y = 0
    mouse_up_x = 0
    mouse_up_y = 0
    
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.cap = cv2.VideoCapture(videoFile)
        grabbed, frame = self.cap.read()
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        self.image = Image.fromarray(frame)
        self.previous_frames.append(self.image)
        self.image = self.image.resize((640, 480))
        self.photo = ImageTk.PhotoImage(self.image)
        self.img_label = tk.Label(self, image=self.photo)
        self.img_label.pack(pady=20)
        self.update()
    
    def mouse_down(self, event):
        
        x = self.img_label.winfo_pointerx() - self.img_label.winfo_rootx()
        y = self.img_label.winfo_pointery() - self.img_label.winfo_rooty()
        self.mouse_down_x = x
        self.mouse_down_y = y
        
    
    def mouse_up(self, event):
        #clear image if theres a previous rectangle
        if(self.mouse_up_x != 0 and self.mouse_up_y != 0):
            self.image = self.previous_frames[-1]
            self.image = self.image.resize((640, 480))
            self.photo = ImageTk.PhotoImage(self.image)
            self.img_label.configure(image=self.photo)
            self.img_label.image = self.photo
        
        
        x = self.img_label.winfo_pointerx() - self.img_label.winfo_rootx()
        y = self.img_label.winfo_pointery() - self.img_label.winfo_rooty()
        
        self.mouse_up_x = x
        self.mouse_up_y = y
        
        # Convert the image to a numpy array
        image_array = np.array(self.image)
        
        # Draw rectangle
        cv2.rectangle(image_array, (self.mouse_down_x, self.mouse_down_y), (self.mouse_up_x, self.mouse_up_y), (0, 255, 0), 2)
        
        # Convert the numpy array back to an Image
        self.image = Image.fromarray(image_array)
        
        # Update the photo and label
        self.photo = ImageTk.PhotoImage(self.image)
        self.img_label.configure(image=self.photo)
        self.img_label.image = self.photo
        
        
        
        
        
    
    
    
    def update(self):
        next_button = tk.Button(self, text="Next", command=self.next_frame)
        next_button.pack(pady=20)
        previous_button = tk.Button(self, text="Previous", command=self.previous_frame)
        previous_button.pack(pady=20)
        self.img_label.bind("<Button-1>", self.mouse_down)
        self.img_label.bind("<ButtonRelease-1>", self.mouse_up)
        
    def next_frame(self):
        fps = self.cap.get(cv2.CAP_PROP_FPS)
        frame_skip = int(fps / 2)
        for _ in range(frame_skip):
            self.cap.read()
        grabbed, frame = self.cap.read()
        self.previous_frames.append(self.image)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        self.image = Image.fromarray(frame)
        self.image = self.image.resize((640, 480))
        self.photo = ImageTk.PhotoImage(self.image)
        self.img_label.configure(image=self.photo)
        self.img_label.image = self.photo
        
    def previous_frame(self):
        if(len(self.previous_frames) > 1):
            self.previous_frames.pop()
            self.image = self.previous_frames[-1]
            self.image = self.image.resize((640, 480))
            self.photo = ImageTk.PhotoImage(self.image)
            self.img_label.configure(image=self.photo)
            self.img_label.image = self.photo
        else:
            #red border to indicate that there are no previous frames
            self.img_label.configure(borderwidth=2, relief="solid")
            self.img_label.update()
            self.img_label.after(1000, lambda: self.img_label.configure(borderwidth=0, relief="flat"))
    

root = tk.Tk()
root.title("Prepare Dataset")
style = ttk.Style()

style.layout('TNotebook.Tab', []) # turn off tabs

notebook = ttk.Notebook(root)
notebook.pack(fill='both', expand=True)




form_frame = FormFrame(notebook)
notebook.add(form_frame, text='Form')

select_video_frame = SelectVideoFrame(notebook)
notebook.add(select_video_frame, text='Blank Page')



root.mainloop()