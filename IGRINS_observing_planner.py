import tkinter as tk
from tkinter.filedialog import asksaveasfile, askopenfilename
import json
from astroquery.simbad import Simbad
import ds9_lib

rotator_zero_point = 193.0       #Instrument rotator zero point (Default East-West setting has PA = 90 deg.)

#Set up window for GUI
window = tk.Tk()
window.title("IGRINS Observing Planner")
frame = tk.Frame(window, height=500, width=600)

#Some global variables
n_guide_stars = tk.StringVar(value='20')

#Open ds9
ds9_lib.ds9.open()

#Class holds all info needed to observe a target
class Target:
	def __init__(self):
		self.ra = tk.StringVar(value='')
		self.dec = tk.StringVar(value='')
		self.dra = tk.StringVar(value='0.0')
		self.ddec = tk.StringVar(value='0.0')
		self.PA = tk.StringVar(value='90.0')
		self.dA = (tk.StringVar(value='-3.4'), tk.StringVar(value='0.0')) #(sl, sw)
		self.dB = (tk.StringVar(value='3.4'), tk.StringVar(value='0.0')) #(sl, sw)
		self.dG = (tk.StringVar(value='0.0'), tk.StringVar(value='0.0')) #(sl, sw)
		self.name = tk.StringVar(value='')
		self.rotator_setting = tk.StringVar(value='0.0')
		self.fov = tk.StringVar(value='6.0') #FOV of the finder chart image in arcmin
		self.update_rotator_setting()
	def simbad_lookup(self): #Lookup RA and Dec from from simbad
		result = Simbad.query_object(self.name.get()) #Lookup information from simbad
		self.ra.set(str(result["RA"].value.data[0]))
		self.dec.set(str(result["DEC"].value.data[0]))
	def update_rotator_setting(self, a=0, b=0, c=0): #When PA changes, update rotator setting (note: tkinter trace_add is weird and passes three variables a,b,c for some reason, just ignore them)
		delta_PA = 90.0 - float(self.PA.get())  #Default instrument East-west setting is 90 degrees in PA
		rotator_setting = rotator_zero_point - delta_PA  #Calculate setting to put the rotator at for a given PA
		if rotator_setting > rotator_zero_point + 180.0: rotator_setting = rotator_setting - 360.0  #Force rotator to be +/- 180 deg from the default PA
		self.rotator_setting.set(str(rotator_setting))
	def generate_dictionary(self): #Create dictionary for saving
		dictionary = { #Construction dictionary
			'ra': self.ra.get(),
			'dec': self.dec.get(),
			'dra': self.dra.get(),
			'ddec': self.ddec.get(),
			'PA': self.PA.get(),
			'dA': (self.dA[0].get(), self.dA[1].get()),
			'dB': (self.dB[0].get(), self.dB[1].get()),
			'dG': (self.dG[0].get(), self.dG[1].get()),
			'name': self.name.get(),
			'rotator_setting': self.rotator_setting.get(),
		}
		return dictionary
	def read_dictionary(self, dictionary): #Read dictionary for loading
		self.ra.set(dictionary['ra'])
		self.dec.set(dictionary['dec'])
		self.dra.set(dictionary['dra'])
		self.ddec.set(dictionary['ddec'])
		self.PA.set(dictionary['PA'])
		self.dA[0].set(dictionary['dA'][0])
		self.dA[1].set(dictionary['dA'][1])
		self.dB[0].set(dictionary['dB'][0])
		self.dB[1].set(dictionary['dB'][1])
		self.dG[0].set(dictionary['dG'][0])
		self.dG[1].set(dictionary['dG'][1])
		self.name.set(dictionary['name'])
		self.rotator_setting.set(dictionary['rotator_setting'])	





target = Target()
guidestar = Target()



def make_finder_chart(grab_image=True):
	ds9_lib.make_finder_chart_in_ds9(target.ra.get(), target.dec.get(), float(guidestar.dra.get()), float(guidestar.ddec.get()), float(guidestar.dG[0].get()), float(guidestar.dG[1].get()), float(target.PA.get()), float(target.fov.get()), grab_image=grab_image)

def remake_regions():
	make_finder_chart(grab_image=False)

def change_PA(a=0, b=0, c=0):
	target.update_rotator_setting()
	remake_regions()

def search_for_guide_stars():
	ds9_lib.search_for_guide_stars(target.ra.get(), target.dec.get(), int(n_guide_stars.get()), float(target.PA.get()))

def grab_guide_star():
	result = ds9_lib.grab_guide_star() #Use xpaget to grab information about the selected region
	result = result.split('(')[1].split(')')[0] #Do some string shenanigans to get the RA and Dec in the right format
	ra, dec = result.split(',')
	guidestar.ra.set(ra)
	guidestar.dec.set(dec)
	guideStarConvertRaDecToSlSw() #Update everything about the selected guide star
	remake_regions() #Remake the regions in the finder chart

def guideStarConvertDraDdecToSlSw():
	sl, sw = ds9_lib.convert_guide_star_from_dra_ddec_to_sl_sw(float(guidestar.dra.get()), float(guidestar.ddec.get()), float(target.PA.get()))
	guidestar.dG[0].set(str(sl))
	guidestar.dG[1].set(str(sw))

