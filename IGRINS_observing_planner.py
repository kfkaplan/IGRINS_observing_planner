import tkinter as tk
from tkinter import ttk
from tkinter.filedialog import asksaveasfile, askopenfilename
import warnings
import json
from astroquery.simbad import Simbad
import ds9_lib

#Add thing to grab from simbad
Simbad.add_votable_fields('pmra', 'pmdec')

rotator_zero_point = 193.0       #Instrument rotator zero point (Default East-West setting has PA = 90 deg.)

#Set up window for GUI
window = tk.Tk()
window.title("IGRINS Observing Planner")
frame = tk.Frame(window, height=800, width=800)

#Some global variables
gs_index = 0 #Index of the current selected guide star
gs_index_tk = tk.StringVar(value='1')
n_guide_stars = tk.StringVar(value='20')

#Open ds9
ds9_lib.ds9.open()

def update_gs_index(a=0, b=0, c=0): #Update gs_index when user sets the guide star index to a different number in the menu
	global gs_index
	print('it is working')
	print(int(gs_index_tk.get()) - 1 )
	gs_index = int(gs_index_tk.get()) - 1 
	print(gs_index)

	# Update dG widgets
	dg_sl_entry.config(textvariable=guidestars[gs_index].dG[0])
	dg_sw_entry.config(textvariable=guidestars[gs_index].dG[1])
	# Update survey menu
	guide_star_survey_menu.config(textvariable=guidestars[gs_index].survey)
	# Update proper motion widgets
	guide_starpm_checkbox.config(variable=guidestars[gs_index].use_proper_motion)
	# Update dra and ddec (RA/Dec offsets) widgets
	guide_star_dra_entry.config(textvariable=guidestars[gs_index].dra)
	guide_star_ddec_entry.config(textvariable=guidestars[gs_index].ddec)
	# Update RA and Dec entries
	guide_star_ra_entry.config(textvariable=guidestars[gs_index].ra)
	guide_star_dec_entry.config(textvariable=guidestars[gs_index].dec)
	# Update name field
	guide_star_simbad_name_entry.config(textvariable=guidestars[gs_index].name)
	guide_star_simbad_button.config(command=guidestars[gs_index].simbad_lookup)

	window.update_idletasks()
	frame.update_idletasks()


