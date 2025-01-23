import tkinter as tk
from tkinter import ttk
from tkinter.filedialog import asksaveasfile, askopenfilename, askdirectory
import warnings
import json
import numpy as np
from astroquery.simbad import Simbad
import ds9_lib
from coordfuncs import *

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
		self.scan_rotation = tk.StringVar(value='Default PA') #Variable that sets of the slit scan PA rotation and columns are the default or +/- 90 degrees for the perpendicular scan
		self.scan_Nstep = tk.StringVar(value='15') #Number of steps in a single block (typically 15)
		self.scan_dstep = tk.StringVar(value='1.0') #Step size between each pointing in a block
		self.scan_perNod = tk.StringVar(value='3') #Number of steps per nod sequence between offs
		self.scan_Nrow = tk.StringVar(value='1') #Number of blocks in rows and columns (parallel with and perpendicular to the slit)
		self.scan_Ncol = tk.StringVar(value='1')
		self.scan_drow = tk.StringVar(value='15.0') #Step size of blocks in rows and columnns (parallel with and perpendicular to the slit) in arcsec, typically 15 arcsec but can be less for overlap
		self.scan_dcol= tk.StringVar(value='15.0')	
		self.scan_blocks = None #Variable to hold list of dictionaries that define slit scan blocks
		self.scan_finder_row = tk.StringVar(value=0) #Variables for position to put the slit when making a finder chart for a slitscan position
		self.scan_finder_col = tk.StringVar(value=0)
		self.scan_finder_pos = tk.StringVar(value=0)
		self.scan_script_targetshortname = tk.StringVar(value='') #Short name of target for generating observing scripts
		self.scan_script_off = (tk.StringVar(value='0.0'), tk.StringVar(value='0.0')) #OFF position (dRA, dDec)
	def simbad_lookup(self): #Lookup RA and Dec from from simbad
		result = Simbad.query_object(self.name.get()) #Lookup information from simbad
		# breakpoint()
		#coords = name_query(self.name.get())
		#self.ra.set(str(result["ra"].value.data[0]))
		#self.dec.set(str(result["dec"].value.data[0]))
		coord_obj = coords(result['ra'].item(), result['dec'].item())		
		ra, dec = coord_obj.showcoords().split()
		self.ra.set(ra)
		self.dec.set(dec)
		self.proper_motion[0].set(str(result['pmra'].value.data[0]))
		self.proper_motion[1].set(str(result['pmdec'].value.data[0]))
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
			'scan_rotation': self.scan_rotation.get(),
			'scan_Nstep': self.scan_Nstep.get(),
			'scan_dstep': self.scan_dstep.get(),
			'scan_perNod' : self.scan_perNod.get(),
			'scan_Nrow': self.scan_Nrow.get(),
			'scan_Ncol': self.scan_Ncol.get(),
			'scan_drow': self.scan_drow.get(),
			'scan_dcol': self.scan_dcol.get(),
			'scan_finder_row': self.scan_finder_row.get(),
			'scan_finder_col': self.scan_finder_col.get(),
			'scan_finder_pos': self.scan_finder_pos.get(),
			'scan_script_targetshortname': self.scan_script_targetshortname.get(),
			'scan_script_off': (self.scan_script_off[0].get(), self.scan_script_off[1].get()),
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
			self.scan_rotation.set(dictionary['scan_rotation'])
			self.scan_Nstep.set(dictionary['scan_Nstep'])
			self.scan_dstep.set(dictionary['scan_dstep'])
			self.scan_perNod.set(dictionary['scan_perNod'])
			self.scan_Nrow.set(dictionary['scan_Nrow'])
			self.scan_Ncol.set(dictionary['scan_Ncol'])
			self.scan_drow.set(dictionary['scan_drow'])
			self.scan_dcol.set(dictionary['scan_dcol'])
			self.scan_finder_row.set(dictionary['scan_finder_row'])
			self.scan_finder_col.set(dictionary['scan_finder_col'])
			self.scan_finder_pos.set(dictionary['scan_finder_pos'])
			self.scan_script_targetshortname.set(dictionary['scan_script_targetshortname'])
			self.scan_script_off[0].set(dictionary['scan_script_off'][0])
			self.scan_script_off[1].set(dictionary['scan_script_off'][1])
		except:
			warnings.warn('Warning: Having trouble reading in slitscan variables.  JSON file being read in might not be correct, or could be created by an older version of the observing planner')		
	def generate_slitscan_blocks(self):
		global guidestars, gs_index
		dg_sl = float(guidestars[gs_index].dG[0].get())
		dg_sw = float(guidestars[gs_index].dG[1].get())
		total_steps = int(self.scan_Nstep.get()) #Number of steps, rows, and cols
		perNod = int(self.scan_perNod.get()) #Number of steps per nod between offs
		nrows = int(self.scan_Nrow.get())
		ncols = int(self.scan_Ncol.get())
		drow = float(self.scan_drow.get()) #Distance between center of each step, row, col, or  in arcsec
		dcol = float(self.scan_dcol.get())
		dstep = float(self.scan_dstep.get())
		if self.scan_rotation.get() != 'Default PA': #Swap number and distance traveled for rows and columns if in perpeindicular rotation
			temp_nrows = nrows
			temp_ncols = ncols
			temp_drow = drow
			temp_dcol = dcol
			nrows = temp_ncols
			ncols = temp_nrows
			drow = temp_dcol
			dcol = temp_drow
		rows_start = ((nrows-1)/2) * drow #Calculate starting coordinate offsets
		cols_start = -((ncols-1)/2) * dcol
		steps_start = -((total_steps-1)/2) * dstep

		rows = []
		cols = []
		steps = []
		steps_centers = []
		#Generate block rows and columns pattern
		if nrows >= 2 and ncols >=2: #Need at least 2x2 rows and cols to do the zig zag pattern
			i=0
			while i+1 < nrows:
				j=0
				while j+1 < ncols:
					print(i, j)
					rows.append(i) #Do the zigzag between chunks of 4 rows and columns
					cols.append(j)
					rows.append(i+1)
					cols.append(j+1)
					rows.append(i+1)
					cols.append(j)
					rows.append(i)
					cols.append(j+1)
					j=j+2
				i=i+2
		if nrows % 2 == 1: #If there are an odd number of rows, fill out the last row by alternating columns, pattern is 1-3-0-2
			j=0
			while j < ncols:
				if ncols - j >= 4: #if 4 or more left
					cols.append(j+2)
					cols.append(j+0)
					cols.append(j+3)
					cols.append(j+1)
					rows.append(nrows-1)
					rows.append(nrows-1)
					rows.append(nrows-1)
					rows.append(nrows-1)
				elif ncols - j == 3: #if 3 left
					cols.append(j+1)
					cols.append(j+0)
					cols.append(j+2)
					rows.append(nrows-1)
					rows.append(nrows-1)
					rows.append(nrows-1)
				elif ncols - j == 2: #If 2 left
					cols.append(j+1)
					cols.append(j+0)
					rows.append(nrows-1)
					rows.append(nrows-1)
				elif ncols - j == 1: #If 1 left
					cols.append(j+0)
					rows.append(nrows-1)
				j = j + 4
			nrows = nrows-1 #Note the last row is filled out now so no need to repeat it for the last column so we subtract 1 here
		if ncols % 2 == 1:
			i=0
			while i < nrows: #1
				if nrows - i >= 4:  #if 4 or more left
					rows.append(i+2)
					rows.append(i+0)
					rows.append(i+3)
					rows.append(i+1)
					cols.append(ncols-1)
					cols.append(ncols-1)
					cols.append(ncols-1)
					cols.append(ncols-1)
				elif nrows - i == 3:
					rows.append(i+1)
					rows.append(i+0)
					rows.append(i+2)
					cols.append(ncols-1)
					cols.append(ncols-1)
					cols.append(ncols-1)
				elif nrows - i == 2:
					rows.append(i+1)
					rows.append(i+0)
					cols.append(ncols-1)
					cols.append(ncols-1)
				elif nrows - i == 1:
					rows.append(i+0)
					cols.append(ncols-1)
				i = i+4
		#Generate step pattern within blocks
		n_sets = int(total_steps / perNod)
		for i in range(n_sets):
			set_of_steps = []
			for j in range(perNod):
				set_of_steps.append(i+n_sets*j)
			for j in range(perNod, 0, -1):
				set_of_steps.append(i+n_sets*(j-1))
			steps.append(set_of_steps)
			steps_centers.append(steps_start + np.array(set_of_steps)*dstep)
		#Organize into list of offs, blocks, and positions into "chunks" between offs
		n_blocks = len(rows)
		blocks = []
		for i in range(0, n_blocks, 2):
			for j in range(n_sets):
				row_center = rows_start - rows[i]*drow
				col_center = cols_start + cols[i]*dcol
				sw = dg_sw + row_center + steps_centers[j]
				sl = dg_sl + col_center
				block1 = {"row":rows[i], "col":cols[i], "pos":steps[j], "sl":sl, "sw":sw}
				blocks.append(block1)
				if n_blocks > 1: #Error catch for when their is only one black
					row_center = rows_start - rows[i+1]*drow
					col_center = cols_start + cols[i+1]*dcol
					sw = dg_sw + row_center + steps_centers[j]
					sl = dg_sl + col_center
					block2 = {"row":rows[i+1], "col":cols[i+1],"pos":steps[j], "sl":sl, "sw":sw}
					blocks.append(block2)
					if i+2 == n_blocks-1: #Handle an odd number of blocks to nod between by mixing 3 instead of 2 blocks
						row_center = rows_start - rows[i+2]*drow
						col_center = cols_start + cols[i+2]*dcol
						sw = dg_sw + row_center + steps_centers[j]
						sl = dg_sl + col_center
						block3 = {"row":rows[i+2], "col":cols[i+2], "pos":steps[j], "sl":sl, "sw":sw}
						blocks.append(block3)
			if i+2 == n_blocks-1: #Handle an odd number of blocks to nod between by mixing 3 instead of 2 blocks
				break #and end the loop
		for block in blocks:
			block['row'] = nrows - block['row'] - 1
			block['col'] = ncols - block['col'] - 1
		if self.scan_rotation.get() == '+90 deg PA': #If perpendicular scan with PA at +90 deg compared to default (e.g. PA 90 is default so this would be PA of 180 deg)
			for block in blocks:
				#block['row'] = nrows - block['row'] - 1
				block['col'] = ncols - block['col'] - 1
				swap_row = block['row']
				swap_col = block['col']
				block['row'] = swap_col
				block['col'] = swap_row
				# for position in block['pos']:
				# 	position = 14 - position
		# elif self.scan_rotation.get() == '-90 deg PA':
		# 	for block in blocks:
		# 		block['row'] = nrows - block['row'] - 1
		# 		block['row'] = ncols - temp_col -1 #order inverted
		self.scan_blocks = blocks
	def generate_slitscan_table(self):

		self.generate_slitscan_blocks()

		#Test creating csv file
		print('Test making CSV file that can be imported into google sheets')
		lines = []
		#Define header line
		blank_line = ', , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , '
		#blank_line = ''
		header_line = 'PA, Night, Exp. time, Block 1, Block 2,'
		n_positions = int(len(self.scan_blocks[0]['pos'])/2)
		for j in range(n_positions):
			header_line += 'Pos '+str(j+1)+', '
		header_line += 'OFF, , '
		for j in range(n_positions):
			header_line += 'Block 1 Pos '+str(j)+', , '
		for j in range(n_positions, 0, -1):
			header_line += 'Block 1 Pos '+str(j)+', , '	
		header_line += 'OFF, , '	
		for j in range(n_positions):
			header_line += 'Block 2 Pos '+str(j+1)+', , '
		for j in range(n_positions, 0, -1):
			header_line += 'Block 2 Pos '+str(j)+', , '
		header_line += 'OFF, , Airmass, UT, Comments'
		lines.append(header_line)
		#Define observing plan
		for i in range(0, len(self.scan_blocks), 2):
			line = '' #start line to output
			line += self.PA.get() +', ' #PA
			line += ', ' #Date of night, leave blank
			line += ', ' #Exp time., leave blank
			line += str(self.scan_blocks[i]['row'])+'-'+str(self.scan_blocks[i]['col'])+', ' #Block 1
			line += str(self.scan_blocks[i+1]['row'])+'-'+str(self.scan_blocks[i+1]['col'])+', ' #Block 2
			for j in range(n_positions):
				line += str(self.scan_blocks[i]['pos'][j])+', ' #Position J (usually 1 2 3 for example)
			line += ', , ' #OFF
			for j in range(2*n_positions):
				line += '%0.2f'%self.scan_blocks[i]['sl']+', %0.2f'%self.scan_blocks[i]['sw'][j]+', ' #Block 1 Pos J
			line += ', , ' #OFF
			if i+1 < len(self.scan_blocks): #Catch if last "chunk" then just leave blanks
				for j in range(2*n_positions):
					line += '%0.2f'%self.scan_blocks[i+1]['sl']+', %0.2f'%self.scan_blocks[i+1]['sw'][j]+', ' #Block 2 Pos J			
			else:
				for j in range(2*n_positions):
					line += ', , '
			line += ', , ' #OFF	
			line += ', ' #Airmass, leave blank
			line += ', ' #UT, leave blank
			line += ', ' #Comments, leave blank
			lines.append(line) #Store line in list
			lines.append(blank_line) #Insert blank line for later data entry
		# for line in lines:
		# 	print(line)
		f = asksaveasfile(initialfile = 'slitscan.csv', #Save table for import into google sheet as an observing log plan
				defaultextension=".csv",filetypes=[("All Files","*.*"),("CSV Documents","*.csv")])
		if f is None: #Error catch if no file is found
			return
		for line in lines:
			f.write(f"{line}\n")
		f.close()
		# for i in range(rows):
		# 	for j in range(cols):
		# 		for k in range(steps):
		# 			label = '%02i'%i + '_' + '%02i'%j + '_' + '%02i'%k
		# 			print(label)
		# 			row_center = rows_start + i*drow
		# 			col_center = cols_start + j*dcol
		# 			step_center = steps_start + k*dstep
		# 			print(row_center, col_center, step_center)
	def get_scan_sl_sw(self, row=0, col=0, pos=0): #Return guidestar sl and sw for a given row, column, and position in a slitscan
		blocks_with_match_rows = [element for element in self.scan_blocks if element['row'] == row]
		blocks_with_matched_row_and_col = [element for element in blocks_with_match_rows if element['col'] == col]
		for block in blocks_with_matched_row_and_col:
			sl = block['sl']
			if block['pos'][0] == pos: #Check all three possible positions
				sw = block['sw'][0]
				return sl, sw
			if block['pos'][1] == pos:
				sw = block['sw'][1]
				return sl, sw
			if block['pos'][2] == pos:
				sw = block['sw'][2]
				return sl, sw
	def generate_slitscan_scripts(self):
		self.generate_slitscan_blocks()
		parent_dir = askdirectory()
		if parent_dir is None: #Error catch if no dir is found
			return
		off_lines = [] #Generate instrucitons to go to off which will form an independent script but also be appended to the end of a set of positions
		off_lines.append('SetObjName '+self.scan_script_targetshortname.get()+'_OFF')
		dra = float(self.scan_script_off[0].get()) #Moving telescope to off (requires <= 300 arcsec for some reason so we do it in increments if we move further)
		ddec = float(self.scan_script_off[1].get())
		while dra > 300.0:		
			off_lines.append('MoveTelescope 300 0')
			off_lines.append('WaitForSeconds 3')
			dra = dra - 300.0
		while dra < -300.0:		
			off_lines.append('MoveTelescope -300 0')
			off_lines.append('WaitForSeconds 3')
			dra = dra + 300.0
		while ddec > 300.0:		
			off_lines.append('MoveTelescope 0 300')
			off_lines.append('WaitForSeconds 3')
			ddec = ddec - 300.0
		while ddec < -300.0:		
			off_lines.append('MoveTelescope 0 -300')
			off_lines.append('WaitForSeconds 3')
			ddec = ddec + 300.0				
		off_lines.append('MoveTelescope '+str(dra)+' '+str(ddec))
		off_lines.append('WaitForSeconds 3')
		off_lines.append('StartGuideBox') #Start and stop guiding to take a single image
		off_lines.append('WaitForSeconds 1')
		off_lines.append('StopAG')
		off_lines.append('StartExposure')
		off_lines.append('WaitForExposureEnds')	
		dra = -float(self.scan_script_off[0].get()) #Moving telescope back to on position (requires <= 300 arcsec for some reason so we do it in increments if we move further)
		ddec = -float(self.scan_script_off[1].get())
		while dra > 300.0:		
			off_lines.append('MoveTelescope 300 0')
			off_lines.append('WaitForSeconds 3')
			dra = dra - 300.0
		while dra < -300.0:		
			off_lines.append('MoveTelescope -300 0')
			off_lines.append('WaitForSeconds 3')
			dra = dra + 300.0
		while ddec > 300.0:		
			off_lines.append('MoveTelescope 0 300')
			off_lines.append('WaitForSeconds 3')
			ddec = ddec - 300.0
		while ddec < -300.0:		
			off_lines.append('MoveTelescope 0 -300')
			off_lines.append('WaitForSeconds 3')
			ddec = ddec + 300.0	
		off_lines.append('MoveTelescope '+str(dra)+' '+str(ddec))
		off_lines.append('WaitForSeconds 3')
		off_lines.append('StartGuideBox') #Start and stop guiding to take a single image
		off_lines.append('WaitForSeconds 1')
		off_lines.append('StopAG')
		f = open(parent_dir+'/'+self.scan_script_targetshortname.get()+'_OFF.script', "w") #Save the OFF script
		for line in off_lines:
			f.write(f"{line}\n")
		f.close()
		scripts = [] #Store all scripts for later combining two block sets
		for scan_block in self.scan_blocks: #Now generate scrips for each set of block positions 123321 and append an off at the end
			lines = []
			lines.append('SetObjType TAR')
			sl = scan_block['sl']
			sw = scan_block['sw'][0]
			lines.append('SetAGPos %0.2f'%sl +' %0.2f'%sw)
			label = self.scan_script_targetshortname.get()+'_'+str(scan_block['row'])+'-'+str(scan_block['col'])+'-'+str(scan_block['pos'][0])
			lines.append('SetObjName '+label)
			text_to_say = 'To start the script for '+str(scan_block['row'])+'-'+str(scan_block['col'])+'-'+str(scan_block['pos'][0])+' (row-col-position), center the guide star on the autoguide position then click OK.'
			text_to_say = text_to_say.replace(' ', r'\ ') #Note needed to replace spaces with \[space] for script to use full sentence
			lines.append('WaitForYes '+text_to_say) 
			lines.append('StartGuideBox')
			lines.append('WaitForSeconds 15')
			lines.append('StartExposure')
			lines.append('WaitForExposureEnds')
			lines.append('StopAG')
			lines.append('WaitForSeconds 3')
			n_pos = len(scan_block['pos'])
			previous_sl = sl
			previous_sw = sw
			i = 1
			while i < n_pos:
				sw = scan_block['sw'][i]
				dra, ddec = ds9_lib.convert_from_sl_sw_to_dra_ddec(sl-previous_sl, sw-previous_sw, float(self.PA.get()))
				previous_sl = sl
				previous_sw = sw
				lines.append('SetObjName '+self.scan_script_targetshortname.get()+'_'+str(scan_block['row'])+'-'+str(scan_block['col'])+'-'+str(scan_block['pos'][i]))
				lines.append('SetAGPos %0.2f'%sl +' %0.2f'%sw)
				if not target.scan_rotation.get()=='+90 deg PA':
					lines.append('MoveTelescope %0.2f'%-dra +' %0.2f'%-ddec)
				else:
					lines.append('MoveTelescope %0.2f'%dra +' %0.2f'%ddec)
				lines.append('WaitForSeconds 3')
				lines.append('StartGuideBox')
				lines.append('StartExposure')
				lines.append('WaitForExposureEnds')
				if i < n_pos-1:
					if scan_block['pos'][i] == scan_block['pos'][i+1]:
						lines.append('StartExposure')
						lines.append('WaitForExposureEnds')	
						i = i+1
				lines.append('StopAG')
				lines.append('WaitForSeconds 3')
				i = i+1
			lines.extend(off_lines) #Add going to the off to the end of the script
			f = open(parent_dir+'/'+label+'.script', "w") #Save the block positions script
			for line in lines:
				f.write(f"{line}\n")
			f.close()
			scripts.append(lines)
		for i in range(0, len(scripts), 2): #Now generate scripts that can run two sets of scan blocks, for convenience
			lines = []
			lines.extend(scripts[i])
			lines.extend(scripts[i+1])
			scan_block_1 = self.scan_blocks[i]
			scan_block_2 = self.scan_blocks[i+1]
			label = self.scan_script_targetshortname.get()+'_'+str(scan_block_1['row'])+'-'+str(scan_block_1['col'])+'-'+str(scan_block_1['pos'][0])+'_'+str(scan_block_2['row'])+'-'+str(scan_block_2['col'])+'-'+str(scan_block_2['pos'][0])
			f = open(parent_dir+'/'+label+'.script', "w") #Save the block positions script
			for line in lines:
				f.write(f"{line}\n")
			f.close()			





