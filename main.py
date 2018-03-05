import sys,os
import operator

import json

from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import *
from PyQt4.QtGui import *

class Place:
	def __init__(self,city=None,state=None,population=None,coordinates=None):
		self.city=city
		self.state=state
		self.population=int(population)
		self.coordinates=coordinates
	def __str__(self):
		return '%s, %s population: %d'%(self.city,self.state,self.population)
	def __repr__(self):
		return self.__str__()

def import_population_data(fname='data/sub-est2016_all.csv'):
	f=open(fname,'r')
	text=f.read()
	lines=text.split('\n')
	place_dict={}
	place_list=[]
	for l in lines[1:]:
		if len(l)>5:
			items=l.split(',')
			if len(items)==19:			
				city=items[8]
				state=items[9]
				pop=items[18] # 2016 population estimate
				new_place=Place(city,state,pop)
				place_list.append(new_place)
				place_dict['%s, %s'%(city,state)]=new_place
	return place_list,place_dict

def import_boundary_data(place_dict,fname='data/admin_level_8.geojson'):
	data=json.load(open(fname))
	num_matched=0
	for i in range(len(data['features'])):
		cur=data['features'][i]
		if 'properties' in cur and 'geometry' in cur:
			geo=cur['geometry']
			if 'coordinates' in geo:
				coords=geo['coordinates']
			else: continue

			props=cur['properties']
			if 'name' in props and 'is_in:state' in props:
				city=props['name']
				state=props['is_in:state']
			else: continue

			city=city.replace('Township','township')

			# here we have city, state, and coordinates for a certain location
			# we need to match these to one of the items in the place_dict
			try:
				place_dict['%s, %s'%(city,state)].coordinates=coords 
				num_matched+=1
			except:
				try:
					place_dict['%s city, %s'%(city,state)].coordinates=coords 
					num_matched+=1
				except:
					try:
						place_dict['%s township, %s'%(city,state)].coordinates=coords 
						num_matched+=1
					except:
						try:
							place_dict['%s village, %s'%(city,state)].coordinates=coords 
							num_matched+=1
						except:
							try:
								place_dict['%s borough, %s'%(city,state)].coordinates=coords 
								num_matched+=1
							except:
								try:
									place_dict['%s town, %s'%(city,state)].coordinates=coords 
									num_matched+=1
								except:
									continue
									print "Couldn't match %s, %s"%(city,state)
	return num_matched

def save_compiled_data(place_list,fname='data/compiled.tsv'):
	f=open(fname,'w')
	num_saved=0
	for place in place_list:
		if place.coordinates!=None and place.population>2000:
			f.write('%s\t%s\t%d\t%s\n'%(
				place.city,
				place.state,
				place.population,
				str(place.coordinates)))
			num_saved+=1
	f.close()
	return num_saved

def boxify_coords(place_list):
	num_boxified=0
	for p in place_list:
		if p.coordinates!=None:
			min_lat,max_lat=None,None
			min_long,max_long=None,None
			for c in p.coordinates[0][0]:
				if c[0]<min_lat or min_lat==None:
					min_lat=c[0]
				if c[0]>max_lat or max_lat==None:
					max_lat=c[0]
				if c[1]<min_long or min_long==None:
					min_long=c[1]
				if c[1]>max_long or max_long==None:
					max_long=c[1]
			p.coordinates=[[min_lat,min_long],[max_lat,max_long]]
			num_boxified+=1
	return num_boxified

def compile_data():
	sys.stdout.write('\n'*2)
	sys.stdout.write('='*25)
	sys.stdout.write('\n')

	sys.stdout.write('Importing population data...')
	place_list,place_dict=import_population_data()
	place_list.sort(key=operator.attrgetter('population'))
	sys.stdout.write(' loaded %d locations!'%len(place_list))
	
	sys.stdout.write('\n')

	if not os.path.exists('data/admin_level_8.geojson'):
		sys.stdout.write('ERROR: Could not locate admin_level_8.geojson\n')
		return
	else:
		sys.stdout.write('Boundary Data found!\n')

	sys.stdout.write('Importing boundary data...')
	num_matched=import_boundary_data(place_dict)
	sys.stdout.write(' loaded %d boundaries!\n'%num_matched)

	sys.stdout.write('Fixing coordinates...')
	num_boxified=boxify_coords(place_list)
	sys.stdout.write(' fixed %d coordinates!\n'%num_boxified)

	sys.stdout.write('Saving compiled data...')
	num_saved=save_compiled_data(place_list)
	sys.stdout.write(' saved %d locations!\n'%num_saved)

	sys.stdout.write('\n')
	sys.stdout.write('='*25)
	sys.stdout.write('\n'*2)


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


def load_compiled_data(fname='data/compiled.tsv'):
	f=open(fname,'r')
	lines=f.read().split('\n')
	places=[]
	for l in lines:
		items=l.strip().split('\t')
		if len(items)==4:
			new_place={}
			new_place['city']=items[0]
			new_place['state']=items[1]
			new_place['pop']=items[2]
			new_place['coords']=items[3]
			places.append(new_place)
	return places


def main():

	places=load_compiled_data()
	print "Found %d cities."%len(places)

	if not os.path.exists('data/maps/usa_map.png'):
		sys.stdout.write('ERROR: Could not locate usa_map.png\n')
		sys.stdout.write('Download from https://drive.google.com/open?id=1zsNRWINdvrrSTeCG0q2IhZc-ak4krHaQ\n')
		sys.stdout.write('and place at \'data/maps/\'\n')
		return
	else:
		sys.stdout.write('Map image found!\n')

	'''
	pyqt_app=QApplication(sys.argv)
	_=MainWindow()
	sys.exit(pyqt_app.exec_())
	'''

if __name__ == '__main__':
	main()