#Class holds all info needed to observe a target
class Target:
	def __init__(self):
		self.ra = tk.StringVar(value='')
		self.dec = tk.StringVar(value='')
		self.dra = tk.StringVar(value='0.0')
		self.ddec = tk.StringVar(value='0.0')
		self.proper_motion = (tk.StringVar(value='0.0'), tk.StringVar(value='0.0')) #proper motion in RA and Dec (mas yr^-1)
		self.use_proper_motion = tk.BooleanVar(value=False)
		self.epoch = tk.StringVar(value='2000.0')
		self.PA = tk.StringVar(value='90.0')
		self.dA = (tk.StringVar(value='-3.33'), tk.StringVar(value='0.0')) #(sl, sw)
		self.dB = (tk.StringVar(value='3.33'), tk.StringVar(value='0.0')) #(sl, sw)
		self.dG = (tk.StringVar(value='0.0'), tk.StringVar(value='0.0')) #(sl, sw)
		self.name = tk.StringVar(value='')
		self.rotator_setting = tk.StringVar(value='0.0')
		self.fov = tk.StringVar(value='6.0') #FOV of the finder chart image in arcmin
		self.survey = tk.StringVar(value='2MASS K-band') #'2MASS K-band' or "POSS2 IR"
		self.epoch = tk.StringVar(value=2025.0) #Epoch used to find positions from proper motion
		self.update_rotator_setting()
		self.use_slitscan = tk.BooleanVar(value=False)
		self.scan_Nstep = tk.StringVar(value='15') #Number of steps in a single block (typically 15)
		self.scan_dstep = tk.StringVar(value='1.0') #Step size between each pointing in a block
		self.scan_Nrow = tk.StringVar(value='1') #Number of blocks in rows and columns (parallel with and perpendicular to the slit)
		self.scan_Ncol = tk.StringVar(value='1')
		self.scan_drow = tk.StringVar(value='15.0') #Step size of blocks in rows and columnns (parallel with and perpendicular to the slit) in arcsec, typically 15 arcsec but can be less for overlap
		self.scan_dcol= tk.StringVar(value='15.0')	
	def simbad_lookup(self): #Lookup RA and Dec from from simbad
		result = Simbad.query_object(self.name.get()) #Lookup information from simbad
		self.ra.set(str(result["RA"].value.data[0]))
		self.dec.set(str(result["DEC"].value.data[0]))
		self.proper_motion[0].set(str(result['PMRA'].value.data[0]))
		self.proper_motion[1].set(str(result['PMDEC'].value.data[0]))
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
			'proper_motion': (self.proper_motion[0].get(), self.proper_motion[1].get()),
			'epoch': self.epoch.get(),
			'PA': self.PA.get(),
			'dA': (self.dA[0].get(), self.dA[1].get()),
			'dB': (self.dB[0].get(), self.dB[1].get()),
			'dG': (self.dG[0].get(), self.dG[1].get()),
			'name': self.name.get(),
			'rotator_setting': self.rotator_setting.get(),
			'fov': self.fov.get(),
			'survey': self.survey.get(),
			'epoch': self.epoch.get(),
			'use_slitscan': self.use_slitscan.get(),
			'scan_Nstep': self.scan_Nstep.get(),
			'scan_dstep': self.scan_dstep.get(),
			'scan_Nrow': self.scan_Nrow.get(),
			'scan_Ncol': self.scan_Ncol.get(),
			'scan_drow': self.scan_drow.get(),
			'scan_dcol': self.scan_dcol.get(),
		}
		return dictionary
	def read_dictionary(self, dictionary): #Read dictionary for loading
		try:
			self.ra.set(dictionary['ra'])
			self.dec.set(dictionary['dec'])
		except:
			warnings.warn('Warning: Having trouble reading in "ra" and "dec".  JSON file being read in might not be correct, or could be created by an older version of the observing planner')
		try:
			self.dra.set(dictionary['dra'])
			self.ddec.set(dictionary['ddec'])
		except:
			warnings.warn('Warning: Having trouble reading in "dra" and "ddec".  JSON file being read in might not be correct, or could be created by an older version of the observing planner')
		try:
			self.proper_motion[0].set(dictionary['proper_motion'][0])
			self.proper_motion[1].set(dictionary['proper_motion'][0])
			self.epoch.set(dictionary['epoch'])
		except:
			warnings.warn('Warning: Having trouble reading in epoch or proper motion.  JSON file being read in might not be correct, or could be created by an older version of the observing planner')
		try:	
			self.PA.set(dictionary['PA'])
		except:
			warnings.warn('Warning: Having trouble reading in "PA".  JSON file being read in might not be correct, or could be created by an older version of the observing planner')
		try:
			self.epoch.set(dictionary['epoch'])
		except:
			warnings.warn('Warning: Having trouble reading in "epoch".  JSON file being read in might not be correct, or could be created by an older version of the observing planner')
		try:
			self.dA[0].set(dictionary['dA'][0])
			self.dA[1].set(dictionary['dA'][1])
			self.dB[0].set(dictionary['dB'][0])
			self.dB[1].set(dictionary['dB'][1])
			self.dG[0].set(dictionary['dG'][0])
			self.dG[1].set(dictionary['dG'][1])
		except:
			warnings.warn('Warning: Having trouble reading in guider coordinates.  JSON file being read in might not be correct, or could be created by an older version of the observing planner')
		try:
			self.name.set(dictionary['name'])
		except:
			warnings.warn('Warning: Having trouble reading in target name.  JSON file being read in might not be correct, or could be created by an older version of the observing planner')
		try:
			self.rotator_setting.set(dictionary['rotator_setting'])
		except:
			warnings.warn('Warning: Having trouble reading in rotator setting.  JSON file being read in might not be correct, or could be created by an older version of the observing planner')			
		try:
			self.fov.set(dictionary['fov'])
		except:
			warnings.warn('Warning: Having trouble reading in image FOV.  JSON file being read in might not be correct, or could be created by an older version of the observing planner')						
		try:
			self.survey.set(dictionary['survey'])
		except:
			warnings.warn('Warning: Having trouble reading in survey.  JSON file being read in might not be correct, or could be created by an older version of the observing planner')		
		try:
			self.use_slitscan.set(dictionary['use_slitscan'])
			self.scan_Nstep.set(dictionary['scan_N'])
			self.scan_dstep.set(dictionary['scan_dstep'])
			self.scan_Nrow.set(dictionary['scan_Nrow'])
			self.scan_Ncol.set(dictionary['scan_Ncol'])
			self.scan_drow.set(dictionary['scan_drow'])
			self.scan_dcol.set(dictionary['scan_dcol'])
		except:
			warnings.warn('Warning: Having trouble reading in slitscan variables.  JSON file being read in might not be correct, or could be created by an older version of the observing planner')		