target = Target()
guidestars = [Target(), Target(), Target(), Target(), Target(), Target(), Target(), Target(), Target(), Target()]
guidestars[gs_index].survey.set('Gaia DR2') #Set guidetar survey default



def make_finder_chart(grab_image=True):
	target.generate_slitscan_blocks()
	ds9_lib.make_finder_chart_in_ds9(target, guidestars[gs_index], grab_image=grab_image)


def remake_regions():
	make_finder_chart(grab_image=False)

def change_PA(a=0, b=0, c=0):
	target.update_rotator_setting()
	guideStarConvertDraDdecToSlSw()
	#remake_regions()

def search_for_guide_stars():
	ds9_lib.search_for_guide_stars(target.ra.get(), target.dec.get(), int(n_guide_stars.get()), float(target.PA.get()), guidestars[gs_index].survey.get(), guidestars[gs_index].use_proper_motion.get(), float(target.epoch.get()))

def grab_guide_star():
	result = ds9_lib.grab_guide_star() #Use xpaget to grab information about the selected region
	if type(result) is bytes: #Catch in case result is a byte string
		result = result.decode()
	result = result.split('(')[1].split(')')[0] #Do some string shenanigans to get the RA and Dec in the right format
	ra, dec = result.split(',')
	guidestars[gs_index].ra.set(ra)
	guidestars[gs_index].dec.set(dec)
	guideStarConvertRaDecToSlSw() #Update everything about the selected guide star
	remake_regions() #Remake the regions in the finder chart