def guideStarConvertRaDecToSlSw():
	dra, ddec = ds9_lib.convert_guide_star_from_ra_dec_to_dra_ddec(guidestar.ra.get(), guidestar.dec.get(), target.ra.get(), target.dec.get())
	guidestar.dra.set(str(dra))
	guidestar.ddec.set(str(ddec))
	guideStarConvertDraDdecToSlSw() #Then convert dRa and dDec to sl and sw


def menusave():
	f = asksaveasfile(initialfile = 'save.json',
		defaultextension=".json",filetypes=[("All Files","*.*"),("Json Documents","*.json")])
	if f is None: #Error catch if no file is found
		return
	target_dictionary = target.generate_dictionary() #Generate dictionaries for each object and combine them into one
	guidestar_dictionary = guidestar.generate_dictionary()
	dictionary = {
		"target": target_dictionary,
		"guidestar": guidestar_dictionary
	}
	json_obj = json.dumps(dictionary, indent=4) #Serialize json
	f.write(json_obj)
	f.close()


def menuload():
	filename = askopenfilename(initialfile = 'save.json',
		defaultextension=".json",filetypes=[("All Files","*.*"),("Json Documents","*.json")])
	if filename == '': #Error catch if no file is found
		return
	with open(filename, 'r') as openfile: 		# Reading from json file
		json_object = json.load(openfile)
	target.read_dictionary(json_object['target'])
	guidestar.read_dictionary(json_object['guidestar'])

menubar = tk.Menu(window)
filemenu = tk.Menu(menubar, tearoff=0)
menubar.add_cascade(label ='File', menu = filemenu)
filemenu.add_command(label='Save', command=menusave)
filemenu.add_command(label='Load', command=menuload)
filemenu.add_separator() 
filemenu.add_command(label ='Exit', command=window.destroy)

#RA, Dec, and PA for target
ra_label = tk.Label(frame, text='RA (J2000):', font=("Arial", 12), anchor=tk.NE)
ra_entry = tk.Entry(frame, font=("Arial", 12), textvariable=target.ra)
ra_label.place(relx=0.03, rely=0.02)
ra_entry.place(relx=0.15, rely=0.02)
dec_label = tk.Label(frame, text='Dec (J2000):', font=("Arial", 12), anchor=tk.NE)
dec_entry = tk.Entry(frame, font=("Arial", 12), textvariable=target.dec)
dec_label.place(relx=0.03, rely=0.08)
dec_entry.place(relx=0.15, rely=0.08)
pa_label = tk.Label(frame, text='PA (deg):', font=("Arial", 12), anchor=tk.NE)
pa_entry = tk.Entry(frame, font=("Arial", 12), textvariable=target.PA)
pa_label.place(relx=0.03, rely=0.14)
pa_entry.place(relx=0.15, rely=0.14)
rotator_setting_text_label = tk.Label(frame, text='Rotator Setting (deg):', font=("Arial", 12), anchor=tk.NE)
rotator_setting_value_label = tk.Label(frame, font=("Arial", 12), anchor=tk.NE, textvariable=target.rotator_setting)
rotator_setting_text_label.place(relx=0.03, rely=0.19)
rotator_setting_value_label.place(relx=0.25, rely=0.19)
target.PA.trace_add('write', change_PA) #Add a trace_add callback to update the rotator setting value label below the PA text entry field


#A, B, and G positions
sl_label = tk.Label(frame, text='SL', font=("Arial", 12), anchor=tk.NE)
sw_label = tk.Label(frame, text='SW', font=("Arial", 12), anchor=tk.NE)
da_label = tk.Label(frame, text='dA', font=("Arial", 12), anchor=tk.NE)
db_label = tk.Label(frame, text='dB', font=("Arial", 12), anchor=tk.NE)
dg_label = tk.Label(frame, text='dG', font=("Arial", 12), anchor=tk.NE)
sl_label.place(relx=0.08, rely=0.5)
sw_label.place(relx=0.17, rely=0.5)
da_label.place(relx=0.02, rely=0.55)
db_label.place(relx=0.02, rely=0.60)
dg_label.place(relx=0.02, rely=0.65)
da_sl_entry = tk.Entry(frame, font=("Arial", 12), textvariable=target.dA[0])
da_sw_entry = tk.Entry(frame, font=("Arial", 12), textvariable=target.dA[1])
db_sl_entry = tk.Entry(frame, font=("Arial", 12), textvariable=target.dB[0])
db_sw_entry = tk.Entry(frame, font=("Arial", 12), textvariable=target.dB[1])
dg_sl_entry = tk.Entry(frame, font=("Arial", 12), textvariable=guidestar.dG[0])
dg_sw_entry = tk.Entry(frame, font=("Arial", 12), textvariable=guidestar.dG[1])
da_sl_entry.place(relx=0.06, rely=0.54, relwidth=0.08)
da_sw_entry.place(relx=0.15, rely=0.54, relwidth=0.08)
db_sl_entry.place(relx=0.06, rely=0.59, relwidth=0.08)
db_sw_entry.place(relx=0.15, rely=0.59, relwidth=0.08)
dg_sl_entry.place(relx=0.06, rely=0.64, relwidth=0.08)
dg_sw_entry.place(relx=0.15, rely=0.64, relwidth=0.08)






