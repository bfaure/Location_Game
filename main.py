import sys,os
import operator

import ast

from copy import deepcopy

from random import randint

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

class MapWidget(QWidget):
	def __init__(self,fname,parent=None):
		super(MapWidget,self).__init__()
		self.parent=parent
		self.fname=fname
		self.vertical=True
		self.last_x,self.last_y=None,None # mouse coordinates
		self.mouse_present=False
		self.setMouseTracking(True)

		self.pic=QPixmap(self.fname)
		width,height=self.pic.size().width(),self.pic.size().height()
		self.orig_dimensions=[0,0,width,height] # dimensions of original image
		self.cur_dimensions=deepcopy(self.orig_dimensions)
		self.cur_aspect_ratio=float(width)/float(height) # width/height ratio, used to scale image
		
		                 # upper left,     bottom right
		self.orig_bounds=[[-125.14,49.23],[-63.35,29.17]] # longitude, latitude of orig image
		self.cur_bounds=deepcopy(self.orig_bounds)

		# amount of longitude & latitude per image pixel
		self.long_per_pixel=float((self.orig_bounds[1][0]-self.orig_bounds[0][0])/self.orig_dimensions[2])
		self.lat_per_pixel=float((self.orig_bounds[0][1]-self.orig_bounds[1][1])/self.orig_dimensions[3])

		print 'long_per_pixel:',self.long_per_pixel
		print 'lat_per_pixel:',self.lat_per_pixel

		a,b,c,d=self.cur_dimensions
		rect=QRect(a,b,c,d)
		self.pic=self.pic.copy(rect)


	def enterEvent(self,event):
		# when mouse enters widget
		self.mouse_present=True

	def leaveEvent(self,event):
		# when mouse leaves widget
		self.mouse_present=False
		self.repaint()

	def mouseMoveEvent(self,event):
		# when mouse moves in widget
		self.last_x,self.last_y=event.x(),event.y()
		self.repaint()

	def get_region_bounds(self,desc):
		# desc is one of ['left','right','top','bottom']
		# returns the bounding longitude, latitude of the provided region
		full_bounds=deepcopy(self.cur_bounds)
		top_left,bottom_right=full_bounds[0],full_bounds[1]
		if desc=='left': # bottom right longitude different
			bottom_right[0]=top_left[0]-((top_left[0]-bottom_right[0])/2)
		elif desc=='right': # top left longitude different
			top_left[0]=top_left[0]-((top_left[0]-bottom_right[0])/2)
		elif desc=='top': # bottom right latitude different
			bottom_right[1]=bottom_right[1]+((top_left[1]-bottom_right[1])/2)
		elif desc=='bottom': # top left latitude different
			top_left[1]=bottom_right[1]+((top_left[1]-bottom_right[1])/2)
		else:
			raise Exception('get_region_bounds was passed invalid desc!')

		print 'Clicked in %s'%desc
		print 'Prior geo bounds:',self.cur_bounds
		print 'New geo bounds:  ',[top_left,bottom_right]
		return [top_left,bottom_right]

	def mousePressEvent(self,event):
		# when mouse clicks somewhere
		if self.mouse_present: # if in widget
			height,width=self.size().height(),self.size().width()
			if self.vertical:
				mid_pt=int(width)/2
				if self.last_x<=mid_pt:
					self.parent.region_clicked(self.get_region_bounds('left'))
				else:
					self.parent.region_clicked(self.get_region_bounds('right'))
			else:
				mid_pt=int(height)/2
				if self.last_y<=mid_pt:
					self.parent.region_clicked(self.get_region_bounds('top'))
				else:
					self.parent.region_clicked(self.get_region_bounds('bottom'))

	def zoom(self,new_geo_bounds):
		self.vertical=False if self.vertical else True

		cur_picture_bounds=deepcopy(self.cur_dimensions)
		cur_geo_bounds=deepcopy(self.cur_bounds)

		new_picture_bounds=deepcopy(self.cur_dimensions)

		# top left longitude component
		if cur_geo_bounds[0][0]!=new_geo_bounds[0][0]: 
			diff=new_geo_bounds[0][0]-cur_geo_bounds[0][0]
			pixel_offset=diff/self.long_per_pixel 
			new_picture_bounds[0]+=pixel_offset

		# bottom right longitude component
		if cur_geo_bounds[1][0]!=new_geo_bounds[1][0]: 
			diff=new_geo_bounds[1][0]-cur_geo_bounds[1][0]
			pixel_offset=diff/self.long_per_pixel
			new_picture_bounds[2]+=pixel_offset

		# top left latitude component
		if cur_geo_bounds[0][1]!=new_geo_bounds[0][1]:
			diff=cur_geo_bounds[0][1]-new_geo_bounds[0][1]
			pixel_offset=diff/self.lat_per_pixel
			new_picture_bounds[1]+=pixel_offset

		# bottom right latitude component
		if cur_geo_bounds[1][1]!=new_geo_bounds[1][1]:
			diff=cur_geo_bounds[1][1]-new_geo_bounds[1][1]
			pixel_offset=diff/self.lat_per_pixel 
			new_picture_bounds[3]-=pixel_offset

		new_picture_bounds=[int(e) for e in new_picture_bounds]

		print 'prior image bounds:',self.cur_dimensions
		print 'new image bounds:',new_picture_bounds

		self.cur_dimensions=new_picture_bounds
		self.cur_bounds=new_geo_bounds
		a,b,c,d=self.cur_dimensions
		self.cur_aspect_ratio=float(c)/float(d) # width/height, used for scaling in drawWidget
		rect=QRect(a,b,c,d)
		self.pic=QPixmap(self.fname)
		self.pic=self.pic.copy(rect)
		self.repaint()

	def restart(self):
		self.cur_dimensions=deepcopy(self.orig_dimensions)
		self.cur_bounds=deepcopy(self.orig_bounds)
		self.pic=QPixmap(self.fname)
		a,b,c,d=self.cur_dimensions
		rect=QRect(a,b,c,d)
		self.vertical=True
		self.pic=self.pic.copy(rect)
		self.repaint()

	def paintEvent(self,e):
		qp=QPainter()
		qp.begin(self)
		self.drawWidget(qp)
		qp.end()

	def drawWidget(self,qp):
		height,width=self.size().height(),self.size().width()

		pic_width=width-50
		pic_height=int(pic_width/self.cur_aspect_ratio)

		#self.pic=self.pic.scaled(width-50,height-50)
		self.pic=self.pic.scaled(pic_width,pic_height)
		qp.drawPixmap(0,0,self.pic)

		qp.setBrush(QColor(0,0,0))

		if self.vertical: # drawing vertical line
			mid_pt=int(pic_width)/2
			qp.drawLine(mid_pt,0,mid_pt,pic_height)
		else: # horizontal line
			mid_pt=int(pic_height)/2
			qp.drawLine(0,mid_pt,pic_width,mid_pt)

		if self.mouse_present:
			opaque_brush=QBrush(QColor(0,0,0,100))
			qp.setBrush(opaque_brush)

			if self.vertical:
				if self.last_x<=mid_pt:
					qp.drawRect(0,0,mid_pt,pic_height)
				else:
					qp.drawRect(mid_pt,0,pic_width,pic_height)
			else: 
				if self.last_y<=mid_pt:
					qp.drawRect(0,0,pic_width,mid_pt)
				else:
					qp.drawRect(0,mid_pt,pic_width,pic_height)