def guideStarConvertDraDdecToSlSw():
	sl, sw = ds9_lib.convert_from_dra_ddec_to_sl_sw(float(guidestars[gs_index].dra.get()), float(guidestars[gs_index].ddec.get()), float(target.PA.get()))
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
epoch_label.place(relx=0.035, rely=0.19)
epoch_entry.place(relx=0.12, rely=0.187)


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
slitscan_header = tk.Label(frame, text='Slitscan', font=("Arial bold", 24), anchor=tk.N)
slitscan_checkbox = tk.Checkbutton(frame, text=r"Plot slitscan?", variable=target.use_slitscan)
slitscan_button = tk.Button(frame, text='Generate Slitscan Table', command=target.generate_slitscan_table)

slitscan_finder_row_label = tk.Label(frame, text="Row", font=("Arial", 12), anchor=tk.NE)
slitscan_finder_col_label = tk.Label(frame, text="Column", font=("Arial", 12), anchor=tk.NE)
slitscan_finder_pos_label = tk.Label(frame, text="Position", font=("Arial", 12), anchor=tk.NE)
slitscan_finder_row_entry = tk.Entry(frame, font=("Arial", 12), textvariable=target.scan_finder_row)
slitscan_finder_col_entry = tk.Entry(frame, font=("Arial", 12), textvariable=target.scan_finder_col)
slitscan_finder_pos_entry = tk.Entry(frame, font=("Arial", 12), textvariable=target.scan_finder_pos)