target = Target()
guidestars = [Target(), Target(), Target(), Target(), Target(), Target(), Target(), Target(), Target(), Target()]
guidestars[gs_index].survey.set('Gaia DR2') #Set guidetar survey default



def make_finder_chart(grab_image=True):
 	ds9_lib.make_finder_chart_in_ds9(target, guidestars[gs_index], grab_image=grab_image)


def remake_regions():
	make_finder_chart(grab_image=False)

def change_PA(a=0, b=0, c=0):
	target.update_rotator_setting()
	remake_regions()

def search_for_guide_stars():
	ds9_lib.search_for_guide_stars(target.ra.get(), target.dec.get(), int(n_guide_stars.get()), float(target.PA.get()), guidestars[gs_index].survey.get(), guidestars[gs_index].use_proper_motion.get(), float(target.epoch.get()))

def grab_guide_star():
	result = ds9_lib.grab_guide_star() #Use xpaget to grab information about the selected region
	result = result.split('(')[1].split(')')[0] #Do some string shenanigans to get the RA and Dec in the right format
	ra, dec = result.split(',')
	guidestars[gs_index].ra.set(ra)
	guidestars[gs_index].dec.set(dec)
	guideStarConvertRaDecToSlSw() #Update everything about the selected guide star
	remake_regions() #Remake the regions in the finder chart

def guideStarConvertDraDdecToSlSw():
	sl, sw = ds9_lib.convert_guide_star_from_dra_ddec_to_sl_sw(float(guidestars[gs_index].dra.get()), float(guidestars[gs_index].ddec.get()), float(target.PA.get()))
	guidestars[gs_index].dG[0].set(str(sl))
	guidestars[gs_index].dG[1].set(str(sw))

def guideStarConvertRaDecToSlSw():
	dra, ddec = ds9_lib.convert_guide_star_from_ra_dec_to_dra_ddec(guidestars[gs_index].ra.get(), guidestars[gs_index].dec.get(), target.ra.get(), target.dec.get())
	guidestars[gs_index].dra.set(str(dra))
	guidestars[gs_index].ddec.set(str(ddec))
	guideStarConvertDraDdecToSlSw() #Then convert dRa and dDec to sl and sw