#Simbad lookup
simbad_name_label = tk.Label(frame, text='Simbad name:', font=("Arial", 12), anchor=tk.NE)
simbad_name_entry = tk.Entry(frame, font=("Arial", 12), textvariable=target.name)
simbad_button = tk.Button(frame, text='Lookup', command=target.simbad_lookup)
simbad_name_label.place(relx=0.42, rely=0.02)
simbad_name_entry.place(relx=0.56, rely=0.02)
simbad_button.place(relx=0.84, rely=0.015)

#make finder chart button
make_finder_chart_button = tk.Button(frame, text='Make Finder Chart', command=make_finder_chart)
make_finder_chart_button.place(relx=0.6, rely=0.18)
fov_label = tk.Label(frame, text='2MASS K Image FOV (arcmin):', font=("Arial", 12), anchor=tk.NE)
fov_entry = tk.Entry(frame, font=("Arial", 12), textvariable=target.fov)
fov_label.place(relx=0.53, rely=0.25, relwidth=0.3)
fov_entry.place(relx=0.83, rely=0.245, relwidth=0.08)




#Search guide star button
search_guide_star_button = tk.Button(frame, text='Search for Guide Stars', command=search_for_guide_stars)
search_guide_star_button.place(relx=0.45, rely=0.6)
#Grab guide star button
search_guide_star_button = tk.Button(frame, text='Grab Guide Star', command=grab_guide_star)
search_guide_star_button.place(relx=0.75, rely=0.6)

#Number of guide stars to grab
n_guide_stars_label = tk.Label(frame, text='# Stars', font=("Arial", 12), anchor=tk.NE)
n_guide_stars_entry = tk.Entry(frame, font=("Arial", 12), textvariable=n_guide_stars)
n_guide_stars_label.place(relx=0.69, rely=0.66, relwidth=0.08)
n_guide_stars_entry.place(relx=0.70, rely=0.657, relwidth=0.08)



#Guide star user parameters
guide_star_label = tk.Label(frame, text='Guide Star', font=("Arial", 12), anchor=tk.NE)
guide_star_dra_label = tk.Label(frame, text='dRA', font=("Arial", 12), anchor=tk.NE)
guide_star_ddec_label = tk.Label(frame, text='dDec', font=("Arial", 12), anchor=tk.NE)
guide_star_label.place(relx=0.08, rely=0.72)
guide_star_dra_label.place(relx=0.06, rely=0.76)
guide_star_ddec_label.place(relx=0.15, rely=0.76)
guide_star_dra_entry = tk.Entry(frame, font=("Arial", 12), textvariable=guidestar.dra)
guide_star_ddec_entry = tk.Entry(frame, font=("Arial", 12), textvariable=guidestar.ddec)
guide_star_dra_entry.place(relx=0.04, rely=0.80, relwidth=0.08)
guide_star_ddec_entry.place(relx=0.15, rely=0.80, relwidth=0.08)


#RA, Dec, and PA for guide star
guide_star_ra_label = tk.Label(frame, text='RA (J2000):', font=("Arial", 12), anchor=tk.NE)
guide_star_ra_entry = tk.Entry(frame, font=("Arial", 12), textvariable=guidestar.ra)
guide_star_ra_label.place(relx=0.03, rely=0.87)
guide_star_ra_entry.place(relx=0.15, rely=0.87)
guide_star_dec_label = tk.Label(frame, text='Dec (J2000):', font=("Arial", 12), anchor=tk.NE)
guide_star_dec_entry = tk.Entry(frame, font=("Arial", 12), textvariable=guidestar.dec)
guide_star_dec_label.place(relx=0.03, rely=0.93)
guide_star_dec_entry.place(relx=0.15, rely=0.93)
guide_star_simbad_name_label = tk.Label(frame, text='Simbad name:', font=("Arial", 12), anchor=tk.NE)
guide_star_simbad_name_entry = tk.Entry(frame, font=("Arial", 12), textvariable=guidestar.name)
guide_star_simbad_button = tk.Button(frame, text='Lookup', command=guidestar.simbad_lookup)
guide_star_simbad_name_label.place(relx=0.42, rely=0.87)
guide_star_simbad_name_entry.place(relx=0.56, rely=0.87)
guide_star_simbad_button.place(relx=0.84, rely=0.865)

guide_star_convert_dra_ddec_button = tk.Button(frame, text='Convert dRA dDec > dG SL SW', command=guideStarConvertDraDdecToSlSw)
guide_star_convert_ra_dec_button = tk.Button(frame, text='Convert RA Dec (J200) > dG SL SW', command=guideStarConvertRaDecToSlSw)
guide_star_convert_dra_ddec_button.place(relx=0.26, rely=0.793)
guide_star_convert_ra_dec_button.place(relx=0.43, rely=0.92)

#Main frame and loop
window.config(menu=menubar)
frame.pack()
window.mainloop()