slitscan_rotation_label = tk.Label(frame, text="PA Rotation", font=("Arial", 12), anchor=tk.NE)
#slitscan_rotation_menu = ttk.Combobox(frame, textvariable=target.scan_rotation, values=('Default PA', '+90 deg PA', '-90 deg PA'), state='readonly')
slitscan_rotation_menu = ttk.Combobox(frame, textvariable=target.scan_rotation, values=('Default PA', '+90 deg PA'), state='readonly')
slitscan_N_label = tk.Label(frame, text='N', font=("Arial", 12), anchor=tk.NE)
slitscan_d_label = tk.Label(frame, text='dist. (arcsec)', font=("Arial", 12), anchor=tk.NE)
slitscan_perNod_label = tk.Label(frame, text="per nod", font=("Arial", 12), anchor=tk.NE)
slitscan_block_label = tk.Label(frame, text='Single Block', font=("Arial", 12), anchor=tk.NE)
slitscan_rows_label = tk.Label(frame, text='Rows', font=("Arial", 12), anchor=tk.NE)
slitscan_cols_label = tk.Label(frame, text='Columns', font=("Arial", 12), anchor=tk.NE)
slitscan_N_entry = tk.Entry(frame, font=("Arial", 12), textvariable=target.scan_Nstep)
slitscan_d_entry = tk.Entry(frame, font=("Arial", 12), textvariable=target.scan_dstep)
slitscan_perNod_entry = tk.Entry(frame, font=("Arial", 12), textvariable=target.scan_perNod)
slitscan_Nrow_entry = tk.Entry(frame, font=("Arial", 12), textvariable=target.scan_Nrow)
slitscan_drow_entry = tk.Entry(frame, font=("Arial", 12), textvariable=target.scan_drow)
slitscan_Ncol_entry = tk.Entry(frame, font=("Arial", 12), textvariable=target.scan_Ncol)
slitscan_dcol_entry = tk.Entry(frame, font=("Arial", 12), textvariable=target.scan_dcol)
slitscan_header.place(relx=0.0, rely=0.25, relwidth=1.0)
slitscan_button.place(relx=0.1, rely=0.47, relwidth=0.2)
slitscan_checkbox.place(relx=0.83, rely=0.30, relwidth=0.15)
slitscan_finder_row_label.place(relx=0.81, rely=0.33, relwidth=0.08)
slitscan_finder_col_label.place(relx=0.81, rely=0.36, relwidth=0.08)
slitscan_finder_pos_label.place(relx=0.81, rely=0.39, relwidth=0.08)
slitscan_finder_row_entry.place(relx=0.89, rely=0.33, relwidth=0.05)
slitscan_finder_col_entry.place(relx=0.89, rely=0.36, relwidth=0.05)
slitscan_finder_pos_entry.place(relx=0.89, rely=0.39, relwidth=0.05)

