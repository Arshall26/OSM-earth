# -*- coding: utf-8 -*-
"""
Created on Wed Feb 16 11:19:35 2022

@author: Pinsel-Lampecinado Tony
@author: Le Bec Fabien

"""


import tkinter as tk
import tkinter.filedialog
from tkinter import ttk
from tileAPI import saveTileImage, getTileMatrixInformation, math
from altitude import altitude
from mesh import triangulate
import os

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg,
NavigationToolbar2Tk)
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
from mpl3d import glm
from mpl3d.mesh import Mesh
from mpl3d.camera import Camera
import meshio
import matplotlib.pyplot as plt

class Application(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)
        self.geometry("1920x1080")
        self.createWidgets()
        self.attributes('-fullscreen', True)
        self.tileMatrixInformation = getTileMatrixInformation("PM")
        
    # plot function is created for
    # plotting the graph in
    # tkinter window
    def plot(self, meshPath):
        fig = plt.figure(figsize=(7,7))
        ax = fig.add_axes([0,0,1,1], xlim=[-1,+1], ylim=[-1,+1], aspect=1)
        ax.axis("off")

        camera = Camera("ortho", scale=2)
        mesh = meshio.read(meshPath)
        vertices = mesh.points
        faces = mesh.cells[0].data
        vertices = glm.fit_unit_cube(vertices)
        mesh = Mesh(ax, camera.transform, vertices, faces,
                    cmap=plt.get_cmap("coolwarm"),  edgecolors=(0,0,0,0.25))
        camera.connect(ax, mesh.update)

        # creating the Tkinter canvas
        # containing the Matplotlib figure
        self.canvas = FigureCanvasTkAgg(fig, master = self)
        self.canvas.draw()

        # placing the canvas on the Tkinter window
        #self.canvas.get_tk_widget().pack()
        self.canvas.get_tk_widget().grid(row =0, column=3, rowspan=14, pady =60)

# fonction effectuant l'appel aux différents scripts
    def displayMesh(self):
        # Initialisation des arguments servant à récupérer les tuiles
        lat = round(float(self.latitudeEntry.get()), 6)
        lon = round(float(self.longitudeEntry.get()), 6)
        zoomLevel = int(8+self.zoomScale.get())
        resolution = int(self.elevationScale.get())
        dataType = 'ign'
        block = 0
        tile = self.tileMatrixInformation['tiles'][zoomLevel]

        self.progressBarText.set("Progression : récupération du fond de carte..")
        self.update()
        cornerCoordinates = saveTileImage(lat, lon, tile, dataType) # Retrieve tile image
        self.progressBar['value'] = 25

        latNO, lonNO = cornerCoordinates[0]
        latSE, lonSE = cornerCoordinates[1]

        output = str(lonNO) + "_" + str(latNO) + "_" + str(lonSE) + "_" + str(latSE) + "_" + str(int(math.sqrt(resolution)))
     
        self.progressBarText.set("Progression : données d'élévation..")
        self.update()
        altitude(lonNO, latNO, lonSE, latSE, resolution, "res/altitude/"+output+".xyz", self) # Retrieve tile cloud points elevation

        self.progressBarText.set("Progression : triangulation du mesh..")
        self.update()
        triangulate("res/altitude/"+output+".xyz", "res/mesh/"+output+".ply") # Triangulate cloud points
        self.progressBar['value'] = 90

        self.progressBarText.set("Progression : affichage..")
        self.update()
        self.plot("res/mesh/"+output+".ply")
        self.progressBar['value'] = 100
            

    def createWidgets(self):
        #self.mapCanvas = tk.Canvas(self, width =300, height =300, bg ='white')
        """self.photo = tk.PhotoImage(file="../res/carte_interface/carte_france.gif")
        self.mapCanvas.create_image(0,0, anchor = "nw", image=self.photo)"""
        self.quitButton = tk.Button(self,text='Quitter', font=("Arial", 20),command=self.closeWindow)
        self.displayButton = tk.Button(self,text='Afficher', font=("Arial", 20),command=self.displayMesh) # bouton lançant l'ensemble des processus de requête
        self.latitudeLabel = tk.Label(self, text = 'Latitude :', font=("Arial", 20))
        self.longitudeLabel = tk.Label(self, text = 'Longitude :', font=("Arial", 20))
        self.latitudeEntry = tk.Entry(self)
        self.latitudeEntry.insert(0, 45.52796757)
        self.longitudeEntry = tk.Entry(self)
        self.longitudeEntry.insert(0, 6.86008761)
        self.zoomScale = tk.Scale(self, from_=0, to=10, orient=tk.HORIZONTAL, label="Zoom", tickinterval=5, length=300)
        self.elevationScale = tk.Scale(self, from_=500, to=5000, orient=tk.HORIZONTAL, label="Nombre de points", resolution=500, tickinterval=1500, length=300)
        self.progressBar = tk.ttk.Progressbar(self, orient='horizontal', mode='determinate', length=220)
        self.progressBarText = tk.StringVar()
        self.progressBarLabel = tk.Label(self, textvariable=self.progressBarText)
        self.progressBarText.set("Progression :")

        self.displayButton.grid(row =0, column =0, padx =50, pady =5, columnspan =3)
        self.latitudeLabel.grid(row =1, column =0, pady =5)
        self.latitudeEntry.grid(row =1, column =1, pady =5)
        self.longitudeLabel.grid(row =2, column =0, pady =5)
        self.longitudeEntry.grid(row =2, column =1, pady =5)
        self.zoomScale.grid(row =3, column =0, padx =50, pady =20, columnspan =2)
        self.elevationScale.grid(row =4, column =0, padx =50, pady =20, columnspan =2)
        #self.mapCanvas.grid(row =5, column =0, rowspan =4, columnspan =3, padx =50, pady =5)
        self.progressBar.grid(row =6, column =0, padx =50, pady =10, columnspan =2)
        self.progressBarLabel.grid(row =7, column =0, padx =50, columnspan =2)
        self.quitButton.grid(row =8, column =0, padx =50, pady =60, columnspan =2)
    
    def closeWindow(self):
        #self.eraseTiles()
        self.destroy()

    def eraseTiles(self):
        path = "res/tile"
        for filename in os.listdir(path):
            os.remove(path + '/' + filename)

if __name__ == "__main__":
    app = Application()
    app.title("OSM Earth")
    app.mainloop()