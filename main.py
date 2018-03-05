import sys,os
import operator

import json

from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import *
from PyQt4.QtGui import *

class Place:
	def __init__(self,city=None,state=None,population=None):
		self.city=city
		self.state=state
		self.population=int(population)
	def __str__(self):
		return '%s, %s population: %d'%(self.city,self.state,self.population)
	def __repr__(self):
		return self.__str__()

def import_population_data(fname='data/sub-est2016_all.csv'):
	f=open(fname,'r')
	text=f.read()
	lines=text.split('\n')
	places=[]
	for l in lines[1:]:
		if len(l)>5:
			items=l.split(',')
			if len(items)==19:			
				city=items[8]
				state=items[9]
				pop=items[18] # 2016 population estimate
				new_place=Place(city,state,pop)
				places.append(new_place)
	return places

def import_boundary_data(fname='data/admin_level_8.geojson'):
	data=json.load(open(fname))
	print data

class MainWindow(QWidget):
	def __init__(self,places=None,parent=None):
		super(MainWindow,self).__init__()
		self.places=places
		self.init_vars()
		self.init_ui()

	def init_vars(self):
		self.image_fname='data/maps/usa_map.png'
		self.min_width=1000
		self.min_height=800

	def init_ui(self):
		
		self.setWindowTitle('Location Game')
		self.window_layout=QVBoxLayout(self)
		self.main_image=QLabel()
		main_row=QHBoxLayout()
		main_row.addStretch()
		main_row.addWidget(self.main_image)
		main_row.addStretch()
		self.window_layout.addLayout(main_row,2)
		self.resize(self.min_width,self.min_height)
		self.update_picture()
		self.show()

	def update_picture(self):
		sys.stdout.write('\nImporting image...')
		self.current_frame=QPixmap(self.image_fname)
		self.current_frame=self.current_frame.scaled(self.size().width()-50,self.size().height()-50)
		self.main_image.setPixmap(self.current_frame)
		sys.stdout.write(' done!\n')

	def resizeEvent(self,e):
		sys.stdout.write('\nImporting image...')
		self.current_frame=QPixmap(self.image_fname)
		self.current_frame=self.current_frame.scaled(self.size().width()-50,self.size().height()-50)
		self.main_image.setPixmap(self.current_frame)
		sys.stdout.write(' done!\n')		



def main():
	sys.stdout.write('\n'*2)
	sys.stdout.write('='*25)
	sys.stdout.write('\n')

	sys.stdout.write('Importing data...')
	places=import_population_data()
	places.sort(key=operator.attrgetter('population'))
	sys.stdout.write(' loaded %d locations!'%len(places))

	sys.stdout.write('\n')

	if not os.path.exists('data/maps/usa_map.png'):
		sys.stdout.write('ERROR: Could not locate usa_map.png\n')
		sys.stdout.write('Download from https://drive.google.com/open?id=1zsNRWINdvrrSTeCG0q2IhZc-ak4krHaQ\n')
		sys.stdout.write('and place at inside data/maps/\n')
	else:
		sys.stdout.write('Map image found!\n')

	boundary_data=import_boundary_data()

	'''
	pyqt_app=QApplication(sys.argv)
	_=MainWindow()
	sys.exit(pyqt_app.exec_())
	'''

	sys.stdout.write('\n')
	sys.stdout.write('='*25)
	sys.stdout.write('\n'*2)

if __name__ == '__main__':
	main()