slitscan_rotation_label.place(relx=0.055, rely=0.305, relwidth=0.1)
slitscan_rotation_menu.place(relx=0.167, rely=0.302, relwidth=0.14)
slitscan_N_label.place(relx=0.065, rely=0.335, relwidth=0.08)
slitscan_d_label.place(relx=0.165, rely=0.335, relwidth=0.10)
slitscan_perNod_label.place(relx=0.27, rely=0.335, relwidth=0.06)
slitscan_block_label.place(relx=0.0, rely=0.3633, relwidth=0.1)
slitscan_rows_label.place(relx=0.0, rely=0.3933, relwidth=0.1)
slitscan_cols_label.place(relx=0.0, rely=0.4233, relwidth=0.1)
slitscan_N_entry.place(relx=0.1, rely=0.36, relwidth=0.08)
slitscan_d_entry.place(relx=0.18, rely=0.36, relwidth=0.08)
slitscan_perNod_entry.place(relx=0.26, rely=0.36, relwidth=0.08)
slitscan_Nrow_entry.place(relx=0.1, rely=0.39, relwidth=0.08)
slitscan_drow_entry.place(relx=0.18, rely=0.39, relwidth=0.08)
slitscan_Ncol_entry.place(relx=0.1, rely=0.42, relwidth=0.08)
slitscan_dcol_entry.place(relx=0.18, rely=0.42, relwidth=0.08)