def menusave():
	f = asksaveasfile(initialfile = 'save.json',
		defaultextension=".json",filetypes=[("All Files","*.*"),("Json Documents","*.json")])
	if f is None: #Error catch if no file is found
		return
	target_dictionary = target.generate_dictionary() #Generate dictionaries for each object and combine them into one
	guidestar_dictionaries = []
	for i in range(len(guidestars)): #Loop through each guidestar
		guidestar_dictionaries.append(guidestars[i].generate_dictionary())		
	dictionary = {
		"target": target_dictionary,
		"guidestar": guidestar_dictionaries
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
	gs_index = 0
	input_guidestars = json_object['guidestar']
	for i in range(len(json_object['guidestar'])):
		guidestars.append(Target())
		guidestars[i].read_dictionary(json_object['guidestar'][i])


def break_debugger():
	breakpoint()


menubar = tk.Menu(window)
filemenu = tk.Menu(menubar, tearoff=0)
menubar.add_cascade(label ='File', menu = filemenu)
filemenu.add_command(label='Save', command=menusave)
filemenu.add_command(label='Load', command=menuload)
filemenu.add_command(label='Break', command=break_debugger)
filemenu.add_separator() 
filemenu.add_command(label ='Exit', command=window.destroy)

#RA, Dec, and PA for target
ra_label = tk.Label(frame, text='RA (J2000):', font=("Arial", 12), anchor=tk.NE)
ra_entry = tk.Entry(frame, font=("Arial", 12), textvariable=target.ra)
ra_label.place(relx=0.03, rely=0.02)
ra_entry.place(relx=0.12, rely=0.017)
dec_label = tk.Label(frame, text='Dec (J2000):', font=("Arial", 12), anchor=tk.NE)
dec_entry = tk.Entry(frame, font=("Arial", 12), textvariable=target.dec)
dec_label.place(relx=0.03, rely=0.06)
dec_entry.place(relx=0.12, rely=0.057)
pa_label = tk.Label(frame, text='PA (deg):', font=("Arial", 12), anchor=tk.NE)
pa_entry = tk.Entry(frame, font=("Arial", 12), textvariable=target.PA)
pa_label.place(relx=0.03, rely=0.10)
pa_entry.place(relx=0.12, rely=0.097)
rotator_setting_text_label = tk.Label(frame, text='Rotator Setting (deg):', font=("Arial", 12), anchor=tk.NE)
rotator_setting_value_label = tk.Label(frame, font=("Arial", 12), anchor=tk.NE, textvariable=target.rotator_setting)
rotator_setting_text_label.place(relx=0.03, rely=0.14)
rotator_setting_value_label.place(relx=0.22, rely=0.14)
target.PA.trace_add('write', change_PA) #Add a trace_add callback to update the rotator setting value label below the PA text entry field

epoch_label = tk.Label(frame, text='Epoch:', font=("Arial", 12), anchor=tk.NE)
epoch_entry = tk.Entry(frame, font=("Arial", 12), textvariable=target.epoch)
epoch_label.place(relx=0.035, rely=0.26)
epoch_entry.place(relx=0.12, rely=0.257)


#Proper motion for target
pm_ra_label = tk.Label(frame, text=r'pm RA (mas yr⁻¹):', font=("Arial", 12), anchor=tk.NE)
pm_dec_label = tk.Label(frame, text=r'pm Dec (mas yr⁻¹):', font=("Arial", 12), anchor=tk.NE)
pm_ra_entry =  tk.Entry(frame, font=("Arial", 12), textvariable=target.proper_motion[0])
pm_dec_entry = tk.Entry(frame, font=("Arial", 12), textvariable=target.proper_motion[1])
pm_ra_label.place(relx=0.32, rely=0.02)
pm_dec_label.place(relx=0.32, rely=0.06)
pm_ra_entry.place(relx=0.45, rely=0.017, relwidth=0.1)
pm_dec_entry.place(relx=0.45, rely=0.057, relwidth=0.1)
pm_checkbox = tk.Checkbutton(frame, text="Use proper motion?", variable=target.use_proper_motion)
pm_checkbox.place(relx=0.33, rely=0.10)



#Slit scan parameters
slitscan_checkbox = tk.Checkbutton(frame, text=r"Use slitscan?", variable=target.use_slitscan)
slitscan_N_label = tk.Label(frame, text='N', font=("Arial", 12), anchor=tk.NE)
slitscan_d_label = tk.Label(frame, text='dist. (arcsec)', font=("Arial", 12), anchor=tk.NE)
slitscan_block_label = tk.Label(frame, text='Single Block', font=("Arial", 12), anchor=tk.NE)
slitscan_rows_label = tk.Label(frame, text='Rows', font=("Arial", 12), anchor=tk.NE)
slitscan_cols_label = tk.Label(frame, text='Columns', font=("Arial", 12), anchor=tk.NE)
slitscan_N_entry = tk.Entry(frame, font=("Arial", 12), textvariable=target.scan_Nstep)
slitscan_d_entry = tk.Entry(frame, font=("Arial", 12), textvariable=target.scan_dstep)
slitscan_Nrow_entry = tk.Entry(frame, font=("Arial", 12), textvariable=target.scan_Nrow)
slitscan_drow_entry = tk.Entry(frame, font=("Arial", 12), textvariable=target.scan_drow)
slitscan_Ncol_entry = tk.Entry(frame, font=("Arial", 12), textvariable=target.scan_Ncol)
slitscan_dcol_entry = tk.Entry(frame, font=("Arial", 12), textvariable=target.scan_dcol)

slitscan_checkbox.place(relx=0.7, rely=0.4, relwidth=0.15)
slitscan_N_label.place(relx=0.645, rely=0.435, relwidth=0.1)
slitscan_d_label.place(relx=0.765, rely=0.435, relwidth=0.1)
slitscan_block_label.place(relx=0.6, rely=0.4633, relwidth=0.1)
slitscan_rows_label.place(relx=0.6, rely=0.4933, relwidth=0.1)
slitscan_cols_label.place(relx=0.6, rely=0.5233, relwidth=0.1)
slitscan_N_entry.place(relx=0.7, rely=0.46, relwidth=0.08)
slitscan_d_entry.place(relx=0.78, rely=0.46, relwidth=0.08)
slitscan_Nrow_entry.place(relx=0.7, rely=0.49, relwidth=0.08)
slitscan_drow_entry.place(relx=0.78, rely=0.49, relwidth=0.08)
slitscan_Ncol_entry.place(relx=0.7, rely=0.52, relwidth=0.08)
slitscan_dcol_entry.place(relx=0.78, rely=0.52, relwidth=0.08)




#A, B, and G positions
sl_label = tk.Label(frame, text='SL', font=("Arial", 12), anchor=tk.NE)
sw_label = tk.Label(frame, text='SW', font=("Arial", 12), anchor=tk.NE)
da_label = tk.Label(frame, text='dA', font=("Arial", 12), anchor=tk.NE)
db_label = tk.Label(frame, text='dB', font=("Arial", 12), anchor=tk.NE)
dg_label = tk.Label(frame, text='dG', font=("Arial", 12), anchor=tk.NE)
sl_label.place(relx=0.08, rely=0.58)
sw_label.place(relx=0.17, rely=0.58)
da_label.place(relx=0.03, rely=0.603)
db_label.place(relx=0.03, rely=0.633)
dg_label.place(relx=0.03, rely=0.663)
da_sl_entry = tk.Entry(frame, font=("Arial", 12), textvariable=target.dA[0])
da_sw_entry = tk.Entry(frame, font=("Arial", 12), textvariable=target.dA[1])
db_sl_entry = tk.Entry(frame, font=("Arial", 12), textvariable=target.dB[0])
db_sw_entry = tk.Entry(frame, font=("Arial", 12), textvariable=target.dB[1])
dg_sl_entry = tk.Entry(frame, font=("Arial", 12), textvariable=guidestars[gs_index].dG[0])
dg_sw_entry = tk.Entry(frame, font=("Arial", 12), textvariable=guidestars[gs_index].dG[1])
da_sl_entry.place(relx=0.06, rely=0.60, relwidth=0.08)
da_sw_entry.place(relx=0.15, rely=0.60, relwidth=0.08)
db_sl_entry.place(relx=0.06, rely=0.63, relwidth=0.08)
db_sw_entry.place(relx=0.15, rely=0.63, relwidth=0.08)
dg_sl_entry.place(relx=0.06, rely=0.66, relwidth=0.08)
dg_sw_entry.place(relx=0.15, rely=0.66, relwidth=0.08)






#Simbad lookup
simbad_name_label = tk.Label(frame, text='Simbad name:', font=("Arial", 12), anchor=tk.NE)
simbad_name_entry = tk.Entry(frame, font=("Arial", 12), textvariable=target.name)
simbad_button = tk.Button(frame, text='Lookup', command=target.simbad_lookup)
simbad_name_label.place(relx=0.57, rely=0.02)
simbad_name_entry.place(relx=0.68, rely=0.017)
simbad_button.place(relx=0.88, rely=0.015)

#make finder chart button
make_finder_chart_button = tk.Button(frame, text='Make Finder Chart', command=make_finder_chart)
make_finder_chart_button.place(relx=0.715, rely=0.18)
survey_label = tk.Label(frame, text='Survey:', font=("Arial", 12), anchor=tk.NE)
survey_menu = ttk.Combobox(frame, textvariable=target.survey, values=('2MASS K-band', 'POSS2 IR'), state='readonly')
survey_label.place(relx=0.53, rely=0.23, relwidth=0.15)
survey_menu.place(relx=0.73, rely=0.225, relwidth=0.16)
fov_label = tk.Label(frame, text='Image FOV (arcmin):', font=("Arial", 12), anchor=tk.NE)
fov_entry = tk.Entry(frame, font=("Arial", 12), textvariable=target.fov)
fov_label.place(relx=0.53, rely=0.265, relwidth=0.2)
fov_entry.place(relx=0.73, rely=0.26, relwidth=0.16)





#Search guide star button
search_guide_star_button = tk.Button(frame, text='Search for Guide Stars', command=search_for_guide_stars)
search_guide_star_button.place(relx=0.6, rely=0.6)
#Grab guide star button
grab_guide_star_button = tk.Button(frame, text='Grab Guide Star', command=grab_guide_star)
grab_guide_star_button.place(relx=0.83, rely=0.6)

#Number of guide stars to grab
n_guide_stars_label = tk.Label(frame, text='# Stars:', font=("Arial", 12), anchor=tk.NE)
n_guide_stars_entry = tk.Entry(frame, font=("Arial", 12), textvariable=n_guide_stars)
n_guide_stars_label.place(relx=0.61, rely=0.642, relwidth=0.08)
n_guide_stars_entry.place(relx=0.7, rely=0.642, relwidth=0.08)

guide_star_survey_label = tk.Label(frame, text='Survey:', font=("Arial", 12), anchor=tk.NE)
guide_star_survey_menu = ttk.Combobox(frame, textvariable=guidestars[gs_index].survey, values=('Gaia DR2', '2MASS point source'), state='readonly')
guide_star_survey_label.place(relx=0.54, rely=0.68, relwidth=0.15)
guide_star_survey_menu.place(relx=0.7, rely=0.677, relwidth=0.19)
guide_starpm_checkbox = tk.Checkbutton(frame, text="Use proper motion?", variable=guidestars[gs_index].use_proper_motion)
guide_starpm_checkbox.place(relx=0.635, rely=0.71)


#Guide star user parameters
guide_star_label = tk.Label(frame, text='Guide Star', font=("Arial", 12), anchor=tk.NE)
guide_star_dra_label = tk.Label(frame, text='dRA', font=("Arial", 12), anchor=tk.NE)
guide_star_ddec_label = tk.Label(frame, text='dDec', font=("Arial", 12), anchor=tk.NE)
guide_star_label.place(relx=0.08, rely=0.72)
guide_star_dra_label.place(relx=0.06, rely=0.76)
guide_star_ddec_label.place(relx=0.15, rely=0.76)
guide_star_dra_entry = tk.Entry(frame, font=("Arial", 12), textvariable=guidestars[gs_index].dra)
guide_star_ddec_entry = tk.Entry(frame, font=("Arial", 12), textvariable=guidestars[gs_index].ddec)
guide_star_dra_entry.place(relx=0.04, rely=0.80, relwidth=0.08)
guide_star_ddec_entry.place(relx=0.15, rely=0.80, relwidth=0.08)

guide_star_index_menu = ttk.Combobox(frame, textvariable=gs_index_tk, values=('1','2','3','4','5','6','7','8','9','10'), state='readonly')
guide_star_index_menu.place(relx=0.17, rely=0.72, relwidth=0.05)
gs_index_tk.trace('w',update_gs_index) #Run function update_gs_index when gs_index_tk changes



#RA, Dec, and PA for guide star
guide_star_ra_label = tk.Label(frame, text='RA (J2000):', font=("Arial", 12), anchor=tk.NE)
guide_star_ra_entry = tk.Entry(frame, font=("Arial", 12), textvariable=guidestars[gs_index].ra)
guide_star_ra_label.place(relx=0.03, rely=0.87)
guide_star_ra_entry.place(relx=0.15, rely=0.87)
guide_star_dec_label = tk.Label(frame, text='Dec (J2000):', font=("Arial", 12), anchor=tk.NE)
guide_star_dec_entry = tk.Entry(frame, font=("Arial", 12), textvariable=guidestars[gs_index].dec)
guide_star_dec_label.place(relx=0.03, rely=0.93)
guide_star_dec_entry.place(relx=0.15, rely=0.93)
guide_star_simbad_name_label = tk.Label(frame, text='Simbad name:', font=("Arial", 12), anchor=tk.NE)
guide_star_simbad_name_entry = tk.Entry(frame, font=("Arial", 12), textvariable=guidestars[gs_index].name)
guide_star_simbad_button = tk.Button(frame, text='Lookup', command=guidestars[gs_index].simbad_lookup)
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