class MainWindow(QWidget):
	def __init__(self,places=None,parent=None):
		super(MainWindow,self).__init__()
		self.places=places
		self.init_vars()
		self.init_ui()

	def init_vars(self):
		#self.image_fname='data/maps/usa_map.png'
		self.image_fname='data/maps/usa_map_downscale.png'
		self.min_width=1200
		self.min_height=800
		self.score=1
		self.current_target=None

	def init_ui(self):
		
		self.setWindowTitle('Location Game')
		self.window_layout=QVBoxLayout(self)
		self.window_layout.addSpacing(25)
		self.map_widget=MapWidget(self.image_fname,self)
		main_row=QHBoxLayout()
		main_row.addStretch()
		main_row.addWidget(self.map_widget,2)
		main_row.addStretch()

		target_row=QHBoxLayout()
		target_label=QLabel('Target: ')
		self.target_box=QLineEdit()
		self.target_box.setEnabled(False)
		target_row.addWidget(target_label)
		target_row.addSpacing(30)
		target_row.addWidget(self.target_box)
		target_row.addStretch()

		self.toolbar=QMenuBar(self)
		self.toolbar.setFixedWidth(self.min_width)

		file_menu=self.toolbar.addMenu("File")
		file_menu.addAction("Quit",self.quit,QKeySequence("Ctrl+Q"))
		file_menu.addAction("Restart",self.restart,QKeySequence("Ctrl+R"))

		self.window_layout.addLayout(main_row,2)
		self.window_layout.addLayout(target_row)
		self.resize(self.min_width,self.min_height)
		self.update_picture()
		self.set_target()
		self.show()
		self.raise_()

	def restart(self):
		self.score=1
		self.set_target()
		self.map_widget.restart()

	def is_within(self,targ_bnd,rgn_bnd):
		if targ_bnd[0][0]>=rgn_bnd[0][0] and targ_bnd[1][0]<=rgn_bnd[1][0]:
			if targ_bnd[0][1]<=rgn_bnd[0][1] and targ_bnd[1][1]>=rgn_bnd[1][1]:
				return True
		return False

	def region_clicked(self,region_bounds):
		targ_bounds=self.current_target['coords']
		if self.is_within(targ_bounds,region_bounds)==True:
			print '%s is within the selection'%self.current_target['city']
			self.map_widget.zoom(region_bounds)
		else:
			print 'GAME OVER'

	def quit(self):
		sys.exit(1)

	def closeEvent(self,e):
		self.quit()

	def set_target(self):
		start_idx=-1*self.score
		end_idx=-1*self.score-10
		idx=randint(end_idx,start_idx)
		self.current_target=self.places[idx]
		self.target_box.setText('%s, %s'%(
			self.current_target['city'],
			self.current_target['state']))
		if type(self.current_target['coords']) is str:
			x=self.current_target['coords']
			x=ast.literal_eval(x)
			for i in range(2):
				for j in range(2):
					x[i][j]=float(x[i][j])
			self.current_target['coords']=x


	def update_picture(self):
		sys.stdout.write('\nImporting image...')
		self.map_widget.repaint()
		#self.current_frame=QPixmap(self.image_fname)
		#self.current_frame=self.current_frame.scaled(self.size().width()-50,self.size().height()-75)
		#self.map_widget.setPixmap(self.current_frame)
		sys.stdout.write(' done!\n')

	def resizeEvent(self,e):
		sys.stdout.write('\nImporting image...')
		#self.current_frame=QPixmap(self.image_fname)
		#self.current_frame=self.current_frame.scaled(self.size().width()-50,self.size().height()-75)
		#self.map_widget.setPixmap(self.current_frame)
		self.toolbar.setFixedWidth(self.size().width())
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
	
	pyqt_app=QApplication(sys.argv)
	_=MainWindow(places)
	sys.exit(pyqt_app.exec_())

if __name__ == '__main__':
	main()