slitscan_script_targetshortname_label = tk.Label(frame, text="Target Shortname", font=("Arial", 12), anchor=tk.NE)
slitscan_script_off_dra_label = tk.Label(frame, text="OFF dRA", font=("Arial", 12), anchor=tk.NE)
slitscan_script_off_ddec_label = tk.Label(frame, text="OFF dDec", font=("Arial", 12), anchor=tk.NE)
slitscan_script_targetshortname_entry = tk.Entry(frame, font=("Arial", 12), textvariable=target.scan_script_targetshortname)
slitscan_script_off_dra_entry = tk.Entry(frame, font=("Arial", 12), textvariable=target.scan_script_off[0])
slitscan_script_off_ddec_entry = tk.Entry(frame, font=("Arial", 12), textvariable=target.scan_script_off[1])
slitscan_script_button = tk.Button(frame, text='Generate Slitscan Scripts', command=target.generate_slitscan_scripts)
slitscan_script_targetshortname_label.place(relx=0.4, rely=0.35, relwidth=0.15)
slitscan_script_off_dra_label.place(relx=0.4, rely=0.38, relwidth=0.15)
slitscan_script_off_ddec_label.place(relx=0.4, rely=0.41, relwidth=0.15)
slitscan_script_targetshortname_entry.place(relx=0.55, rely=0.347, relwidth=0.15)
slitscan_script_off_dra_entry.place(relx=0.55, rely=0.377, relwidth=0.1)
slitscan_script_off_ddec_entry.place(relx=0.55, rely=0.407, relwidth=0.1)
slitscan_script_button.place(relx=0.47, rely=0.47, relwidth=0.225)

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
make_finder_chart_button.place(relx=0.59, rely=0.12)
update_finder_chart_button = tk.Button(frame, text='Update Finder Chart', command=remake_regions)
update_finder_chart_button.place(relx=0.77, rely=0.12)
survey_label = tk.Label(frame, text='Survey:', font=("Arial", 12), anchor=tk.NE)
survey_menu = ttk.Combobox(frame, textvariable=target.survey, values=('2MASS K-band', 'POSS2 IR'), state='readonly')
survey_label.place(relx=0.53, rely=0.17, relwidth=0.13)
survey_menu.place(relx=0.73, rely=0.165, relwidth=0.16)
fov_label = tk.Label(frame, text='Image FOV (arcmin):', font=("Arial", 12), anchor=tk.NE)
fov_entry = tk.Entry(frame, font=("Arial", 12), textvariable=target.fov)
fov_label.place(relx=0.53, rely=0.205, relwidth=0.2)
fov_entry.place(relx=0.73, rely=0.20, relwidth=0.16)




gidestar_header = tk.Label(frame, text='Guide Star', font=("Arial bold", 24), anchor=tk.N)
gidestar_header.place(relx=0.0, rely=0.53, relwidth=1.0)

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
