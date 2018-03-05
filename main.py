import sys
import operator

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

class MainWindow(QWidget):
	def __init__(self,places=None,parent=None):
		super(MainWindow,self).__init__()
		self.places=places
		self.init_ui()
	def init_ui(self):
		print 'here'
		self.show()

def main():
	sys.stdout.write('\n'*2)
	sys.stdout.write('='*25)
	sys.stdout.write('\n')

	sys.stdout.write('Importing data...')
	places=import_population_data()
	places.sort(key=operator.attrgetter('population'))
	sys.stdout.write(' loaded %d locations!'%len(places))

	sys.stdout.write('\n')
	sys.stdout.write('='*25)
	sys.stdout.write('\n'*2)

	pyqt_app=QApplication(sys.argv)
	_=MainWindow()
	sys.exit(pyqt_app.exec_())


if __name__ == '__main__':
	main()



